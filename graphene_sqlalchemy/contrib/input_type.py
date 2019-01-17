# -*- coding: utf-8 -*-

import graphene

from graphene.types.utils import yank_fields_from_attrs

from ..types import SQLAlchemyObjectTypeOptions
from ..api import construct_fields, dispatch, get_registry, set_registry_class
from ..utils import is_mapped_class


class SQLAlchemyInputObjectType(graphene.InputObjectType):
    @classmethod
    def __init_subclass_with_meta__(cls, model=None, registry=None,
                                    skip_registry=False,
                                    only_fields=[], exclude_fields=[],
                                    _meta=None, **options):
        """Initializes an input object type based on a sqlalchemy model.
        
        Loops through a model's fields and generates GraphQL types based on
        the individual model field types, then updates the class's fields to
        match. Afterwards it ensures the class is registered in the registry
        for late-binding relationships.
        """
        assert is_mapped_class(model), (
                    "You need to pass a valid SQLAlchemy Model in " '{}.Meta, received "{}".'
        ).format(cls.__name__, model)

        # Provide defaults for optional arguments.
        registry = registry or get_registry(set_registry_class(cls))
        _meta = _meta or SQLAlchemyObjectTypeOptions(cls)

        _meta.model = model
        _meta.registry = registry
        _meta.fields = _meta.fields or {}

        # Automatically construct GraphQL fields from the SQLAlchemy model.
        # Excludes anything explicitly passed in via the `exclude_fields`
        # field on the class.
        _meta.fields.update(
            yank_fields_from_attrs(
                construct_fields(
                    model, registry,
                    only_fields, exclude_fields,
                    cls=cls),
                _as=graphene.Field))

        super(SQLAlchemyInputObjectType,
              cls).__init_subclass_with_meta__(_meta=_meta, **options)

        if not skip_registry:
            registry.register(cls)


@dispatch()
def set_registry_class(cls: SQLAlchemyInputObjectType):
    return SQLAlchemyInputObjectType
