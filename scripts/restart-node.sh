#!/bin/bash

# ============================================================================
# RESTART NODE SCRIPT
# ============================================================================
# Gracefully restarts a blockchain node container with pre/post checks
# Usage: ./scripts/restart-node.sh <chain_name>
# Example: ./scripts/restart-node.sh ethereum

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.nodes.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Container name mapping
declare -A CONTAINERS=(
    ["ethereum"]="ethereum-node"
    ["polygon"]="polygon-bor"
    ["arbitrum"]="arbitrum-node"
    ["bsc"]="bsc-node"
    ["avalanche"]="avalanche-node"
    ["base"]="base-node"
)

declare -A HTTP_ENDPOINTS=(
    ["ethereum"]="http://localhost:8080"
    ["polygon"]="http://localhost:8081"
    ["arbitrum"]="http://localhost:8082"
    ["bsc"]="http://localhost:8083"
    ["avalanche"]="http://localhost:8084"
    ["base"]="http://localhost:8085"
)

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

log_debug() {
    echo -e "${BLUE}🔍 $1${NC}"
}

validate_chain() {
    local chain=$1
    
    if [ -z "$chain" ]; then
        log_error "No chain specified"
        log_info "Usage: $0 <chain_name>"
        log_info "Available chains: ethereum, polygon, arbitrum, bsc, avalanche, base"
        exit 1
    fi
    
    if [ -z "${CONTAINERS[$chain]}" ]; then
        log_error "Unknown chain: $chain"
        log_info "Available chains: ethereum, polygon, arbitrum, bsc, avalanche, base"
        exit 1
    fi
}

pre_restart_check() {
    local chain=$1
    local endpoint=${HTTP_ENDPOINTS[$chain]}
    
    log_info "Running pre-restart health check for $chain..."
    
    local response=$(curl -s -X POST "$endpoint" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' 2>/dev/null || echo '{}')
    
    if echo "$response" | grep -q '"result"'; then
        local block=$(echo "$response" | grep -o '"result":"0x[0-9a-f]*' | cut -d'"' -f4)
        if [ -n "$block" ]; then
            local block_num=$((16#${block:2}))
            log_info "✓ Pre-restart: Block $block_num - Node is operational"
            echo "$block_num"
            return 0
        fi
    fi
    
    log_warn "⚠️  Pre-restart: Could not determine block number (node may be syncing)"
    echo "unknown"
    return 0
}

post_restart_check() {
    local chain=$1
    local endpoint=${HTTP_ENDPOINTS[$chain]}
    local max_wait=60
    local elapsed=0
    local check_interval=5
    
    log_info "Waiting for $chain to restart and become healthy..."
    
    while [ $elapsed -lt $max_wait ]; do
        local response=$(curl -s -m 5 -X POST "$endpoint" \
            -H "Content-Type: application/json" \
            -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' 2>/dev/null || echo '{}')
        
        if echo "$response" | grep -q '"result"'; then
            local block=$(echo "$response" | grep -o '"result":"0x[0-9a-f]*' | cut -d'"' -f4)
            if [ -n "$block" ]; then
                local block_num=$((16#${block:2}))
                log_info "✓ Post-restart: Block $block_num - Node is operational"
                return 0
            fi
        fi
        
        log_debug "Waiting... (${elapsed}s elapsed)"
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
    done
    
    log_warn "⚠️  Post-restart timeout reached. Node may still be starting."
    log_info "Check status with: docker-compose logs ${CONTAINERS[$chain]}"
    return 1
}

restart_container() {
    local chain=$1
    local container=${CONTAINERS[$chain]}
    
    log_info "Restarting container: $container"
    
    # Get pre-restart state
    pre_block=$(pre_restart_check "$chain")
    
    # Stop container
    log_info "Stopping $container..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" stop "$container"
    
    # Wait a moment for graceful shutdown
    sleep 3
    
    # Start container
    log_info "Starting $container..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" start "$container"
    
    # Wait for container to start
    sleep 5
    
    # Check post-restart state
    post_restart_check "$chain"
    
    return 0
}

print_status() {
    local chain=$1
    
    log_info "\n========================================="
    log_info "  Container Status"
    log_info "========================================="
    
    docker-compose -f "$PROJECT_ROOT/docker-compose.nodes.yml" ps "${CONTAINERS[$chain]}"
    
    log_info "\nTo view logs:"
    log_info "  docker-compose logs -f ${CONTAINERS[$chain]}"
    
    log_info "\nTo check health:"
    log_info "  $SCRIPT_DIR/check-node-health.sh"
}

# Main execution
main() {
    local chain=$1
    
    validate_chain "$chain"
    
    log_info "========================================="
    log_info "  Node Restart Script"
    log_info "========================================="
    log_info "Chain: $chain"
    log_info "Container: ${CONTAINERS[$chain]}"
    
    restart_container "$chain"
    
    print_status "$chain"
    
    log_info "========================================="
    log_info "✓ Restart completed"
    log_info "========================================="
}

# Run main
main "$@"
