"""General identity and network information for display pages."""

from dataclasses import dataclass
import getpass
import socket

import psutil


@dataclass(frozen=True)
class SystemInfo:
    username: str
    hostname: str
    local_ip: str | None
    tailscale_ip: str | None


class SystemInfoProvider:
    """Collect user, host, and IPv4 network information."""

    def read(self) -> SystemInfo:
        local_ip: str | None = None
        tailscale_ip: str | None = None

        interfaces = psutil.net_if_addrs()
        preferred_interfaces = ("eth0", "wlan0", "end0")

        for interface_name, addresses in interfaces.items():
            for address in addresses:
                if address.family != socket.AF_INET or address.address.startswith("127."):
                    continue

                if interface_name.startswith("tailscale"):
                    tailscale_ip = address.address
                elif interface_name in preferred_interfaces and local_ip is None:
                    local_ip = address.address

        # Support systems whose primary interface has a different name.
        if local_ip is None:
            ignored_prefixes = ("docker", "tailscale", "veth", "br-")
            for interface_name, addresses in interfaces.items():
                if interface_name.startswith(ignored_prefixes):
                    continue
                for address in addresses:
                    if address.family == socket.AF_INET and not address.address.startswith("127."):
                        local_ip = address.address
                        break
                if local_ip is not None:
                    break

        return SystemInfo(
            username=getpass.getuser(),
            hostname=socket.gethostname(),
            local_ip=local_ip,
            tailscale_ip=tailscale_ip,
        )
