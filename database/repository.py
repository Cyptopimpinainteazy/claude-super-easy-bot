"""
Repository layer for database operations - abstracts SQLAlchemy queries.
"""

from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import logging

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

logger = logging.getLogger(__name__)


class OpportunityRepository:
    """Repository for opportunity operations"""

    async def create(
        self, session: AsyncSession, opportunity_data: dict
    ) -> Opportunity:
        """Create new opportunity record"""
        opp = Opportunity(**opportunity_data)
        session.add(opp)
        await session.flush()
        return opp

    async def get_by_id(
        self, session: AsyncSession, opportunity_id: str
    ) -> Optional[Opportunity]:
        """Get opportunity by ID"""
        result = await session.execute(
            select(Opportunity).where(Opportunity.opportunity_id == opportunity_id)
        )
        return result.scalars().first()

    async def get_recent(
        self, session: AsyncSession, limit: int = 20, chain: Optional[str] = None
    ) -> List[Opportunity]:
        """Get recent opportunities"""
        query = select(Opportunity).order_by(desc(Opportunity.detected_at)).limit(limit)

        if chain:
            query = query.where(Opportunity.chain == chain)

        result = await session.execute(query)
        return result.scalars().all()

    async def get_top_profitable(
        self, session: AsyncSession, limit: int = 10, hours: int = 24
    ) -> List[Opportunity]:
        """Get top opportunities by net profit"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        query = (
            select(Opportunity)
            .where(Opportunity.detected_at > cutoff_time)
            .order_by(desc(Opportunity.net_profit))
            .limit(limit)
        )

        result = await session.execute(query)
        return result.scalars().all()

    async def mark_executed(
        self, session: AsyncSession, opportunity_id: str, execution_id: int
    ) -> None:
        """Mark opportunity as executed"""
        await session.execute(
            update(Opportunity)
            .where(Opportunity.opportunity_id == opportunity_id)
            .values(executed=True, execution_id=execution_id)
        )

    async def get_statistics(self, session: AsyncSession, hours: int = 24) -> dict:
        """Get aggregated opportunity statistics"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        result = await session.execute(
            select(
                func.count(Opportunity.id).label("count"),
                func.avg(Opportunity.net_profit).label("avg_profit"),
                func.max(Opportunity.net_profit).label("max_profit"),
                func.min(Opportunity.net_profit).label("min_profit"),
                func.sum(Opportunity.net_profit).label("total_profit"),
                func.avg(Opportunity.confidence).label("avg_confidence"),
            ).where(Opportunity.detected_at > cutoff_time)
        )

        row = result.first()
        return {
            "count": row.count or 0,
            "avg_profit": float(row.avg_profit) if row.avg_profit else 0,
            "max_profit": float(row.max_profit) if row.max_profit else 0,
            "min_profit": float(row.min_profit) if row.min_profit else 0,
            "total_profit": float(row.total_profit) if row.total_profit else 0,
            "avg_confidence": float(row.avg_confidence) if row.avg_confidence else 0,
        }


