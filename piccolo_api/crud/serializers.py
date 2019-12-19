from __future__ import annotations
from functools import lru_cache
import typing as t
import uuid

from asyncpg.pgproto.pgproto import UUID
from piccolo.columns.column_types import ForeignKey
import pydantic

if t.TYPE_CHECKING:
    from piccolo.table import Table


class Config(pydantic.BaseConfig):
    json_encoders = {uuid.UUID: lambda i: str(i), UUID: lambda i: str(i)}
    arbitrary_types_allowed = True


@lru_cache()
def create_pydantic_model(
    table: Table, include_default_columns=False, include_readable=False
):
    """
    Create a Pydantic model representing a table.

    :param include_default_columns: Whether to include columns like 'id' in the
        serialiser.
    :param include_readable: Whether to include 'readable' columns, which
        give a string representation of a foreign key.
    """
    columns: t.Dict[str, t.Any] = {}
    piccolo_columns = (
        table._meta.columns
        if include_default_columns
        else table._meta.non_default_columns
    )
    for column in piccolo_columns:
        column_name = column._meta.name
        if type(column) == ForeignKey:
            is_optional = hasattr(column, "default") or column._meta.null
            _type = (
                t.Optional[column.value_type]
                if is_optional
                else column.value_type
            )
            field = pydantic.Field(
                default=None,
                foreign_key=True,
                to=column._foreign_key_meta.references._meta.tablename,
            )
            columns[column_name] = (_type, field)
            if include_readable:
                columns[f"{column_name}_readable"] = (str, None)
        else:
            _type = (
                t.Optional[column.value_type]
                if hasattr(column, "default")
                else column.value_type
            )
            columns[column_name] = (_type, None)

    return pydantic.create_model(
        str(table.__name__), __config__=Config, **columns,
    )
