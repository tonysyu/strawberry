---
title: Schema Directives
---

# Schema Directives

Strawberry supports
[schema directives](https://spec.graphql.org/June2018/#TypeSystemDirectiveLocation),
which are directives that provide a way to add additional metadata to your GraphQL
schema and hooks to alter how types behave.

> For example our [Apollo Federation integration](../guides/federation.md) is
> based on schema directives.

Let's see how you can implement a schema directive in Strawberry, here we are
creating a directive called `keys` that can be applied to
[Object types definitions](./object-types.md) and accepts one parameter called
`fields`. Note that directive names, by default, are converted to camelCase on
the GraphQL schema.

Here's how we can use it in our schema:

```python
import strawberry
from strawberry.schema_directive import Location

@strawberry.schema_directive(locations=[Location.OBJECT])
class Keys:
    fields: str


from .directives import Keys

@strawberry.type(directives=[Keys(fields="id")])
class User:
    id: strawberry.ID
    name: str
```

This will result in the following schema:

```graphql
type User @keys(fields: "id") {
  id: ID!
  name: String!
}
```

## Overriding field names

You can use `strawberry.directive_field` to override the name of a field:

```python
@strawberry.schema_directive(locations=[Location.OBJECT])
class Keys:
    fields: str = strawberry.directive_field(name="as")
```

## Locations

Schema directives can be applied to many different parts of a schema. Here's the
list of all the allowed locations:

| Name                   |                         | Description                                              |
| ---------------------- | ----------------------- | -------------------------------------------------------- |
| SCHEMA                 | `strawberry.Schema`     | The definition of a schema                               |
| SCALAR                 | `strawberry.scalar`     | The definition of a scalar                               |
| OBJECT                 | `strawberry.type`       | The definition of an object type                         |
| FIELD_DEFINITION       | `strawberry.field`      | The definition of a field on an object type or interface |
| ARGUMENT_DEFINITION    | `strawberry.argument`   | The definition of an argument                            |
| INTERFACE              | `strawberry.interface`  | The definition of an interface                           |
| UNION                  | `strawberry.union`      | The definition of an union                               |
| ENUM                   | `strawberry.enum`       | The definition of a enum                                 |
| ENUM_VALUE             | `strawberry.enum_value` | The definition of a enum value                           |
| INPUT_OBJECT           | `strawberry.input`      | The definition of an input object type                   |
| INPUT_FIELD_DEFINITION | `strawberry.field`      | The definition of a field on an input type               |

## Implementing schema directive behavior

If you have schema directives that alter the behavior of resolvers, then you'll need to add the
`SchemaDirectivesExtensionSync` extension when creating your schema:

```python
from strawberry.extensions.schema_directives import SchemaDirectivesExtensionSync

@strawberry.type
class Query:
    ...

schema = strawberry.Schema(query=Query, extensions=[SchemaDirectivesExtensionSync])
```

You can add behavior by adding the `on_resolve_start` and/or `on_resolve_end` methods, which are
run before and after resolvers are executed. For example:

```python
@strawberry.schema_directive(locations=[Location.OBJECT])
class Example:

    def on_resolve_start(
        self, root, info: GraphQLResolveInfo, *args, **kwargs
    ) -> None:
        # Add your logic here.

    def on_resolve_end(
        self, value: Any, root, info: GraphQLResolveInfo, *args, **kwargs
    ) -> AwaitableOrValue[Any]:
        # Add your logic here---possibly modifying the resolved value.
        return value
```

### Example: `datetime` format

The following example formats a `datetime` value returned by a resolver as a datetime string with a
pre-specified format:

```python
from graphql import GraphQLResolveInfo

@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
class Date:
    format: str

    def on_resolve_end(
        self, value: Any, root, info: GraphQLResolveInfo, *args, **kwargs
    ) -> None:
        if not isinstance(value, datetime):
            return value

        if self.format:
            return value.strftime(self.format)

        return value.isoformat()
```

You can then add the directive to a field in your API:

```python
from datetime import datetime

def get_date():
    return datetime(2020, 1, 1)

@strawberry.type
class Query:
    date: str = strawberry.field(directives=[Date(format="%Y-%m-%d")], resolver=get_date)
```

### Example: `IsAuthenticated` check

You can also use schema directives to require authentication to access fields:

```python
@strawberry.schema_directive(locations=[Location.OBJECT, Location.FIELD_DEFINITION])
class IsAuthenticated:
    unauthorized_message: str = "User is not authenticated"

    def on_resolve_start(
        self, root, info: GraphQLResolveInfo, *args, **kwargs
    ) -> AwaitableOrValue[Any]:
        # This assumes that authenticated users are added to the execution context:
        if "user" not in info.context:
            raise PermissionError(self.unauthorized_message)
```

This can be used as a type directive:

```python
@strawberry.type(directives=[IsAuthenticated()])
class User:
    name: str = "Tony"

@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return User()
```

or as a field directive:

```python
@strawberry.type
class User:
    name: str = "Tony"

@strawberry.type
class Query:
    @strawberry.field(directives=[IsAuthenticated()])
    def user(self) -> User:
        return User()
```
