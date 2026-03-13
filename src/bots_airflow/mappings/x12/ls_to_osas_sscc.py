from __future__ import annotations

from bots.botsconfig import DONE

from bots_airflow.context import TranslationContext
from bots_airflow.mapping import BaseMapping


class LivingSpacesToOsasSscc(BaseMapping):
    def _setting(self, context: TranslationContext, key: str, default):
        value = context.value(key, None)
        if value is not None:
            return value
        return self.options.get(key, default)

    @staticmethod
    def _normalize(value) -> str:
        if value is None:
            return ''
        return str(value).strip()

    def _partner_value(self, context: TranslationContext, partner_id: str, field: str) -> str:
        return self._normalize(self.partner_value(context, partner_id, field, default=''))

    def _customer_id(self, inn, context: TranslationContext) -> str:
        explicit = self._normalize(self._setting(context, 'customer_id', ''))
        if explicit:
            return explicit

        partner_field = self._setting(context, 'customer_id_partner_field', 'attr2')
        default_customer_id = self._normalize(self._setting(context, 'default_customer_id', ''))

        for partner_id in (
            context.frompartner,
            context.topartner,
            inn.ta_info.get('frompartner'),
            inn.ta_info.get('topartner'),
        ):
            value = self._partner_value(context, partner_id, partner_field)
            if value:
                return value

        if default_customer_id:
            return default_customer_id

        raise ValueError(
            'Could not determine OSAS customer id. '
            f'Provide context.values["customer_id"], set context partner data for {partner_field}, '
            'or configure default_customer_id.'
        )

    def _po_number(self, inn, context: TranslationContext) -> str:
        explicit = self._normalize(self._setting(context, 'po_number', ''))
        if explicit:
            return explicit

        source = self._setting(context, 'po_number_source', 'beg03')
        if source == 'placeholder':
            placeholder = self._normalize(self._setting(context, 'po_number_placeholder', 'PO_NUM'))
            if placeholder:
                return placeholder
            raise ValueError('po_number_source is "placeholder" but no po_number_placeholder was provided.')

        po_number = self._normalize(inn.get({'BOTSID': 'ST'}, {'BOTSID': 'BEG', 'BEG03': None}))
        if po_number:
            return po_number

        raise ValueError('Inbound 850 is missing BEG03 purchase order number.')

    def _po1_identifiers(self, po1) -> dict[str, str]:
        identifiers = {}
        for qualifier_pos in range(106, 125, 2):
            qualifier_field = f'PO{qualifier_pos}'
            value_field = f'PO{qualifier_pos + 1}'

            qualifier = self._normalize(po1.get({'BOTSID': 'PO1', qualifier_field: None}))
            value = self._normalize(po1.get({'BOTSID': 'PO1', value_field: None}))

            if qualifier and value and qualifier not in identifiers:
                identifiers[qualifier] = value

        return identifiers

    def _serial_rows(self, inn, customer_id: str, po_number: str, context: TranslationContext):
        item_id_qualifier = self._setting(context, 'item_id_qualifier', 'SK')
        customer_part_qualifier = self._setting(context, 'customer_part_qualifier', 'VN')
        serial_qualifier = self._setting(context, 'serial_qualifier', 'GM')

        for po1 in inn.getloop({'BOTSID': 'ST'}, {'BOTSID': 'PO1'}):
            identifiers = self._po1_identifiers(po1)
            line_number = self._normalize(po1.get({'BOTSID': 'PO1', 'PO101': None}))

            item_id = (
                identifiers.get(item_id_qualifier)
                or identifiers.get(customer_part_qualifier)
            )
            customer_part_number = (
                identifiers.get(customer_part_qualifier)
                or identifiers.get(item_id_qualifier)
            )

            if not item_id:
                raise ValueError(
                    f'PO1 line {line_number or "?"} is missing a usable item identifier '
                    f'({item_id_qualifier}/{customer_part_qualifier}).'
                )

            for man in po1.getloop({'BOTSID': 'PO1'}, {'BOTSID': 'MAN'}):
                qualifier = self._normalize(man.get({'BOTSID': 'MAN', 'MAN01': None}))
                serial_number = self._normalize(man.get({'BOTSID': 'MAN', 'MAN02': None}))

                if qualifier != serial_qualifier or not serial_number:
                    continue

                yield {
                    'BOTSID': 'root',
                    'customer_id': customer_id,
                    'po_number': po_number,
                    'item_id': item_id,
                    'serial_number': serial_number,
                    'customer_part_number': customer_part_number,
                }

    def translate(self, inn, out, *, context: TranslationContext, **kwargs):
        customer_id = self._customer_id(inn, context)
        po_number = self._po_number(inn, context)
        serial_count = 0

        for row in self._serial_rows(inn, customer_id, po_number, context):
            out.putloop(row)
            serial_count += 1

        out.ta_info['reference'] = po_number
        out.ta_info['botskey'] = po_number
        out.ta_info['divtext'] = f'sscc:{serial_count}'

        if not serial_count:
            out.ta_info['statust'] = DONE
