import graphene

class DatabaseId(graphene.Interface):
    db_id = graphene.ID(required=True)
