#!/usr/bin/env python3

"""
Data retention policy enforcement script for Arbitrage Bot
Runs scheduled cleanup of old data according to retention policies
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timedelta
from decimal import Decimal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import DatabaseManager, get_db_manager
from database.models import Opportunity, Alert, ChainMetric, GasPrice
from sqlalchemy import delete, select, func, and_


async def cleanup_opportunities():
    """Delete opportunities older than retention period"""
    retention_days = int(os.getenv('OPPORTUNITIES_RETENTION_DAYS', '7'))
    dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'

    db_manager = get_db_manager()
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

    try:
        async with db_manager.get_session() as session:
            # Count records to delete
            count_result = await session.execute(
                select(func.count(Opportunity.id)).where(
                    Opportunity.detected_at < cutoff_date
                )
            )
            count = count_result.scalar() or 0

            if count == 0:
                logger.info(f"✓ No opportunities to delete (older than {retention_days} days)")
                return

            logger.info(f"Found {count} opportunities to delete")

            if not dry_run:
                # Delete opportunities
                await session.execute(
                    delete(Opportunity).where(Opportunity.detected_at < cutoff_date)
                )
                await session.commit()
                logger.info(f"✓ Deleted {count} old opportunities")
            else:
                logger.info(f"[DRY RUN] Would delete {count} old opportunities")

    except Exception as e:
        logger.error(f"✗ Failed to cleanup opportunities: {e}")
        raise


async def cleanup_alerts():
    """Delete acknowledged alerts older than retention period"""
    retention_days = int(os.getenv('ALERTS_RETENTION_DAYS', '30'))
    dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'

    db_manager = get_db_manager()
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

    try:
        async with db_manager.get_session() as session:
            # Count records to delete
            count_result = await session.execute(
                select(func.count(Alert.id)).where(
                    and_(
                        Alert.created_at < cutoff_date,
                        Alert.acknowledged == True
                    )
                )
            )
            count = count_result.scalar() or 0

            if count == 0:
                logger.info(f"✓ No alerts to delete (older than {retention_days} days)")
                return

            logger.info(f"Found {count} alerts to delete")

            if not dry_run:
                # Delete alerts
                await session.execute(
                    delete(Alert).where(
                        and_(
                            Alert.created_at < cutoff_date,
                            Alert.acknowledged == True
                        )
                    )
                )
                await session.commit()
                logger.info(f"✓ Deleted {count} old alerts")
            else:
                logger.info(f"[DRY RUN] Would delete {count} old alerts")

    except Exception as e:
        logger.error(f"✗ Failed to cleanup alerts: {e}")
        raise


async def cleanup_chain_metrics():
    """Delete chain metrics older than retention period"""
    retention_days = int(os.getenv('CHAIN_METRICS_RETENTION_DAYS', '7'))
    dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'

    db_manager = get_db_manager()
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

    try:
        async with db_manager.get_session() as session:
            # Count records to delete
            count_result = await session.execute(
                select(func.count(ChainMetric.id)).where(
                    ChainMetric.timestamp < cutoff_date
                )
            )
            count = count_result.scalar() or 0

            if count == 0:
                logger.info(f"✓ No chain metrics to delete (older than {retention_days} days)")
                return

            logger.info(f"Found {count} chain metrics to delete")

            if not dry_run:
                # Delete metrics
                await session.execute(
                    delete(ChainMetric).where(ChainMetric.timestamp < cutoff_date)
                )
                await session.commit()
                logger.info(f"✓ Deleted {count} old chain metrics")
            else:
                logger.info(f"[DRY RUN] Would delete {count} old chain metrics")

    except Exception as e:
        logger.error(f"✗ Failed to cleanup chain metrics: {e}")
        raise


async def cleanup_gas_prices():
    """Delete gas prices older than retention period"""
    retention_days = int(os.getenv('GAS_PRICES_RETENTION_DAYS', '30'))
    dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'

    db_manager = get_db_manager()
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

    try:
        async with db_manager.get_session() as session:
            # Count records to delete
            count_result = await session.execute(
                select(func.count(GasPrice.id)).where(
                    GasPrice.timestamp < cutoff_date
                )
            )
            count = count_result.scalar() or 0

            if count == 0:
                logger.info(f"✓ No gas prices to delete (older than {retention_days} days)")
                return

            logger.info(f"Found {count} gas prices to delete")

            if not dry_run:
                # Delete gas prices
                await session.execute(
                    delete(GasPrice).where(GasPrice.timestamp < cutoff_date)
                )
                await session.commit()
                logger.info(f"✓ Deleted {count} old gas prices")
            else:
                logger.info(f"[DRY RUN] Would delete {count} old gas prices")

    except Exception as e:
        logger.error(f"✗ Failed to cleanup gas prices: {e}")
        raise


async def main():
    """Main cleanup function"""
    logger.info("=" * 60)
    logger.info("Starting data retention cleanup")
    logger.info("=" * 60)

    db_manager = get_db_manager()

    try:
        # Initialize database
        await db_manager.initialize()

        # Run cleanup tasks
        await cleanup_opportunities()
        await cleanup_alerts()
        await cleanup_chain_metrics()
        await cleanup_gas_prices()

        logger.info("=" * 60)
        logger.info("✓ Cleanup completed successfully")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗ Cleanup failed: {e}")
        logger.error("=" * 60)
        sys.exit(1)

    finally:
        await db_manager.close()


if __name__ == '__main__':
    asyncio.run(main())
