from datetime import datetime
from typing import Any

from graphql import GraphQLResolveInfo

import strawberry
from strawberry.extensions.schema_directives import SchemaDirectivesExtensionSync
from strawberry.schema_directive import Location
from strawberry.utils.await_maybe import AwaitableOrValue


@strawberry.schema_directive(locations=[Location.OBJECT, Location.FIELD_DEFINITION])
class IsAuthenticated:
    unauthorized_message: str = "User is not authenticated"

    def on_resolve_start(self, root, info: GraphQLResolveInfo, *args, **kwargs):
        raise PermissionError(self.unauthorized_message)


def test_is_authenticated_field_directive():
    @strawberry.type
    class User:
        name: str = "Tony"

    @strawberry.type
    class Query:
        @strawberry.field(directives=[IsAuthenticated()])
        def user(self) -> User:
            return User()

    schema = strawberry.Schema(query=Query, extensions=[SchemaDirectivesExtensionSync])

    result = schema.execute_sync("query { user { name }}")

    assert result.errors
    assert result.errors[0].message == IsAuthenticated.unauthorized_message


def test_is_authenticated_type_directive():
    @strawberry.type(directives=[IsAuthenticated()])
    class User:
        name: str = "Tony"

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User()

    schema = strawberry.Schema(query=Query, extensions=[SchemaDirectivesExtensionSync])

    result = schema.execute_sync("query { user { name }}")

    assert result.errors
    assert result.errors[0].message == IsAuthenticated.unauthorized_message


def test_date_string_format_directive():
    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Date:
        format: str

        def on_resolve_end(
            self, value: Any, root, info: GraphQLResolveInfo, *args, **kwargs
        ) -> AwaitableOrValue[Any]:
            if not isinstance(value, datetime):
                return value

            if self.format:
                return value.strftime(self.format)

            return value.isoformat()

    @strawberry.type
    class Query:
        date: str = strawberry.field(
            directives=[Date(format="%Y-%m-%d")],
            resolver=lambda: datetime(2020, 1, 1),
        )

    schema = strawberry.Schema(query=Query, extensions=[SchemaDirectivesExtensionSync])
    result = schema.execute_sync("query { date }")

    assert not result.errors
    assert result.data["date"] == "2020-01-01"
