from importlib import import_module

__all__ = ['LivingSpacesToOsasSscc']


def __getattr__(name):
    if name == 'LivingSpacesToOsasSscc':
        return import_module(f'{__name__}.ls_to_osas_sscc').LivingSpacesToOsasSscc
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


def __dir__():
    return sorted(list(globals()) + __all__)
