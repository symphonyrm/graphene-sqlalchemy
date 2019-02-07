from graphene.types.base import BaseType
from sqlalchemy import Column
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.ext.hybrid import hybrid_property

from .field_types import OrmLike
from .namespace import dispatch


@dispatch()
def get_doc(cls: type, model: DeclarativeMeta, orm_prop: OrmLike):
    func = get_doc.dispatch(cls, type(model), type(orm_prop))
    return func(cls, model, orm_prop)


@dispatch()
def get_doc(cls: BaseType, model: DeclarativeMeta, column: Column):
    return getattr(column, "doc", None)


@dispatch()
def get_doc(cls: BaseType, model: DeclarativeMeta, column: hybrid_property):
    return getattr(hybrid_item, "__doc__", None)
