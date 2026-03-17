import sys

from bots_airflow import clear_import_registry, register_grammar, register_mapping
from bots_airflow.registry import resolve_import
from bots_airflow.runner import _load_mapping_main


def test_registered_mapping_string_is_imported_lazily():
    clear_import_registry()
    sys.modules.pop('tests.runtime_modules.mappings.order_lines_module', None)
    register_mapping(
        'runtime.order_lines',
        'tests.runtime_modules.mappings.order_lines_module',
    )

    try:
        assert 'tests.runtime_modules.mappings.order_lines_module' not in sys.modules

        mapping_main = _load_mapping_main('runtime.order_lines')

        assert callable(mapping_main)
        assert 'tests.runtime_modules.mappings.order_lines_module' in sys.modules
    finally:
        clear_import_registry()


def test_registered_grammar_string_is_imported_lazily():
    clear_import_registry()
    sys.modules.pop('tests.runtime_modules.grammars.json.orders_in', None)
    register_grammar(
        'json',
        'orders',
        'tests.runtime_modules.grammars.json.orders_in',
    )

    try:
        assert 'tests.runtime_modules.grammars.json.orders_in' not in sys.modules

        resolved = resolve_import('grammars', 'json', 'orders')

        assert resolved is not None
        module, _module_file = resolved
        assert module.__name__ == 'tests.runtime_modules.grammars.json.orders_in'
        assert 'tests.runtime_modules.grammars.json.orders_in' in sys.modules
    finally:
        clear_import_registry()
