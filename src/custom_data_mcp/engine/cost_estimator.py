"""Estimate BigQuery query cost via dry run."""

from google.cloud import bigquery
from pydantic import BaseModel


class CostEstimate(BaseModel):
    bytes_processed: int
    cost_usd: float
    needs_confirmation: bool


class CostEstimator:
    """Estimate query cost before execution."""

    PRICE_PER_TB_USD = 6.25
    BYTES_PER_TB = 1_099_511_627_776

    def __init__(self, bq_client: bigquery.Client, max_bytes: int) -> None:
        self._client = bq_client
        self._max_bytes = max_bytes

    def estimate(self, sql: str, params: list | None = None) -> CostEstimate:
        """Run a dry-run query to estimate cost."""
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        if params:
            job_config.query_parameters = params
        job = self._client.query(sql, job_config=job_config)
        bytes_processed = job.total_bytes_processed
        cost_usd = (bytes_processed / self.BYTES_PER_TB) * self.PRICE_PER_TB_USD
        return CostEstimate(
            bytes_processed=bytes_processed,
            cost_usd=cost_usd,
            needs_confirmation=bytes_processed > self._max_bytes,
        )
