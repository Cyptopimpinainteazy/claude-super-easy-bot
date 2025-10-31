"""
ARBITRAGE BOT API SERVER
========================
FastAPI server to connect backend arbitrage engine with frontend dashboard
"""

# OpenTelemetry Tracing Setup - Must be first
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aiohttp import AioHTTPClientInstrumentor
from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure tracing
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
    )
)

# Instrument libraries
AioHTTPClientInstrumentor().instrument()
AsyncioInstrumentor().instrument()

# Standard library imports
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

# Third-party imports
from fastapi import FastAPI, HTTPException, Path, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Local imports
from arbitrage_backend import ArbitrageEngine
from database.cache import get_redis_cache
from database.connection import get_db_manager
from database.repository import (
    AlertRepository,
    ChainMetricRepository,
    ExecutionRepository,
    GasPriceRepository,
    OpportunityRepository,
    StatsRepository,
)
from infrastructure import ChainHealth

logger = logging.getLogger(__name__)

# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title="Arbitrage Nexus API",
    description="Real-time arbitrage opportunity API",
    version="5.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument FastAPI for tracing
FastAPIInstrumentor.instrument_app(app)

# ============================================================================
# DATA MODELS
# ============================================================================


class OpportunityResponse(BaseModel):
    id: str
    pair: str
    chain: str
    buyExchange: str
    sellExchange: str
    buyPrice: float
    sellPrice: float
    spread: float
    profit: float
    gasEstimate: float
    netProfit: float
    volume24h: float
    liquidity: float
    confidence: float
    risk: str
    flashLoanAvailable: bool


class ExecutionRequest(BaseModel):
    opportunity_id: str
    use_flash_loan: bool
    slippage_tolerance: float = 0.5


class StatsResponse(BaseModel):
    totalPnL: float
    todayPnL: float
    successRate: float
    totalTrades: int
    averageProfit: float
    maxDrawdown: float
    winRate: float
    avgExecutionTime: float
    gasEfficiency: float
    sharpeRatio: float
    maxConsecutiveWins: int
    activeCapital: float


class ChainStatus(BaseModel):
    name: str
    status: str
    trades: int
    gas: int
    latency: int


class GasPriceData(BaseModel):
    time: str
    eth: float
    polygon: float
    arbitrum: float
    bsc: float


class NodeHealthResponse(BaseModel):
    chain: str
    status: str
    is_syncing: Optional[bool]
    block_number: Optional[int]
    peer_count: Optional[int]
    net_version: Optional[int]
    last_check: Optional[str]
    consecutive_failures: int


class NodesHealthSummary(BaseModel):
    timestamp: str
    overall_status: str
    chains: Dict[str, NodeHealthResponse]


class ChainMetricsResponse(BaseModel):
    chain: str
    status: str
    block_number: Optional[int]
    peer_count: Optional[int]
    syncing: Optional[bool]
    uptime_percent: float
    last_check_age_seconds: int


# ============================================================================
# GLOBAL STATE
# ============================================================================


class BotState:
    """Global bot state"""

    def __init__(self):
        self.is_running = False
        self.connected_clients = set()
        self.engine: Optional[ArbitrageEngine] = None
        self.last_health_update: Optional[ChainHealth] = None
        
        # Database and cache managers
        self.db_manager = get_db_manager()
        self.redis_cache = get_redis_cache()
        self.opportunity_repo: Optional[OpportunityRepository] = None
        self.execution_repo: Optional[ExecutionRepository] = None
        self.stats_repo: Optional[StatsRepository] = None
        self.gas_price_repo: Optional[GasPriceRepository] = None
        self.alert_repo: Optional[AlertRepository] = None
        self.chain_metric_repo: Optional[ChainMetricRepository] = None
        
        # Rate limiting state
        self.execution_rate_limit_key = "api:executions:rate_limit"
        self.max_executions_per_minute = 10


