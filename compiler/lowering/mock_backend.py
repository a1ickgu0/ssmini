"""
Mock backend implementation for OSC DSL compiler.

This module provides a mock execution engine that simulates
enterprise network operations without requiring actual infrastructure.
"""

import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class OperationStatus(str, Enum):
    """Status of a backend operation."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class OperationResult:
    """
    Result of a backend operation.

    Attributes:
        operation: The operation name
        status: Operation status (pending/running/completed/failed/timeout)
        metrics: Dictionary of outcome metrics
        duration_ms: Operation duration in milliseconds
        error: Error message if failed
    """
    operation: str
    status: OperationStatus
    metrics: dict
    duration_ms: float
    error: Optional[str] = None

    def to_dict(self) -> dict:
        result = {
            "operation": self.operation,
            "status": self.status.value,
            "metrics": self.metrics,
            "duration_ms": self.duration_ms
        }
        if self.error:
            result["error"] = self.error
        return result


class MockBackend:
    """
    Mock backend that simulates enterprise network operations.

    Operations:
    - wifi.scan: Scan for WiFi networks
    - wifi.associate: Associate with a WiFi network
    - aaa.authenticate: Authenticate with AAA server
    - aaa.login: Login to network services
    - network.configure: Configure network devices
    - network.deploy_ap: Deploy access point
    - traffic.generate: Generate network traffic
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize the mock backend."""
        if seed is not None:
            random.seed(seed)
        self._operations = {
            "wifi.scan": self._scan_ssid,
            "wifi.associate": self._associate,
            "aaa.authenticate": self._authenticate,
            "aaa.login": self._login,
            "network.configure": self._configure_router,
            "network.deploy_ap": self._deploy_ap,
            "traffic.generate": self._generate_traffic,
        }

    def execute(self, operation: str, **kwargs) -> OperationResult:
        """
        Execute a backend operation.

        Args:
            operation: The operation to execute
            **kwargs: Operation parameters

        Returns:
            OperationResult with metrics
        """
        start_time = time.time()

        if operation not in self._operations:
            return OperationResult(
                operation=operation,
                status=OperationStatus.FAILED,
                metrics={},
                duration_ms=0,
                error=f"Unknown operation: {operation}"
            )

        try:
            result = self._operations[operation](**kwargs)
            duration_ms = (time.time() - start_time) * 1000
            return OperationResult(
                operation=operation,
                status=OperationStatus.COMPLETED,
                metrics=result,
                duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return OperationResult(
                operation=operation,
                status=OperationStatus.FAILED,
                metrics={},
                duration_ms=duration_ms,
                error=str(e)
            )

    def _scan_ssid(self, **kwargs) -> dict:
        """Simulate WiFi SSID scan."""
        ssids = ["Enterprise-Network", "Guest-WiFi", "IoT-Devices"]
        channels = [1, 6, 11, 36, 40, 149]
        security = ["WPA2-ENT", "WPA3-ENT", "WPA2-PSK"]

        # Generate realistic signal strength based on "distance"
        base_signal = random.randint(-40, -30)
        distance_factor = random.randint(0, 50)
        signal_strength = base_signal - distance_factor

        network = random.choice(ssids)
        return {
            "ssid": network,
            "bssid": f"{'%02x' % random.randint(0, 255)}:{'%02x' % random.randint(0, 255)}:{'%02x' % random.randint(0, 255)}",
            "channel": random.choice(channels),
            "signal_strength": signal_strength,
            "security": random.choice(security),
            "frequency": "2.4" if random.random() > 0.5 else "5.0"
        }

    def _associate(self, ssid: str, **kwargs) -> dict:
        """Simulate associating with a WiFi network."""
        # 95% success rate
        success = random.random() < 0.95
        if not success:
            return {
                "associated": False,
                "error": "Association timeout",
                "retry_count": random.randint(1, 3)
            }

        return {
            "associated": True,
            "ssid": ssid,
            "bssid": "aa:bb:cc:dd:ee:ff",
            "assoc_id": random.randint(1, 65535),
            "signal_strength": random.randint(-70, -40)
        }

    def _authenticate(self, ssid: str, username: str = "user", password: str = "pass", **kwargs) -> dict:
        """Simulate AAA authentication."""
        # Simulate realistic auth latency
        base_latency = 300
        latency = base_latency + random.randint(-100, 300)

        # 90% success rate
        success = random.random() < 0.90

        if not success:
            return {
                "auth_status": "failed",
                "error": "Authentication rejected",
                "retry_count": random.randint(1, 3)
            }

        return {
            "auth_status": "success",
            "ssid": ssid,
            "username": username,
            "auth_latency_ms": max(latency, 0),
            "session_id": f"sess_{random.randint(100000, 999999)}",
            "auth_protocol": "802.1X"
        }

    def _login(self, credential: str, **kwargs) -> dict:
        """Simulate user login to network services."""
        return {
            "login_status": "success",
            "session_token": f"token_{random.randint(1000000, 9999999)}",
            "user_id": f"user_{random.randint(1000, 9999)}",
            "roles": ["employee", "network_user"],
            "login_latency_ms": random.randint(50, 200)
        }

    def _configure_router(self, config: str = "default", **kwargs) -> dict:
        """Simulate router configuration."""
        return {
            "config_status": "success",
            "change_id": f"chg_{random.randint(1000, 9999)}",
            "applied": True,
            "configuration": config,
            "config_latency_ms": random.randint(100, 500)
        }

    def _deploy_ap(self, ssid: str, security: str = "WPA2-ENT", **kwargs) -> dict:
        """Simulate access point deployment."""
        return {
            "deploy_status": "success",
            "ap_id": f"ap_{random.randint(100, 999)}",
            "ssid": ssid,
            "security": security,
            "radios": [{"band": "2.4", "enabled": True}, {"band": "5.0", "enabled": True}],
            "deployment_latency_ms": random.randint(500, 2000)
        }

    def _generate_traffic(self, duration: int = 60, volume: str = "low", **kwargs) -> dict:
        """Simulate network traffic generation."""
        volumes = {
            "low": (1000000, 5000000),    # 1-5 MB
            "medium": (50000000, 100000000),  # 50-100 MB
            "high": (500000000, 1000000000)   # 500 MB - 1 GB
        }

        min_bytes, max_bytes = volumes.get(volume, volumes["low"])
        bytes_transferred = random.randint(min_bytes, max_bytes)

        return {
            "traffic_status": "success",
            "duration_sec": duration,
            "volume": volume,
            "bytes_transferred": bytes_transferred,
            "packets_transferred": bytes_transferred // random.randint(500, 1500),
            "throughput_mbps": round(bytes_transferred * 8 / (duration * 1000000), 2),
            "latency_ms": random.randint(5, 50),
            "jitter_ms": round(random.random() * 10, 2)
        }

    def execute_all(self, operations: List[Dict]) -> List[OperationResult]:
        """
        Execute a sequence of operations.

        Args:
            operations: List of {operation, **kwargs} dicts

        Returns:
            List of OperationResults
        """
        results = []
        for op in operations:
            operation = op.pop("operation")
            result = self.execute(operation, **op)
            results.append(result)
        return results
