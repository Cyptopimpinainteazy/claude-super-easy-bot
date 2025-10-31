"""
Node configuration loader - handles YAML/environment-based node endpoint configuration.
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class NodeEndpoint:
    """Represents a single blockchain node endpoint."""

    url: str
    type: str  # 'http' or 'ws'
    chain: str
    priority: int = 0
    timeout: int = 30
    is_primary: bool = False

    def __hash__(self):
        return hash((self.url, self.chain))

    def __eq__(self, other):
        if not isinstance(other, NodeEndpoint):
            return False
        return self.url == other.url and self.chain == other.chain


@dataclass
class ChainNodeConfig:
    """Configuration for a specific chain's nodes."""

    chain_id: int
    gas_token: str
    http_endpoints: List[NodeEndpoint] = field(default_factory=list)
    ws_endpoints: List[NodeEndpoint] = field(default_factory=list)
    min_profit_threshold: float = 0.0
    sync_check_interval: int = 30
    health_check_timeout: int = 10
    max_retries: int = 3
    failover_delay: float = 2.0

    def get_primary_http(self) -> Optional[NodeEndpoint]:
        """Get primary HTTP endpoint."""
        for ep in self.http_endpoints:
            if ep.is_primary:
                return ep
        return self.http_endpoints[0] if self.http_endpoints else None

    def get_primary_ws(self) -> Optional[NodeEndpoint]:
        """Get primary WebSocket endpoint."""
        for ep in self.ws_endpoints:
            if ep.is_primary:
                return ep
        return self.ws_endpoints[0] if self.ws_endpoints else None


@dataclass
class NodeConfig:
    """Complete node configuration for all chains."""

    chains: Dict[str, ChainNodeConfig] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, yaml_file: str) -> "NodeConfig":
        """Load configuration from YAML file."""
        if not os.path.exists(yaml_file):
            raise FileNotFoundError(f"Config file not found: {yaml_file}")

        with open(yaml_file, "r") as f:
            data = yaml.safe_load(f)

        return cls._parse_yaml(data)

    @classmethod
    def from_env(cls) -> "NodeConfig":
        """Load configuration from environment variables."""
        config_file = os.getenv("NODE_CONFIG_FILE", "node-config.yaml")
        return cls.from_yaml(config_file)

    @classmethod
    def _parse_yaml(cls, data: Dict[str, Any]) -> "NodeConfig":
        """Parse YAML data into NodeConfig."""
        chains = {}

        if "chains" not in data:
            raise ValueError("YAML must contain 'chains' key")

        for chain_name, chain_data in data["chains"].items():
            chain_id = chain_data.get("chain_id")
            gas_token = chain_data.get("gas_token")

            if not chain_id or not gas_token:
                raise ValueError(f"Chain {chain_name} missing chain_id or gas_token")

            # Parse HTTP endpoints
            http_endpoints = []
            for i, http_url in enumerate(chain_data.get("http_endpoints", [])):
                is_primary = i == 0
                http_endpoints.append(
                    NodeEndpoint(
                        url=http_url,
                        type="http",
                        chain=chain_name,
                        is_primary=is_primary,
                        priority=i,
                    )
                )

            # Parse WebSocket endpoints
            ws_endpoints = []
            for i, ws_url in enumerate(chain_data.get("ws_endpoints", [])):
                is_primary = i == 0
                ws_endpoints.append(
                    NodeEndpoint(
                        url=ws_url,
                        type="ws",
                        chain=chain_name,
                        is_primary=is_primary,
                        priority=i,
                    )
                )

            chain_config = ChainNodeConfig(
                chain_id=chain_id,
                gas_token=gas_token,
                http_endpoints=http_endpoints,
                ws_endpoints=ws_endpoints,
                min_profit_threshold=chain_data.get("min_profit_threshold", 0.0),
                sync_check_interval=chain_data.get("sync_check_interval", 30),
                health_check_timeout=chain_data.get("health_check_timeout", 10),
                max_retries=chain_data.get("max_retries", 3),
                failover_delay=chain_data.get("failover_delay", 2.0),
            )

            chains[chain_name] = chain_config

        return cls(chains=chains)

    def get_chain_config(self, chain: str) -> Optional[ChainNodeConfig]:
        """Get configuration for a specific chain."""
        return self.chains.get(chain)

    def get_all_chains(self) -> List[str]:
        """Get list of all configured chains."""
        return list(self.chains.keys())
