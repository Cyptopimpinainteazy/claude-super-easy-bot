# 🚀 Arbitrage Nexus - Complete Setup Guide

## 📋 Requirements

### Python Dependencies (requirements.txt)
```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0

# Blockchain
web3==6.11.3
eth-account==0.9.0
eth-utils==2.3.1

# HTTP Clients
aiohttp==3.9.1
requests==2.31.0

# Database
sqlalchemy[asyncio]==2.0.23
alembic==1.13.1
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Cache
redis[hiredis]==5.0.1

# Data Processing
pandas==2.1.3
numpy==1.26.2

# Utilities
python-dotenv==1.0.0
pydantic==2.5.2
python-dateutil==2.8.2
pyyaml==6.0.1

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
```

## 🔧 Installation Steps

### 1. Clone/Create Project Structure
```bash
arbitrage-nexus/
├── backend/
│   ├── arbitrage_backend.py      # Main engine
│   ├── flash_loan_executor.py    # Flash loan logic
│   ├── api_server.py              # FastAPI server
│   ├── config.py                  # Configuration
│   └── utils.py                   # Helper functions
├── contracts/
│   ├── FlashLoanArbitrage.sol    # Solidity contract
│   └── interfaces/
├── frontend/
│   └── dashboard.html             # React dashboard
├── tests/
│   ├── test_backend.py
│   └── test_executor.py
├── .env                           # Environment variables
├── requirements.txt
└── README.md
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file:
```bash
# RPC Endpoints
ETHEREUM_RPC=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
POLYGON_RPC=https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY
ARBITRUM_RPC=https://arb-mainnet.g.alchemy.com/v2/YOUR_KEY
BSC_RPC=https://bsc-dataseed.binance.org/
AVALANCHE_RPC=https://api.avax.network/ext/bc/C/rpc
BASE_RPC=https://mainnet.base.org

# Private Key (NEVER COMMIT THIS!)
PRIVATE_KEY=your_private_key_here

# Trading Parameters
MIN_PROFIT_USD=50
MAX_GAS_PRICE_GWEI=100
SLIPPAGE_TOLERANCE=0.5

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Flash Loan Settings
USE_FLASH_LOANS=true
AAVE_REFERRAL_CODE=0

# Monitoring
ENABLE_DISCORD_ALERTS=false
DISCORD_WEBHOOK_URL=

# Safety
DRY_RUN_MODE=true  # Set to false for live trading
MAX_POSITION_SIZE=1000
```

### 4. Get API Keys

#### Alchemy (Recommended for Ethereum, Polygon, Arbitrum)
1. Go to https://www.alchemy.com/
2. Create free account
3. Create apps for each chain
4. Copy API keys to `.env`

#### Other RPC Providers (Alternatives)
- **Infura**: https://infura.io/
- **QuickNode**: https://www.quicknode.com/
- **Ankr**: https://www.ankr.com/

### 4b. Database & Cache Setup

**Option 1: Docker (Recommended)**

Start database services:
```bash
# Start PostgreSQL and Redis
docker-compose -f docker-compose.db.yml up -d

# Verify services are running
docker-compose -f docker-compose.db.yml ps

# Check logs
docker-compose -f docker-compose.db.yml logs -f postgres-timescale
```

Initialize database:
```bash
# Run migrations
alembic upgrade head

# Verify tables created
docker exec -it arbitrage-postgres psql -U arbitrage_user -d arbitrage_bot -c "\dt"
```

**Option 2: Local Installation**

Install PostgreSQL with TimescaleDB:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-16 postgresql-16-timescaledb

# macOS
brew install postgresql@16 timescaledb
```

Install Redis:
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
redis-server --daemonize yes
```

Create database:
```bash
sudo -u postgres psql
CREATE DATABASE arbitrage_bot;
CREATE USER arbitrage_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE arbitrage_bot TO arbitrage_user;
\q

# Run migrations
alembic upgrade head
```

### 5. Fund Your Wallet
```bash
# For testing, use testnet faucets first!
# Ethereum Goerli: https://goerlifaucet.com/
# Polygon Mumbai: https://faucet.polygon.technology/
# Arbitrum Goerli: https://faucet.quicknode.com/arbitrum/goerli

