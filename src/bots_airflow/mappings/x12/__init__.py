from importlib import import_module

__all__ = ['LivingSpacesToOsasSscc', 'pass_through']


def __getattr__(name):
    if name == 'LivingSpacesToOsasSscc':
        return import_module(f'{__name__}.ls_to_osas_sscc').LivingSpacesToOsasSscc
    if name == 'pass_through':
        return import_module(f'{__name__}.pass_through').main
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


def __dir__():
    return sorted(list(globals()) + __all__)
