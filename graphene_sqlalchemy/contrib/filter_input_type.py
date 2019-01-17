# -*- coding: utf-8 -*-

import graphene
from graphene.types import InputObjectType
from sqlalchemy import Column, types
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import ColumnProperty, Mapper, Query, RelationshipProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
try:
    from sqlalchemy_utils import ChoiceType, JSONType, ScalarListType, TSVectorType
except ImportError:
    ChoiceType = JSONType = ScalarListType = TSVectorType = object

from .input_type import SQLAlchemyInputObjectType
from ..api import (
    dispatch,
    explicitly_ignored,
    FloatLike,
    get_registry,
    Int8Like,
    Int16Like,
    Int24Like,
    Int32Like,
    StringLike,
)
from ..scalars import SignedInt32


class FilterInputObjectType(InputObjectType):
    pass


class StringFilterInputObjectType(FilterInputObjectType):
    equalTo = graphene.String()
    inList = graphene.List(graphene.String)
    isNull = graphene.Boolean()
    isLike = graphene.String()
    notEqualTo = graphene.String()


class BooleanFilterInputObjectType(FilterInputObjectType):
    equalTo = graphene.Boolean()
    isNull = graphene.Boolean()
    notEqualTo = graphene.Boolean()


class DateTimeFilterInputObjectType(FilterInputObjectType):
    equalTo = graphene.DateTime()
    greaterThan = graphene.DateTime()
    greaterThanOrEqualTo = graphene.DateTime()
    inList = graphene.List(graphene.DateTime)
    isNull = graphene.Boolean()
    lessThan = graphene.DateTime()
    lessThanOrEqualTo = graphene.DateTime()
    notEqualTo = graphene.DateTime()


class SignedInt32FilterInputObjectType(FilterInputObjectType):
    equalTo = SignedInt32()
    greaterThan = SignedInt32()
    greaterThanOrEqualTo = SignedInt32()
    inList = graphene.List(SignedInt32)
    isNull = graphene.Boolean()
    lessThan = SignedInt32()
    lessThanOrEqualTo = SignedInt32()
    notEqualTo = SignedInt32()


class FloatFilterInputObjectType(FilterInputObjectType):
    equalTo = graphene.Float()
    greaterThan = graphene.Float()
    greaterThanOrEqualTo = graphene.Float()
    inList = graphene.List(graphene.Float)
    isNull = graphene.Boolean()
    lessThan = graphene.Float()
    lessThanOrEqualTo = graphene.Float()
    notEqualTo = graphene.Float()


class SQLAlchemyFilterInputObjectType(SQLAlchemyInputObjectType):
    class Meta:
        abstract = True


def convert_comparator(comparator):
    if comparator == 'equalTo':
        return 'eq'
    elif comparator == 'greaterThan':
        return 'gt'
    elif comparator == 'greaterThanOrEqualTo':
        return 'ge'
    elif comparator == 'inList':
        return 'in'
    elif comparator == 'lessThan':
        return 'lt'
    elif comparator == 'lessThanOrEqualTo':
        return 'le'
    elif comparator == 'notEqualTo':
        return 'ne'


@dispatch()
def set_registry_class(cls: SQLAlchemyFilterInputObjectType):
    return SQLAlchemyFilterInputObjectType


@dispatch()
def convert_to_query(
    model: DeclarativeMeta,
    query: Query,
    filters: SQLAlchemyFilterInputObjectType
) -> Query:
    for key, comparators in filters.items():
        orm_prop = getattr(model, key)
        query = convert_to_query(
            orm_prop,
            orm_prop.property,
            query,
            comparators)
    return query


@dispatch()
def convert_to_query(
    column: InstrumentedAttribute,
    _type: ColumnProperty,
    query: Query,
    filters: FilterInputObjectType
) -> Query:
    for comparator, value in filters.items():
        op = convert_comparator(comparator)
        attr = [
            c % op
            for c in ['%s', '%s_', '__%s__']
            if hasattr(column, c % op)
        ][0]

        query = query.filter(getattr(column, attr)(value))
    return query


@dispatch()
def convert_to_query(
    relationship: InstrumentedAttribute,
    _type: RelationshipProperty,
    query: Query,
    filters: SQLAlchemyFilterInputObjectType
) -> Query:
    query = query.join(relationship)
    model = relationship.mapper.entity
    return convert_to_query(model, query, filters)


@dispatch()
def convert_to_query(
    relationship: InstrumentedAttribute,
    _type: RelationshipProperty,
    query: Query,
    filters: list
) -> Query:
    model = relationship.mapper.entity
    query = query.join(relationship)
    for item in filters:
        query = convert_to_query(model, query, item)
    return query.distinct()


@dispatch()
def ignore_field(
    column: Column,
    cls: SQLAlchemyFilterInputObjectType,
    only_fields: list,
    exclude_fields: list,
) -> bool:
    name = column.name
    explicit = explicitly_ignored(name, only_fields, exclude_fields)

    is_foreign_key = bool(column.foreign_keys)

    return explicit or is_foreign_key


@dispatch()
def is_nullable(column: Column, cls: SQLAlchemyFilterInputObjectType) -> bool:
    return True


# TODO: Support `get_doc` and `is_nullable` interfaces?
#       No to `is_nullable`, at least. does not make sense to have a
#       required filter.
@dispatch()
def convert_sqlalchemy_type(
    cls: type,
    _type: types.TypeEngine,
    column: Column
) -> None:
    func = convert_sqlalchemy_type.dispatch(cls,
                                            type(_type),
                                            type(column))
    return func(cls, _type, column)


@dispatch()
def convert_sqlalchemy_type(
    cls: SQLAlchemyFilterInputObjectType,
    type: StringLike,
    column: Column
) -> StringFilterInputObjectType:
    return StringFilterInputObjectType()


@dispatch()
def convert_sqlalchemy_type(
    cls: SQLAlchemyFilterInputObjectType,
    type: types.DateTime,
    column: Column
) -> DateTimeFilterInputObjectType:
    return DateTimeFilterInputObjectType()


@dispatch()
def convert_sqlalchemy_type(
    cls: SQLAlchemyFilterInputObjectType,
    type: (Int8Like, Int16Like, Int24Like, Int32Like),
    column: Column
) -> SignedInt32FilterInputObjectType:
    return SignedInt32FilterInputObjectType()


@dispatch()
def convert_sqlalchemy_type(
    cls: SQLAlchemyFilterInputObjectType,
    type: types.Boolean,
    column: Column
) -> BooleanFilterInputObjectType:
    return BooleanFilterInputObjectType()


@dispatch()
def convert_sqlalchemy_type(
    cls: SQLAlchemyFilterInputObjectType,
    type: FloatLike,
    column: Column
) -> FloatFilterInputObjectType:
    return FloatFilterInputObjectType()
