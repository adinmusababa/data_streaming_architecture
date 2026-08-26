"""
Schema Validator - Pydantic-based schema validation for data rows.

Validates each row against a configurable schema definition.
Supports both strict mode (raise on error) and permissive mode (collect errors).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ValidationError, create_model
from shared_sdk.logger import get_logger

logger = get_logger("schema_validator")


@dataclass
class SchemaValidationResult:
    """Result of schema validation for a single row."""

    is_valid: bool
    row_index: int
    validated_data: dict[str, Any] | None = None
    errors: list[dict[str, Any]] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.utcnow)


class SchemaValidator:
    """
    Validates data rows against a configurable schema.

    Schema is defined as a dict mapping field names to type specifications.
    Supports: str, int, float, bool, datetime, and optional variants.
    """

    # Type mapping from config strings to Python types
    TYPE_MAP = {
        "string": str,
        "int": int,
        "integer": int,
        "float": float,
        "double": float,
        "bool": bool,
        "boolean": bool,
        "datetime": datetime,
        "date": datetime,
    }

    def __init__(
        self,
        schema: dict[str, Any] | None = None,
        strict: bool = False,
        required_fields: list[str] | None = None,
        field_types: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize validator.

        Args:
            schema: Full schema dict (e.g., {"fields": [{"name": "temp", "type": "float", "required": true}]})
            strict: If True, raise on validation error; if False, collect errors
            required_fields: List of required field names (alternative to schema)
            field_types: Dict of field_name -> type_string (alternative to schema)
        """
        self.strict = strict
        self._model: type[BaseModel] | None = None
        self._field_types: dict[str, type] = {}
        self._required_fields: set[str] = set(required_fields or [])
        self._schema_config = schema or {}

        if schema:
            self._build_from_schema(schema)
        elif field_types:
            self._build_from_field_types(field_types)

    def _build_from_schema(self, schema: dict[str, Any]) -> None:
        """Build Pydantic model from schema definition."""
        fields: dict[str, tuple[type, Any]] = {}

        for field_def in schema.get("fields", []):
            name = field_def["name"]
            type_str = field_def.get("type", "string")
            required = field_def.get("required", False)
            default = field_def.get("default", ...)

            py_type = self.TYPE_MAP.get(type_str.lower(), str)

            if not required:
                py_type = Optional[py_type]
                default = default if default is not ... else None

            fields[name] = (py_type, default)
            self._field_types[name] = py_type
            if required:
                self._required_fields.add(name)

        if fields:
            self._model = create_model("DynamicSchema", **fields)

    def _build_from_field_types(self, field_types: dict[str, str]) -> None:
        """Build Pydantic model from simple field_types dict."""
        fields: dict[str, tuple[type, Any]] = {}

        for name, type_str in field_types.items():
            py_type = self.TYPE_MAP.get(type_str.lower(), str)
            required = name in self._required_fields
            if not required:
                py_type = Optional[py_type]
                fields[name] = (py_type, None)
            else:
                fields[name] = (py_type, ...)
            self._field_types[name] = py_type

        if fields:
            self._model = create_model("DynamicSchema", **fields)

    def update_schema(self, schema: dict[str, Any]) -> None:
        """Update schema at runtime (e.g., from config service reload)."""
        self._build_from_schema(schema)
        logger.info("Schema validator updated", fields=list(self._field_types.keys()))

    def validate(self, row: dict[str, Any], row_index: int = 0) -> SchemaValidationResult:
        """
        Validate a single row against the schema.

        Returns:
            SchemaValidationResult with validated data or errors.
        """
        if self._model is None:
            # No schema defined - pass through
            return SchemaValidationResult(
                is_valid=True,
                row_index=row_index,
                validated_data=row,
            )

        try:
            validated = self._model(**row)
            return SchemaValidationResult(
                is_valid=True,
                row_index=row_index,
                validated_data=validated.model_dump(),
            )
        except ValidationError as e:
            errors = [
                {
                    "field": ".".join(str(x) for x in err["loc"]),
                    "message": err["msg"],
                    "type": err["type"],
                    "input": err.get("input"),
                }
                for err in e.errors()
            ]

            if self.strict:
                raise

            logger.warning(
                "Schema validation failed",
                row_index=row_index,
                errors=errors,
            )

            return SchemaValidationResult(
                is_valid=False,
                row_index=row_index,
                validated_data=None,
                errors=errors,
            )

    def validate_batch(self, rows: list[dict[str, Any]]) -> list[SchemaValidationResult]:
        """Validate a batch of rows."""
        return [self.validate(row, i) for i, row in enumerate(rows)]

    @property
    def fields(self) -> dict[str, type]:
        """Return field type mapping."""
        return self._field_types.copy()

    @property
    def required_fields(self) -> set[str]:
        """Return required field names."""
        return self._required_fields.copy()