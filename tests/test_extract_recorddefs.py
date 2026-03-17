from bots_airflow.devtools.extract_recorddefs import build_recorddefs_module


def test_build_recorddefs_module_for_external_grammar():
    segments, extracted, rendered = build_recorddefs_module(
        source_reference='tests.runtime_modules.legacy_recorddefs',
        grammar_references=['tests.runtime_modules.grammars.x12.sample_850'],
    )

    assert 'PO1' in segments
    assert 'BEG' in extracted
    assert 'recorddefs =' in rendered