bot_state = BotState()

# ============================================================================
# WEBSOCKET CONNECTION MANAGER
# ============================================================================


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✓ Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"✗ Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending to client: {e}")
                dead_connections.append(connection)

        # Remove dead connections
        for conn in dead_connections:
            self.disconnect(conn)


manager = ConnectionManager()

# ============================================================================
# API ENDPOINTS
# ============================================================================


@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "online",
        "version": "5.0",
        "bot_running": bot_state.is_running
    }


@app.get("/api/opportunities", response_model=List[OpportunityResponse])
async def get_opportunities():
    """Get current arbitrage opportunities from cache/database"""
    try:
        # Try to get from Redis cache first
        cached_opps = await bot_state.redis_cache.get("opportunities:recent")
        if cached_opps:
            return json.loads(cached_opps)
        
        # If cache miss, query database
        if bot_state.opportunity_repo:
            opps = await bot_state.opportunity_repo.get_recent(limit=50)
            
            # Convert to response format
            response_opps = []
            for opp in opps:
                response_opps.append(OpportunityResponse(
                    id=str(opp.id),
                    pair=opp.pair,
                    chain=opp.chain,
                    buyExchange=opp.buy_exchange,
                    sellExchange=opp.sell_exchange,
                    buyPrice=float(opp.buy_price),
                    sellPrice=float(opp.sell_price),
                    spread=float(opp.spread),
                    profit=float(opp.gross_profit),
                    gasEstimate=float(opp.gross_profit - opp.net_profit),
                    netProfit=float(opp.net_profit),
                    volume24h=0.0,
                    liquidity=0.0,
                    confidence=float(opp.confidence),
                    risk=opp.risk_level.upper(),
                    flashLoanAvailable=opp.flash_loan_available,
                ))
            
            # Cache result for 10 seconds
            await bot_state.redis_cache.set(
                "opportunities:recent",
                json.dumps([o.dict() for o in response_opps]),
                ttl=10
            )
            
            return response_opps
        
        return []
    except Exception as e:
        logger.warning(f"Error fetching opportunities: {e}")
        return []


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get bot statistics from database or cache"""
    try:
        # Try to get from Redis cache first
        cached_stats = await bot_state.redis_cache.get("bot:stats:current")
        if cached_stats:
            stats_data = json.loads(cached_stats)
            return StatsResponse(**stats_data)
        
        # Query database for latest stats
        if bot_state.stats_repo:
            latest_stats = await bot_state.stats_repo.get_latest()
            
            if latest_stats:
                stats_data = {
                    "totalPnL": float(latest_stats.total_profit),
                    "todayPnL": float(latest_stats.total_profit) * 0.1,  # Approximation
                    "successRate": float(latest_stats.success_rate) if latest_stats.success_rate else 0.0,
                    "totalTrades": latest_stats.trades_executed,
                    "averageProfit": float(latest_stats.avg_profit_per_trade) if latest_stats.avg_profit_per_trade else 0.0,
                    "maxDrawdown": float(latest_stats.max_drawdown) if latest_stats.max_drawdown else 0.0,
                    "winRate": float(latest_stats.success_rate) if latest_stats.success_rate else 0.0,
                    "avgExecutionTime": 0.0,
                    "gasEfficiency": 0.0,
                    "sharpeRatio": float(latest_stats.sharpe_ratio) if latest_stats.sharpe_ratio else 0.0,
                    "maxConsecutiveWins": 0,
                    "activeCapital": float(latest_stats.active_capital) if latest_stats.active_capital else 0.0,
                }
                
                # Cache for 5 seconds
                await bot_state.redis_cache.set("bot:stats:current", json.dumps(stats_data), ttl=5)
                
                return StatsResponse(**stats_data)
        
        # Return default stats if no data available
        return StatsResponse(
            totalPnL=0.0, todayPnL=0.0, successRate=0.0, totalTrades=0,
            averageProfit=0.0, maxDrawdown=0.0, winRate=0.0, avgExecutionTime=0.0,
            gasEfficiency=0.0, sharpeRatio=0.0, maxConsecutiveWins=0, activeCapital=0.0
        )
    except Exception as e:
        logger.warning(f"Error fetching stats: {e}")
        return StatsResponse(
            totalPnL=0.0, todayPnL=0.0, successRate=0.0, totalTrades=0,
            averageProfit=0.0, maxDrawdown=0.0, winRate=0.0, avgExecutionTime=0.0,
            gasEfficiency=0.0, sharpeRatio=0.0, maxConsecutiveWins=0, activeCapital=0.0
        )


@app.post("/api/bot/start")
async def start_bot():
    """Start the arbitrage bot"""
    if bot_state.is_running:
        raise HTTPException(status_code=400, detail="Bot is already running")

    bot_state.is_running = True

    # Start the engine in background
    asyncio.create_task(run_bot_engine())

    return {"status": "started", "message": "Bot started successfully"}


@app.post("/api/bot/stop")
async def stop_bot():
    """Stop the arbitrage bot"""
    if not bot_state.is_running:
        raise HTTPException(status_code=400, detail="Bot is not running")

    bot_state.is_running = False

    if bot_state.engine:
        bot_state.engine.stop_scanning()

    return {"status": "stopped", "message": "Bot stopped successfully"}


@app.post("/api/execute")
async def execute_arbitrage(request: ExecutionRequest):
    """Execute an arbitrage opportunity with rate limiting"""
    
    # Check rate limit
    try:
        is_allowed = await bot_state.redis_cache.rate_limit(
            bot_state.execution_rate_limit_key,
            max_requests=bot_state.max_executions_per_minute,
            window_seconds=60
        )
        
        if not is_allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {bot_state.max_executions_per_minute} executions per minute"
            )
    except Exception as e:
        logger.warning(f"Rate limit check failed, allowing request: {e}")
    
    # Find the opportunity in database
    try:
        if bot_state.opportunity_repo:
            opp = await bot_state.opportunity_repo.get_by_id(int(request.opportunity_id))
            
            if not opp:
                raise HTTPException(status_code=404, detail="Opportunity not found")
            
            # Create execution record
            execution = await bot_state.execution_repo.create(
                opportunity_id=request.opportunity_id,
                chain=opp.chain,
                status="pending",
                tx_hash=None,
                block_number=None,
                gas_used=None,
                gas_price=None,
                actual_profit=None,
                slippage=request.slippage_tolerance,
                error_message=None,
                executed_at=datetime.utcnow(),
            )
            
            # Simulated result
            result = {
                "success": True,
                "profit": float(opp.net_profit),
                "gas_used": 250000,
                "tx_hash": "0x" + "1234567890abcdef" * 4,
                "execution_id": execution.id,
            }
            
            # Update execution status
            await bot_state.execution_repo.update_status(
                execution.id,
                "success",
                tx_hash=result["tx_hash"],
                actual_profit=float(opp.net_profit)
            )
            
            # Publish execution event to Redis pub/sub for WebSocket broadcast
            await bot_state.redis_cache.publish(
                "arbitrage:executions",
                json.dumps(result)
            )
            
            return result
        
        raise HTTPException(status_code=500, detail="Database not available")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chains", response_model=List[ChainStatus])
async def get_chain_status():
    """Get status of all blockchain networks"""
    chains = [
        {
            "name": "Ethereum",
            "status": "online",
            "trades": 420,
            "gas": 45,
            "latency": 12,
        },
        {
            "name": "Polygon",
            "status": "online",
            "trades": 380,
            "gas": 120,
            "latency": 8,
        },
        {
            "name": "Arbitrum",
            "status": "online",
            "trades": 290,
            "gas": 0,
            "latency": 10,
        },
        {"name": "BSC", "status": "online", "trades": 210, "gas": 3, "latency": 15},
        {
            "name": "Avalanche",
            "status": "online",
            "trades": 145,
            "gas": 25,
            "latency": 18,
        },
        {"name": "Base", "status": "online", "trades": 95, "gas": 0, "latency": 9},
    ]
    return chains


@app.get("/api/executions")
async def get_executions(limit: int = 50, offset: int = 0):
    """Get recent executions from database"""
    try:
        if bot_state.execution_repo:
            executions = await bot_state.execution_repo.get_recent(limit=limit)
            
            result = []
            for exec_record in executions:
                result.append({
                    "id": exec_record.id,
                    "opportunityId": exec_record.opportunity_id,
                    "chain": exec_record.chain,
                    "status": exec_record.status,
                    "txHash": exec_record.tx_hash,
                    "profit": float(exec_record.actual_profit) if exec_record.actual_profit else 0.0,
                    "gasUsed": exec_record.gas_used,
                    "slippage": exec_record.slippage,
                    "executedAt": exec_record.executed_at.isoformat() if exec_record.executed_at else None,
                })
            
            return {"total": len(result), "executions": result}
        
        return {"total": 0, "executions": []}
    except Exception as e:
        logger.warning(f"Error fetching executions: {e}")
        return {"total": 0, "executions": []}


@app.get("/api/alerts")
async def get_alerts(limit: int = 50, acknowledged: Optional[bool] = False):
    """Get alerts from database"""
    try:
        if bot_state.alert_repo:
            if acknowledged:
                alerts = await bot_state.alert_repo.get_recent(limit=limit)
            else:
                alerts = await bot_state.alert_repo.get_unacknowledged(limit=limit)
            
            result = []
            for alert in alerts:
                result.append({
                    "id": alert.id,
                    "severity": alert.severity,
                    "category": alert.category,
                    "chain": alert.chain,
                    "message": alert.message,
                    "details": alert.details,
                    "createdAt": alert.created_at.isoformat() if alert.created_at else None,
                    "acknowledged": alert.acknowledged,
                })
            
            return {"total": len(result), "alerts": result}
        
        return {"total": 0, "alerts": []}
    except Exception as e:
        logger.warning(f"Error fetching alerts: {e}")
        return {"total": 0, "alerts": []}


@app.get("/api/gas-prices", response_model=List[GasPriceData])
async def get_gas_prices():
    """Get historical gas prices"""
    # This would come from your actual monitoring
    import time

    current_time = time.strftime("%H:%M")

    return [
        {"time": current_time, "eth": 45, "polygon": 120, "arbitrum": 0.15, "bsc": 3},
    ]


@app.get("/api/gas-prices", response_model=List[GasPriceData])
async def get_gas_prices():
    """Get historical gas prices"""
    # This would come from your actual monitoring
    import time

    current_time = time.strftime("%H:%M")

    return [
        {"time": current_time, "eth": 45, "polygon": 120, "arbitrum": 0.15, "bsc": 3},
    ]


# ============================================================================
# NODE HEALTH MONITORING ENDPOINTS
# ============================================================================


@app.get("/api/nodes/health", response_model=NodesHealthSummary)
async def get_nodes_health():
    """Get health status of all monitored blockchain nodes"""
    if not bot_state.engine or not bot_state.engine.health_monitor:
        raise HTTPException(
            status_code=503, detail="Health monitor not available - engine not running"
        )

    health = bot_state.engine.health_monitor.get_health_summary()

    chains_data = {}
    for chain_name, metrics in health.chains.items():
        chains_data[chain_name] = NodeHealthResponse(
            chain=chain_name,
            status=metrics.status.value,
            is_syncing=metrics.is_syncing,
            block_number=metrics.block_number,
            peer_count=metrics.peer_count,
            net_version=metrics.net_version,
            last_check=metrics.last_check.isoformat() if metrics.last_check else None,
            consecutive_failures=metrics.consecutive_failures,
        )

    return NodesHealthSummary(
        timestamp=health.timestamp.isoformat(),
        overall_status=health.overall_status.value,
        chains=chains_data,
    )


@app.get("/api/nodes/{chain}/metrics", response_model=ChainMetricsResponse)
async def get_chain_metrics(
    chain: str = Path(
        ...,
        description="Blockchain chain name (ethereum, polygon, arbitrum, bsc, avalanche, base)",
    )
):
    """Get detailed metrics for a specific blockchain node"""
    if not bot_state.engine or not bot_state.engine.health_monitor:
        raise HTTPException(
            status_code=503, detail="Health monitor not available - engine not running"
        )

    health = bot_state.engine.health_monitor.get_health_summary()

    if chain not in health.chains:
        raise HTTPException(status_code=404, detail=f"Chain {chain} not monitored")

    metrics = health.chains[chain]

    # Calculate uptime percent (simplified)
    uptime = (
        100.0
        if metrics.consecutive_failures == 0
        else max(0, 100 - (metrics.consecutive_failures * 10))
    )

    # Calculate time since last check
    time_since_check = 0
    if metrics.last_check:
        time_since_check = int(
            (datetime.now() - metrics.last_check.replace(tzinfo=None)).total_seconds()
        )

    return ChainMetricsResponse(
        chain=chain,
        status=metrics.status.value,
        block_number=metrics.block_number,
        peer_count=metrics.peer_count,
        syncing=metrics.is_syncing,
        uptime_percent=uptime,
        last_check_age_seconds=time_since_check,
    )


@app.get("/api/nodes/config")
async def get_nodes_config():
    """Get current node configuration"""
    if not bot_state.engine or not bot_state.engine.node_config:
        raise HTTPException(
            status_code=503, detail="Engine not running - no config available"
        )

    config_data = {}
    for chain in bot_state.engine.node_config.get_all_chains():
        chain_config = bot_state.engine.node_config.get_chain_config(chain)
        if chain_config:
            config_data[chain] = {
                "chain_id": chain_config.chain_id,
                "gas_token": chain_config.gas_token,
                "min_profit_threshold": chain_config.min_profit_threshold,
                "http_endpoints": [ep.url for ep in chain_config.http_endpoints],
                "ws_endpoints": [ep.url for ep in chain_config.ws_endpoints],
            }

    return {"chains": config_data, "total_chains": len(config_data)}


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)

    try:
        # Send initial state
        await websocket.send_json(
            {
                "type": "initial_state",
                "data": {
                    "is_running": bot_state.is_running,
                    "opportunities": bot_state.opportunities,
                    "stats": bot_state.stats,
                },
            }
        )

        # Keep connection alive and listen for messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

            except asyncio.TimeoutError:
                continue

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# ============================================================================
# BACKGROUND TASKS
# ============================================================================


async def run_bot_engine():
    """Run the bot engine and broadcast updates"""

    logger.info("🚀 Starting bot engine...")

    try:
        # Load configuration
        config_file = os.getenv("NODE_CONFIG_FILE", "node-config.yaml")
        if not os.path.exists(config_file):
            logger.error(f"Config file not found: {config_file}")
            bot_state.is_running = False
            return

        from infrastructure import NodeConfig

        node_config = NodeConfig.from_yaml(config_file)

        # Create and initialize engine
        bot_state.engine = ArbitrageEngine(node_config)
        await bot_state.engine.initialize()

        # Start mempool monitoring
        await bot_state.engine.start_mempool_monitoring(
            ["ethereum", "polygon", "arbitrum"]
        )

        logger.info("✓ Engine initialized")

        while bot_state.is_running:
            try:
                # TODO: Get real opportunities from engine
                # opportunities = await bot_state.engine.arbitrage_detector.scan_all_chains()

                # Simulated opportunities for now
                opportunities = generate_mock_opportunities()
                bot_state.opportunities = opportunities

                # Broadcast opportunities update
                await manager.broadcast(
                    {"type": "opportunities_update", "data": opportunities}
                )

                # Broadcast stats
                await manager.broadcast(
                    {"type": "stats_update", "data": bot_state.stats}
                )

                # Broadcast health status if available
                if bot_state.engine.health_monitor:
                    health = bot_state.engine.health_monitor.get_health_summary()
                    bot_state.last_health_update = health

                    health_data = {
                        "timestamp": health.timestamp.isoformat(),
                        "overall_status": health.overall_status.value,
                        "chains": {
                            k: {
                                "status": v.status.value,
                                "block_number": v.block_number,
                                "peer_count": v.peer_count,
                                "is_syncing": v.is_syncing,
                                "consecutive_failures": v.consecutive_failures,
                            }
                            for k, v in health.chains.items()
                        },
                    }

                    await manager.broadcast(
                        {"type": "node_health_update", "data": health_data}
                    )

                # Wait before next scan
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error in bot engine loop: {e}")
                await asyncio.sleep(5)

    except Exception as e:
        logger.error(f"Fatal error starting engine: {e}")

    finally:
        logger.info("🛑 Bot engine stopping...")
        if bot_state.engine:
            await bot_state.engine.cleanup()
        bot_state.is_running = False


def generate_mock_opportunities() -> List[Dict]:
    """Generate mock opportunities for testing"""
    import random

    pairs = ["ETH/USDT", "BTC/USDC", "MATIC/USDT", "AVAX/USDT", "ARB/USDC"]
    chains = ["Ethereum", "Polygon", "Arbitrum", "BSC", "Avalanche"]
    exchanges = ["Uniswap V3", "SushiSwap", "PancakeSwap", "QuickSwap", "Camelot"]

    opportunities = []

    for i in range(5):
        pair = random.choice(pairs)
        chain = random.choice(chains)
        buy_ex = random.choice(exchanges)
        sell_ex = random.choice([e for e in exchanges if e != buy_ex])

        buy_price = 3250 + random.uniform(-50, 50)
        spread = random.uniform(0.05, 0.5)
        sell_price = buy_price * (1 + spread / 100)

        gross_profit = spread * 10
        gas_cost = random.uniform(10, 50)
        net_profit = gross_profit - gas_cost

        if net_profit > 0:
            opportunities.append(
                {
                    "id": f"{chain}_{pair}_{int(datetime.now().timestamp())}_{i}",
                    "pair": pair,
                    "chain": chain,
                    "buyExchange": buy_ex,
                    "sellExchange": sell_ex,
                    "buyPrice": round(buy_price, 4),
                    "sellPrice": round(sell_price, 4),
                    "spread": round(spread, 2),
                    "profit": round(gross_profit, 2),
                    "gasEstimate": round(gas_cost, 2),
                    "netProfit": round(net_profit, 2),
                    "volume24h": random.uniform(500000, 5000000),
                    "liquidity": random.uniform(200000, 2000000),
                    "confidence": random.uniform(75, 99),
                    "risk": random.choice(["Low", "Medium", "High"]),
                    "flashLoanAvailable": True,
                }
            )

    return opportunities


# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("\n" + "=" * 60)
    logger.info("🚀 ARBITRAGE NEXUS API SERVER (v5.0)")
    logger.info("=" * 60)
    logger.info(f"Server started at: {datetime.now()}")
    logger.info("API Documentation: http://localhost:8000/docs")
    logger.info("WebSocket: ws://localhost:8000/ws")
    logger.info("Health Check: http://localhost:8000/api/nodes/health")
    logger.info("=" * 60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("\n🛑 Shutting down server...")

    if bot_state.is_running and bot_state.engine:
        bot_state.is_running = False
        await bot_state.engine.cleanup()

    logger.info("✓ Server shutdown complete\n")


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info",
    )
