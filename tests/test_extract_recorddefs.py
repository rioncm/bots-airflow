from pathlib import Path

from bots_airflow.devtools.extract_recorddefs import build_recorddefs_module


def test_build_recorddefs_module_for_ls_850():
    fixture = Path(__file__).resolve().parents[1] / 'examples' / 'fixtures' / 'legacy_records004010.py'
    segments, extracted, rendered = build_recorddefs_module(
        source_reference=str(fixture),
        grammar_references=['bots_airflow.grammars.x12._850_ls_inbound4010'],
    )

    assert 'PO1' in segments
    assert 'N1' in extracted
    assert 'recorddefs =' in rendered
