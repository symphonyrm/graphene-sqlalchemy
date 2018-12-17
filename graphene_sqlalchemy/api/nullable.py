from graphene.types.base import BaseType
from sqlalchemy import Column

from .field_types import OrmLike
from .namespace import dispatch


@dispatch()
def is_nullable(column: OrmLike, cls: type) -> bool:
    func = is_nullable.dispatch(type(column), cls)
    return func(column, cls)


@dispatch()
def is_nullable(column: Column, cls: BaseType) -> bool:
    return bool(getattr(column, "nullable", True))