class ExecutionRepository:
    """Repository for execution operations"""

    async def create(self, session: AsyncSession, execution_data: dict) -> Execution:
        """Create new execution record"""
        execution = Execution(**execution_data)
        session.add(execution)
        await session.flush()
        return execution

    async def update_status(
        self,
        session: AsyncSession,
        execution_id: int,
        status: ExecutionStatus,
        **kwargs
    ) -> None:
        """Update execution status and related fields"""
        update_data = {"status": status}
        update_data.update(kwargs)

        await session.execute(
            update(Execution).where(Execution.id == execution_id).values(**update_data)
        )

    async def get_by_tx_hash(
        self, session: AsyncSession, tx_hash: str
    ) -> Optional[Execution]:
        """Get execution by transaction hash"""
        result = await session.execute(
            select(Execution).where(Execution.tx_hash == tx_hash)
        )
        return result.scalars().first()

    async def get_recent(
        self,
        session: AsyncSession,
        limit: int = 50,
        status: Optional[ExecutionStatus] = None,
    ) -> List[Execution]:
        """Get recent executions"""
        query = select(Execution).order_by(desc(Execution.executed_at)).limit(limit)

        if status:
            query = query.where(Execution.status == status)

        result = await session.execute(query)
        return result.scalars().all()

    async def get_statistics(self, session: AsyncSession, hours: int = 24) -> dict:
        """Calculate execution statistics"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # Total stats
        total_result = await session.execute(
            select(
                func.count(Execution.id).label("total"),
                func.sum(
                    (Execution.status == ExecutionStatus.SUCCESS).cast(
                        __import__("sqlalchemy").Integer
                    )
                ).label("successful"),
                func.sum(
                    (Execution.status == ExecutionStatus.FAILED).cast(
                        __import__("sqlalchemy").Integer
                    )
                ).label("failed"),
                func.sum(Execution.actual_profit).label("total_profit"),
                func.sum(Execution.gas_used).label("total_gas"),
            ).where(Execution.executed_at > cutoff_time)
        )

        row = total_result.first()
        total_count = row.total or 0
        successful = row.successful or 0
        failed = row.failed or 0

        return {
            "total_executions": total_count,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_count * 100) if total_count > 0 else 0,
            "total_profit": float(row.total_profit) if row.total_profit else 0,
            "total_gas": float(row.total_gas) if row.total_gas else 0,
            "avg_profit_per_trade": (
                (float(row.total_profit) / successful) if successful > 0 else 0
            ),
        }


class StatsRepository:
    """Repository for statistics operations"""

    async def create_snapshot(
        self, session: AsyncSession, stats_data: dict
    ) -> StatsSnapshot:
        """Create stats snapshot"""
        snapshot = StatsSnapshot(**stats_data)
        session.add(snapshot)
        await session.flush()
        return snapshot

    async def get_latest(self, session: AsyncSession) -> Optional[StatsSnapshot]:
        """Get most recent stats snapshot"""
        result = await session.execute(
            select(StatsSnapshot).order_by(desc(StatsSnapshot.timestamp)).limit(1)
        )
        return result.scalars().first()

    async def get_time_series(
        self, session: AsyncSession, hours: int = 24, interval_minutes: int = 5
    ) -> List[StatsSnapshot]:
        """Get stats time series for charting"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        result = await session.execute(
            select(StatsSnapshot)
            .where(StatsSnapshot.timestamp > cutoff_time)
            .order_by(StatsSnapshot.timestamp)
        )
        return result.scalars().all()

    async def calculate_current_stats(self, session: AsyncSession) -> dict:
        """Calculate current stats from executions table"""
        # Get execution stats for last 24 hours
        execution_repo = ExecutionRepository()
        exec_stats = await execution_repo.get_statistics(session, hours=24)

        # Get opportunity stats
        opportunity_repo = OpportunityRepository()
        opp_stats = await opportunity_repo.get_statistics(session, hours=24)

        return {
            "total_scans": opp_stats.get("count", 0),
            "opportunities_found": opp_stats.get("count", 0),
            "trades_executed": exec_stats.get("total_executions", 0),
            "successful_trades": exec_stats.get("successful", 0),
            "failed_trades": exec_stats.get("failed", 0),
            "total_profit": Decimal(str(exec_stats.get("total_profit", 0))),
            "total_gas_spent": Decimal(str(exec_stats.get("total_gas", 0))),
            "net_profit": Decimal(
                str(exec_stats.get("total_profit", 0) - exec_stats.get("total_gas", 0))
            ),
            "success_rate": Decimal(str(exec_stats.get("success_rate", 0))),
            "avg_profit_per_trade": Decimal(
                str(exec_stats.get("avg_profit_per_trade", 0))
            ),
            "max_drawdown": Decimal("0"),  # TODO: Calculate from time series
            "sharpe_ratio": None,  # TODO: Calculate from returns
            "active_capital": Decimal("0"),  # TODO: Get from configuration
        }


