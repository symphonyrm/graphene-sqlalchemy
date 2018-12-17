# -*- coding: utf-8 -*-

from typing import Callable, Dict, Type

from graphql import GraphQLError
from graphene.types import Argument, Field, Mutation, ID
from graphene.types.objecttype import ObjectType, ObjectTypeOptions
from sqlalchemy.exc import OperationalError

from .create_input_type import SQLAlchemyCreateInputObjectType
from .edit_input_type import SQLAlchemyEditInputObjectType
from ..types import SQLAlchemyObjectType
from ..api import convert_to_instance, generate_type
from ..utils import get_session


class SQLAlchemyMutationOptions(ObjectTypeOptions):
    model = None
    arguments = None  # type: Dict[str, Argument]
    output = None  # type: Type[ObjectType]
    resolver = None  # type: Callable


class SQLAlchemyMutation(Mutation):
    @classmethod
    def mutate(cls, self, info, **kwargs):
        pass


    @classmethod
    def Field(cls, *args, **kwargs):
        return Field(
            cls._meta.output,
            args=cls._meta.arguments,
            resolver=cls._meta.resolver
        )


class SQLAlchemyCreateMutation(SQLAlchemyMutation):
    @classmethod
    def __init_subclass_with_meta__(cls, model=None, arguments=None,
                                    input_type=None, output_type=None,
                                    output=None, **options):
        meta = SQLAlchemyMutationOptions(cls)
        meta.model = model

        input_type = input_type or SQLAlchemyCreateInputObjectType
        input_name = '{}CreateInput'.format(model.__name__)
        input_class = generate_type(model, input_type, input_name)

        output_type = output_type or SQLAlchemyObjectType
        output_name = '{}'.format(model.__name__)
        output_class = generate_type(model, output_type, output_name)

        arguments = arguments or {}
        output = output or output_class

        arguments.setdefault('input', Argument(input_class, required=True))

        super(SQLAlchemyCreateMutation,
              cls).__init_subclass_with_meta__(_meta=meta,
                                               arguments=arguments,
                                               output=output,
                                               **options)


    @classmethod
    def mutate(cls, self, info, **kwargs):
        session = get_session(info.context)
        model = cls._meta.model

        instance = convert_to_instance(model, kwargs['input'])
        session.add(instance)

        try:
            session.commit()
        except OperationalError as e:
            raise GraphQLError(e.orig.args[1])

        return instance


class SQLAlchemyEditMutation(SQLAlchemyMutation):
    @classmethod
    def __init_subclass_with_meta__(cls, model=None, arguments=None,
                                    input_type=None, output_type=None,
                                    output=None, **options):
        meta = SQLAlchemyMutationOptions(cls)
        meta.model = model

        input_type = input_type or SQLAlchemyEditInputObjectType
        input_name = '{}EditInput'.format(model.__name__)
        input_class = generate_type(model, input_type, input_name)

        output_type = output_type or SQLAlchemyObjectType
        output_name = '{}'.format(model.__name__)
        output_class = generate_type(model, output_type, output_name)

        arguments = arguments or {}
        output = output or output_class

        arguments.setdefault('id', ID(required=True))
        arguments.setdefault('input', Argument(input_class, required=True))

        super(SQLAlchemyEditMutation,
              cls).__init_subclass_with_meta__(_meta=meta,
                                               arguments=arguments,
                                               output=output,
                                               **options)


    @classmethod
    def mutate(cls, self, info, **kwargs):
        session = get_session(info.context)
        model = cls._meta.model

        kwargs['input']['id'] = kwargs['id']
        instance = convert_to_instance(model, kwargs['input'])

        instance = session.merge(instance)

        try:
            session.commit()
        except OperationalError as e:
            raise GraphQLError(e.orig.args[1])

        return instance


class SQLAlchemyDeleteMutation(SQLAlchemyMutation):
    @classmethod
    def __init_subclass_with_meta__(cls, model=None, arguments=None,
                                    input_type=None, output_type=None,
                                    output=None, **options):
        meta = SQLAlchemyMutationOptions(cls)
        meta.model = model

        output_type = output_type or SQLAlchemyObjectType
        output_name = '{}'.format(model.__name__)
        output_class = generate_type(model, output_type, output_name)

        arguments = arguments or {}
        output = output or output_class

        arguments.setdefault('id', ID(required=True))

        super(SQLAlchemyDeleteMutation,
              cls).__init_subclass_with_meta__(_meta=meta,
                                               arguments=arguments,
                                               output=output,
                                               **options)


    @classmethod
    def mutate(cls, self, info, **kwargs):
        session = get_session(info.context)
        model = cls._meta.model

        instance = session.query(model).get(kwargs['id'])
        if instance:
            session.delete(instance)
        else:
            raise GraphQLError(
                'No such instance of type %s with id %s' % (model.__name__, kwargs['id']))

        try:
            session.commit()
        except OperationalError as e:
            raise GraphQLError(e.orig.args[1])

        return instance
