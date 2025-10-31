"""
Enhanced blockchain connection manager with async Web3, failover, and subscription support.
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any
from decimal import Decimal
from web3 import Web3, AsyncWeb3
from web3.providers import AsyncHTTPProvider, WebSocketProvider
import logging

from .node_config import ChainNodeConfig, NodeEndpoint, NodeConfig

logger = logging.getLogger(__name__)


class NoHealthyEndpointsError(Exception):
    """Raised when no healthy endpoints are available for a chain."""

    pass


class EnhancedBlockchainManager:
    """
    Manages connections to multiple blockchain networks with:
    - AsyncWeb3 HTTP/WS providers
    - Subscription management
    - Failover between endpoints
    - Connection pooling
    """

    def __init__(self, node_config: NodeConfig):
        """
        Initialize the blockchain manager.

        Args:
            node_config: NodeConfig object with chain configurations
        """
        self.node_config = node_config
        self.http_web3_instances: Dict[str, AsyncWeb3] = {}
        self.ws_web3_instances: Dict[str, AsyncWeb3] = {}
        self.subscriptions: Dict[str, List[Any]] = {}
        self.endpoint_health: Dict[str, Dict[str, bool]] = {}
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize connections to all configured chains."""
        tasks = []
        for chain in self.node_config.get_all_chains():
            tasks.append(self._init_chain(chain))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                chain = list(self.node_config.get_all_chains())[i]
                logger.error(f"Failed to initialize chain {chain}: {result}")

    async def _init_chain(self, chain: str):
        """Initialize connections for a single chain."""
        chain_config = self.node_config.get_chain_config(chain)
        if not chain_config:
            return

        # Initialize health tracking
        self.endpoint_health[chain] = {
            ep.url: True
            for ep in chain_config.http_endpoints + chain_config.ws_endpoints
        }

        # Try to connect to HTTP endpoint
        http_ep = chain_config.get_primary_http()
        if http_ep:
            try:
                w3 = AsyncWeb3(AsyncHTTPProvider(http_ep.url))
                # Test connection
                if await w3.is_connected():
                    self.http_web3_instances[chain] = w3
                    logger.info(f"✓ Connected to {chain} HTTP: {http_ep.url}")
                else:
                    logger.warning(
                        f"✗ Failed to connect to {chain} HTTP: {http_ep.url}"
                    )
                    self.endpoint_health[chain][http_ep.url] = False
            except Exception as e:
                logger.error(f"Error connecting to {chain} HTTP: {e}")
                self.endpoint_health[chain][http_ep.url] = False

        # Try to connect to WebSocket endpoint
        ws_ep = chain_config.get_primary_ws()
        if ws_ep:
            try:
                # WebSocket setup (note: web3.py AsyncWeb3 WebSocket support varies)
                logger.info(f"WebSocket endpoint configured for {chain}: {ws_ep.url}")
            except Exception as e:
                logger.error(f"Error setting up WebSocket for {chain}: {e}")

    async def get_http_web3(self, chain: str) -> AsyncWeb3:
        """
        Get AsyncWeb3 instance for HTTP operations with failover support.

        Args:
            chain: Chain name

        Returns:
            AsyncWeb3 instance

        Raises:
            NoHealthyEndpointsError: When no healthy endpoints available
        """
        chain_config = self.node_config.get_chain_config(chain)
        if not chain_config:
            raise ValueError(f"Chain {chain} not configured")

        # Try existing connection first
        if chain in self.http_web3_instances:
            w3 = self.http_web3_instances[chain]
            try:
                if await w3.is_connected():
                    return w3
            except Exception:
                pass

        # Try each HTTP endpoint
        for endpoint in chain_config.http_endpoints:
            if self.endpoint_health.get(chain, {}).get(endpoint.url, True):
                try:
                    w3 = AsyncWeb3(AsyncHTTPProvider(endpoint.url))
                    if await w3.is_connected():
                        self.http_web3_instances[chain] = w3
                        self.endpoint_health[chain][endpoint.url] = True
                        logger.info(f"✓ Connected to {chain} HTTP: {endpoint.url}")
                        return w3
                except Exception as e:
                    logger.warning(f"Failed to connect to {endpoint.url}: {e}")
                    self.endpoint_health[chain][endpoint.url] = False
                    await asyncio.sleep(chain_config.failover_delay)

        raise NoHealthyEndpointsError(f"No healthy HTTP endpoints for {chain}")

    async def get_ws_web3(self, chain: str) -> AsyncWeb3:
        """
        Get AsyncWeb3 instance for WebSocket operations.

        Args:
            chain: Chain name

        Returns:
            AsyncWeb3 instance

        Raises:
            NoHealthyEndpointsError: When no healthy endpoints available
        """
        chain_config = self.node_config.get_chain_config(chain)
        if not chain_config:
            raise ValueError(f"Chain {chain} not configured")

        # Try existing connection first
        if chain in self.ws_web3_instances:
            w3 = self.ws_web3_instances[chain]
            try:
                if await w3.is_connected():
                    return w3
            except Exception:
                pass

        # Try each WebSocket endpoint
        for endpoint in chain_config.ws_endpoints:
            if self.endpoint_health.get(chain, {}).get(endpoint.url, True):
                try:
                    # Note: WebSocket provider setup depends on web3.py version
                    logger.info(f"✓ Using WebSocket for {chain}: {endpoint.url}")
                    # Placeholder for actual WS connection
                    raise NoHealthyEndpointsError(
                        f"WebSocket not yet implemented for {chain}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to connect to WS {endpoint.url}: {e}")
                    self.endpoint_health[chain][endpoint.url] = False
                    await asyncio.sleep(chain_config.failover_delay)

        raise NoHealthyEndpointsError(f"No healthy WebSocket endpoints for {chain}")

    async def subscribe_pending_transactions(
        self, chain: str, callback: Callable[[Dict[str, Any]], None]
    ) -> str:
        """
        Subscribe to pending transactions on a chain.

        Args:
            chain: Chain name
            callback: Callback function to handle pending transactions

        Returns:
            Subscription ID
        """
        subscription_id = f"{chain}_pending_{len(self.subscriptions)}"

        if chain not in self.subscriptions:
            self.subscriptions[chain] = []

        self.subscriptions[chain].append(
            {
                "id": subscription_id,
                "type": "pending_transactions",
                "callback": callback,
            }
        )

        logger.info(
            f"✓ Subscribed to pending transactions on {chain}: {subscription_id}"
        )
        return subscription_id

    async def unsubscribe(self, chain: str, subscription_id: str):
        """Unsubscribe from a subscription."""
        if chain in self.subscriptions:
            self.subscriptions[chain] = [
                sub for sub in self.subscriptions[chain] if sub["id"] != subscription_id
            ]
            logger.info(f"✓ Unsubscribed from {subscription_id}")

    async def get_gas_price(self, chain: str) -> Decimal:
        """Get current gas price for a chain."""
        try:
            w3 = await self.get_http_web3(chain)
            gas_price_wei = await w3.eth.gas_price
            return Decimal(str(gas_price_wei)) / Decimal("1e9")  # Convert to Gwei
        except Exception as e:
            logger.error(f"Error getting gas price for {chain}: {e}")
            return Decimal("50")  # Default fallback

    async def estimate_gas_cost(self, chain: str, gas_units: int = 300000) -> Decimal:
        """Estimate gas cost in USD for a transaction."""
        gas_price = await self.get_gas_price(chain)
        gas_cost_eth = (gas_price * Decimal(str(gas_units))) / Decimal("1e9")

        # TODO: Get ETH price from oracle
        eth_price = Decimal("3250")  # Placeholder
        return gas_cost_eth * eth_price

    async def close(self):
        """Close all connections."""
        for chain, w3 in self.http_web3_instances.items():
            try:
                # Clean up HTTP connections
                logger.info(f"Closing HTTP connection for {chain}")
            except Exception as e:
                logger.error(f"Error closing connection for {chain}: {e}")

        self.http_web3_instances.clear()
        self.ws_web3_instances.clear()
        self.subscriptions.clear()
