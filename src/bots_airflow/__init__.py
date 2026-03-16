import importlib

_runtime_support = importlib.import_module("._runtime_support", __name__)
_runtime_support.ensure_botscore_importable()

__version__ = importlib.import_module(".__about__", __name__).__version__

_bootstrap = importlib.import_module(".bootstrap", __name__)
RuntimePaths = _bootstrap.RuntimePaths
ensure_runtime = _bootstrap.ensure_runtime

TranslationContext = importlib.import_module(".context", __name__).TranslationContext

_mapping = importlib.import_module(".mapping", __name__)
BaseMapping = _mapping.BaseMapping
MappingServices = _mapping.MappingServices

_registry = importlib.import_module(".registry", __name__)
clear_import_registry = _registry.clear_import_registry
register_grammar = _registry.register_grammar
register_mapping = _registry.register_mapping
registry_snapshot = _registry.registry_snapshot

_runner = importlib.import_module(".runner", __name__)
TranslationRequest = _runner.TranslationRequest
TranslationResult = _runner.TranslationResult
translate_text = _runner.translate_text

GrammarSpec = importlib.import_module(".specs", __name__).GrammarSpec

_translator = importlib.import_module(".translator", __name__)
Translator = _translator.Translator
init = _translator.init

__all__ = [
    'BaseMapping',
    'clear_import_registry',
    'GrammarSpec',
    'MappingServices',
    'RuntimePaths',
    'register_grammar',
    'register_mapping',
    'registry_snapshot',
    'TranslationContext',
    'TranslationRequest',
    'TranslationResult',
    'Translator',
    'ensure_runtime',
    'init',
    'translate_text',
    '__version__',
]
