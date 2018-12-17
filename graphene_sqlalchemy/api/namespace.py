
from multipledispatch import dispatch
from functools import partial

from ..registry import get_registry


dispatch_namespace = dict()
dispatch = partial(dispatch, namespace=dispatch_namespace)


registry_namespace = dict()
get_registry = partial(get_registry, registry_namespace)


def generate_type(model, _type, name, meta=None):
    registry = get_registry(_type)
    _class = registry.get_type_for_model(model)
    if not meta:
        meta = {
            'Meta': {
                'model': model
            }
        }

    if not _class:
        _class = type(
            name,
            (_type,),
            # TODO: Define submeta
            meta
        )

    return _class