class GasPriceRepository:
    """Repository for gas price operations"""

    async def record(
        self, session: AsyncSession, chain: str, gas_price: Decimal, **kwargs
    ) -> GasPrice:
        """Record gas price observation"""
        data = {"chain": chain, "gas_price_gwei": gas_price, **kwargs}
        gas_price_obj = GasPrice(**data)
        session.add(gas_price_obj)
        await session.flush()
        return gas_price_obj

    async def get_latest(
        self, session: AsyncSession, chain: Optional[str] = None
    ) -> Dict[str, Decimal]:
        """Get latest gas price for each chain"""
        if chain:
            result = await session.execute(
                select(GasPrice)
                .where(GasPrice.chain == chain)
                .order_by(desc(GasPrice.timestamp))
                .limit(1)
            )
            gas_prices = result.scalars().all()
        else:
            # Get latest for each chain
            subquery = (
                select(GasPrice.chain, GasPrice.gas_price_gwei, GasPrice.timestamp)
                .order_by(GasPrice.chain, desc(GasPrice.timestamp))
                .distinct(GasPrice.chain)
            )

            result = await session.execute(select(GasPrice).from_statement(subquery))
            gas_prices = result.scalars().all()

        return {gp.chain: gp.gas_price_gwei for gp in gas_prices}

    async def get_time_series(
        self, session: AsyncSession, chain: str, hours: int = 24
    ) -> List[GasPrice]:
        """Get gas price history"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        result = await session.execute(
            select(GasPrice)
            .where(and_(GasPrice.chain == chain, GasPrice.timestamp > cutoff_time))
            .order_by(GasPrice.timestamp)
        )
        return result.scalars().all()

    async def get_average(
        self, session: AsyncSession, chain: str, hours: int = 1
    ) -> Decimal:
        """Calculate average gas price over time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        result = await session.execute(
            select(func.avg(GasPrice.gas_price_gwei).label("avg_price")).where(
                and_(GasPrice.chain == chain, GasPrice.timestamp > cutoff_time)
            )
        )

        avg = result.scalar()
        return Decimal(str(avg)) if avg else Decimal("0")


class AlertRepository:
    """Repository for alert operations"""

    async def create(
        self,
        session: AsyncSession,
        severity: AlertSeverity,
        category: str,
        message: str,
        **kwargs
    ) -> Alert:
        """Create new alert"""
        alert = Alert(severity=severity, category=category, message=message, **kwargs)
        session.add(alert)
        await session.flush()
        return alert

    async def get_unacknowledged(
        self, session: AsyncSession, severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get unacknowledged alerts"""
        query = select(Alert).where(Alert.acknowledged == False)

        if severity:
            query = query.where(Alert.severity == severity)

        query = query.order_by(desc(Alert.created_at))

        result = await session.execute(query)
        return result.scalars().all()

    async def acknowledge(self, session: AsyncSession, alert_id: int) -> None:
        """Mark alert as acknowledged"""
        await session.execute(
            update(Alert)
            .where(Alert.id == alert_id)
            .values(acknowledged=True, acknowledged_at=datetime.utcnow())
        )

    async def get_recent(
        self,
        session: AsyncSession,
        limit: int = 100,
        severity: Optional[AlertSeverity] = None,
    ) -> List[Alert]:
        """Get recent alerts"""
        query = select(Alert).order_by(desc(Alert.created_at)).limit(limit)

        if severity:
            query = query.where(Alert.severity == severity)

        result = await session.execute(query)
        return result.scalars().all()


class ChainMetricRepository:
    """Repository for chain metrics operations"""

    async def record(
        self, session: AsyncSession, chain: str, metrics: dict
    ) -> ChainMetric:
        """Record chain health metrics"""
        data = {"chain": chain, **metrics}
        metric = ChainMetric(**data)
        session.add(metric)
        await session.flush()
        return metric

    async def get_latest(self, session: AsyncSession) -> Dict[str, ChainMetric]:
        """Get latest metrics for all chains"""
        result = await session.execute(
            select(ChainMetric)
            .order_by(ChainMetric.chain, desc(ChainMetric.timestamp))
            .distinct(ChainMetric.chain)
        )
        metrics = result.scalars().all()
        return {m.chain: m for m in metrics}

    async def get_time_series(
        self, session: AsyncSession, chain: str, hours: int = 24
    ) -> List[ChainMetric]:
        """Get metrics history"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        result = await session.execute(
            select(ChainMetric)
            .where(
                and_(ChainMetric.chain == chain, ChainMetric.timestamp > cutoff_time)
            )
            .order_by(ChainMetric.timestamp)
        )
        return result.scalars().all()
