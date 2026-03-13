from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import django.conf
from django.utils import translation as django_translation

from .registry import resolve_import

DEFAULT_RUNTIME_ROOT = Path(tempfile.gettempdir()) / 'bots_airflow_runtime'


@dataclass(frozen=True)
class RuntimePaths:
    repo_root: Path
    source_root: Path
    bots_root: Path
    bots_package_root: Path
    runtime_root: Path
    config_dir: Path
    botssys_dir: Path
    usersys_root: Path
    usersys_setting: str
    usersys_import_path: str


def _resolve_project_layout() -> tuple[Path, Path]:
    package_root = Path(__file__).resolve().parent
    if package_root.parent.name == 'src':
        source_root = package_root.parent
        return source_root.parent, source_root
    source_root = package_root.parent
    return source_root, source_root


def _resolve_bots_runtime(project_root: Path) -> tuple[Path, Path]:
    spec = importlib.util.find_spec('bots')
    if spec is not None and spec.submodule_search_locations:
        package_root = Path(next(iter(spec.submodule_search_locations))).resolve()
        return package_root.parent, package_root

    fallback_root = (project_root.parent / 'bots_edi' / 'bots').resolve()
    fallback_package_root = fallback_root / 'bots'
    if fallback_package_root.exists():
        return fallback_root, fallback_package_root

    raise ImportError(
        "Could not locate the 'bots' package. Install 'bots-ediint' or provide a local checkout."
    )


def _ensure_import_path(path: Path) -> None:
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)


def _resolve_usersys(usersys_root: str | Path | None) -> tuple[str, Path, str]:
    if isinstance(usersys_root, Path):
        resolved = usersys_root.resolve()
        import_path = resolved.name
        _ensure_import_path(resolved.parent)
        importlib.import_module(import_path)
        return str(resolved), resolved, import_path

    candidate = Path(usersys_root)
    if candidate.exists():
        resolved = candidate.resolve()
        import_path = resolved.name
        _ensure_import_path(resolved.parent)
        importlib.import_module(import_path)
        return str(resolved), resolved, import_path

    module = importlib.import_module(usersys_root)
    return usersys_root, Path(module.__path__[0]), usersys_root


def _prepare_registry_stub(runtime_root: Path) -> tuple[str, Path, str]:
    stub_root = runtime_root / '_usersys_stub'
    stub_root.mkdir(parents=True, exist_ok=True)
    init_file = stub_root / '__init__.py'
    if not init_file.exists():
        init_file.write_text('')
    return str(stub_root), stub_root, stub_root.name


def _prepare_runtime_layout(
    runtime_root: Path,
    usersys_setting: str,
    usersys_root: Path,
    usersys_import_path: str,
) -> RuntimePaths:
    repo_root, source_root = _resolve_project_layout()
    bots_root, bots_package_root = _resolve_bots_runtime(repo_root)
    config_dir = runtime_root / 'config'
    botssys_dir = runtime_root / 'botssys'

    config_dir.mkdir(parents=True, exist_ok=True)
    botssys_dir.mkdir(parents=True, exist_ok=True)
    (botssys_dir / 'data').mkdir(parents=True, exist_ok=True)
    (botssys_dir / 'logging').mkdir(parents=True, exist_ok=True)

    return RuntimePaths(
        repo_root=repo_root,
        source_root=source_root,
        bots_root=bots_root,
        bots_package_root=bots_package_root,
        runtime_root=runtime_root,
        config_dir=config_dir,
        botssys_dir=botssys_dir,
        usersys_root=usersys_root,
        usersys_setting=usersys_setting,
        usersys_import_path=usersys_import_path,
    )


def _set_ini_defaults(ini) -> None:
    defaults = {
        'settings': {
            'get_checklevel': '1',
            'globaltimeout': '10',
            'max_number_errors': '10',
            'debug': 'False',
            'readrecorddebug': 'False',
            'mappingdebug': 'False',
            'log_level': 'INFO',
            'log_console': 'False',
            'log_console_level': 'INFO',
            'log_file_level': 'INFO',
            'log_file_number': '5',
            'django_db_connection': '',
            'botsreplacechar': ' ',
            'log_when': 'report',
        },
        'webserver': {
            'environment': 'production',
        },
        'charsets': {},
        'dirmonitor': {},
    }

    for section, values in defaults.items():
        if not ini.has_section(section):
            ini.add_section(section)
        for key, value in values.items():
            ini.set(section, key, value)


def _init_logger() -> logging.Logger:
    logger = logging.getLogger('bots.airflow')
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    logger.setLevel(logging.INFO)
    return logger


