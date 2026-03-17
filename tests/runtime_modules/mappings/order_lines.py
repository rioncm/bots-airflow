from bots_airflow.context import TranslationContext
from bots_airflow.mapping import BaseMapping


class JsonOrdersToCsv(BaseMapping):
    def translate(self, inn, out, *, context: TranslationContext, **kwargs):
        order_prefix = str(context.value('order_prefix', ''))
        row_count = 0

        for item in inn.getloop({'BOTSID': 'root'}):
            out.putloop(
                {
                    'BOTSID': 'root',
                    'order_id': f"{order_prefix}{item.record.get('order_id', '')}",
                    'sku': item.record.get('sku', ''),
                    'quantity': str(item.record.get('quantity', '')),
                }
            )
            row_count += 1

        out.ta_info['reference'] = context.reference
        out.ta_info['botskey'] = str(row_count)
        return {'row_count': row_count}

