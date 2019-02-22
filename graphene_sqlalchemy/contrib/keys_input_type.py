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


class SQLAlchemyKeysInputObjectType(SQLAlchemyInputObjectType):
    class Meta:
        abstract = True


@dispatch()
def set_registry_class(cls: SQLAlchemyKeysInputObjectType):
    return SQLAlchemyKeysInputObjectType


@dispatch()
def ignore_field(
    cls: SQLAlchemyKeysInputObjectType,
    model: DeclarativeMeta,
    column: Column
) -> bool:
    is_primary_key = bool(column.primary_key)

    return not is_primary_key


@dispatch()
def ignore_field(
    cls: SQLAlchemyKeysInputObjectType,
    model: DeclarativeMeta,
    column: NotColumnLike
) -> bool:
    return True


@dispatch()
def convert_name(cls: SQLAlchemyKeysInputObjectType, model: DeclarativeMeta):
    return '{}KeysInput'.format(model.__name__)
