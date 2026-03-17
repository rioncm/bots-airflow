from importlib import import_module

__all__ = ['json', 'x12']


def __getattr__(name):
    if name in __all__:
        return import_module(f'{__name__}.{name}')
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


def __dir__():
    return sorted(list(globals()) + __all__)
