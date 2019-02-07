
from graphene.types.objecttype import ObjectType
from inflection import pluralize, singularize, underscore

from .mutation import (
    SQLAlchemyCreateMutation,
    SQLAlchemyDeleteMutation,
    SQLAlchemyEditMutation,
)
from ..types import SQLAlchemyObjectType
from ..api import generate_type, get_connection_field


class SQLAlchemyAutogenQuery(ObjectType):
    @classmethod
    def __init_subclass_with_meta__(cls, models=None, exclude=[],
                                    object_type=None, **options):
        object_type = object_type or SQLAlchemyObjectType
        models = [
            model
            for model in models
            if model.__name__ not in exclude
        ]

        for model in models:
            _class = generate_type(object_type, model)
            field_name = underscore(_class.__name__)

            if not hasattr(cls, field_name):
                setattr(cls, singularize(field_name), _class.Field())
                setattr(cls, pluralize(field_name), get_connection_field(_class, model))

        super(SQLAlchemyAutogenQuery,
              cls).__init_subclass_with_meta__(**options)


class SQLAlchemyAutogenMutations(ObjectType):
    @classmethod
    def __init_subclass_with_meta__(cls, models=None, exclude=[],
                                    mutations=[], **options):
        models = [
            model
            for model in models
            if model.__name__ not in exclude
        ]
        mutations = mutations or [
            SQLAlchemyEditMutation,
            SQLAlchemyCreateMutation,
            SQLAlchemyDeleteMutation,
        ]

        for model in models:
            for mutation in mutations:
                _class = generate_type(mutation, model)
                field_name = underscore(_class.__name__)

                if not hasattr(cls, field_name):
                    setattr(cls, field_name, _class.Field())

        super(SQLAlchemyAutogenMutations,
              cls).__init_subclass_with_meta__(**options)

