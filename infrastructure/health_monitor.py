"""
Node health monitor - periodic health checks and alert callbacks.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from datetime import datetime

from .connection_manager import EnhancedBlockchainManager

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status enum."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ChainMetrics:
    """Metrics for a single chain."""

    chain: str
    status: HealthStatus = HealthStatus.UNKNOWN
    is_syncing: Optional[bool] = None
    block_number: Optional[int] = None
    peer_count: Optional[int] = None
    net_version: Optional[int] = None
    last_check: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chain": self.chain,
            "status": self.status.value,
            "is_syncing": self.is_syncing,
            "block_number": self.block_number,
            "peer_count": self.peer_count,
            "net_version": self.net_version,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_error": self.last_error,
            "consecutive_failures": self.consecutive_failures,
        }


@dataclass
class ChainHealth:
    """Health status for all chains."""

    timestamp: datetime = field(default_factory=datetime.utcnow)
    chains: Dict[str, ChainMetrics] = field(default_factory=dict)
    overall_status: HealthStatus = HealthStatus.UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "overall_status": self.overall_status.value,
            "chains": {k: v.to_dict() for k, v in self.chains.items()},
        }


class NodeHealthMonitor:
    """
    Monitors health of blockchain nodes with periodic checks.
    Performs: eth_syncing, net_version, eth_blockNumber, net_peerCount checks.
    """

    def __init__(
        self,
        blockchain_manager: EnhancedBlockchainManager,
        check_interval: int = 30,
        max_failures: int = 5,
    ):
        """
        Initialize health monitor.

        Args:
            blockchain_manager: EnhancedBlockchainManager instance
            check_interval: Seconds between health checks
            max_failures: Max consecutive failures before marking unhealthy
        """
        self.blockchain_manager = blockchain_manager
        self.check_interval = check_interval
        self.max_failures = max_failures
        self.is_running = False
        self.metrics: Dict[str, ChainMetrics] = {}
        self.alert_callbacks: List[Callable[[ChainHealth], None]] = []
        self._monitor_task = None

    def register_alert_callback(self, callback: Callable[[ChainHealth], None]):
        """Register a callback to be called on health updates."""
        self.alert_callbacks.append(callback)

    def get_health_summary(self) -> ChainHealth:
        """Get current health summary for all chains."""
        # Determine overall status
        if not self.metrics:
            overall = HealthStatus.UNKNOWN
        else:
            statuses = [m.status for m in self.metrics.values()]
            if all(s == HealthStatus.HEALTHY for s in statuses):
                overall = HealthStatus.HEALTHY
            elif any(s == HealthStatus.UNHEALTHY for s in statuses):
                overall = HealthStatus.UNHEALTHY
            else:
                overall = HealthStatus.DEGRADED

        return ChainHealth(
            chains={k: v for k, v in self.metrics.items()}, overall_status=overall
        )

    async def start(self):
        """Start the health monitor."""
        if self.is_running:
            logger.warning("Health monitor already running")
            return

        self.is_running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("✓ Health monitor started")

    async def stop(self):
        """Stop the health monitor."""
        self.is_running = False
        if self._monitor_task:
            try:
                await asyncio.wait_for(self._monitor_task, timeout=5)
            except asyncio.TimeoutError:
                self._monitor_task.cancel()
        logger.info("✓ Health monitor stopped")

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_running:
            try:
                await self._check_all_chains()

                # Notify callbacks
                health = self.get_health_summary()
                for callback in self.alert_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(health)
                        else:
                            callback(health)
                    except Exception as e:
                        logger.error(f"Error in alert callback: {e}")

                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(self.check_interval)

    async def _check_all_chains(self):
        """Check health of all configured chains."""
        tasks = []
        for chain in self.blockchain_manager.node_config.get_all_chains():
            tasks.append(self._check_chain(chain))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            chain = list(self.blockchain_manager.node_config.get_all_chains())[i]
            if isinstance(result, Exception):
                logger.error(f"Error checking {chain}: {result}")

    async def _check_chain(self, chain: str):
        """Check health of a specific chain."""
        if chain not in self.metrics:
            self.metrics[chain] = ChainMetrics(chain=chain)

        metrics = self.metrics[chain]

        try:
            w3 = await self.blockchain_manager.get_http_web3(chain)

            # Perform health checks
            checks = await asyncio.gather(
                self._check_eth_syncing(w3),
                self._check_net_version(w3),
                self._check_block_number(w3),
                self._check_peer_count(w3),
                return_exceptions=True,
            )

            is_syncing, net_version, block_number, peer_count = checks

            # Update metrics
            metrics.is_syncing = (
                is_syncing if not isinstance(is_syncing, Exception) else None
            )
            metrics.net_version = (
                net_version if not isinstance(net_version, Exception) else None
            )
            metrics.block_number = (
                block_number if not isinstance(block_number, Exception) else None
            )
            metrics.peer_count = (
                peer_count if not isinstance(peer_count, Exception) else None
            )
            metrics.last_check = datetime.utcnow()
            metrics.last_error = None
            metrics.consecutive_failures = 0

            # Determine status
            if isinstance(is_syncing, Exception) or isinstance(block_number, Exception):
                metrics.status = HealthStatus.UNHEALTHY
                metrics.consecutive_failures += 1
                metrics.last_error = str(
                    is_syncing if isinstance(is_syncing, Exception) else block_number
                )
            else:
                if is_syncing and block_number:
                    metrics.status = HealthStatus.HEALTHY
                else:
                    metrics.status = HealthStatus.DEGRADED

            logger.debug(
                f"✓ {chain.upper()} health: {metrics.status.value} "
                f"(block: {metrics.block_number}, peers: {metrics.peer_count})"
            )

        except Exception as e:
            metrics.status = HealthStatus.UNHEALTHY
            metrics.consecutive_failures += 1
            metrics.last_error = str(e)
            metrics.last_check = datetime.utcnow()
            logger.warning(f"✗ {chain.upper()} health check failed: {e}")

    async def _check_eth_syncing(self, w3) -> bool:
        """Check eth_syncing - returns False if synced."""
        result = await w3.eth.syncing
        # False means synced, any dict means syncing
        return not isinstance(result, bool) or result

    async def _check_net_version(self, w3) -> int:
        """Check net_version - returns chain ID."""
        return int(await w3.net.version)

    async def _check_block_number(self, w3) -> int:
        """Check eth_blockNumber - returns latest block number."""
        return await w3.eth.block_number

    async def _check_peer_count(self, w3) -> int:
        """Check net_peerCount - returns number of connected peers."""
        return await w3.net.peer_count
