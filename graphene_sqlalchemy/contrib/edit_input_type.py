from functools import partial
from inflection import camelize, underscore

from graphene import Dynamic, Field, List
from graphql import GraphQLError
from sqlalchemy import Column, inspect
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import interfaces, RelationshipProperty, Session
from sqlalchemy_utils.generic import GenericRelationshipProperty

from .create_input_type import SQLAlchemyCreateInputObjectType
from .input_type import SQLAlchemyInputObjectType
from ..api import dispatch, dynamic_type, get_registry, order_orm_properties


class SQLAlchemyEditInputObjectType(SQLAlchemyInputObjectType):
    class Meta:
        abstract = True


@dispatch()
def set_registry_class(cls: SQLAlchemyEditInputObjectType):
    return SQLAlchemyEditInputObjectType


@dispatch()
def ignore_field(
    cls: SQLAlchemyEditInputObjectType,
    model: DeclarativeMeta,
    column: Column
) -> bool:
    auto_fields = ['created_at', 'updated_at']
    is_auto = bool(column.server_default) and underscore(column.name) in auto_fields

    return is_auto


@dispatch()
def ignore_field(
    cls: SQLAlchemyEditInputObjectType,
    model: DeclarativeMeta,
    relationship: RelationshipProperty
) -> bool:
    is_dual_key = any([
        column.primary_key and bool(column.foreign_keys)
        for column in relationship.local_columns
    ])

    return is_dual_key


@dispatch()
def convert_name(cls: SQLAlchemyEditInputObjectType, model: DeclarativeMeta):
    return '{}EditInput'.format(model.__name__)


@dispatch()
def convert_name(
    cls: SQLAlchemyEditInputObjectType,
    model: DeclarativeMeta,
    column: Column
) -> str:
    if column.foreign_keys and not column.primary_key:
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
    cls: SQLAlchemyEditInputObjectType,
    model: DeclarativeMeta,
    relationship: RelationshipProperty,
) -> str:
    return 'create_and_attach_to_{name}'.format(name=relationship.key)


@dispatch()
def is_nullable(
    cls: SQLAlchemyEditInputObjectType,
    model: DeclarativeMeta,
    column: Column
) -> bool:
    is_primary_key = bool(column.primary_key) and column.autoincrement

    return not is_primary_key


@dispatch()
def construct_fields(
    cls: SQLAlchemyEditInputObjectType,
    model: DeclarativeMeta,
    relationship: RelationshipProperty,
):
    create_key = 'create_and_attach_to_{name}'.format(name=relationship.key)
    edit_key = 'edit_and_attach_to_{name}'.format(name=relationship.key)
    direction = relationship.direction
    foreign_model = relationship.mapper.entity

    if direction == interfaces.MANYTOONE or not relationship.uselist:
        uselist = False
    elif direction in (interfaces.ONETOMANY, interfaces.MANYTOMANY):
        uselist = True

    create_dynamic = partial(dynamic_type, SQLAlchemyCreateInputObjectType, model, relationship, foreign_model, uselist)
    edit_dynamic = partial(dynamic_type, SQLAlchemyEditInputObjectType, model, relationship, foreign_model, uselist)
    setattr(cls, create_key, Dynamic(create_dynamic))
    setattr(cls, edit_key, Dynamic(edit_dynamic))


@dispatch()
def construct_fields(
    cls: SQLAlchemyEditInputObjectType,
    model: DeclarativeMeta,
    relationship: GenericRelationshipProperty,
):
    for foreign_model in relationship.get_all_related_models():
        create_key = 'createAndAttach{}To{}'.format(
            foreign_model.__name__,
            camelize(relationship.key)
        )
        edit_key = 'editAndAttach{}To{}'.format(
            foreign_model.__name__,
            camelize(relationship.key)
        )
        create_dynamic = partial(dynamic_type, SQLAlchemyCreateInputObjectType, model, relationship, foreign_model)
        edit_dynamic = partial(dynamic_type, SQLAlchemyEditInputObjectType, model, relationship, foreign_model)
        setattr(cls, create_key, Dynamic(create_dynamic))
        setattr(cls, edit_key, Dynamic(edit_dynamic))


@dispatch()
def convert_to_instance(
    inputs: SQLAlchemyEditInputObjectType,
    model: DeclarativeMeta,
    session: Session
):
    keys = inspect(model).primary_key
    key_input = {}
    for key in keys:
        name = key.name
        if name in inputs:
            key_input[key.name] = inputs.pop(name)

    orm_prop_list = order_orm_properties(model)
    instance = session.query(model).get(key_input.values())
    if not instance:
        raise GraphQLError(
            'No such instance of type {} with keys {}'.format(
                model.__name__,
                key_input))

    for orm_prop in orm_prop_list:
        instance = convert_to_instance(inputs, instance, orm_prop, session)
    return instance


@dispatch()
def convert_to_instance(
    inputs: SQLAlchemyEditInputObjectType,
    instance: object,
    relationship: RelationshipProperty,
    session: Session
):
    input_name = None
    create_key = 'create_and_attach_to_{name}'.format(name=relationship.key)
    edit_key = 'edit_and_attach_to_{name}'.format(name=relationship.key)
    if create_key in inputs.keys():
        input_name = create_key
    elif edit_key in inputs.keys():
        input_name = edit_key

    if input_name:
        setattr(
            instance,
            relationship.key,
            convert_to_instance(inputs[input_name], relationship.mapper.entity, session)
        )

    return instance
