from __future__ import annotations

import socket

import psutil
from agents import function_tool

from core.powershell import run_ps
from core.risk import Risk, risk


@risk(Risk.LOW)
@function_tool
def get_network_adapters() -> dict[str, str]:
    """List network adapters with IP address configuration.

    Returns:
        A dict with status and an 'adapters' table string.
    """
    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        lines = ["ADAPTER                        STATUS  SPEED(Mbps)  ADDRESS"]
        for name, addr_list in addrs.items():
            stat = stats.get(name)
            up = "UP" if (stat and stat.isup) else "DOWN"
            speed = str(stat.speed) if stat else "?"
            ips = [a.address for a in addr_list if a.family == socket.AF_INET]
            ip_str = ", ".join(ips) if ips else "-"
            lines.append(f"{name:<30} {up:<7} {speed:<12} {ip_str}")
        return {"status": "ok", "adapters": "\n".join(lines)}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_network_stats() -> dict[str, str]:
    """Show bytes sent and received per network adapter.

    Returns:
        A dict with status and a 'stats' table string.
    """
    try:
        counters = psutil.net_io_counters(pernic=True)
        lines = [
            "ADAPTER                        SENT(MB)  RECV(MB)  PKTS_SENT  PKTS_RECV"
        ]
        for name, c in counters.items():
            lines.append(
                f"{name:<30} {c.bytes_sent / 1e6:>8.1f}  {c.bytes_recv / 1e6:>8.1f}  "
                f"{c.packets_sent:>9}  {c.packets_recv:>9}"
            )
        return {"status": "ok", "stats": "\n".join(lines)}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def test_connectivity(
    host: str = "8.8.8.8", port: int = 0, count: int = 4
) -> dict[str, str]:
    """Test network connectivity by pinging a host or checking a TCP port.

    Args:
        host: Hostname or IP address to test (default 8.8.8.8).
        port: TCP port to test. If 0, ICMP ping is used instead.
        count: Number of ping packets (ignored for TCP test).

    Returns:
        A dict with status and 'result' string.
    """
    try:
        if port > 0:
            sock = socket.create_connection((host, port), timeout=5)
            sock.close()
            return {
                "status": "ok",
                "result": f"TCP connection to {host}:{port} successful.",
            }
        result = run_ps(
            f"Test-Connection -ComputerName '{host}' -Count {count} | Format-Table -AutoSize | Out-String"
        )
        return {"status": "ok", "result": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_active_connections() -> dict[str, str]:
    """List active TCP/UDP connections on this machine.

    Returns:
        A dict with status and a 'connections' table string.
    """
    try:
        conns = psutil.net_connections()
        lines = ["PROTO  LOCAL_ADDR            REMOTE_ADDR          STATUS    PID"]
        for c in sorted(
            conns, key=lambda x: (x.status, x.laddr.port if c.laddr else 0)
        ):
            local = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "-"
            remote = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "-"
            lines.append(
                f"{c.type.name:<6} {local:<20} {remote:<20} {c.status:<9} {c.pid or '-'}"
            )
        return {"status": "ok", "connections": "\n".join(lines)}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_dns_settings() -> dict[str, str]:
    """Show DNS server configuration for all network adapters.

    Returns:
        A dict with status and 'dns_settings' string.
    """
    try:
        result = run_ps(
            "Get-DnsClientServerAddress | Select-Object InterfaceAlias, AddressFamily, ServerAddresses | "
            "Format-Table -AutoSize | Out-String"
        )
        return {"status": "ok", "dns_settings": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def list_firewall_rules(direction: str = "both") -> dict[str, str]:
    """List Windows Firewall rules.

    Args:
        direction: 'inbound', 'outbound', or 'both' (default 'both').

    Returns:
        A dict with status and a 'rules' summary string.
    """
    try:
        filter_clause = ""
        if direction == "inbound":
            filter_clause = "| Where-Object { $_.Direction -eq 'Inbound' } "
        elif direction == "outbound":
            filter_clause = "| Where-Object { $_.Direction -eq 'Outbound' } "
        result = run_ps(
            f"Get-NetFirewallRule {filter_clause}"
            "| Select-Object Name, DisplayName, Direction, Action, Enabled "
            "| Format-Table -AutoSize | Out-String"
        )
        return {"status": "ok", "rules": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def flush_dns_cache() -> dict[str, str]:
    """Flush the local DNS resolver cache.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps("Clear-DnsClientCache")
        return {"status": "ok", "message": "DNS cache flushed successfully."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def add_firewall_rule(
    name: str,
    direction: str = "Inbound",
    action: str = "Allow",
    protocol: str = "TCP",
    local_port: str = "",
    description: str = "",
) -> dict[str, str]:
    """Add a new Windows Firewall rule.

    Args:
        name: Unique name for the rule.
        direction: 'Inbound' or 'Outbound'.
        action: 'Allow' or 'Block'.
        protocol: 'TCP', 'UDP', or 'Any'.
        local_port: Port number or range (e.g. '8080' or '8080-8090'). Empty = any.
        description: Optional description for the rule.

    Returns:
        A dict with status and message.
    """
    try:
        port_clause = f"-LocalPort {local_port} " if local_port else ""
        desc_clause = f"-Description '{description}' " if description else ""
        run_ps(
            f"New-NetFirewallRule -DisplayName '{name}' -Direction {direction} "
            f"-Action {action} -Protocol {protocol} {port_clause}{desc_clause}-ErrorAction Stop"
        )
        return {
            "status": "ok",
            "message": f"Firewall rule '{name}' created ({direction}/{action}/{protocol}).",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def remove_firewall_rule(name: str) -> dict[str, str]:
    """Remove a Windows Firewall rule by display name.

    Args:
        name: The display name of the rule to remove.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps(f"Remove-NetFirewallRule -DisplayName '{name}' -ErrorAction Stop")
        return {"status": "ok", "message": f"Firewall rule '{name}' removed."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def reset_network_stack() -> dict[str, str]:
    """Reset the TCP/IP stack and Winsock catalog. Requires a reboot to take effect.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps("netsh int ip reset | Out-String")
        run_ps("netsh winsock reset | Out-String")
        return {
            "status": "ok",
            "message": "TCP/IP stack and Winsock reset. Please reboot for changes to take effect.",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def set_dns_servers(adapter_name: str, dns_servers: list[str]) -> dict[str, str]:
    """Set DNS server addresses for a network adapter.

    Args:
        adapter_name: The interface alias (e.g. 'Ethernet', 'Wi-Fi').
        dns_servers: List of DNS server IP addresses, e.g. ['8.8.8.8', '1.1.1.1'].

    Returns:
        A dict with status and message.
    """
    try:
        servers_str = ", ".join(f"'{s}'" for s in dns_servers)
        run_ps(
            f"Set-DnsClientServerAddress -InterfaceAlias '{adapter_name}' "
            f"-ServerAddresses ({servers_str}) -ErrorAction Stop"
        )
        return {
            "status": "ok",
            "message": f"DNS servers for '{adapter_name}' set to {dns_servers}.",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
