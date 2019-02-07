
from multipledispatch import dispatch
from functools import partial

from ..registry import get_registry


dispatch_namespace = dict()
dispatch = partial(dispatch, namespace=dispatch_namespace)


registry_namespace = dict()
get_registry = partial(get_registry, registry_namespace)
