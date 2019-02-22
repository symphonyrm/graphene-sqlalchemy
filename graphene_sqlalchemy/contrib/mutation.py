from graphql import GraphQLError
from graphene.types import Argument, Field, Mutation, ID
from graphene.types.mutation import MutationOptions
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative.api import DeclarativeMeta

from ..api import convert_to_instance, dispatch, generate_type
from .create_input_type import SQLAlchemyCreateInputObjectType
from .delete_input_type import SQLAlchemyKeysInputObjectType
from .edit_input_type import SQLAlchemyEditInputObjectType
from .filter_object_type import SQLAlchemyFilterObjectType
from ..utils import get_session


class SQLAlchemyMutationOptions(MutationOptions):
    model = None


class SQLAlchemyMutation(Mutation):
    class Meta:
        abstract = True


    @classmethod
    def __init_subclass_with_meta__(cls, model=None, **options):
        meta = SQLAlchemyMutationOptions(cls)
        meta.model = model

        fields = construct_fields(cls, model)
        fields.update(options)

        super(SQLAlchemyMutation,
              cls).__init_subclass_with_meta__(_meta=meta, **fields)


    @classmethod
    def mutate_session(cls, session, model, **kwargs):
        raise NotImplementedError(
            'mutate_session must be defined on subclasses of SQLAlchemyMutation'
        )


    @classmethod
    def mutate(cls, self, info, **kwargs):
        session = get_session(info.context)
        model = cls._meta.model

        instance = cls.mutate_session(session, model, **kwargs)

        try:
            session.commit()
        except OperationalError as e:
            raise GraphQLError(e.orig.args[1])

        return instance


    @classmethod
    def Field(cls, *args, **kwargs):
        return Field(
            cls._meta.output,
            args=cls._meta.arguments,
            resolver=cls._meta.resolver
        )


class SQLAlchemyCreateMutation(SQLAlchemyMutation):
    class Meta:
        abstract = True


    @classmethod
    def mutate_session(cls, session, model, **kwargs):
        instance = convert_to_instance(kwargs['input'], model)
        session.add(instance)

        return instance


@dispatch()
def convert_name(cls: SQLAlchemyCreateMutation, model: DeclarativeMeta):
    return 'Create{}'.format(model.__name__)


@dispatch()
def construct_fields(cls: SQLAlchemyCreateMutation, model: DeclarativeMeta):
    return {
        'arguments': {
            'input': Argument(
                generate_type(SQLAlchemyCreateInputObjectType, model),
                required=True,
            )
        },
        'output': generate_type(SQLAlchemyFilterObjectType, model)
    }


class SQLAlchemyEditMutation(SQLAlchemyMutation):
    class Meta:
        abstract = True


    @classmethod
    def mutate_session(cls, session, model, **kwargs):
        keys = inspect(model).primary_key
        key_input = {}
        for key in keys:
            name = key.name
            if name in kwargs['input']:
                key_input[key.name] = kwargs['input'].pop(name)

        old_instance = session.query(model).get(key_input.values())
        if not old_instance:
            raise GraphQLError(
                'No such instance of type {} with keys {}'.format(
                    model.__name__,
                    key_input))

        new_instance = convert_to_instance(kwargs['input'], model)

        for key, value in new_instance.__dict__.items():
            if not key.startswith('_'):
                setattr(old_instance, key, value)

        return old_instance


@dispatch()
def convert_name(cls: SQLAlchemyEditMutation, model: DeclarativeMeta):
    return 'Edit{}'.format(model.__name__)


@dispatch()
def construct_fields(cls: SQLAlchemyEditMutation, model: DeclarativeMeta):
    return {
        'arguments': {
            'input': Argument(
                generate_type(SQLAlchemyEditInputObjectType, model),
                required=True,
            )
        },
        'output': generate_type(SQLAlchemyFilterObjectType, model)
    }


class SQLAlchemyDeleteMutation(SQLAlchemyMutation):
    class Meta:
        abstract = True


    @classmethod
    def mutate_session(cls, session, model, **kwargs):
        keys = inspect(model).primary_key
        key_input = {}
        for key in keys:
            name = key.name
            if name in kwargs['input']:
                key_input[key.name] = kwargs['input'].pop(name)

        instance = session.query(model).get(key_input.values())
        if instance:
            session.delete(instance)
        else:
            raise GraphQLError(
                'No such instance of type {} with keys {}'.format(
                    model.__name__,
                    key_input))

        return instance


@dispatch()
def convert_name(cls: SQLAlchemyDeleteMutation, model: DeclarativeMeta):
    return 'Delete{}'.format(model.__name__)


@dispatch()
def construct_fields(cls: SQLAlchemyDeleteMutation, model: DeclarativeMeta):
    return {
        'arguments': {
            'input': Argument(
                generate_type(SQLAlchemyKeysInputObjectType, model),
                required=True,
            )
        },
        'output': generate_type(SQLAlchemyFilterObjectType, model)
    }
