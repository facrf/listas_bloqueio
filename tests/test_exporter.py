"""
Testes unitários para o módulo de exportação multi-formato.
"""

from src.exporter import (
    export_adguard,
    export_dnsmasq,
    export_domains,
    export_hosts,
    export_pihole_regex,
    export_unbound,
    wildcard_to_pihole_regex,
)

METADATA = {
    "title": "Test List",
    "description": "Test Description",
    "version": "1.0.0",
    "homepage": "https://example.com",
    "license": "MIT",
}


def test_export_adguard():
    domains = ["doubleclick.net", "samsungads.com"]
    wildcards = ["darkmahou.*"]
    out = export_adguard(domains, wildcards, METADATA)
    assert "||doubleclick.net^" in out
    assert "||samsungads.com^" in out
    assert "||darkmahou.*^" in out
    assert "! Title: Test List" in out


def test_export_domains():
    domains = ["doubleclick.net", "samsungads.com"]
    out = export_domains(domains, METADATA)
    assert "doubleclick.net" in out
    assert "samsungads.com" in out
    assert "||" not in out
    assert "# Title: Test List" in out


def test_export_hosts():
    domains = ["doubleclick.net"]
    out = export_hosts(domains, METADATA, redirect_ip="0.0.0.0")
    assert "0.0.0.0 doubleclick.net" in out


def test_wildcard_to_pihole_regex():
    assert wildcard_to_pihole_regex("darkmahou.*") == r"(^|\.)darkmahou\.[a-z0-9-]+$"
    assert wildcard_to_pihole_regex("*.example.com") == r"(^|\.)example\.com$"


def test_export_pihole_regex():
    wildcards = ["darkmahou.*", "superanimes.*"]
    out = export_pihole_regex(wildcards, METADATA)
    assert r"(^|\.)darkmahou\.[a-z0-9-]+$" in out
    assert r"(^|\.)superanimes\.[a-z0-9-]+$" in out


def test_export_dnsmasq():
    domains = ["doubleclick.net"]
    out = export_dnsmasq(domains, METADATA, redirect_ip="0.0.0.0")
    assert "address=/doubleclick.net/0.0.0.0" in out


def test_export_unbound():
    domains = ["doubleclick.net"]
    out = export_unbound(domains, METADATA)
    assert 'local-zone: "doubleclick.net" always_nxdomain' in out
