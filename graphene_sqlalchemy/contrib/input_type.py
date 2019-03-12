from functools import partial

import graphene
from graphene.types.utils import yank_fields_from_attrs
from inflection import camelize, underscore
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import Session
from sqlalchemy_utils.generic import GenericRelationshipProperty

from ..options import SQLAlchemyObjectTypeOptions
from ..api import (
    construct_fields,
    dispatch,
    dynamic_type,
    get_registry,
    set_registry_class
)
from ..utils import check_mapped_class, is_generic_discriminator, is_generic_key


class SQLAlchemyInputObjectType(graphene.InputObjectType):
    @classmethod
    def __init_subclass_with_meta__(cls, model=None, _meta=None,
                                    skip_registry=False, **options):
        """Initializes an input object type based on a sqlalchemy model."""
        check_mapped_class(model)

        # Provide defaults for optional arguments.
        _meta = _meta or SQLAlchemyObjectTypeOptions(cls)
        _meta.model = model
        _meta.fields = _meta.fields or {}

        # Automatically construct GraphQL fields from the SQLAlchemy model.
        # _meta.fields.update(
        yank_fields_from_attrs(
            construct_fields(cls, model),
            _as=graphene.Field)#)

        super(SQLAlchemyInputObjectType,
              cls).__init_subclass_with_meta__(_meta=_meta, **options)

        if not skip_registry:
            registry = get_registry(set_registry_class(cls))
            registry.register(cls)


@dispatch()
def set_registry_class(cls: SQLAlchemyInputObjectType):
    return SQLAlchemyInputObjectType


@dispatch()
def construct_fields(
    cls: SQLAlchemyInputObjectType,
    model: DeclarativeMeta,
    relationship: GenericRelationshipProperty,
):
    for foreign_model in relationship.get_all_related_models():
        create_key = 'createAndAttach{}To{}'.format(
            foreign_model.__name__,
            camelize(relationship.key)
        )
        generic = partial(dynamic_type, cls, model, relationship, foreign_model)
        setattr(cls, create_key, graphene.Dynamic(generic))


@dispatch()
def convert_to_instance(
    inputs: SQLAlchemyInputObjectType,
    instance: object, # TODO: See if we can get a better type here
    relationship: GenericRelationshipProperty,
    session: Session
):
    for foreign_model in relationship.get_all_related_models():
        create_key = 'createAndAttach{}To{}'.format(
            foreign_model.__name__,
            camelize(relationship.key)
        )
        if create_key in inputs:
            entity_input = inputs[create_key]
            setattr(
                instance,
                relationship.key,
                convert_to_instance(entity_input, entity_input._meta.model, session)
            )
            break

    return instance
