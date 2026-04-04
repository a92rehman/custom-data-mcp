"""Validate that queries include required partition filters."""

from pydantic import BaseModel


class ValidationResult(BaseModel):
    valid: bool
    error: str = ""


class PartitionValidator:
    """Enforces partition-first execution policy."""

    def validate(
        self, partition_column: str | None, filters: dict[str, str]
    ) -> ValidationResult:
        if partition_column is None:
            return ValidationResult(
                valid=False,
                error=(
                    "This table has no partition column."
                    " Flagged as partition debt for the data team."
                ),
            )
        date_from_key = f"{partition_column}_from"
        date_to_key = f"{partition_column}_to"
        has_filter = date_from_key in filters or date_to_key in filters
        if not has_filter:
            return ValidationResult(
                valid=False,
                error=(
                    f"Please specify a date range. Without a filter on '{partition_column}',"
                    " this query would scan the entire table."
                ),
            )
        return ValidationResult(valid=True)
