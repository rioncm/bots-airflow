
try:
    from airflow.decorators import task
except ImportError:  # pragma: no cover - illustrative fallback for local imports.
    def task():
        def decorator(func):
            return func
        return decorator


from bots_airflow import TranslationContext, init
from local_runtime.grammar.livingspaces import x12_in
from local_runtime.grammar.pminc import json_out
from local_runtime.translate.livingspaces import x12_to_json


@task()
def mock_dag(edi_file_path: str, output_file_path: str) -> None:
    translator = init(
        grammar_in=x12_in,
        grammar_out=json_out,
        map=x12_to_json,
    )
    translator.translate(
        edi_file_path,
        output_file_path,
        context=TranslationContext(
            frompartner='DEMORETAIL',
            topartner='DEMOFULFILL',
            metadata={'source': 'dag_mock'},
            partners={
                'DEMORETAIL': {
                    'customer_id': '900001',
                },
            },
        ),
    )
