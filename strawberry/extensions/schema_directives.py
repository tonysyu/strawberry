from typing import TYPE_CHECKING, Any, Tuple

from graphql import GraphQLResolveInfo

from strawberry.extensions import Extension
from strawberry.field import StrawberryField
from strawberry.utils.await_maybe import AwaitableOrValue

if TYPE_CHECKING:
    pass


class SchemaDirectivesExtensionSync(Extension):
    def resolve(
        self, _next, root, info: GraphQLResolveInfo, *args, **kwargs
    ) -> AwaitableOrValue[Any]:
        schema_directives = get_directives_for_resolver_info(info)

        for directive in schema_directives:
            if hasattr(directive, "on_resolve_start"):
                directive.on_resolve_start(root, info, *args, **kwargs)

        value = _next(root, info, *args, **kwargs)

        for directive in schema_directives:
            if hasattr(directive, "on_resolve_end"):
                value = directive.on_resolve_end(value, root, info, *args, **kwargs)

        return value


def get_directives_for_resolver_info(info: GraphQLResolveInfo) -> Tuple[Any, ...]:
    schema = info.schema._strawberry_schema  # type: ignore
    field = schema.get_field_for_type(
        field_name=info.field_name, type_name=info.parent_type.name
    )

    if field is None:
        return ()

    return tuple(field.directives) + get_type_directives_from_field(field)


def get_type_directives_from_field(field: StrawberryField) -> Tuple[Any, ...]:
    if not hasattr(field.type, "_type_definition"):
        return ()

    return tuple(field.type._type_definition.directives)
