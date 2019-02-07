import graphene
import sqlalchemy

from graphene.utils.str_converters import to_snake_case
from sqlalchemy.ext.declarative.api import DeclarativeMeta

from .filter_by_input_type import SQLAlchemyFilterByInputObjectType
from .filter_input_type import convert_to_query, SQLAlchemyFilterInputObjectType
from ..api import dispatch, generate_type
from ..fields import SQLAlchemyConnectionField


ORDER_FUNCTIONS = {
    'asc': sqlalchemy.asc,
    'desc': sqlalchemy.desc
}


class InstrumentedQuery(SQLAlchemyConnectionField):
    def __init__(self, _type, *args, **kwargs):
        model = _type._meta.model
        kwargs.setdefault('args', construct_fields(self, model))

        super(InstrumentedQuery, self).__init__(_type, *args, **kwargs)


    @classmethod
    def get_query(cls, model, info, **kwargs):
        query = super(InstrumentedQuery, cls).get_query(model, info, **kwargs)

        query = query.filter_by(**kwargs.get('filter_by', {}))
        query = convert_to_query(
            kwargs.get('filter', {}),
            model,
            query)

        orderings = [
            convert_order_by_params(model, *order.split(' '))
            for order in kwargs.get('order_by', [])
        ]
        query = query.order_by(*orderings)

        return query


def convert_order_by_params(model, name, direction='asc'):
    return ORDER_FUNCTIONS[direction.lower()](getattr(model, to_snake_case(name)))


@dispatch()
def construct_fields(cls: InstrumentedQuery, model: DeclarativeMeta):
    return {
        'filter_by': graphene.Argument(generate_type(SQLAlchemyFilterByInputObjectType, model)),
        'filter': graphene.Argument(generate_type(SQLAlchemyFilterInputObjectType, model)),
        'order_by': graphene.List(graphene.String)
    }
