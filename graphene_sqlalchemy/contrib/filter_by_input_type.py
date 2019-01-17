# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy.orm import RelationshipProperty

from .input_type import SQLAlchemyInputObjectType
from ..api import dispatch, get_registry


class SQLAlchemyFilterByInputObjectType(SQLAlchemyInputObjectType):
    class Meta:
        abstract = True


@dispatch()
def set_registry_class(cls: SQLAlchemyFilterByInputObjectType):
    return SQLAlchemyFilterByInputObjectType


@dispatch()
def ignore_field(
    column: RelationshipProperty,
    cls: SQLAlchemyFilterByInputObjectType,
    only_fields: list,
    exclude_fields: list,
) -> bool:
    return True


@dispatch()
def is_nullable(column: Column, cls: SQLAlchemyFilterByInputObjectType) -> bool:
    return True
