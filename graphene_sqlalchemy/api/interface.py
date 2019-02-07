from graphene.types.base import BaseType
from sqlalchemy.ext.declarative.api import DeclarativeMeta

from .namespace import dispatch


@dispatch()
def get_interfaces(cls: type, model: DeclarativeMeta):
    func = get_interfaces.dispatch(cls, type(model))
    return func(cls, model)


@dispatch()
def get_interfaces(cls: BaseType, model: DeclarativeMeta):
    return []
