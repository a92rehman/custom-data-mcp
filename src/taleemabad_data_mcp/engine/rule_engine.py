"""Load Gold metric definitions from YAML and resolve queries to metrics."""

from pathlib import Path

import structlog
import yaml

from taleemabad_data_mcp.models.metric import GoldMetric

logger = structlog.get_logger()


class RuleEngine:
    """Loads metric YAML files and resolves queries to GoldMetric objects."""

    def __init__(self, rules_dir: Path) -> None:
        self._rules_dir = rules_dir
        self._metrics: dict[str, GoldMetric] = {}
        self._synonyms: dict[str, str] = {}

    def load(self) -> None:
        """Load all YAML metric definitions from the rules directory."""
        self._metrics.clear()
        self._synonyms.clear()

        for yaml_file in self._rules_dir.rglob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    logger.warning("skipping_non_dict_yaml", file=str(yaml_file))
                    continue
                metric = GoldMetric(**data)
            except (yaml.YAMLError, Exception) as e:
                logger.error("failed_to_load_metric", file=str(yaml_file), error=str(e))
                continue

            key = metric.name.lower()
            if key in self._metrics:
                logger.warning("duplicate_metric_name", name=metric.name, file=str(yaml_file))
            self._metrics[key] = metric
            for synonym in metric.synonyms:
                syn_key = synonym.lower()
                if syn_key in self._synonyms:
                    logger.warning("duplicate_synonym", synonym=synonym, file=str(yaml_file))
                self._synonyms[syn_key] = key

    def resolve(self, name_or_synonym: str) -> GoldMetric | None:
        """Resolve a metric by exact name or synonym. Returns None if not found."""
        key = name_or_synonym.lower().strip()
        if key in self._metrics:
            return self._metrics[key]
        metric_name = self._synonyms.get(key)
        if metric_name:
            return self._metrics.get(metric_name)
        return None

    def list_all(self) -> list[GoldMetric]:
        """Return all loaded metrics."""
        return list(self._metrics.values())

    def list_by_category(self, category: str) -> list[GoldMetric]:
        """Return metrics filtered by category."""
        return [m for m in self._metrics.values() if m.category == category]

    @property
    def metrics(self) -> dict[str, GoldMetric]:
        return self._metrics
