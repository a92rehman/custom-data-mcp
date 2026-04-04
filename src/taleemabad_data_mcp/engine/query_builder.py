"""Generate parameterized SQL from Gold metric definitions."""

from google.cloud import bigquery

from taleemabad_data_mcp.models.metric import GoldMetric


class QueryBuilder:
    """Builds parameterized BigQuery SQL from metric definitions."""

    def __init__(self, project: str, dataset: str) -> None:
        self._project = project
        self._dataset = dataset

    def build(
        self,
        metric: GoldMetric,
        filters: dict[str, str],
    ) -> tuple[str, list[bigquery.ScalarQueryParameter]]:
        """Build a parameterized SQL query from a metric and filters."""
        table = f"{self._project}.{self._dataset}.{metric.source_table}"
        params: list[bigquery.ScalarQueryParameter] = []
        where_clauses: list[str] = []

        pc = metric.partition_column
        from_key = f"{pc}_from"
        to_key = f"{pc}_to"

        if from_key in filters:
            where_clauses.append(f"{pc} >= @date_from")
            params.append(bigquery.ScalarQueryParameter("date_from", "STRING", filters[from_key]))

        if to_key in filters:
            where_clauses.append(f"{pc} <= @date_to")
            params.append(bigquery.ScalarQueryParameter("date_to", "STRING", filters[to_key]))

        reserved_keys = {from_key, to_key}
        for key, value in filters.items():
            if key in reserved_keys:
                continue
            if key not in metric.dimensions:
                raise ValueError(
                    f"'{key}' is not a valid dimension for metric '{metric.name}'. "
                    f"Valid dimensions: {metric.dimensions}"
                )
            param_name = f"dim_{key}"
            where_clauses.append(f"{key} = @{param_name}")
            params.append(bigquery.ScalarQueryParameter(param_name, "STRING", value))

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        sql = f"SELECT * FROM `{table}` WHERE {where_sql} LIMIT 1000"
        return sql, params
