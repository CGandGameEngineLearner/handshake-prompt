# encoding=utf-8
"""Pluggable mode handlers — application logic lives here, not in the transport layer."""
from .form_fill import FormFillHandler
from .generic import GenericHandler

DEFAULT_HANDLERS = {
    'form-fill': FormFillHandler(),
    'default':   GenericHandler(),
}


def get_handler(mode, registry=None):
    registry = registry or DEFAULT_HANDLERS
    return registry.get(mode) or registry.get('default') or GenericHandler()
