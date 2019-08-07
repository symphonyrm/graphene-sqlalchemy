from inspect import getmro
from graphene.types.base import BaseType
from sqlalchemy import Column
from sqlalchemy.ext.declarative.api import DeclarativeMeta

from .field_types import OrmLike
from .namespace import dispatch


@dispatch()
def is_nullable(cls: type, model: DeclarativeMeta, column: OrmLike) -> bool:
    func = None
    model_mro = getmro(model)
    if model_mro:
        model_type = model_mro[0]
        func = is_nullable.dispatch(cls, model_type, type(column))
    if not func:
        func = is_nullable.dispatch(cls, type(model), type(column))
    return func(cls, model, column)


@dispatch()
def is_nullable(cls: BaseType, model: DeclarativeMeta, column: Column) -> bool:
    nullable = bool(getattr(column, "nullable", True))
    has_default = bool(getattr(column, "default")) or bool(getattr(column, "server_default"))
    return nullable or has_default
