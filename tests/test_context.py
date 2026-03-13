from bots_airflow.context import TranslationContext, coerce_translation_context


def test_context_value_and_partner_value_accessors():
    context = TranslationContext(
        frompartner='DEMORETAIL',
        values={'route': 'internal'},
        partners={'DEMORETAIL': {'attr2': '900001'}},
    )

    assert context.value('route') == 'internal'
    assert context.partner_value('DEMORETAIL', 'attr2') == '900001'
    assert context.partner_value('UNKNOWN', 'attr2', 'fallback') == 'fallback'


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
