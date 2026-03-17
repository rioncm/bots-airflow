import csv
import importlib

from bots_airflow import GrammarSpec, TranslationContext, clear_import_registry, init, register_mapping

ORDERS_JSON = """[
  {"order_id": "1001", "sku": "SKU-001", "quantity": "2"},
  {"order_id": "1002", "sku": "SKU-002", "quantity": "5"}
]"""


def test_translate_with_imported_runtime_modules(tmp_path):
    grammar_in_module = importlib.import_module('tests.runtime_modules.grammars.json.orders_in')
    grammar_out_module = importlib.import_module('tests.runtime_modules.grammars.csv.order_lines_out')
    mapping_cls = importlib.import_module('tests.runtime_modules.mappings.order_lines').JsonOrdersToCsv

    translator = init(
        grammar_in=GrammarSpec(
            editype='json',
            messagetype='orders',
            module=grammar_in_module,
        ),
        grammar_out=GrammarSpec(
            editype='csv',
            messagetype='order_lines',
            module=grammar_out_module,
        ),
        map=mapping_cls,
    )

    result = translator.translate_text(
        ORDERS_JSON,
        output_filename='order_lines.csv',
        context=TranslationContext(
            reference='batch-001',
            values={'order_prefix': 'WEB-'},
        ),
    )

    assert result.output_text is not None
    lines = result.output_text.splitlines()
    first_row = next(csv.reader([lines[0]]))
    second_row = next(csv.reader([lines[1]]))

    assert first_row == ['WEB-1001', 'SKU-001', '2']
    assert second_row == ['WEB-1002', 'SKU-002', '5']
    assert result.ta_info['reference'] == 'batch-001'


def test_translate_with_external_module_path_strings(tmp_path):
    translator = init(
        grammar_in=GrammarSpec(
            editype='json',
            messagetype='orders',
            module='tests.runtime_modules.grammars.json.orders_in',
        ),
        grammar_out=GrammarSpec(
            editype='csv',
            messagetype='order_lines',
            module='tests.runtime_modules.grammars.csv.order_lines_out',
        ),
        map='tests.runtime_modules.mappings.order_lines_module',
    )

    input_path = tmp_path / 'orders.json'
    input_path.write_text(ORDERS_JSON)
    output_path = tmp_path / 'order_lines.csv'
    result = translator.translate(
        input_path,
        output_path,
        context=TranslationContext(
            reference='batch-002',
            values={'order_prefix': 'EDI-'},
        ),
    )

    lines = output_path.read_text().splitlines()
    first_row = next(csv.reader([lines[0]]))

    assert result.output_text is not None
    assert len(lines) == 2
    assert first_row == ['EDI-1001', 'SKU-001', '2']
    assert result.ta_info['reference'] == 'batch-002'


def test_registered_mapping_module_resolves_without_usersys_mode(tmp_path):
    clear_import_registry()
    register_mapping(
        'runtime.order_lines',
        'tests.runtime_modules.mappings.order_lines_module',
    )

    try:
        translator = init(
            grammar_in=GrammarSpec(
                editype='json',
                messagetype='orders',
                module='tests.runtime_modules.grammars.json.orders_in',
            ),
            grammar_out=GrammarSpec(
                editype='csv',
                messagetype='order_lines',
                module='tests.runtime_modules.grammars.csv.order_lines_out',
            ),
            map='runtime.order_lines',
        )

        output_path = tmp_path / 'order_lines.csv'
        input_path = tmp_path / 'orders.json'
        input_path.write_text(ORDERS_JSON)
        result = translator.translate(
            input_path,
            output_path,
            context=TranslationContext(
                reference='batch-003',
                values={'order_prefix': 'API-'},
            ),
        )

        assert result.output_text is not None
        assert output_path.exists()
        rows = list(csv.reader(output_path.read_text().splitlines()))
        assert rows[0] == ['API-1001', 'SKU-001', '2']
    finally:
        clear_import_registry()
