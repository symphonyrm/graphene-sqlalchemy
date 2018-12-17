# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy.orm import RelationshipProperty

from .input_type import SQLAlchemyInputObjectType
from ..api import dispatch, get_registry


class SQLAlchemyFilterByInputObjectType(SQLAlchemyInputObjectType):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, registry=None, **options):
        if not registry:
            registry = get_registry(SQLAlchemyFilterByInputObjectType)

        super(SQLAlchemyFilterByInputObjectType,
              cls).__init_subclass_with_meta__(registry=registry, **options)


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
