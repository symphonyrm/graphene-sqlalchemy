from collections import Iterable

from graphene.types.base import BaseType
from sqlalchemy import Column
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import CompositeProperty, RelationshipProperty

from .field_types import OrmLike
from .namespace import dispatch


@dispatch()
def ignore_field(
    cls: type,
    model: DeclarativeMeta,
    orm_prop: OrmLike
) -> bool:
    func = ignore_field.dispatch(cls, type(model), type(orm_prop))
    return func(cls, model, orm_prop)


@dispatch()
def ignore_field(
    cls: BaseType,
    model: DeclarativeMeta,
    orm_prop: OrmLike
) -> bool:
    return False
