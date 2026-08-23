"""
Testes unitários para o módulo de deduplicação e Trie.
"""

from src.deduplicator import DomainTrie, deduplicate_and_optimize


def test_domain_trie_subdomain_pruning():
    trie = DomainTrie()
    # Inserir raiz primeiro
    assert trie.insert("samsung.com") is True
    # Inserir subdomínio deve retornar False (coberto)
    assert trie.insert("dqa.samsung.com") is False
    assert trie.insert("sub.dqa.samsung.com") is False
    # Outro domínio independente deve retornar True
    assert trie.insert("google.com") is True


def test_deduplicate_and_optimize():
    raw_domains = [
        "telemetry.microsoft.com",
        "watson.telemetry.microsoft.com",  # Redundante
        "samsung.com",
        "dqa.samsung.com",                 # Redundante
        "google-analytics.com",
        "google-analytics.com",            # Duplicata exata
        "allowed-tracker.com",
    ]
    raw_wildcards = [
        "darkmahou.*",
        "darkmahou.*",                    # Duplicata
        "sub.darkmahou.*",                # Redundante
    ]
    whitelist = {"allowed-tracker.com"}

    opt_domains, opt_wildcards, redundancies = deduplicate_and_optimize(
        domains=raw_domains,
        wildcards=raw_wildcards,
        whitelist=whitelist,
    )

    # Verifica domínios resultantes
    assert "watson.telemetry.microsoft.com" not in opt_domains
    assert "telemetry.microsoft.com" in opt_domains
    assert "dqa.samsung.com" not in opt_domains
    assert "samsung.com" in opt_domains
    assert "allowed-tracker.com" not in opt_domains
    assert "google-analytics.com" in opt_domains

    # Verifica wildcards resultantes
    assert "darkmahou.*" in opt_wildcards
    assert "sub.darkmahou.*" not in opt_wildcards

    assert redundancies >= 3