def _install_django_translation_compat() -> None:
    aliases = {
        'ugettext': 'gettext',
        'ugettext_lazy': 'gettext_lazy',
        'ungettext': 'ngettext',
        'ungettext_lazy': 'ngettext_lazy',
        'ugettext_noop': 'gettext_noop',
    }

    for legacy_name, modern_name in aliases.items():
        if hasattr(django_translation, legacy_name):
            continue
        setattr(django_translation, legacy_name, getattr(django_translation, modern_name))


def _install_botsimport_hook() -> None:
    from bots import botslib

    if getattr(botslib, '_bots_airflow_registry_hook', False):
        return

    original_botsimport = botslib.botsimport

    def registry_first_botsimport(*args):
        resolved = resolve_import(*args)
        if resolved is not None:
            return resolved
        return original_botsimport(*args)

    botslib._bots_airflow_original_botsimport = original_botsimport
    botslib.botsimport = registry_first_botsimport
    botslib._bots_airflow_registry_hook = True


def _core_init(runtime_paths: RuntimePaths) -> None:
    _ensure_import_path(runtime_paths.source_root)
    _ensure_import_path(runtime_paths.bots_root)
    _ensure_import_path(runtime_paths.usersys_root.parent)
    _install_django_translation_compat()

    from bots import botsglobal, botsinit, botslib, node

    ini = botsinit.BotsConfig()
    if not ini.has_section('directories'):
        ini.add_section('directories')

    _set_ini_defaults(ini)

    ini.set('directories', 'botspath', str(runtime_paths.bots_package_root))
    ini.set('directories', 'config', str(runtime_paths.config_dir))
    ini.set('directories', 'config_org', str(runtime_paths.config_dir))
    ini.set('directories', 'botsenv', str(runtime_paths.runtime_root))
    ini.set('directories', 'usersys', runtime_paths.usersys_setting)
    ini.set('directories', 'usersysabs', str(runtime_paths.usersys_root))
    ini.set(
        'directories',
        'templatehtml',
        str(runtime_paths.usersys_root / 'grammars' / 'templatehtml' / 'templates'),
    )
    ini.set('directories', 'botssys_org', str(runtime_paths.botssys_dir))
    ini.set('directories', 'botssys', str(runtime_paths.botssys_dir))
    ini.set('directories', 'data', str(runtime_paths.botssys_dir / 'data'))
    ini.set('directories', 'logging', str(runtime_paths.botssys_dir / 'logging'))
    ini.set('directories', 'users', str(runtime_paths.botssys_dir / '.users'))
    ini.set(
        'dirmonitor',
        'trigger',
        str(runtime_paths.botssys_dir / '.dirmonitor.trigger'),
    )

    botsglobal.ini = ini
    botsglobal.configdir = str(runtime_paths.config_dir)
    botsglobal.usersysimportpath = runtime_paths.usersys_import_path
    botsglobal.not_import.clear()
    botsglobal.logger = _init_logger()
    botsglobal.logmap = botsglobal.logger

    if not django.conf.settings.configured:
        django.conf.settings.configure(
            USE_I18N=False,
            USE_TZ=False,
            INSTALLED_APPS=[],
            SECRET_KEY='bots-airflow-core',
        )
    botsglobal.settings = django.conf.settings

    botslib.dirshouldbethere(botsglobal.ini.get('directories', 'data'))
    botslib.dirshouldbethere(botsglobal.ini.get('directories', 'logging'))
    _install_botsimport_hook()
    botsinit.initbotscharsets()
    node.Node.checklevel = botsglobal.ini.getint('settings', 'get_checklevel', 1)
    botslib.settimeout(botsglobal.ini.getint('settings', 'globaltimeout', 10))


def ensure_runtime(
    usersys_root: str | Path | None = None,
    runtime_root: str | Path | None = None,
) -> RuntimePaths:
    runtime_root_path = Path(runtime_root) if runtime_root else DEFAULT_RUNTIME_ROOT
    if usersys_root is None:
        usersys_setting, resolved_usersys_root, usersys_import_path = _prepare_registry_stub(
            runtime_root_path
        )
    else:
        usersys_setting, resolved_usersys_root, usersys_import_path = _resolve_usersys(usersys_root)
    runtime_paths = _prepare_runtime_layout(
        runtime_root=runtime_root_path,
        usersys_setting=usersys_setting,
        usersys_root=resolved_usersys_root,
        usersys_import_path=usersys_import_path,
    )
    _core_init(runtime_paths)
    return runtime_paths
