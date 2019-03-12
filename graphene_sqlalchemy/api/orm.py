import functools
from collections import Iterable, OrderedDict
from inspect import getmro
from operator import iconcat
from six import string_types
from typing import Dict

from graphene import Dynamic, Field, List, String, Union
from graphene.types.base import BaseType
from sqlalchemy import Column, inspect
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import CompositeProperty, interfaces, RelationshipProperty
from sqlalchemy_utils.generic import GenericRelationshipProperty

from .doc import get_doc
from .field_types import OrmLike
from .ignore import ignore_field
from .name import convert_name
from .namespace import dispatch, get_registry
from .nullable import is_nullable
from .registry import set_registry_class
from .type import convert_type
from ..fields import createConnectionField
from ..registry import Registry


def order_orm_properties(model):
    inspected_model = inspect(model)

    list_of_lists = [
        inspected_model.columns,
        inspected_model.composites,
        [
            hybrid_item
            for hybrid_item in inspected_model.all_orm_descriptors
            if type(hybrid_item) == hybrid_property
        ],
        inspected_model.relationships,
        [
            gen_rel.property
            for gen_rel in inspected_model.all_orm_descriptors
            if getattr(gen_rel, 'property', None)
            and type(gen_rel.property) == GenericRelationshipProperty
        ]
    ]
    return functools.reduce(iconcat, list_of_lists, [])
    # {
    #     name: type(value.property)
    #     for name, value in inspected_model.all_orm_descriptors.items()
    #     if hasattr(value, 'property')
    # }


@dispatch()
def construct_fields(
    cls: BaseType,
    model: DeclarativeMeta,
) -> Dict:
    orm_prop_list = order_orm_properties(model)
    fields = OrderedDict()

    for orm_prop in orm_prop_list:
        if not ignore_field(cls, model, orm_prop):
            construct_fields(cls, model, orm_prop)
            # fields.update(construct_fields(cls, model, orm_prop))

    return fields


@dispatch()
def construct_fields(
    cls: type,
    model: DeclarativeMeta,
    orm_prop: OrmLike,
) -> Dict[str, Field]:
    func = None
    model_mro = getmro(model)
    if model_mro:
        model_type = model_mro[0]
        func = construct_fields.dispatch(cls, model_type, type(orm_prop))
    if not func:
        func = construct_fields.dispatch(cls, type(model), type(orm_prop))
    return func(cls, model, orm_prop)


@dispatch()
def construct_fields(
    cls: type,
    model: DeclarativeMeta,
) -> Dict[str, Field]:
    model_mro = getmro(model)
    if model_mro:
        model_type = model_mro[0]
        func = construct_fields.dispatch(cls, model_type)
    if not func:
        func = construct_fields.dispatch(cls, type(model))
    return func(cls, model)


@dispatch()
def construct_fields(
    cls: BaseType,
    model: DeclarativeMeta,
    column: Column,
) -> Dict[str, Field]:
    _type = getattr(column, 'type', None)
    name = convert_name(cls, model, column)
    graphene_type = convert_type(cls, model, column, _type)
    graphene_type = graphene_type(
        description=get_doc(cls, model, column),
        required=not (is_nullable(cls, model, column)),
    )
    # return {
    #     name: graphene_type
    # }
    setattr(cls, name, graphene_type)


@dispatch()
def construct_fields(
    cls: BaseType,
    model: DeclarativeMeta,
    composite: CompositeProperty,
) -> Dict[str, Field]:
    name = convert_name(cls, model, composite)
    graphene_type = convert_type(cls, model, composite)
    graphene_type = graphene_type(
        description=get_doc(cls, model, composite),
        required=not (is_nullable(cls, model, composite)),
    )
    # return {
    #     name: graphene_type
    # }
    setattr(cls, name, graphene_type)


@dispatch()
def construct_fields(
    cls: BaseType,
    model: DeclarativeMeta,
    hybrid_item: hybrid_property,
) -> Dict[str, String]:
    name = convert_name(cls, model, hybrid_item)
    graphene_type = String(
        description=get_doc(cls, model, hybrid_item),
        required=False
    )
    # return {
    #     name: graphene_type
    # }
    setattr(cls, name, graphene_type)


@dispatch()
def construct_fields(
    cls: BaseType,
    model: DeclarativeMeta,
    relationship: RelationshipProperty,
) -> Dict[str, Dynamic]:
    name = convert_name(cls, model, relationship)
    direction = relationship.direction
    foreign_model = relationship.mapper.entity

    if direction == interfaces.MANYTOONE or not relationship.uselist:
        uselist = False
    elif direction in (interfaces.ONETOMANY, interfaces.MANYTOMANY):
        uselist = True

    generic = functools.partial(dynamic_type, cls, model, relationship, foreign_model, uselist)
    setattr(cls, name, Dynamic(generic))


@dispatch()
def construct_fields(
    cls: BaseType,
    model: DeclarativeMeta,
    relationship: GenericRelationshipProperty,
):
    pass


def dynamic_type(registry_class, model, relationship, foreign_models, uselist=False):
    # TODO: Think about changing the registry interface
    #       This feels clunky
    registry = get_registry(set_registry_class(registry_class))
    if isinstance(foreign_models, Iterable) and not isinstance(foreign_models, string_types):
        _types = [
            registry.get_type_for_model(foreign)
            for foreign in foreign_models
        ]
    else:
        _types = registry.get_type_for_model(foreign_models)
    if not _types:
        return None
    if type(_types) is list:
        name = '{}{}Union'.format(model.__name__, relationship.key)
        return type(
            name,
            (Union,),
            {
                'Meta': {
                    'types': _types
                }
            })()
    else:
        if not uselist:
            return Field(_types)
        else:
            if _types._meta.connection:
                return createConnectionField(_types._meta.connection)
            return Field(List(_types))
