from django.utils import translation

from bots_airflow.bootstrap import _install_django_translation_compat


def test_install_django_translation_compat_adds_legacy_aliases():
    _install_django_translation_compat()

    assert translation.ugettext is translation.gettext
    assert translation.ugettext_lazy is translation.gettext_lazy
    assert translation.ungettext is translation.ngettext
    assert translation.ungettext_lazy is translation.ngettext_lazy
    assert translation.ugettext_noop is translation.gettext_noop
