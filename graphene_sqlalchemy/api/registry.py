from graphene.types.base import BaseType

from .namespace import dispatch

@dispatch()
def set_registry_class(cls: type):
    func = set_registry_class.dispatch(cls)
    return func(cls)


@dispatch()
def set_registry_class(cls: BaseType):
    return BaseType
