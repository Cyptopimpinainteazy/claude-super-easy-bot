#!/bin/bash

# ============================================================================
# DEPLOY NODES SCRIPT
# ============================================================================
# Deploys blockchain nodes using docker-compose with optional snapshot fetching
# Usage: ./scripts/deploy-nodes.sh [--fetch-snapshots]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.nodes.yml"
DATA_DIR="$PROJECT_ROOT/.node-data"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}ℹ️  $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

validate_environment() {
    log_info "Validating environment..."
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if docker-compose is installed
    if ! docker-compose --version &> /dev/null; then
        log_error "docker-compose is not installed. Please install it first."
        exit 1
    fi
    
    # Check if docker daemon is running
    if ! docker ps &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    # Check if docker-compose file exists
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        log_error "docker-compose file not found: $DOCKER_COMPOSE_FILE"
        exit 1
    fi
    
    log_info "✓ Environment validation passed"
}

create_data_directories() {
    log_info "Creating data directories..."
    
    mkdir -p "$DATA_DIR"/{ethereum,polygon_heimdall,polygon_bor,arbitrum,bsc,avalanche,base}
    
    # Set permissions
    chmod 755 "$DATA_DIR"/*
    
    log_info "✓ Data directories created at $DATA_DIR"
}

fetch_snapshots() {
    log_warn "Snapshot fetching not yet implemented"
    log_info "Nodes will sync from genesis (this may take time)"
    log_info "Consider using snapshot providers for faster sync:"
    log_info "  - Ethereum: https://ethscan.io/nodetracker/mainnet"
    log_info "  - Polygon: https://snapshot.polygon.technology/"
    log_info "  - Arbitrum: https://snapshot.arbitrum.foundation/"
}

deploy_containers() {
    log_info "Deploying blockchain node containers..."
    
    cd "$PROJECT_ROOT"
    
    # Pull latest images
    log_info "Pulling latest Docker images..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" pull
    
    # Start containers
    log_info "Starting containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    log_info "✓ Containers deployed successfully"
}

wait_for_nodes() {
    log_info "Waiting for nodes to start and perform healthchecks..."
    
    CHAINS=("ethereum" "polygon-bor" "arbitrum-node" "bsc-node" "avalanche-node" "base-node")
    MAX_WAIT=120  # 2 minutes
    ELAPSED=0
    CHECK_INTERVAL=5
    
    for chain in "${CHAINS[@]}"; do
        log_info "Waiting for $chain..."
        ELAPSED=0
        
        while [ $ELAPSED -lt $MAX_WAIT ]; do
            if docker-compose -f "$DOCKER_COMPOSE_FILE" ps "$chain" | grep -q "healthy"; then
                log_info "✓ $chain is healthy"
                break
            elif docker-compose -f "$DOCKER_COMPOSE_FILE" ps "$chain" | grep -q "starting"; then
                log_warn "$chain is still starting (${ELAPSED}s elapsed)..."
                sleep $CHECK_INTERVAL
                ELAPSED=$((ELAPSED + CHECK_INTERVAL))
            else
                log_warn "$chain status unknown"
                sleep $CHECK_INTERVAL
                ELAPSED=$((ELAPSED + CHECK_INTERVAL))
            fi
        done
        
        if [ $ELAPSED -ge $MAX_WAIT ]; then
            log_warn "$chain did not become healthy within ${MAX_WAIT}s (this may be normal for first sync)"
        fi
    done
}

print_status() {
    log_info "Container Status:"
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    
    log_info "\nHAProxy Stats: http://localhost:8404/stats"
    log_info "\nNode Endpoints:"
    log_info "  Ethereum HTTP:   http://localhost:8080"
    log_info "  Ethereum WebSocket: ws://localhost:8180"
    log_info "  Polygon HTTP:    http://localhost:8081"
    log_info "  Polygon WebSocket: ws://localhost:8181"
    log_info "  Arbitrum HTTP:   http://localhost:8082"
    log_info "  Arbitrum WebSocket: ws://localhost:8182"
    log_info "  BSC HTTP:        http://localhost:8083"
    log_info "  BSC WebSocket:   ws://localhost:8183"
    log_info "  Avalanche HTTP:  http://localhost:8084"
    log_info "  Avalanche WebSocket: ws://localhost:8184"
    log_info "  Base HTTP:       http://localhost:8085"
    log_info "  Base WebSocket:  ws://localhost:8185"
}

# Main execution
main() {
    log_info "========================================="
    log_info "  Blockchain Nodes Deployment Script"
    log_info "========================================="
    
    validate_environment
    create_data_directories
    
    # Check for flags
    if [[ "$@" == *"--fetch-snapshots"* ]]; then
        fetch_snapshots
    fi
    
    deploy_containers
    wait_for_nodes
    print_status
    
    log_info "========================================="
    log_info "✓ Deployment completed successfully!"
    log_info "========================================="
}

# Run main
main "$@"
