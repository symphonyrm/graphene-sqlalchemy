
from graphene import relay
from graphene.types.objecttype import ObjectType, ObjectTypeOptions
from inflection import pluralize, singularize, underscore

from .countable_connection import CountableConnection
from .filter_connection import InstrumentedQuery
from .mutation import (
    SQLAlchemyCreateMutation,
    SQLAlchemyDeleteMutation,
    SQLAlchemyEditMutation,
)
from ..types import SQLAlchemyObjectType
from ..api import generate_type


class SQLAlchemyAutogenQueryOptions(ObjectTypeOptions):
    model_list = None
    exclude_models = None
    interfaces = None
    object_type = None
    connection_class = None
    connection_field = None


class SQLAlchemyAutogenMutationsOptions(ObjectTypeOptions):
    model_list = None
    exclude_models = None


class SQLAlchemyAutogenQuery(ObjectType):
    @classmethod
    def __init_subclass_with_meta__(cls, model_list=None, exclude_models=[],
                                    interfaces=None, object_type=None,
                                    connection_class=None, connection_field=None,
                                    **options):
        meta = SQLAlchemyAutogenQueryOptions(cls)
        interfaces = interfaces or (relay.Node,)
        object_type = object_type or SQLAlchemyObjectType
        connection_class = connection_class or CountableConnection
        connection_field = connection_field or InstrumentedQuery

        meta.model_list = model_list
        meta.exclude_models = exclude_models
        meta.interfaces = interfaces
        meta.object_type = object_type

        classes = []
        for model in model_list:
            if model.__name__ not in exclude_models:
                submeta = {
                    'Meta': {
                        'model': model,
                        'interfaces': interfaces,
                        'connection_class': connection_class,
                    }
                }
                name = '{}'.format(model.__name__)
                _class = generate_type(model, object_type, name, submeta)
                classes.append(_class)

        for _class in classes:
            field_name = underscore(_class.__name__)
            if not hasattr(cls, field_name):
                setattr(cls, singularize(field_name), _class.Field())
                setattr(cls, pluralize(field_name), connection_field(_class))

        super(SQLAlchemyAutogenQuery,
              cls).__init_subclass_with_meta__(_meta=meta, **options)


class SQLAlchemyAutogenMutations(ObjectType):
    @classmethod
    def __init_subclass_with_meta__(cls, model_list=None, exclude_models=[], **options):
        meta = SQLAlchemyAutogenMutationsOptions(cls)
        meta.model_list = model_list
        meta.exclude_models = exclude_models

        types = [
            (SQLAlchemyEditMutation, 'Edit'),
            (SQLAlchemyCreateMutation, 'Create'),
            (SQLAlchemyDeleteMutation, 'Delete'),
        ]

        classes = []
        for model in model_list:
            if model.__name__ not in exclude_models:
                for (_type, prefix) in types:
                    name = '{}{}'.format(prefix, model.__name__)
                    _class = generate_type(model, _type, name)
                    classes.append(_class)

        for _class in classes:
            field_name = underscore(_class.__name__)
            if not hasattr(cls, field_name):
                setattr(cls, field_name, _class.Field())

        super(SQLAlchemyAutogenMutations,
              cls).__init_subclass_with_meta__(_meta=meta, **options)

