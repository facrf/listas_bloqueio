"""
Módulo de exportação multi-formato para DNS, AdGuard, Pi-hole, Hosts e Firewalls.
"""

from datetime import datetime, timezone
import re
from typing import Any, Dict, List


def generate_header(
    comment_char: str,
    metadata: Dict[str, Any],
    total_rules: int,
    format_name: str,
) -> str:
    """Gera o cabeçalho padronizado com metadados para as listas exportadas."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        f"{comment_char} ==============================================================================",
        f"{comment_char} Title: {metadata.get('title', 'Lista de Bloqueio')}",
        f"{comment_char} Description: {metadata.get('description', 'Filtro DNS unificado')}",
        f"{comment_char} Format: {format_name}",
        f"{comment_char} Version: {metadata.get('version', '1.0.0')}",
        f"{comment_char} Last Modified: {now_utc}",
        f"{comment_char} Total Entries: {total_rules}",
        f"{comment_char} Homepage: {metadata.get('homepage', '')}",
        f"{comment_char} License: {metadata.get('license', 'MIT')}",
        f"{comment_char} ==============================================================================",
        "",
    ]
    return "\n".join(lines)


def export_adguard(
    domains: List[str],
    wildcards: List[str],
    metadata: Dict[str, Any],
) -> str:
    """Exporta lista no formato AdGuard / Adblock Plus (||dominio^)."""
    total = len(domains) + len(wildcards)
    header = generate_header("!", metadata, total, "AdGuard Home / Adblock Plus")
    
    entries = []
    # Domínios regulares
    for d in domains:
        entries.append(f"||{d}^")
    # Wildcards
    for w in wildcards:
        entries.append(f"||{w}^")
        
    entries.sort()
    return header + "\n".join(entries) + "\n"


def export_domains(
    domains: List[str],
    metadata: Dict[str, Any],
) -> str:
    """Exporta lista em formato puro FQDN (um domínio por linha, ideal para Pi-hole Gravity)."""
    header = generate_header("#", metadata, len(domains), "Pi-hole / Plain Domains (FQDN)")
    return header + "\n".join(domains) + "\n"


def export_hosts(
    domains: List[str],
    metadata: Dict[str, Any],
    redirect_ip: str = "0.0.0.0",
) -> str:
    """Exporta lista no formato Hosts tradicional (0.0.0.0 dominio.com)."""
    header = generate_header("#", metadata, len(domains), f"Hosts File ({redirect_ip})")
    lines = [f"{redirect_ip} {d}" for d in domains]
    return header + "\n".join(lines) + "\n"


def wildcard_to_pihole_regex(wildcard: str) -> str:
    r"""
    Converte um padrão wildcard (ex: 'darkmahou.*' ou '*.example.com')
    em uma expressão regular padrão do Pi-hole FTL DNS.
    Exemplo: 'darkmahou.*' -> '(^|\.)darkmahou\.[a-z0-9-]+$'
    """
    pattern = wildcard.strip()
    if pattern.endswith(".*"):
        base = pattern[:-2]
        escaped_base = re.escape(base)
        return f"(^|\\.){escaped_base}\\.[a-z0-9-]+$"
    elif pattern.startswith("*."):
        base = pattern[2:]
        escaped_base = re.escape(base)
        return f"(^|\\.){escaped_base}$"
    else:
        # Substituir asteriscos genéricos
        parts = pattern.split("*")
        escaped_parts = [re.escape(p) for p in parts]
        return f"(^|\\.)" + ".*".join(escaped_parts) + "$"


def export_pihole_regex(
    wildcards: List[str],
    metadata: Dict[str, Any],
) -> str:
    """Exporta regras Regex para importação no Pi-hole (Regex Blacklist)."""
    header = generate_header("#", metadata, len(wildcards), "Pi-hole Regex Rules")
    regexes = [wildcard_to_pihole_regex(w) for w in wildcards]
    regexes.sort()
    return header + "\n".join(regexes) + "\n"


def export_dnsmasq(
    domains: List[str],
    metadata: Dict[str, Any],
    redirect_ip: str = "0.0.0.0",
) -> str:
    """Exporta lista no formato Dnsmasq (address=/dominio.com/0.0.0.0)."""
    header = generate_header("#", metadata, len(domains), "Dnsmasq Configuration")
    lines = [f"address=/{d}/{redirect_ip}" for d in domains]
    return header + "\n".join(lines) + "\n"


def export_unbound(
    domains: List[str],
    metadata: Dict[str, Any],
) -> str:
    """Exporta lista no formato Unbound DNS (local-zone: "dominio.com" always_nxdomain)."""
    header = generate_header("#", metadata, len(domains), "Unbound DNS Configuration")
    lines = [f'local-zone: "{d}" always_nxdomain' for d in domains]
    return header + "\n".join(lines) + "\n"
