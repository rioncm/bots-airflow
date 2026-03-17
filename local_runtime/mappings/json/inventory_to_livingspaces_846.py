from __future__ import annotations

from datetime import date

from bots_airflow.context import TranslationContext
from bots_airflow.mapping import BaseMapping


class InventoryJsonToLivingSpaces846(BaseMapping):
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

    def _icn(self, context: TranslationContext) -> str:
        explicit = self._normalize(self._setting(context, 'icn', ''))
        if explicit:
            return explicit.zfill(6)

        if self.services.unique_value is not None:
            return self._normalize(self.services.unique_value('ls_846_icn')).zfill(6)

        fallback = self._normalize(self._setting(context, 'fallback_icn', '000001'))
        if fallback:
            return fallback.zfill(6)

        raise ValueError('Could not determine 846 control number (icn).')

    def _as_of_date(self, context: TranslationContext) -> str:
        explicit = self._normalize(self._setting(context, 'as_of_date', ''))
        if explicit:
            return explicit
        return date.today().strftime('%Y%m%d')

    def translate(self, inn, out, *, context: TranslationContext, **kwargs):
        sender_name = self._setting(context, 'sender_name', 'Pleasant Mattress')
        sender_id_code = self._setting(context, 'sender_id_code', 'ASSIGNED_ID')
        open_qty = self._setting(context, 'open_qty', '999')
        qty_qualifier = self._setting(context, 'qty_qualifier', '17')
        date_qualifier = self._setting(context, 'date_qualifier', '169')
        reference_prefix = self._setting(context, 'reference_prefix', 'ref-')

        icn = self._icn(context)
        as_of_date = self._as_of_date(context)

        out.envelope_content[0]['ISA12'] = '00401'
        out.envelope_content[1]['GS08'] = '004010'

        out.put({
            'BOTSID': 'ST',
            'ST01': '846',
            'ST02': icn,
        })

        out.put({'BOTSID': 'ST'}, {
            'BOTSID': 'BIA',
            'BIA01': '00',
            'BIA02': 'SI',
            'BIA03': f'{reference_prefix}{icn}',
            'BIA04': as_of_date,
        })

        n1loop = out.putloop({'BOTSID': 'ST'}, {'BOTSID': 'N1'})
        n1loop.put({
            'BOTSID': 'N1',
            'N101': 'SU',
            'N102': sender_name,
            'N103': '92',
            'N104': sender_id_code,
        })

        line_count = 0
        for item in inn.getloop({'BOTSID': 'root'}):
            line_count += 1

            linloop = out.putloop({'BOTSID': 'ST'}, {'BOTSID': 'LIN'})
            linloop.put({
                'BOTSID': 'LIN',
                'LIN01': str(line_count),
                'LIN02': 'UP',
                'LIN03': item.record.get('sku_upc', ''),
                'LIN04': 'VN',
                'LIN05': item.record.get('item_sku', ''),
                'LIN06': 'SK',
                'LIN07': item.record.get('customer_sku', ''),
            })
            linloop.put({'BOTSID': 'LIN'}, {
                'BOTSID': 'QTY',
                'QTY01': qty_qualifier,
                'QTY02': open_qty,
            })
            linloop.put({'BOTSID': 'LIN'}, {
                'BOTSID': 'DTM',
                'DTM01': date_qualifier,
                'DTM02': as_of_date,
            })

        out.put({'BOTSID': 'ST'}, {
            'BOTSID': 'CTT',
            'CTT01': str(line_count),
        })

        out.put({'BOTSID': 'ST'}, {
            'BOTSID': 'SE',
            'SE01': out.getcount() + 1,
            'SE02': icn,
        })