# For mainnet, send:
# - ETH for Ethereum gas
# - MATIC for Polygon gas  
# - ETH for Arbitrum/Base gas
# - BNB for BSC gas
# - AVAX for Avalanche gas
# - Initial capital for trading
```

## 🚀 Running the Bot

### Method 1: Run Components Separately

#### Terminal 1: Start Backend Engine
```bash
python backend/arbitrage_backend.py
```

#### Terminal 2: Start API Server
```bash
python backend/api_server.py
# or with uvicorn:
uvicorn backend.api_server:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 3: Serve Frontend
```bash
cd frontend
python -m http.server 3000
# Open browser to http://localhost:3000
```

### Method 2: Docker (Recommended for Production)

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./backend:/app
    restart: unless-stopped

  frontend:
    image: nginx:alpine
    ports:
      - "3000:80"
    volumes:
      - ./frontend:/usr/share/nginx/html
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

## 🧪 Testing

### Run on Testnets First!
```bash
# Update .env for testnet
ETHEREUM_RPC=https://eth-goerli.g.alchemy.com/v2/YOUR_KEY
POLYGON_RPC=https://polygon-mumbai.g.alchemy.com/v2/YOUR_KEY
# etc...

# Run in dry-run mode
DRY_RUN_MODE=true

# Run tests
pytest tests/ -v
```

### Test Endpoints
```bash
# Check API health
curl http://localhost:8000/

# Get opportunities
curl http://localhost:8000/api/opportunities

# Get stats
curl http://localhost:8000/api/stats

# Start bot
curl -X POST http://localhost:8000/api/bot/start

# Stop bot
curl -X POST http://localhost:8000/api/bot/stop
```

## 📊 Monitoring & Alerts

### Enable Discord Alerts
1. Create Discord webhook
2. Add to `.env`:
```bash
ENABLE_DISCORD_ALERTS=true
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK
```

### Add Logging
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arbitrage.log'),
        logging.StreamHandler()
    ]
)
```

## 📊 Data Management

### Backups

**Manual backup**:
```bash
# Backup database
./scripts/backup-database.sh

# Backup Redis
./scripts/backup-redis.sh
```

**Automated backups** (add to crontab):
```bash
# Edit crontab
crontab -e

# Add these lines:
# Daily database backup at 2 AM
0 2 * * * /path/to/scripts/backup-database.sh >> /path/to/logs/backup.log 2>&1

# Redis backup every 6 hours
0 */6 * * * /path/to/scripts/backup-redis.sh >> /path/to/logs/backup.log 2>&1

# Daily cleanup at 3 AM
0 3 * * * cd /path/to/bot && python scripts/cleanup-old-data.py >> logs/cleanup.log 2>&1
```

**Restore from backup**:
```bash
./scripts/restore-database.sh ./backups/postgres/arbitrage_bot_20240115_020000.sql.gz
```

### Data Retention

**Automatic retention** (TimescaleDB):
- Opportunities: 7 days
- Stats snapshots: 90 days (then downsampled to hourly)
- Gas prices: 30 days (then downsampled to 5-minute intervals)
- Chain metrics: 7 days (then downsampled to 5-minute intervals)
- Alerts: 30 days
- Executions: Kept indefinitely (audit trail)

**Manual cleanup**:
```bash
# Preview what would be deleted
DRY_RUN=true python scripts/cleanup-old-data.py

# Actually delete
python scripts/cleanup-old-data.py
```

### Database Maintenance

**Check database size**:
```bash
docker exec -it arbitrage-postgres psql -U arbitrage_user -d arbitrage_bot -c "
  SELECT pg_size_pretty(pg_database_size('arbitrage_bot'));
"
```

**Vacuum and analyze**:
```bash
docker exec -it arbitrage-postgres psql -U arbitrage_user -d arbitrage_bot -c "VACUUM ANALYZE;"
```

**View table sizes**:
```bash
docker exec -it arbitrage-postgres psql -U arbitrage_user -d arbitrage_bot -c "
  SELECT schemaname, tablename,
         pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
  FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

## ⚠️ Safety Checklist

Before going live:

