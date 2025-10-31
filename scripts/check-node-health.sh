#!/bin/bash

# ============================================================================
# CHECK NODE HEALTH SCRIPT
# ============================================================================
# Queries blockchain nodes and prints health status
# Usage: ./scripts/check-node-health.sh [--detailed]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Node endpoints
declare -A NODES=(
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
    if [ "$DETAILED" = true ]; then
        echo -e "${BLUE}🔍 $1${NC}"
    fi
}

check_eth_syncing() {
    local endpoint=$1
    local chain=$2
    
    local response=$(curl -s -X POST "$endpoint" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"eth_syncing","params":[],"id":1}' 2>/dev/null || echo '{}')
    
    # eth_syncing returns false if synced, or syncing info if syncing
    if echo "$response" | grep -q '"result":false'; then
        log_info "$chain: ✓ Synced (eth_syncing = false)"
        return 0
    elif echo "$response" | grep -q '"result":{'; then
        local current_block=$(echo "$response" | grep -o '"currentBlockHex":"0x[0-9a-f]*' | head -1 | cut -d'"' -f4)
        local highest_block=$(echo "$response" | grep -o '"highestBlockHex":"0x[0-9a-f]*' | head -1 | cut -d'"' -f4)
        local synced_block=$(echo "$response" | grep -o '"startingBlockHex":"0x[0-9a-f]*' | head -1 | cut -d'"' -f4)
        
        if [ -n "$current_block" ] && [ -n "$highest_block" ]; then
            local current=$((16#${current_block:2}))
            local highest=$((16#${highest_block:2}))
            local percent=$((current * 100 / highest))
            log_warn "$chain: ⚙️  Syncing... ($percent%) - Block: $current / $highest"
        else
            log_warn "$chain: ⚙️  Syncing..."
        fi
        return 1
    else
        log_error "$chain: ✗ Unable to check sync status"
        log_debug "Response: $response"
        return 2
    fi
}

check_block_number() {
    local endpoint=$1
    local chain=$2
    
    local response=$(curl -s -X POST "$endpoint" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' 2>/dev/null || echo '{}')
    
    local block=$(echo "$response" | grep -o '"result":"0x[0-9a-f]*' | cut -d'"' -f4)
    
    if [ -n "$block" ]; then
        local block_num=$((16#${block:2}))
        log_debug "$chain: Block number: $block_num"
        echo "$block_num"
    else
        log_error "$chain: Unable to get block number"
        return 1
    fi
}

check_peer_count() {
    local endpoint=$1
    local chain=$2
    
    local response=$(curl -s -X POST "$endpoint" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"net_peerCount","params":[],"id":1}' 2>/dev/null || echo '{}')
    
    local peers=$(echo "$response" | grep -o '"result":"0x[0-9a-f]*' | cut -d'"' -f4)
    
    if [ -n "$peers" ]; then
        local peer_num=$((16#${peers:2}))
        if [ "$peer_num" -eq 0 ]; then
            log_warn "$chain: ⚠️  No peers connected"
        else
            log_info "$chain: ✓ Connected to $peer_num peers"
        fi
        log_debug "$chain: Peer count: $peer_num"
        return 0
    else
        log_error "$chain: Unable to get peer count"
        return 1
    fi
}

check_net_version() {
    local endpoint=$1
    local chain=$2
    
    local response=$(curl -s -X POST "$endpoint" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}' 2>/dev/null || echo '{}')
    
    local version=$(echo "$response" | grep -o '"result":"[0-9]*' | cut -d'"' -f4)
    
    if [ -n "$version" ]; then
        log_debug "$chain: Network version: $version"
        return 0
    else
        return 1
    fi
}

check_endpoint() {
    local chain=$1
    local endpoint=${NODES[$chain]}
    
    echo ""
    log_info "Checking $chain ($endpoint)..."
    
    # Test connectivity
    if ! curl -s --max-time 5 "$endpoint" > /dev/null 2>&1; then
        log_error "$chain: ✗ Endpoint unreachable"
        return 1
    fi
    
    # Check syncing status
    check_eth_syncing "$endpoint" "$chain"
    sync_status=$?
    
    # Check block number
    check_block_number "$endpoint" "$chain"
    
    # Check peer count
    check_peer_count "$endpoint" "$chain"
    
    # Check network version
    check_net_version "$endpoint" "$chain"
    
    return $sync_status
}

check_haproxy_stats() {
    log_info "\nChecking HAProxy stats..."
    
    local response=$(curl -s http://localhost:8404/stats 2>/dev/null || echo "")
    
    if [ -n "$response" ]; then
        log_info "✓ HAProxy is responding"
        if [ "$DETAILED" = true ]; then
            log_debug "HAProxy stats available at http://localhost:8404/stats"
        fi
    else
        log_error "✗ HAProxy is not responding"
    fi
}

print_summary() {
    echo ""
    log_info "========================================="
    log_info "  Node Health Summary"
    log_info "========================================="
    log_info "Check individual node logs with:"
    log_info "  docker-compose logs <container_name>"
    echo ""
    log_info "Container Names:"
    log_info "  - ethereum-node"
    log_info "  - polygon-heimdall"
    log_info "  - polygon-bor"
    log_info "  - arbitrum-node"
    log_info "  - bsc-node"
    log_info "  - avalanche-node"
    log_info "  - base-node"
    log_info "  - haproxy"
    echo ""
}

# Main execution
main() {
    # Check for --detailed flag
    DETAILED=false
    if [[ "$@" == *"--detailed"* ]]; then
        DETAILED=true
    fi
    
    log_info "========================================="
    log_info "  Node Health Check"
    log_info "========================================="
    
    # Check each node
    for chain in "${!NODES[@]}"; do
        check_endpoint "$chain"
    done
    
    # Check HAProxy
    check_haproxy_stats
    
    print_summary
}

# Run main
main "$@"
