from functools import partial
from inspect import getmro
from typing import Union

import graphene
from graphene.types import InputObjectType
from sqlalchemy import Column, types
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import ColumnProperty, Mapper, Query, RelationshipProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy_utils.generic import GenericRelationshipProperty
try:
    from sqlalchemy_utils import ChoiceType, JSONType, ScalarListType, TSVectorType
except ImportError:
    ChoiceType = JSONType = ScalarListType = TSVectorType = object

from .input_type import SQLAlchemyInputObjectType
from ..api import (
    dispatch,
    dynamic_type,
    order_orm_properties,
    FloatLike,
    get_registry,
    is_key,
    IntLike,
    Int8Like,
    Int16Like,
    Int24Like,
    Int32Like,
    OrmLike,
    StringLike,
)
from ..scalars import SignedInt32


class FilterInputObjectType(InputObjectType):
    pass


class IDFilterInputObjectType(FilterInputObjectType):
    equalTo = graphene.ID()
    inList = graphene.List(graphene.String)
    isNull = graphene.Boolean()
    notEqualTo = graphene.String()


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
def convert_name(cls: SQLAlchemyFilterInputObjectType, model: DeclarativeMeta):
    return '{}FilterInput'.format(model.__name__)


@dispatch()
def convert_to_query(
    filters: SQLAlchemyFilterInputObjectType,
    model: DeclarativeMeta,
    query: Query
) -> Query:
    orm_prop_list = order_orm_properties(model)
    model_mro = getmro(model)[0]

    for orm_prop in orm_prop_list:
        func = convert_to_query.dispatch(type(filters), model_mro, type(orm_prop), type(query))
        if not func:
            func = convert_to_query.dispatch(type(filters), type(model), type(orm_prop), type(query))

        query = func(filters, model, orm_prop, query)
    return query


@dispatch()
def convert_to_query(
    filters: SQLAlchemyFilterInputObjectType,
    model: DeclarativeMeta,
    column: Column,
    query: Query
) -> Query:
    filter_name = convert_name(filters, model, column)
    if filter_name in filters.keys():
        for comparator, value in filters[filter_name].items():
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
    filters: SQLAlchemyFilterInputObjectType,
    model: DeclarativeMeta,
    relationship: RelationshipProperty,
    query: Query
) -> Query:
    filter_name = convert_name(filters, filters._meta.model, relationship)
    if filter_name in filters.keys():
        _filter = filters[filter_name]
        model = relationship.mapper.entity
        query = query.join(model)

        if type(_filter) == list:
            for item in _filter:
                query = convert_to_query(item, model, query)
            return query.distinct()
        return convert_to_query(filters[filter_name], model, query)
    return query


@dispatch()
def convert_to_query(
    inputs: SQLAlchemyFilterInputObjectType,
    model: DeclarativeMeta,
    relationship: GenericRelationshipProperty,
    query: Query
) -> Query:
    if hasattr(relationship, '_map_discriminator2type'):
        attr_pairs = relationship.discriminator_model_pairs()
        for key, foreign_model in attr_pairs:
            if key in inputs:
                entity_input = inputs[key]
                entity_model = entity_input._meta.model
                entity_attr = getattr(model, relationship.key)
                entity_id = getattr(model, relationship.id[0].key)

                query = query.join(entity_model, entity_id == entity_model.id)
                query = convert_to_query(entity_input, entity_model, query)
                break

    return query


@dispatch()
def construct_fields(
    cls: SQLAlchemyFilterInputObjectType,
    model: DeclarativeMeta,
    relationship: GenericRelationshipProperty,
):
    if hasattr(relationship, '_map_discriminator2type'):
        attr_pairs = relationship.discriminator_model_pairs()
        for key, foreign_model in attr_pairs:
            generic = partial(dynamic_type, cls, model, relationship, foreign_model)
            setattr(cls, key, graphene.Dynamic(generic))


@dispatch()
def ignore_field(
    cls: SQLAlchemyFilterInputObjectType,
    model: DeclarativeMeta,
    column: Column
) -> bool:
    # NOTE: We used to ignore foreign keys here, since they're on the
    #       relationship anyway.
    #       This is problematic however, for two reasons:
    #       - Using the relationship requires a join where one may be
    #         unnecessary.
    #       - If the table consists only of foreign keys with no known
    #         relationships, this results in an empty type, which causes
    #         graphene to throw an error, since an InputObjectType with
    #         no fields doesn't make any sense.
    return False


@dispatch()
def is_nullable(
    cls: SQLAlchemyFilterInputObjectType,
    model: DeclarativeMeta,
    orm_prop: OrmLike
) -> bool:
    return True


@dispatch()
def convert_type(
    cls: SQLAlchemyFilterInputObjectType,
    model: DeclarativeMeta,
    column: Column,
    _type: StringLike,
) -> Union[IDFilterInputObjectType, StringFilterInputObjectType]:
    if is_key(model, column):
        return IDFilterInputObjectType
    return StringFilterInputObjectType


@dispatch()
def convert_type(
    cls: SQLAlchemyFilterInputObjectType,
    model: DeclarativeMeta,
    column: Column,
    _type: types.DateTime
) -> DateTimeFilterInputObjectType:
    return DateTimeFilterInputObjectType


@dispatch()
def convert_type(
    cls: SQLAlchemyFilterInputObjectType,
    model: DeclarativeMeta,
    column: Column,
    _type: IntLike
) -> Union[IDFilterInputObjectType, SignedInt32FilterInputObjectType]:
    if is_key(model, column):
        return IDFilterInputObjectType
    return SignedInt32FilterInputObjectType


@dispatch()
def convert_type(
    cls: SQLAlchemyFilterInputObjectType,
    model: DeclarativeMeta,
    column: Column,
    _type: types.Boolean
) -> BooleanFilterInputObjectType:
    return BooleanFilterInputObjectType


@dispatch()
def convert_type(
    cls: SQLAlchemyFilterInputObjectType,
    model: DeclarativeMeta,
    column: Column,
    _type: FloatLike
) -> FloatFilterInputObjectType:
    return FloatFilterInputObjectType
