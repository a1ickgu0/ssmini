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
    - wifi.scan_channels: Scan WiFi channels
    - wifi.associate: Associate with a WiFi network
    - wifi.disassociate: Disassociate from WiFi network
    - wifi.detect_signal: Detect signal strength
    - wifi.roam: Roam to stronger AP
    - aaa.authenticate: Authenticate with AAA server
    - aaa.login: Login to network services
    - aaa.deauthenticate: Deauthenticate from network
    - dhcp.discover: DHCP discover
    - dns.resolve: DNS resolution
    - vpn.connect: Connect to VPN
    - proxy.connect: Connect to proxy
    - file.share_access: Access file share
    - email.send: Send email
    - http.access: Access HTTP/intranet
    - service.reconnect: Reconnect services
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
            "wifi.scan_channels": self._scan_channels,
            "wifi.associate": self._associate,
            "wifi.disassociate": self._disassociate,
            "wifi.detect_signal": self._detect_signal,
            "wifi.roam": self._roam,
            "aaa.authenticate": self._authenticate,
            "aaa.login": self._login,
            "aaa.deauthenticate": self._deauthenticate,
            "dhcp.discover": self._dhcp_discover,
            "dns.resolve": self._dns_resolve,
            "vpn.connect": self._vpn_connect,
            "proxy.connect": self._proxy_connect,
            "file.share_access": self._file_share_access,
            "email.send": self._send_email,
            "http.access": self._http_access,
            "service.reconnect": self._service_reconnect,
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

    def _scan_channels(self, **kwargs) -> dict:
        """Simulate WiFi channel scan."""
        latency = random.randint(100, 800)
        channels = random.sample(range(1, 14), random.randint(3, 13))
        return {
            "channels_found": len(channels),
            "scan_latency_ms": latency,
            "channels": channels
        }

    def _disassociate(self, **kwargs) -> dict:
        """Simulate WiFi disassociation."""
        return {
            "disassoc_status": "success",
            "disassoc_latency_ms": random.randint(10, 50)
        }

    def _detect_signal(self, **kwargs) -> dict:
        """Simulate signal strength detection."""
        # Generate weak signal for roaming scenario
        signal = random.randint(-75, -67)
        return {
            "signal_strength": signal
        }

    def _roam(self, **kwargs) -> dict:
        """Simulate roaming to stronger AP."""
        latency = random.randint(500, 2000)
        packet_loss = random.randint(0, 5)
        return {
            "roam_status": "success",
            "roam_latency_ms": latency,
            "packet_loss_percent": packet_loss,
            "new_ap_id": f"ap_{random.randint(100, 999)}"
        }

    def _deauthenticate(self, **kwargs) -> dict:
        """Simulate deauthentication."""
        return {
            "deauth_status": "success",
            "deauth_latency_ms": random.randint(10, 100)
        }

    def _dhcp_discover(self, **kwargs) -> dict:
        """Simulate DHCP discover."""
        latency = random.randint(50, 500)
        return {
            "dhcp_status": "success",
            "dhcp_latency_ms": latency,
            "ip_assigned": True,
            "ip_address": f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "lease_time": 3600
        }

    def _dns_resolve(self, **kwargs) -> dict:
        """Simulate DNS resolution."""
        latency = random.randint(10, 200)
        return {
            "dns_status": "success",
            "dns_latency_ms": latency,
            "resolved_addresses": [f"10.0.{random.randint(0, 255)}.{random.randint(1, 254)}"]
        }

    def _vpn_connect(self, vpn_server: str = "vpn.enterprise.com", **kwargs) -> dict:
        """Simulate VPN connection."""
        latency = random.randint(500, 3000)
        return {
            "vpn_status": "connected",
            "vpn_latency_ms": latency,
            "vpn_server": vpn_server,
            "vpn_protocol": "IKEv2"
        }

    def _proxy_connect(self, proxy_server: str = "proxy.enterprise.com", **kwargs) -> dict:
        """Simulate proxy connection."""
        latency = random.randint(100, 500)
        return {
            "proxy_status": "authenticated",
            "proxy_latency_ms": latency,
            "proxy_server": proxy_server
        }

    def _file_share_access(self, share_name: str = "share", **kwargs) -> dict:
        """Simulate file share access."""
        latency = random.randint(50, 1000)
        bandwidth = random.randint(1, 50)
        return {
            "share_access_status": "success",
            "file_transfer_bandwidth_mbps": bandwidth,
            "file_transfer_latency_ms": latency,
            "share_name": share_name
        }

    def _send_email(self, **kwargs) -> dict:
        """Simulate email sending."""
        latency = random.randint(100, 2000)
        return {
            "email_status": "success",
            "email_latency_ms": latency,
            "message_id": f"msg_{random.randint(100000, 999999)}"
        }

    def _http_access(self, url: str = "http://intranet.enterprise.com", **kwargs) -> dict:
        """Simulate HTTP/intranet access."""
        latency = random.randint(100, 5000)
        return {
            "http_status": 200,
            "page_load_latency_ms": latency,
            "url": url
        }

    def _service_reconnect(self, **kwargs) -> dict:
        """Simulate service reconnection."""
        latency = random.randint(200, 1000)
        return {
            "service_reconnect_status": "success",
            "service_latency_ms": latency,
            "services_reconnected": ["vpn", "proxy", "file_share"]
        }

    def _associate(self, ssid: str = None, **kwargs) -> dict:
        """Simulate associating with a WiFi network."""
        # Generate signal strength in range [-67..-55] for constraint satisfaction
        signal = random.randint(-67, -55)
        latency = random.randint(50, 300)
        return {
            "association_status": "success",
            "association_latency_ms": latency,
            "signal_strength": signal,
            "ssid": ssid or "Enterprise-Network",
            "bssid": "aa:bb:cc:dd:ee:ff",
            "assoc_id": random.randint(1, 65535)
        }

    def _authenticate(self, ssid: str = None, username: str = "user", password: str = "pass", **kwargs) -> dict:
        """Simulate AAA authentication."""
        # Simulate realistic auth latency in range [200..1500]
        latency = random.randint(200, 1500)
        return {
            "auth_status": "success",
            "auth_latency_ms": latency,
            "auth_method": "eap_peap",
            "certificate_valid": True,
            "ssid": ssid or "Enterprise-Network",
            "username": username,
            "session_id": f"sess_{random.randint(100000, 999999)}",
            "auth_protocol": "802.1X"
        }

    def _scan_ssid(self, **kwargs) -> dict:
        """Simulate WiFi SSID scan."""
        # Generate signal strength in range [-67..-55] for constraint satisfaction
        signal = random.randint(-67, -55)
        return {
            "ssid": "Enterprise-Network",
            "ssid_found": True,
            "bssid": f"{'%02x' % random.randint(0, 255)}:{'%02x' % random.randint(0, 255)}:{'%02x' % random.randint(0, 255)}",
            "channel": random.choice([1, 6, 11, 36, 40, 149]),
            "signal_strength": signal,
            "security": "WPA2-ENT",
            "frequency": "5.0"
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
