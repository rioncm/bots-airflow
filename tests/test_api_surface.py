import inspect
import importlib.util
from dataclasses import fields

from bots_airflow import GrammarSpec, TranslationRequest, Translator, ensure_runtime
from bots_airflow.specs import coerce_grammar_spec


def test_public_api_no_longer_exposes_usersys_parameters():
    grammar_fields = {field.name for field in fields(GrammarSpec)}
    request_fields = {field.name for field in fields(TranslationRequest)}

    assert 'usersys_root' not in inspect.signature(Translator).parameters
    assert 'mapping_source' not in inspect.signature(Translator).parameters
    assert 'usersys_root' not in inspect.signature(ensure_runtime).parameters
    assert 'usersys_root' not in grammar_fields
    assert 'usersys_root' not in request_fields
    assert 'mapping_source' not in request_fields


def test_legacy_usersys_field_is_ignored_when_coercing_grammar_spec():
    spec = coerce_grammar_spec(
        {
            'editype': 'json',
            'messagetype': 'orders',
            'module': 'my_company_edi.grammars.json.orders_in',
            'usersys_root': 'legacy.usersys',
        }
    )

    assert spec.editype == 'json'
    assert spec.messagetype == 'orders'
    assert spec.module == 'my_company_edi.grammars.json.orders_in'


def test_public_package_does_not_bundle_project_flows():
    assert importlib.util.find_spec('bots_airflow.grammar') is None
    assert importlib.util.find_spec('bots_airflow.grammars') is None
    assert importlib.util.find_spec('bots_airflow.mappings') is None
    assert importlib.util.find_spec('bots_airflow.translate') is None


def test_runtime_bootstrap_does_not_create_usersys_stub(tmp_path):
    runtime = ensure_runtime(runtime_root=tmp_path / 'runtime')

    from botscore import state

    assert state.usersysimportpath is None
    assert not (runtime.runtime_root / '_runtime_import_stub').exists()
