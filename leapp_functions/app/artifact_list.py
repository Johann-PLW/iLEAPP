"""
The artifacts lists, and those selected when it opens.
"""

from collections import namedtuple
from fnmatch import fnmatchcase
from types import SimpleNamespace

from leapp_functions import leapp
from scripts import plugin_loader
from scripts.modules_to_exclude import modules_to_exclude

HIDDEN = tuple(getattr(leapp, "hidden_artifacts", ()))

Artifact = namedtuple("Artifact", "name title category module default")


def is_hidden(name):
    """ Whether an artifact is left out of the list, from its name. """
    return any(fnmatchcase(name, pattern) for pattern in HIDDEN)


def list_artifacts(loader):
    """
    The artifacts that can be chosen, sorted by category then by title.
    Args:
        loader (PluginLoader): the artifacts found in scripts/artifacts.
    Returns:
        list of Artifact: name is the key used in profiles and by the loader, title the name
        shown, default whether it is selected when the window opens (modules_to_exclude
        holds the modules that are not).
    """
    listed = [Artifact(plugin.name, plugin.artifact_info.get("name", plugin.name), plugin.category,
                       plugin.module_name, plugin.module_name not in modules_to_exclude)
              for plugin in loader.plugins if not is_hidden(plugin.name)]
    return sorted(listed, key=lambda artifact: (artifact.category.upper(), artifact.title.upper()))


def load_artifacts():
    """ Load every artifact module once.
    Returns:
        SimpleNamespace: loader, which the run needs; listed, the artifacts that can be
        chosen; selected, the names of those selected by default.
    """
    loader = plugin_loader.PluginLoader()
    listed = list_artifacts(loader)
    return SimpleNamespace(loader=loader, listed=listed,
                           selected={artifact.name for artifact in listed if artifact.default})
