import inspect
from dataclasses import fields

from bots_airflow import GrammarSpec, TranslationRequest, Translator, ensure_runtime
from bots_airflow.grammar.pminc import json_out
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
            'messagetype': 'inventory_846_json',
            'module': 'bots_airflow.grammars.json.inventory_846_json',
            'usersys_root': 'legacy.usersys',
        }
    )

    assert spec.editype == 'json'
    assert spec.messagetype == 'inventory_846_json'
    assert spec.module == 'bots_airflow.grammars.json.inventory_846_json'


def test_pminc_json_out_uses_first_class_grammar_module():
    assert json_out.module == 'bots_airflow.grammars.json.jsonnocheck'


def test_runtime_bootstrap_does_not_create_usersys_stub(tmp_path):
    runtime = ensure_runtime(runtime_root=tmp_path / 'runtime')

    from botscore import state

    assert state.usersysimportpath is None
    assert not (runtime.runtime_root / '_runtime_import_stub').exists()
