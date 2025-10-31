"""
SQLAlchemy ORM models for database tables.
Includes: Opportunity, Execution, StatsSnapshot, GasPrice, Alert, ChainMetric
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    Boolean,
    Enum,
    Text,
    Index,
    ForeignKey,
    func,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
import enum


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all ORM models"""

    pass


class ExecutionStatus(enum.Enum):
    """Execution status enum"""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REVERTED = "reverted"


class RiskLevel(enum.Enum):
    """Risk level enum"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AlertSeverity(enum.Enum):
    """Alert severity enum"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Opportunity(Base):
    """Arbitrage opportunity model"""

    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    opportunity_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    chain: Mapped[str] = mapped_column(String(50), index=True)
    pair: Mapped[str] = mapped_column(String(50), index=True)
    buy_exchange: Mapped[str] = mapped_column(String(100))
    sell_exchange: Mapped[str] = mapped_column(String(100))
    buy_price: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    sell_price: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    spread_percent: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    gross_profit: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    gas_cost: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    net_profit: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    volume_24h: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    liquidity: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel))
    flash_loan_available: Mapped[bool] = mapped_column(Boolean, default=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, index=True, default=datetime.utcnow
    )
    executed: Mapped[bool] = mapped_column(Boolean, default=False)
    execution_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("executions.id"), nullable=True
    )

    # Indexes
    __table_args__ = (
        Index("ix_opportunities_chain_detected", "chain", "detected_at"),
        Index("ix_opportunities_profit_detected", "net_profit", "detected_at"),
    )

    # Relationships
    execution: Mapped[Optional["Execution"]] = relationship(
        back_populates="opportunity"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "chain": self.chain,
            "pair": self.pair,
            "buyExchange": self.buy_exchange,
            "sellExchange": self.sell_exchange,
            "buyPrice": float(self.buy_price),
            "sellPrice": float(self.sell_price),
            "spread": float(self.spread_percent),
            "profit": float(self.gross_profit),
            "gasEstimate": float(self.gas_cost),
            "netProfit": float(self.net_profit),
            "volume24h": float(self.volume_24h),
            "liquidity": float(self.liquidity),
            "confidence": float(self.confidence),
            "risk": self.risk_level.value,
            "flashLoanAvailable": self.flash_loan_available,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
        }


class Execution(Base):
    """Trade execution model"""

    __tablename__ = "executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("opportunities.opportunity_id")
    )
    chain: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus), index=True)
    tx_hash: Mapped[Optional[str]] = mapped_column(
        String(66), unique=True, nullable=True
    )
    block_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gas_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gas_price_gwei: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    actual_profit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8), nullable=True
    )
    slippage: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime, index=True, default=datetime.utcnow
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Indexes
    __table_args__ = (
        Index("ix_executions_chain_time", "chain", "executed_at"),
        Index("ix_executions_status_time", "status", "executed_at"),
    )

    # Relationships
    opportunity: Mapped["Opportunity"] = relationship(back_populates="execution")

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "chain": self.chain,
            "status": self.status.value,
            "tx_hash": self.tx_hash,
            "block_number": self.block_number,
            "gas_used": self.gas_used,
            "gas_price": float(self.gas_price_gwei) if self.gas_price_gwei else None,
            "actual_profit": float(self.actual_profit) if self.actual_profit else None,
            "slippage": float(self.slippage) if self.slippage else None,
            "error_message": self.error_message,
            "executed_at": self.executed_at.isoformat(),
            "confirmed_at": (
                self.confirmed_at.isoformat() if self.confirmed_at else None
            ),
            "execution_time_ms": self.execution_time_ms,
        }


class StatsSnapshot(Base):
    """Bot performance statistics snapshot (TimescaleDB hypertable)"""

    __tablename__ = "stats_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, index=True, default=datetime.utcnow
    )
    total_scans: Mapped[int] = mapped_column(Integer)
    opportunities_found: Mapped[int] = mapped_column(Integer)
    trades_executed: Mapped[int] = mapped_column(Integer)
    successful_trades: Mapped[int] = mapped_column(Integer)
    failed_trades: Mapped[int] = mapped_column(Integer)
    total_profit: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    total_gas_spent: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    net_profit: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    success_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    avg_profit_per_trade: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    max_drawdown: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    sharpe_ratio: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 4), nullable=True
    )
    active_capital: Mapped[Decimal] = mapped_column(Numeric(20, 2))

    # Indexes
    __table_args__ = (Index("ix_stats_timestamp_desc", "timestamp"),)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "totalScans": self.total_scans,
            "opportunitiesFound": self.opportunities_found,
            "tradesExecuted": self.trades_executed,
            "successfulTrades": self.successful_trades,
            "failedTrades": self.failed_trades,
            "totalProfit": float(self.total_profit),
            "totalGasSpent": float(self.total_gas_spent),
            "netProfit": float(self.net_profit),
            "successRate": float(self.success_rate),
            "avgProfitPerTrade": float(self.avg_profit_per_trade),
            "maxDrawdown": float(self.max_drawdown),
            "sharpeRatio": float(self.sharpe_ratio) if self.sharpe_ratio else None,
            "activeCapital": float(self.active_capital),
        }


class GasPrice(Base):
    """Historical gas price data (TimescaleDB hypertable)"""

    __tablename__ = "gas_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain: Mapped[str] = mapped_column(String(50), index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, index=True, default=datetime.utcnow
    )
    gas_price_gwei: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    base_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    priority_fee: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    block_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Indexes
    __table_args__ = (Index("ix_gas_prices_chain_time", "chain", "timestamp"),)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "chain": self.chain,
            "timestamp": self.timestamp.isoformat(),
            "gasPrice": float(self.gas_price_gwei),
            "baseFee": float(self.base_fee) if self.base_fee else None,
            "priorityFee": float(self.priority_fee) if self.priority_fee else None,
            "blockNumber": self.block_number,
        }


class Alert(Base):
    """System alerts and anomalies"""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    severity: Mapped[AlertSeverity] = mapped_column(Enum(AlertSeverity), index=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    chain: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    message: Mapped[str] = mapped_column(Text)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, index=True, default=datetime.utcnow
    )
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Indexes
    __table_args__ = (Index("ix_alerts_severity_time", "severity", "created_at"),)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "severity": self.severity.value,
            "category": self.category,
            "chain": self.chain,
            "message": self.message,
            "details": self.details,
            "created_at": self.created_at.isoformat(),
            "acknowledged": self.acknowledged,
            "acknowledged_at": (
                self.acknowledged_at.isoformat() if self.acknowledged_at else None
            ),
        }


class ChainMetric(Base):
    """Node health metrics (TimescaleDB hypertable)"""

    __tablename__ = "chain_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain: Mapped[str] = mapped_column(String(50), index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, index=True, default=datetime.utcnow
    )
    block_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    peer_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_syncing: Mapped[bool] = mapped_column(Boolean)
    sync_progress: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20))

    # Indexes
    __table_args__ = (Index("ix_chain_metrics_chain_time", "chain", "timestamp"),)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "chain": self.chain,
            "timestamp": self.timestamp.isoformat(),
            "block_number": self.block_number,
            "peer_count": self.peer_count,
            "is_syncing": self.is_syncing,
            "sync_progress": float(self.sync_progress) if self.sync_progress else None,
            "response_time_ms": self.response_time_ms,
            "status": self.status,
        }
