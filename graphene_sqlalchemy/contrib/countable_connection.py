from graphene import Int, relay


class CountableConnection(relay.Connection):
    class Meta:
        abstract = True

    total_count = Int()

    @staticmethod
    def resolve_total_count(root, info, *args, **kwargs):
        return root.length
