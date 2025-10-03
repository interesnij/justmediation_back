# Все эти методы скопированы из Check Mixing из django_health_check,
# но лишь слегка отредактированы

import copy
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Iterable, Tuple
from health_check.plugins import plugin_dir
from .backends.base import AbstractHealthCheckBackend


def get_plugins(
    plugins_list: Iterable[str]
) -> Tuple[AbstractHealthCheckBackend]:
    """ Получите все определенные плагины для проверки работоспособности, 
    указанной в plugins_list.
    Добавлена фильтрация и удалена сортировка по идентификатору.
    """
    plugins = (
        plugin_class(**copy.deepcopy(options))
        for plugin_class, options in plugin_dir._registry
    )
    if plugins_list:
        plugins = filter(lambda x: x.identifier() in plugins_list, plugins)
    return tuple(plugins)


def run_plugin(plugin: AbstractHealthCheckBackend):
    """ Запустите проверку работоспособности с помощью плагина.
    Перемещен за пределы run_checks.
    """
    plugin.run_check()
    try:
        return plugin
    finally:
        from django.db import connections
        connections.close_all()


def run_checks(
    checks: Iterable[str] = None
) -> Tuple[AbstractHealthCheckBackend]:
    """ Запустите проверки работоспособности, указанные в разделе проверки (если пусто, 
    запустите их все).
    Сделайте так, чтобы он возвращал плагины вместо собранных ошибок.
    """
    if not checks:
        checks = tuple()
    plugins = get_plugins(checks)

    with ThreadPoolExecutor(max_workers=len(plugins) or 1) as executor:
        for _ in executor.map(run_plugin, plugins):
            pass

    return plugins
