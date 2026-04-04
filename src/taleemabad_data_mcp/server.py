"""FastMCP server setup with lifespan and tool registration."""

from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from taleemabad_data_mcp.config import ServerConfig
from taleemabad_data_mcp.engine.audit_logger import AuditLogger
from taleemabad_data_mcp.engine.rule_engine import RuleEngine
from taleemabad_data_mcp.tools.governance_tools import register_governance_tools


@dataclass
class AppContext:
    config: ServerConfig
    rule_engine: RuleEngine
    audit_logger: AuditLogger


@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Initialize server-wide resources."""
    config = ServerConfig()
    rules_dir = Path(__file__).parent / "rules"
    rule_engine = RuleEngine(rules_dir)
    rule_engine.load()
    audit_logger = AuditLogger()
    yield AppContext(config=config, rule_engine=rule_engine, audit_logger=audit_logger)


mcp = FastMCP("Taleemabad Data Navigator", lifespan=app_lifespan)

# For Phase 1: also load eagerly for direct call_tool compatibility in tests
_rules_dir = Path(__file__).parent / "rules"
_rule_engine = RuleEngine(_rules_dir)
_rule_engine.load()
register_governance_tools(mcp, _rule_engine)
