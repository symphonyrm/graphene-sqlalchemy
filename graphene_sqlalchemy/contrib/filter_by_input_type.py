from sqlalchemy import Column
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import RelationshipProperty

from .input_type import SQLAlchemyInputObjectType
from ..api import dispatch, get_registry, OrmLike


class SQLAlchemyFilterByInputObjectType(SQLAlchemyInputObjectType):
    class Meta:
        abstract = True


@dispatch()
def set_registry_class(cls: SQLAlchemyFilterByInputObjectType):
    return SQLAlchemyFilterByInputObjectType


@dispatch()
def convert_name(cls: SQLAlchemyFilterByInputObjectType, model: DeclarativeMeta):
    return '{}FilterByInput'.format(model.__name__)


@dispatch()
def ignore_field(
    cls: SQLAlchemyFilterByInputObjectType,
    model: DeclarativeMeta,
    column: RelationshipProperty
) -> bool:
    return True


@dispatch()
def is_nullable(
    cls: SQLAlchemyFilterByInputObjectType,
    model: DeclarativeMeta,
    orm_prop: OrmLike
) -> bool:
    return True
