import graphene
import sqlalchemy

from graphene.utils.str_converters import to_snake_case

from .filter_by_input_type import SQLAlchemyFilterByInputObjectType
from .filter_input_type import convert_to_query, SQLAlchemyFilterInputObjectType
from ..fields import SQLAlchemyConnectionField


ORDER_FUNCTIONS = {
    'asc': sqlalchemy.asc,
    'desc': sqlalchemy.desc
}


class InstrumentedQuery(SQLAlchemyConnectionField):
    def __init__(self, _type, *args, **kwargs):
        model = _type._meta.model

        exclude = kwargs.get('exclude_fields', [])
        only = kwargs.get('only_fields', [])
        filter_by_class = kwargs.get('filter_by_class', SQLAlchemyFilterByInputObjectType)
        filter_class = kwargs.get('filter_class', SQLAlchemyFilterInputObjectType)

        kwargs = {k: v for k, v in kwargs if k not in exclude}
        args = kwargs.pop('args', dict())
        meta = {
            'Meta': {
                'model': model,
                'exclude_fields': exclude,
                'only_fields': only
            }
        }

        filter_by_type = type(
            '{}FilterByInput'.format(model.__name__),
            (filter_by_class,),
            meta
        )
        args.setdefault('filter_by', graphene.Argument(filter_by_type))

        filter_type = type(
            '{}FilterInput'.format(model.__name__),
            (filter_class,),
            meta
        )
        args.setdefault('filter', graphene.Argument(filter_type))

        args['order_by'] = graphene.List(graphene.String, required=False)

        super(InstrumentedQuery, self).__init__(_type, args=args, **kwargs)


    @classmethod
    def get_query(cls, model, info, **kwargs):
        query = super(InstrumentedQuery, cls).get_query(model, info, **kwargs)

        query = query.filter_by(**kwargs.get('filter_by', {}))
        query = convert_to_query(
            model,
            query,
            kwargs.get('filter', {}))

        orderings = [
            convert_order_by_params(model, *order.split(' '))
            for order in kwargs.get('order_by', [])
        ]
        query = query.order_by(*orderings)

        return query


def convert_order_by_params(model, name, direction='asc'):
    return ORDER_FUNCTIONS[direction.lower()](getattr(model, to_snake_case(name)))
