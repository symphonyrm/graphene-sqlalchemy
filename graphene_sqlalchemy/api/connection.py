from graphene.relay import Connection
from graphene.types.base import BaseType
from sqlalchemy.ext.declarative.api import DeclarativeMeta

from .namespace import dispatch
from ..fields import SQLAlchemyConnectionField


@dispatch()
def get_connection(cls: type, model: DeclarativeMeta):
    func = get_connection.dispatch(cls, type(model))
    return func(cls, model)


@dispatch()
def get_connection(cls: BaseType, model: DeclarativeMeta):
    name = "{}Connection".format(cls.__name__)
    return Connection.create_type(name, node=cls)


@dispatch()
def get_connection_field(cls: type, model: DeclarativeMeta):
    func = get_connection_field.dispatch(cls, type(model))
    return func(cls, model)


@dispatch()
def get_connection_field(cls: BaseType, model: DeclarativeMeta):
    return SQLAlchemyConnectionField(cls)
