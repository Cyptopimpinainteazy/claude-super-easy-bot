"""
ARBITRAGE BOT BACKEND - MULTI-CHAIN DEX ARBITRAGE SYSTEM
========================================================
Complete backend infrastructure for the Arbitrage Nexus dashboard
"""

import asyncio
import json
import logging
import os
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Tuple

import aiohttp
from web3 import Web3

from database.cache import get_redis_cache
from database.connection import get_db_manager
from database.models import RiskLevel
from database.repository import (
    AlertRepository,
    ChainMetricRepository,
    ExecutionRepository,
    GasPriceRepository,
    OpportunityRepository,
    StatsRepository,
)
from infrastructure import EnhancedBlockchainManager, NodeConfig, NodeHealthMonitor, NoHealthyEndpointsError

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Chain metadata mapping (still useful for app-level config)
CHAIN_METADATA = {
    "ethereum": {"aave_pool_provider": "0xa97684ead0e402dc232d5a977953df7ecbab3cdb"},
    "polygon": {"aave_pool_provider": "0xa97684ead0e402dc232d5a977953df7ecbab3cdb"},
    "arbitrum": {"aave_pool_provider": "0xa97684ead0e402dc232d5a977953df7ecbab3cdb"},
    "bsc": {"aave_pool_provider": "0xff75A4B698E3Ec95E608ac0f22A03B8368E05F5D"},
    "avalanche": {"aave_pool_provider": "0xa97684ead0e402dc232d5a977953df7ecbab3cdb"},
    "base": {"aave_pool_provider": "0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D"},
}

DEX_ROUTERS = {
    "ethereum": {
        "uniswap_v3": "0xe592427a0aece92de3edee1f18e0157c05861564",
        "uniswap_v2": "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
        "sushiswap": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
    },
    "polygon": {
        "quickswap": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
        "sushiswap": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
        "uniswap_v3": "0xe592427a0aece92de3edee1f18e0157c05861564",
    },
    "arbitrum": {
        "sushiswap": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
        "camelot": "0xc873fEcbd354f5A56E00E710B90EF4201db2448d",
        "uniswap_v3": "0xe592427a0aece92de3edee1f18e0157c05861564",
    },
    "bsc": {
        "pancakeswap_v2": "0x10ED43C718714eb63d5aA57B78B54704E256024E",
        "pancakeswap_v3": "0x1b81D678ffb9C0263b24A97847620C99d213eB14",
        "biswap": "0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8",
    },
    "avalanche": {
        "traderjoe": "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",
        "pangolin": "0xE54Ca86531e17Ef3616d22Ca28b0D458b6C89106",
        "sushiswap": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
    },
    "base": {
        "baseswap": "0x327Df1E6de05895d2ab08513aaDD9313Fe505d86",
        "aerodrome": "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43",
        "uniswap_v3": "0xe592427a0aece92de3edee1f18e0157c05861564",
    },
}

# Trading pairs to monitor
TRADING_PAIRS = [
    ("WETH", "USDT"),
    ("WETH", "USDC"),
    ("WBTC", "USDC"),
    ("WBTC", "USDT"),
    ("MATIC", "USDT"),
    ("AVAX", "USDT"),
    ("ARB", "USDC"),
    ("LINK", "USDT"),
    ("UNI", "USDT"),
    ("AAVE", "USDT"),
]

# Token addresses (example for Ethereum - need to add for each chain)
TOKEN_ADDRESSES = {
    "ethereum": {
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    },
    # Add other chains...
}

# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class PriceQuote:
    """Price quote from a DEX"""

    chain: str
    dex: str
    token_in: str
    token_out: str
    amount_in: Decimal
    amount_out: Decimal
    price: Decimal
    timestamp: float
    gas_estimate: Decimal
    liquidity: Decimal


