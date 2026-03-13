import csv
from pathlib import Path

from bots_airflow import TranslationContext, init
from bots_airflow.grammar.livingspaces import x12_846_out, x12_in
from bots_airflow.grammar.osas import inventory_json_in, sscc_out
from bots_airflow.mappings.json.inventory_to_livingspaces_846 import (
    InventoryJsonToLivingSpaces846,
)
from bots_airflow.mappings.x12.ls_to_osas_sscc import LivingSpacesToOsasSscc


FIXTURES = Path(__file__).resolve().parents[1] / 'examples' / 'fixtures'


def test_ls_850_to_sscc_translation_smoke(tmp_path):
    translator = init(
        grammar_in=x12_in,
        grammar_out=sscc_out,
        map=LivingSpacesToOsasSscc,
    )

    output_path = tmp_path / 'sscc.csv'
    result = translator.translate(
        FIXTURES / 'sample_850.edi',
        output_path,
        context=TranslationContext(
            frompartner='DEMORETAIL',
            topartner='DEMOFULFILL',
            partners={'DEMORETAIL': {'attr2': '900001'}},
        ),
    )

    lines = output_path.read_text().splitlines()
    first_row = next(csv.reader([lines[0]]))

    assert result.output_text is not None
    assert len(lines) == 34
    assert first_row == [
        '900001',
        'PO-EXAMPLE-001',
        '100001',
        '00000000000000000001',
        'ITEM-DEMO-001',
    ]
    assert result.ta_info['reference'] == 'PO-EXAMPLE-001'


def test_inventory_json_to_846_translation_smoke(tmp_path):
    translator = init(
        grammar_in=inventory_json_in,
        grammar_out=x12_846_out,
        map=InventoryJsonToLivingSpaces846,
    )

    output_path = tmp_path / 'inventory_846.edi'
    result = translator.translate(
        FIXTURES / 'sample_inventory_846.json',
        output_path,
        context=TranslationContext(
            values={
                'icn': '123456',
                'as_of_date': '20260313',
            },
        ),
    )

    output_text = output_path.read_text()

    assert result.output_text is not None
    assert 'ST*846*123456~' in output_text
    assert 'BIA*00*SI*ref-123456*20260313~' in output_text
    assert output_text.count('LIN*') >= 10
