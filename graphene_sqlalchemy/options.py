from graphene.types.objecttype import ObjectType, ObjectTypeOptions

class SQLAlchemyObjectTypeOptions(ObjectTypeOptions):
    model = None  # type: Model
    connection = None  # type: Type[Connection]
    id = None  # type: str
    arguments = None
    resolver = None  # type: Callable
