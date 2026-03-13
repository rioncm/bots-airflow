from bots_airflow.context import TranslationContext
from bots_airflow.mapping import BaseMapping


class x12_to_json(BaseMapping):
    def translate(self, inn, out, *, context: TranslationContext, **kwargs):
        # Placeholder translation logic. The next pass should replace this with
        # real field extraction and out.put(...) calls.
        return {
            'message': 'This is a mock translation from X12 to JSON.',
            'frompartner': context.frompartner,
            'topartner': context.topartner,
            'metadata': dict(context.metadata),
        }
    
