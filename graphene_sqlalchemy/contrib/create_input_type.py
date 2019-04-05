from inflection import underscore

from sqlalchemy import Column, DefaultClause, FetchedValue, inspect
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import RelationshipProperty

from .input_type import SQLAlchemyInputObjectType
from ..api import dispatch, get_registry
from ..utils import is_generic_discriminator, is_generic_key


class SQLAlchemyCreateInputObjectType(SQLAlchemyInputObjectType):
    class Meta:
        abstract = True


@dispatch()
def set_registry_class(cls: SQLAlchemyCreateInputObjectType):
    return SQLAlchemyCreateInputObjectType


@dispatch()
def ignore_field(
    cls: SQLAlchemyCreateInputObjectType,
    model: DeclarativeMeta,
    column: Column
) -> bool:
    auto_fields = ['created_at', 'updated_at']
    default = column.server_default
    is_auto = bool(default) and underscore(column.name) in auto_fields
    is_generated = (
        bool(default)
        and isinstance(default, FetchedValue)
        and not isinstance(default, DefaultClause)
    )
    is_primary_key = (
        bool(column.primary_key)
        and column.autoincrement
        and not column.foreign_keys
    )

    return is_auto or is_generated or is_primary_key


@dispatch()
def convert_name(cls: SQLAlchemyCreateInputObjectType, model: DeclarativeMeta):
    return '{}CreateInput'.format(model.__name__)


@dispatch()
def convert_name(
    cls: SQLAlchemyCreateInputObjectType,
    model: DeclarativeMeta,
    column: Column,
) -> str:
    if column.foreign_keys:
        name = column.name.rsplit('_id', 1)[0]
        relationships = [
            rel
            for rel in inspect(model).relationships
            if column in rel.local_columns
        ]
        if relationships:
            name = relationships[0].key
        return 'attach_to_{name}'.format(name=name)
    return column.name


@dispatch()
def convert_name(
    cls: SQLAlchemyCreateInputObjectType,
    model: DeclarativeMeta,
    relationship: RelationshipProperty,
) -> str:
    return 'create_and_attach_to_{name}'.format(name=relationship.key)


@dispatch()
def is_nullable(
    cls: SQLAlchemyCreateInputObjectType,
    model: DeclarativeMeta,
    column: Column
) -> bool:
    if column.foreign_keys:
        return True
    if is_generic_discriminator(model, column):
        return True
    if is_generic_key(model, column):
        return True
    return bool(getattr(column, "nullable", True))