- [ ] Tested on testnets extensively
- [ ] Verified all contract addresses
- [ ] Set reasonable profit thresholds
- [ ] Limited max position sizes
- [ ] Implemented stop-loss mechanisms
- [ ] Set up monitoring & alerts
- [ ] Backed up private keys securely
- [ ] Understood MEV risks
- [ ] Started with small capital
- [ ] Have emergency shutdown plan

## 🔒 Security Best Practices

### 1. Private Key Management
```bash
# NEVER do this:
PRIVATE_KEY="0x1234..." # in code or committed files

# DO this:
# Use environment variables
# Use hardware wallets for production
# Use key management services (AWS KMS, etc.)
```

### 2. Rate Limiting
```python
# Add to api_server.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/execute")
@limiter.limit("10/minute")  # Max 10 executions per minute
async def execute_arbitrage(request: Request, ...):
    ...
```

### 3. Transaction Monitoring
```python
# Monitor for:
# - Failed transactions
# - High gas costs
# - Slippage exceeding limits
# - Unusual profit/loss patterns
```

## 📈 Performance Optimization

### 1. Use Faster RPC Endpoints
- Dedicated nodes
- Regional optimization
- Websocket connections

### 2. Optimize Gas Usage
```python
# Use multicall for batch operations
# Optimize contract code
# Monitor gas prices and adjust dynamically
```

### 3. Parallel Processing
```python
# Scan multiple chains simultaneously
tasks = [scan_chain(chain) for chain in chains]
results = await asyncio.gather(*tasks)
```

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.db.yml ps postgres-timescale

# Check logs
docker-compose -f docker-compose.db.yml logs postgres-timescale

# Test connection
psql postgresql://arbitrage_user:password@localhost:5432/arbitrage_bot -c "SELECT 1;"
```

### Redis Connection Issues
```bash
# Check if Redis is running
docker-compose -f docker-compose.db.yml ps redis

# Test connection
redis-cli -h localhost -p 6379 ping

# Check memory usage
redis-cli -h localhost -p 6379 INFO memory
```

### Migration Issues
```bash
# Check current migration version
alembic current

# View migration history
alembic history

# Rollback one migration
alembic downgrade -1

# Upgrade to latest
alembic upgrade head
```

### Connection Errors
```bash
# Check RPC endpoint
curl -X POST $ETHEREUM_RPC \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

### Gas Estimation Failures
```python
# Add buffer to gas estimates
gas_estimate = gas_estimate * 1.2  # 20% buffer
```

### Slippage Issues
```python
# Increase slippage tolerance or
# Check liquidity before executing
```

## 📚 Additional Resources

### Documentation
- Web3.py: https://web3py.readthedocs.io/
- Aave V3 Docs: https://docs.aave.com/
- Uniswap V3 Docs: https://docs.uniswap.org/
- FastAPI: https://fastapi.tiangolo.com/

### Communities
- Discord: Arbitrage traders communities
- Telegram: DeFi developer groups
- Reddit: r/mev, r/CryptoCurrency

### Tools
- Tenderly: Transaction simulation
- Etherscan: Contract verification
- DeFi Llama: Protocol analytics
- Dune Analytics: On-chain data

## 💰 Cost Estimates

### Initial Setup
- RPC API (Alchemy Free): $0
- Testing on testnets: $0 (free faucet ETH)

### Monthly Operational Costs
- RPC API (paid tier): $50-200/month
- Server hosting: $20-100/month
- Gas fees: Varies heavily
  - Ethereum: $5-50 per transaction
  - Polygon: $0.01-0.50 per transaction
  - Arbitrum: $0.10-2 per transaction

### Recommended Starting Capital
- Testnet: $0 (free test tokens)
- Mainnet (conservative): $1,000-5,000
- Mainnet (aggressive): $10,000+

## 🎓 Learning Path

1. **Week 1**: Set up environment, understand code
2. **Week 2**: Test on testnets, monitor opportunities
3. **Week 3**: Paper trade (dry-run mode)
4. **Week 4**: Small live trades with minimal capital
5. **Week 5+**: Scale gradually based on success rate

## ✅ Ready to Launch!

You now have everything you need to run a professional arbitrage bot. Remember:

- **Start small** and scale gradually
- **Test thoroughly** before going live
- **Monitor constantly** during operation
- **Stay updated** on DeFi protocols
- **Learn continuously** from results

Good luck! 🚀💰
