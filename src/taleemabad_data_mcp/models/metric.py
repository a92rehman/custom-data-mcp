"""Gold metric definition model."""

from enum import StrEnum

from pydantic import BaseModel


class MetricStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    CERTIFIED = "certified"
    DEPRECATED = "deprecated"


class MetricType(StrEnum):
    SIMPLE = "simple"
    RATIO = "ratio"
    CUMULATIVE = "cumulative"
    DERIVED = "derived"


class Sensitivity(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    EXTERNAL_GUARDED = "external_guarded"


class MetricLineage(BaseModel):
    silver: str
    bronze: str


class GoldMetric(BaseModel):
    name: str
    display_name: str
    description: str
    category: str
    tier: str = "gold"
    status: MetricStatus
    type: MetricType
    target: str
    source_table: str
    partition_column: str
    dimensions: list[str]
    freshness_sla_hours: int
    sensitivity: Sensitivity
    owner: str
    lineage: MetricLineage
    synonyms: list[str] = []

    @property
    def is_queryable(self) -> bool:
        return self.status == MetricStatus.CERTIFIED
