import pytest

from bots_airflow.context import TranslationContext, coerce_translation_context


def test_context_value_and_partner_value_accessors():
    context = TranslationContext(
        frompartner='DEMORETAIL',
        topartner='DEMOFULFILL',
        values={'route': 'internal', 'customer_id': '900001', 'blank_value': '   '},
        partners={
            'DEMORETAIL': {'attr2': '900001', 'blank_field': '   '},
            'DEMOFULFILL': {'attr1': '0645'},
        },
    )

    assert context.value('route') == 'internal'
    assert context.required_value('customer_id') == '900001'
    assert context.partner_value('DEMORETAIL', 'attr2') == '900001'
    assert context.required_partner_value('DEMORETAIL', 'attr2') == '900001'
    assert context.partner_value('from', 'attr2') == '900001'
    assert context.partner_value('frompartner', 'attr2') == '900001'
    assert context.required_partner_value('from', 'attr2') == '900001'
    assert context.partner_value('to', 'attr1') == '0645'
    assert context.partner_value('topartner', 'attr1') == '0645'
    assert context.partner_value('UNKNOWN', 'attr2', 'fallback') == 'fallback'

    with pytest.raises(ValueError, match='Required context.values'):
        context.required_value('missing_key')

    with pytest.raises(ValueError, match='was blank'):
        context.required_value('blank_value', allow_blank=False)

    with pytest.raises(ValueError, match='Required partner field'):
        context.required_partner_value('from', 'missing_field')

    with pytest.raises(ValueError, match='was blank'):
        context.required_partner_value('from', 'blank_field', allow_blank=False)

    empty_context = TranslationContext()
    with pytest.raises(ValueError, match='did not resolve to a partner id'):
        empty_context.required_partner_value('from', 'attr2')


def test_coerce_translation_context_from_mapping():
    context = coerce_translation_context(
        {
            'frompartner': 'DEMORETAIL',
            'values': {'flag': True},
        }
    )

    assert isinstance(context, TranslationContext)
    assert context.frompartner == 'DEMORETAIL'
    assert context.value('flag') is True
