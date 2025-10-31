"""
Database module for arbitrage bot - handles persistence, caching, and data management.
"""

from .models import (
    Opportunity,
    Execution,
    StatsSnapshot,
    GasPrice,
    Alert,
    ChainMetric,
    ExecutionStatus,
    RiskLevel,
    AlertSeverity,
)
from .connection import DatabaseManager, get_db_manager
from .cache import RedisCache, get_redis_cache

__all__ = [
    "Opportunity",
    "Execution",
    "StatsSnapshot",
    "GasPrice",
    "Alert",
    "ChainMetric",
    "ExecutionStatus",
    "RiskLevel",
    "AlertSeverity",
    "DatabaseManager",
    "get_db_manager",
    "RedisCache",
    "get_redis_cache",
]
