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
    # if model.__name__ in ['ActivityEntity', 'activity_entity']:
    #     print('here')
    #     if column.name in ['entity_type', 'entity_id']:
    #         print('double here')
    if model_mro:
        model_type = model_mro[0]
        func = is_nullable.dispatch(cls, model_type, type(column))
    if not func:
        func = is_nullable.dispatch(cls, type(model), type(column))
    return func(cls, model, column)


@dispatch()
def is_nullable(cls: BaseType, model: DeclarativeMeta, column: Column) -> bool:
    return bool(getattr(column, "nullable", True))