@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity between two DEXs"""

    id: str
    chain: str
    pair: str
    buy_exchange: str
    sell_exchange: str
    buy_price: Decimal
    sell_price: Decimal
    spread_percent: Decimal
    gross_profit: Decimal
    gas_cost: Decimal
    net_profit: Decimal
    volume_24h: Decimal
    liquidity: Decimal
    confidence: float
    risk_level: str
    flash_loan_available: bool
    timestamp: float

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "pair": self.pair,
            "chain": self.chain,
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
            "confidence": self.confidence,
            "risk": self.risk_level,
            "flashLoanAvailable": self.flash_loan_available,
        }


# ============================================================================
# BLOCKCHAIN MANAGER (REPLACED BY ENHANCED VERSION)
# ============================================================================
# EnhancedBlockchainManager is now imported from infrastructure.connection_manager


# ============================================================================
# PRICE FETCHER
# ============================================================================


class PriceFetcher:
    """Fetches prices from multiple DEXs across chains"""

    def __init__(self, blockchain_manager: EnhancedBlockchainManager):
        self.blockchain_manager = blockchain_manager
        self.price_cache = defaultdict(dict)
        self.cache_ttl = 5  # seconds

    async def fetch_dex_price(
        self, chain: str, dex: str, token_in: str, token_out: str, amount_in: Decimal
    ) -> Optional[PriceQuote]:
        """Fetch price quote from a specific DEX"""

        # Check cache first
        cache_key = f"{chain}:{dex}:{token_in}:{token_out}"
        if cache_key in self.price_cache:
            cached_quote, timestamp = self.price_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_quote

        try:
            # Use EnhancedBlockchainManager with proper error handling
            try:
                w3 = await self.blockchain_manager.get_http_web3(chain)
            except NoHealthyEndpointsError as e:
                logger.error(f"No healthy endpoints for {chain}: {e}")
                return None

            if not w3:
                return None

            # TODO: Implement actual DEX price fetching
            # This would involve calling the router contract's getAmountsOut function
            # For now, returning simulated data

            amount_out = amount_in * Decimal("3250")  # Simulated
            price = amount_out / amount_in

            quote = PriceQuote(
                chain=chain,
                dex=dex,
                token_in=token_in,
                token_out=token_out,
                amount_in=amount_in,
                amount_out=amount_out,
                price=price,
                timestamp=time.time(),
                gas_estimate=await self.blockchain_manager.estimate_gas_cost(chain),
                liquidity=Decimal("1000000"),  # Simulated
            )

            # Update cache
            self.price_cache[cache_key] = (quote, time.time())

            return quote

        except Exception as e:
            logger.error(f"Error fetching price from {dex} on {chain}: {e}")
            return None

    async def fetch_all_prices(self, chain: str, pair: Tuple[str, str]) -> List[PriceQuote]:
        """Fetch prices for a pair from all DEXs on a chain"""
        token_in, token_out = pair
        amount_in = Decimal("1")  # 1 token

        dexs = DEX_ROUTERS.get(chain, {})
        quotes = []

        tasks = []
        for dex_name in dexs.keys():
            task = self.fetch_dex_price(chain, dex_name, token_in, token_out, amount_in)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, PriceQuote):
                quotes.append(result)

        return quotes


# ============================================================================
# ARBITRAGE DETECTOR
# ============================================================================


class ArbitrageDetector:
    """Detects arbitrage opportunities across DEXs"""

    def __init__(self, blockchain_manager: EnhancedBlockchainManager, price_fetcher: PriceFetcher):
        self.blockchain_manager = blockchain_manager
        self.price_fetcher = price_fetcher
        self.opportunities = []

    def calculate_confidence(self, spread: Decimal, liquidity: Decimal, volatility: Decimal) -> float:
        """Calculate confidence score for an opportunity"""
        confidence = 50.0

        # Higher spread = higher confidence
        if spread > Decimal("0.5"):
            confidence += 30
        elif spread > Decimal("0.2"):
            confidence += 20
        elif spread > Decimal("0.1"):
            confidence += 10

        # Higher liquidity = higher confidence
        if liquidity > Decimal("1000000"):
            confidence += 15
        elif liquidity > Decimal("500000"):
            confidence += 10

        # Lower volatility = higher confidence
        if volatility < Decimal("0.05"):
            confidence += 5

        return min(99.0, confidence)

    def assess_risk(self, spread: Decimal, gas_cost: Decimal, net_profit: Decimal) -> str:
        """Assess risk level of an opportunity"""
        profit_margin = net_profit / (net_profit + gas_cost) if net_profit > 0 else Decimal("0")

        if profit_margin > Decimal("0.5") and spread > Decimal("0.3"):
            return "Low"
        elif profit_margin > Decimal("0.3") and spread > Decimal("0.15"):
            return "Medium"
        else:
            return "High"

    async def detect_opportunities(self, chain: str, pair: Tuple[str, str]) -> List[ArbitrageOpportunity]:
        """Detect arbitrage opportunities for a pair on a chain"""
        # Get min_profit_threshold from node config
        chain_config = self.blockchain_manager.node_config.get_chain_config(chain)
        min_profit = chain_config.min_profit_threshold if chain_config else 0.0

        quotes = await self.price_fetcher.fetch_all_prices(chain, pair)

        if len(quotes) < 2:
            return []

        opportunities = []

        # Compare all quote pairs
        for i, buy_quote in enumerate(quotes):
            for sell_quote in quotes[i + 1 :]:
                # Check if profitable to buy from first and sell to second
                spread = ((sell_quote.price - buy_quote.price) / buy_quote.price) * Decimal("100")

                if spread > Decimal("0.05"):  # Minimum 0.05% spread
                    gross_profit = sell_quote.amount_out - buy_quote.amount_in
                    gas_cost = buy_quote.gas_estimate + sell_quote.gas_estimate
                    net_profit = gross_profit - gas_cost

                    if net_profit > Decimal(str(min_profit)):
                        confidence = self.calculate_confidence(
                            spread,
                            min(buy_quote.liquidity, sell_quote.liquidity),
                            Decimal("0.1"),  # Simulated volatility
                        )

                        opp = ArbitrageOpportunity(
                            id=f"{chain}_{pair[0]}_{pair[1]}_{int(time.time())}",
                            chain=chain,
                            pair=f"{pair[0]}/{pair[1]}",
                            buy_exchange=buy_quote.dex,
                            sell_exchange=sell_quote.dex,
                            buy_price=buy_quote.price,
                            sell_price=sell_quote.price,
                            spread_percent=spread,
                            gross_profit=gross_profit,
                            gas_cost=gas_cost,
                            net_profit=net_profit,
                            volume_24h=Decimal("1000000"),  # Simulated
                            liquidity=min(buy_quote.liquidity, sell_quote.liquidity),
                            confidence=confidence,
                            risk_level=self.assess_risk(spread, gas_cost, net_profit),
                            flash_loan_available=True,
                            timestamp=time.time(),
                        )

                        opportunities.append(opp)

        return opportunities

    async def scan_all_chains(self) -> List[ArbitrageOpportunity]:
        """Scan all chains and pairs for opportunities"""
        all_opportunities = []

        tasks = []
        for chain in CHAINS_CONFIG.keys():
            for pair in TRADING_PAIRS:
                task = self.detect_opportunities(chain, pair)
                tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_opportunities.extend(result)

        # Sort by net profit descending
        all_opportunities.sort(key=lambda x: x.net_profit, reverse=True)

        return all_opportunities[:20]  # Return top 20


# ============================================================================
# MAIN ARBITRAGE ENGINE
# ============================================================================


class ArbitrageEngine:
    """Main arbitrage bot engine"""

    def __init__(self, node_config: NodeConfig):
        """
        Initialize the engine.

        Args:
            node_config: NodeConfig object with blockchain configuration
        """
        self.node_config = node_config
        self.blockchain_manager = EnhancedBlockchainManager(node_config)
        self.health_monitor = NodeHealthMonitor(self.blockchain_manager)
        self.price_fetcher = PriceFetcher(self.blockchain_manager)
        self.arbitrage_detector = ArbitrageDetector(self.blockchain_manager, self.price_fetcher)
        self.is_running = False
        self.mempool_subs: Dict[str, str] = {}  # chain -> subscription_id
        self.stats = {
            "total_scans": 0,
            "opportunities_found": 0,
            "trades_executed": 0,
            "total_profit": Decimal("0"),
        }

        # Database and cache managers
        self.db_manager = get_db_manager()
        self.redis_cache = get_redis_cache()
        self.opportunity_repo = OpportunityRepository(self.db_manager)
        self.execution_repo = ExecutionRepository(self.db_manager)
        self.stats_repo = StatsRepository(self.db_manager)
        self.gas_price_repo = GasPriceRepository(self.db_manager)
        self.alert_repo = AlertRepository(self.db_manager)
        self.chain_metric_repo = ChainMetricRepository(self.db_manager)

        # Tracking for stats snapshot timing
        self.last_stats_snapshot = time.time()
        self.stats_snapshot_interval = 60  # Update stats every 60 seconds

    async def initialize(self):
        """Initialize connections and monitoring."""
        logger.info("Initializing arbitrage engine...")
        await self.blockchain_manager.initialize()

        # Initialize database
        try:
            await self.db_manager.initialize()
            await self.db_manager.create_tables()
            await self.db_manager.setup_timescale_hypertables()
            logger.info("✓ Database initialized and ready")
        except Exception as e:
            logger.error(f"⚠️  Database initialization failed (continuing without persistence): {e}")

        # Register health alert callback
        self.health_monitor.register_alert_callback(self._on_health_update)

        logger.info("✓ Engine initialized")

    def _on_health_update(self, health_status):
        """Callback for health monitor updates."""
        logger.info(f"Health update: {health_status.overall_status.value}")

    async def _persist_opportunities(self, opportunities: List[ArbitrageOpportunity]):
        """Persist opportunities to database and cache"""
        if not opportunities:
            return

        try:
            # Persist to database
            for opp in opportunities:
                await self.opportunity_repo.create(
                    opportunity_id=f"{opp.chain}_{opp.pair}_{int(time.time())}",
                    chain=opp.chain,
                    pair=opp.pair,
                    buy_exchange=opp.buy_exchange,
                    sell_exchange=opp.sell_exchange,
                    buy_price=opp.buy_price,
                    sell_price=opp.sell_price,
                    spread=opp.spread_percent,
                    gross_profit=opp.gross_profit,
                    net_profit=opp.net_profit,
                    confidence=opp.confidence,
                    risk_level=opp.risk_level.lower(),
                    flash_loan_available=getattr(opp, "flash_loan_available", False),
                    detected_at=datetime.utcnow(),
                )

            # Cache top opportunities for quick API access
            await self.redis_cache.cache_opportunities(opportunities)

            logger.debug(f"✓ Persisted {len(opportunities)} opportunities to database and cache")
        except Exception as e:
            logger.warning(f"Failed to persist opportunities: {e}")

    async def _update_stats_snapshot(self):
        """Update statistics snapshot in database"""
        try:
            if time.time() - self.last_stats_snapshot < self.stats_snapshot_interval:
                return

            # Create stats snapshot
            await self.stats_repo.create_snapshot(
                total_scans=self.stats["total_scans"],
                opportunities_found=self.stats["opportunities_found"],
                trades_executed=self.stats["trades_executed"],
                successful_trades=self.stats.get("successful_trades", 0),
                failed_trades=self.stats.get("failed_trades", 0),
                total_profit=float(self.stats["total_profit"]),
                gas_spent=float(self.stats.get("gas_spent", 0)),
                net_profit=float(self.stats.get("net_profit", 0)),
                success_rate=float(self.stats.get("success_rate", 0)),
                avg_profit_per_trade=float(self.stats.get("avg_profit_per_trade", 0)),
                max_drawdown=float(self.stats.get("max_drawdown", 0)),
                sharpe_ratio=float(self.stats.get("sharpe_ratio", 0)),
                active_capital=float(self.stats.get("active_capital", 0)),
            )

            self.last_stats_snapshot = time.time()
            logger.debug("✓ Stats snapshot saved to database")
        except Exception as e:
            logger.warning(f"Failed to update stats snapshot: {e}")

    async def _record_chain_metrics(self):
        """Record chain health metrics to database"""
        try:
            for chain in self.node_config.get_all_chains():
                try:
                    w3 = await self.blockchain_manager.get_http_web3(chain)
                    if not w3:
                        continue

                    block = w3.eth.block_number
                    peer_count = len(w3.net.peer_count) if hasattr(w3.net, "peer_count") else 0

                    await self.chain_metric_repo.record(
                        chain=chain,
                        block_number=block,
                        peer_count=peer_count,
                        is_syncing=False,
                        sync_progress=100.0,
                        response_time_ms=0,
                        status="healthy",
                    )
                except Exception as e:
                    logger.debug(f"Could not record metrics for {chain}: {e}")
        except Exception as e:
            logger.debug(f"Error recording chain metrics: {e}")

    async def start_mempool_monitoring(self, chains: Optional[List[str]] = None):
        """
        Start monitoring mempool for pending transactions.

        Args:
            chains: List of chains to monitor (defaults to all configured chains)
        """
        if not chains:
            chains = self.node_config.get_all_chains()

        logger.info(f"Starting mempool monitoring for chains: {chains}")

        for chain in chains:
            try:
                sub_id = await self.blockchain_manager.subscribe_pending_transactions(chain, self._handle_pending_tx)
                self.mempool_subs[chain] = sub_id
                logger.info(f"✓ Mempool monitoring started for {chain}")
            except Exception as e:
                logger.error(f"Failed to start mempool monitoring for {chain}: {e}")

    async def _handle_pending_tx(self, tx_data: Dict[str, Any]):
        """Handle pending transaction from mempool subscription."""
        try:
            # TODO: Implement pending transaction analysis
            # This would analyze pending transactions for MEV opportunities
            logger.debug(f"Pending transaction: {tx_data}")
        except Exception as e:
            logger.error(f"Error handling pending transaction: {e}")

    async def start_scanning(self, interval: int = 5):
        """Start continuous scanning for opportunities"""
        self.is_running = True
        await self.health_monitor.start()

        logger.info("\n🚀 Arbitrage Engine Started!")
        logger.info("=" * 60)

        while self.is_running:
            try:
                start_time = time.time()

                # Scan for opportunities
                opportunities = await self.arbitrage_detector.scan_all_chains()

                # Update stats
                self.stats["total_scans"] += 1
                self.stats["opportunities_found"] += len(opportunities)

                # Persist opportunities to database and cache
                await self._persist_opportunities(opportunities)

                # Update stats snapshot periodically
                await self._update_stats_snapshot()

                # Record chain metrics
                await self._record_chain_metrics()

                # Display results
                logger.info(f"\n⚡ Scan #{self.stats['total_scans']} - Found {len(opportunities)} opportunities")
                logger.info(f"⏱️  Scan time: {time.time() - start_time:.2f}s")

                if opportunities:
                    logger.info("\n🎯 Top Opportunities:")
                    for i, opp in enumerate(opportunities[:5], 1):
                        logger.info(f"  {i}. {opp.pair} on {opp.chain.upper()}")
                        logger.info(f"     Buy: {opp.buy_exchange} @ ${opp.buy_price:.4f}")
                        logger.info(f"     Sell: {opp.sell_exchange} @ ${opp.sell_price:.4f}")
                        logger.info(f"     Spread: {opp.spread_percent:.2f}% | Net: ${opp.net_profit:.2f}")
                        logger.info(f"     Confidence: {opp.confidence:.0f}% | Risk: {opp.risk_level}")

                # Wait for next scan
                await asyncio.sleep(interval)

            except KeyboardInterrupt:
                logger.info("\n\n⏹️  Stopping engine...")
                self.is_running = False
                break
            except Exception as e:
                logger.error(f"\n❌ Error in scan loop: {e}")
                await asyncio.sleep(interval)

        logger.info("\n✓ Engine stopped")
        self.print_stats()

    def stop_scanning(self):
        """Stop the scanning loop and cleanup resources."""
        logger.info("Stopping arbitrage engine...")
        self.is_running = False

    async def cleanup(self):
        """Cleanup resources - close connections and stop monitor."""
        logger.info("Cleaning up engine resources...")

        # Stop health monitor
        await self.health_monitor.stop()

        # Unsubscribe from mempool streams
        for chain, sub_id in self.mempool_subs.items():
            try:
                await self.blockchain_manager.unsubscribe(chain, sub_id)
                logger.info(f"✓ Unsubscribed from {chain} mempool")
            except Exception as e:
                logger.error(f"Error unsubscribing from {chain}: {e}")

        # Final stats snapshot
        try:
            await self._update_stats_snapshot()
        except Exception as e:
            logger.debug(f"Could not save final stats snapshot: {e}")

        # Close database connections
        try:
            await self.db_manager.close()
            logger.info("✓ Database connections closed")
        except Exception as e:
            logger.debug(f"Error closing database: {e}")

        # Close blockchain manager connections
        await self.blockchain_manager.close()
        logger.info("✓ Cleanup complete")

    def print_stats(self):
        """Print engine statistics"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 ENGINE STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total Scans: {self.stats['total_scans']}")
        logger.info(f"Opportunities Found: {self.stats['opportunities_found']}")
        logger.info(f"Trades Executed: {self.stats['trades_executed']}")
        logger.info(f"Total Profit: ${self.stats['total_profit']:.2f}")
        logger.info("=" * 60)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


async def main():
    """Main entry point"""
    # Load configuration from file or environment
    config_file = os.getenv("NODE_CONFIG_FILE", "node-config.yaml")

    if not os.path.exists(config_file):
        logger.error(f"Config file not found: {config_file}")
        logger.info("Please create node-config.yaml with your node configuration")
        return

    try:
        node_config = NodeConfig.from_yaml(config_file)
        engine = ArbitrageEngine(node_config)

        # Initialize connections
        await engine.initialize()

        # Start mempool monitoring for selected chains
        await engine.start_mempool_monitoring(["ethereum", "polygon", "arbitrum"])

        # Start scanning
        await engine.start_scanning(interval=10)  # Scan every 10 seconds

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        # Cleanup
        if "engine" in locals():
            await engine.cleanup()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("arbitrage.log"), logging.StreamHandler()],
    )

    print(
        """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                   ARBITRAGE NEXUS v5.0                        ║
    ║               Multi-Chain DEX Arbitrage Engine                ║
    ║         (Infrastructure & Node Health Monitoring)             ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    )

    asyncio.run(main())
