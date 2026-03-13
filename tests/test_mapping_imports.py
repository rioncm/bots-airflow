import importlib
import sys


def test_json_mapping_import_does_not_eagerly_load_x12():
    sys.modules.pop('bots_airflow.mappings', None)
    sys.modules.pop('bots_airflow.mappings.x12', None)
    sys.modules.pop('bots_airflow.mappings.x12.pass_through', None)

    module = importlib.import_module('bots_airflow.mappings.json.inventory_to_livingspaces_846')

    assert module.InventoryJsonToLivingSpaces846 is not None
    assert 'bots_airflow.mappings.x12' not in sys.modules
    assert 'bots_airflow.mappings.x12.pass_through' not in sys.modules


def test_x12_pass_through_is_resolved_lazily():
    sys.modules.pop('bots_airflow.mappings.x12', None)
    sys.modules.pop('bots_airflow.mappings.x12.pass_through', None)

    module = importlib.import_module('bots_airflow.mappings.x12')

    assert 'bots_airflow.mappings.x12.pass_through' not in sys.modules

    pass_through = module.pass_through

    assert callable(pass_through)
    assert 'bots_airflow.mappings.x12.pass_through' in sys.modules
