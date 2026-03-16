import importlib
import sys


def test_json_mapping_import_does_not_eagerly_load_x12():
    sys.modules.pop('bots_airflow.mappings', None)
    sys.modules.pop('bots_airflow.mappings.x12', None)
    sys.modules.pop('bots_airflow.mappings.x12.ls_to_osas_sscc', None)

    module = importlib.import_module('bots_airflow.mappings.json.inventory_to_livingspaces_846')

    assert module.InventoryJsonToLivingSpaces846 is not None
    assert 'bots_airflow.mappings.x12' not in sys.modules
    assert 'bots_airflow.mappings.x12.ls_to_osas_sscc' not in sys.modules


def test_x12_mapping_export_is_resolved_lazily():
    sys.modules.pop('bots_airflow.mappings.x12', None)
    sys.modules.pop('bots_airflow.mappings.x12.ls_to_osas_sscc', None)

    module = importlib.import_module('bots_airflow.mappings.x12')

    assert 'bots_airflow.mappings.x12.ls_to_osas_sscc' not in sys.modules

    mapping_cls = module.LivingSpacesToOsasSscc

    assert callable(mapping_cls)
    assert 'bots_airflow.mappings.x12.ls_to_osas_sscc' in sys.modules
