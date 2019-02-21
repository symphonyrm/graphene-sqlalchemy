from sqlalchemy import Column
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy_utils.generic import GenericRelationshipProperty

from .input_type import SQLAlchemyInputObjectType
from ..api import dispatch, OrmLike


NotColumnLike = tuple([
    orm_type
    for orm_type in OrmLike
    if orm_type != Column
])


class SQLAlchemyDeleteInputObjectType(SQLAlchemyInputObjectType):
    class Meta:
        abstract = True


@dispatch()
def set_registry_class(cls: SQLAlchemyDeleteInputObjectType):
    return SQLAlchemyDeleteInputObjectType


@dispatch()
def ignore_field(
    cls: SQLAlchemyDeleteInputObjectType,
    model: DeclarativeMeta,
    column: Column
) -> bool:
    is_primary_key = bool(column.primary_key)

    return not is_primary_key


@dispatch()
def ignore_field(
    cls: SQLAlchemyDeleteInputObjectType,
    model: DeclarativeMeta,
    column: NotColumnLike
) -> bool:
    return True


@dispatch()
def convert_name(cls: SQLAlchemyDeleteInputObjectType, model: DeclarativeMeta):
    return '{}DeleteInput'.format(model.__name__)
