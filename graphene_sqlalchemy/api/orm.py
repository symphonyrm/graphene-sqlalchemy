from collections import OrderedDict

from graphene import Dynamic, Field, List, String
from graphene.types.base import BaseType
from sqlalchemy import Column, inspect
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import CompositeProperty, interfaces, RelationshipProperty

from .field_types import OrmLike
from .ignore import ignore_field
from .name import convert_name
from .namespace import dispatch
from .type import convert_sqlalchemy_type
from ..fields import createConnectionField
from ..registry import Registry


def order_orm_properties(model):
    orm_prop_list = []
    inspected_model = inspect(model)

    orm_prop_list += inspected_model.columns
    orm_prop_list += inspected_model.composites
    orm_prop_list += [
        hybrid_item
        for hybrid_item in inspected_model.all_orm_descriptors
        if type(hybrid_item) == hybrid_property
    ]
    orm_prop_list += inspected_model.relationships

    return orm_prop_list


def construct_fields(model, registry, only_fields, exclude_fields, cls):
    orm_prop_list = order_orm_properties(model)
    fields = OrderedDict()

    fields.update({
        convert_name(orm_prop, cls, model): convert_orm_prop(orm_prop, cls, registry)
        for orm_prop in orm_prop_list
        if not ignore_field(orm_prop, cls, only_fields, exclude_fields)
    })

    return fields


@dispatch()
def convert_orm_prop(
    orm_prop: OrmLike,
    cls: type,
    registry: Registry
) -> Field:
    func = convert_orm_prop.dispatch(type(orm_prop), cls, type(registry))
    return func(orm_prop, cls, registry)


@dispatch()
def convert_orm_prop(
    column: Column,
    cls: BaseType,
    registry: Registry
) -> Field:
    _type = getattr(column, 'type', None)
    return convert_sqlalchemy_type(cls, _type, column)


@dispatch()
def convert_orm_prop(composite: CompositeProperty, cls: BaseType, registry: Registry):
    converter = registry.get_converter_for_composite(composite.composite_class)
    if not converter:
        try:
            raise Exception(
                "Don't know how to convert the composite field %s (%s)"
                % (composite, composite.composite_class)
            )
        except AttributeError:
            # handle fields that are not attached to a class yet (don't have a parent)
            raise Exception(
                "Don't know how to convert the composite field %r (%s)"
                % (composite, composite.composite_class)
            )
    return converter(composite, registry)


def _register_composite_class(cls, registry=None):
    def inner(fn):
        registry.register_composite_converter(cls, fn)

    return inner


# TODO: What even is this? There don't seem to be good test cases for
#       composite objects, need to add some to ensure we're handling
#       this correctly.
#
#       Also doesn't seem to break anything when I comment it out, but
#       still definitely requires more testing.
# convert_sqlalchemy_composite.register = _register_composite_class


@dispatch()
def convert_orm_prop(hybrid_item: hybrid_property, cls: BaseType, registry: Registry):
    return String(description=getattr(hybrid_item, "__doc__", None), required=False)


@dispatch()
def convert_orm_prop(relationship: RelationshipProperty, cls: BaseType, registry: Registry):
    direction = relationship.direction
    model = relationship.mapper.entity

    def dynamic_type():
        _type = registry.get_type_for_model(model)
        if not _type:
            return None
        if direction == interfaces.MANYTOONE or not relationship.uselist:
            return Field(_type)
        elif direction in (interfaces.ONETOMANY, interfaces.MANYTOMANY):
            if _type._meta.connection:
                return createConnectionField(_type._meta.connection)
            return Field(List(_type))

    return Dynamic(dynamic_type)
