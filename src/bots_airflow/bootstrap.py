from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ._core_discovery import find_local_botscore_checkout
from .registry import resolve_import

DEFAULT_RUNTIME_ROOT = Path(tempfile.gettempdir()) / 'bots_airflow_runtime'


@dataclass(frozen=True)
class RuntimePaths:
    repo_root: Path
    source_root: Path
    core_root: Path
    core_package_root: Path
    runtime_root: Path
    config_dir: Path
    botssys_dir: Path

    @property
    def bots_root(self) -> Path:
        return self.core_root

    @property
    def bots_package_root(self) -> Path:
        return self.core_package_root


def _resolve_project_layout() -> tuple[Path, Path]:
    package_root = Path(__file__).resolve().parent
    if package_root.parent.name == 'src':
        source_root = package_root.parent
        return source_root.parent, source_root
    source_root = package_root.parent
    return source_root, source_root


def _resolve_core_runtime(project_root: Path) -> tuple[Path, Path]:
    spec = importlib.util.find_spec('botscore')
    if spec is not None and spec.submodule_search_locations:
        package_root = Path(next(iter(spec.submodule_search_locations))).resolve()
        return package_root.parent, package_root

    fallback = find_local_botscore_checkout(project_root)
    if fallback is not None:
        return fallback

    raise ImportError(
        "Could not locate the 'botscore' package. Install a distribution that provides "
        "'botscore' or provide a local checkout."
    )


def _ensure_import_path(path: Path) -> None:
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)


def _prepare_runtime_layout(runtime_root: Path) -> RuntimePaths:
    repo_root, source_root = _resolve_project_layout()
    core_root, core_package_root = _resolve_core_runtime(repo_root)
    config_dir = runtime_root / 'config'
    botssys_dir = runtime_root / 'botssys'

    config_dir.mkdir(parents=True, exist_ok=True)
    botssys_dir.mkdir(parents=True, exist_ok=True)
    (botssys_dir / 'data').mkdir(parents=True, exist_ok=True)
    (botssys_dir / 'logging').mkdir(parents=True, exist_ok=True)

    return RuntimePaths(
        repo_root=repo_root,
        source_root=source_root,
        core_root=core_root,
        core_package_root=core_package_root,
        runtime_root=runtime_root,
        config_dir=config_dir,
        botssys_dir=botssys_dir,
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


def _install_botsimport_hook() -> None:
    from botscore import imports as core_imports

    if getattr(core_imports, '_bots_airflow_registry_hook', False):
        return

    original_botsimport = core_imports.botsimport

    def registry_first_botsimport(*args):
        resolved = resolve_import(*args)
        if resolved is not None:
            return resolved
        return original_botsimport(*args)

    core_imports._bots_airflow_original_botsimport = original_botsimport
    core_imports.botsimport = registry_first_botsimport
    core_imports._bots_airflow_registry_hook = True


def _core_init(runtime_paths: RuntimePaths) -> None:
    _ensure_import_path(runtime_paths.source_root)
    _ensure_import_path(runtime_paths.core_root)

    from botscore import config as core_config
    from botscore import runtime as core_runtime
    from botscore import state
    from botscore import node as core_node

    ini = core_config.BotsConfig()
    if not ini.has_section('directories'):
        ini.add_section('directories')

    _set_ini_defaults(ini)

    ini.set('directories', 'botspath', str(runtime_paths.core_package_root))
    ini.set('directories', 'config', str(runtime_paths.config_dir))
    ini.set('directories', 'config_org', str(runtime_paths.config_dir))
    ini.set('directories', 'botsenv', str(runtime_paths.runtime_root))
    ini.set('directories', 'usersys', '')
    ini.set('directories', 'usersysabs', '')
    ini.set(
        'directories',
        'templatehtml',
        str(runtime_paths.runtime_root / 'templatehtml'),
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

    _install_botsimport_hook()
    logger = _init_logger()
    core_runtime.install_runtime(
        ini,
        configdir=str(runtime_paths.config_dir),
        logger=logger,
        logmap=logger,
        node_class=core_node.Node,
        clear_not_import=True,
    )
    state.settings = None


def ensure_runtime(
    runtime_root: str | Path | None = None,
    **compat_kwargs,
) -> RuntimePaths:
    compat_kwargs.pop('usersys_root', None)
    if compat_kwargs:
        unexpected = ', '.join(sorted(compat_kwargs))
        raise TypeError(f'Unexpected keyword argument(s): {unexpected}')

    runtime_root_path = Path(runtime_root) if runtime_root else DEFAULT_RUNTIME_ROOT
    runtime_paths = _prepare_runtime_layout(runtime_root=runtime_root_path)
    _core_init(runtime_paths)
    return runtime_paths
