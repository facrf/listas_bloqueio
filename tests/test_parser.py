"""
Testes unitários para o parser de domínios.
"""

from src.parser import clean_line, normalize_domain


def test_clean_line():
    assert clean_line("   ") is None
    assert clean_line("# comentario") is None
    assert clean_line("! comentario abp") is None
    assert clean_line("// comentario c") is None
    assert clean_line("dominio.com # inline comment") == "dominio.com"
    assert clean_line("||dominio.com^ ! adguard") == "||dominio.com^"


def test_normalize_domain_plain():
    entry = normalize_domain("example.com")
    assert entry is not None
    assert entry.cleaned == "example.com"
    assert not entry.is_wildcard
    assert not entry.is_whitelist


def test_normalize_domain_abp_adguard():
    entry = normalize_domain("||ads.example.com^")
    assert entry is not None
    assert entry.cleaned == "ads.example.com"
    assert not entry.is_wildcard

    entry_mod = normalize_domain("||tracker.com^$third-party")
    assert entry_mod is not None
    assert entry_mod.cleaned == "tracker.com"


def test_normalize_domain_hosts_format():
    entry = normalize_domain("0.0.0.0 telemetry.samsung.com")
    assert entry is not None
    assert entry.cleaned == "telemetry.samsung.com"

    entry127 = normalize_domain("127.0.0.1 malware.site.org")
    assert entry127 is not None
    assert entry127.cleaned == "malware.site.org"


def test_normalize_domain_url_and_ports():
    entry = normalize_domain("https://badsite.com:8443/login/track")
    assert entry is not None
    assert entry.cleaned == "badsite.com"


def test_normalize_domain_idn_punycode():
    entry = normalize_domain("münchen.de")
    assert entry is not None
    assert entry.cleaned == "xn--mnchen-3ya.de"


def test_normalize_domain_wildcard():
    entry = normalize_domain("||darkmahou.*^")
    assert entry is not None
    assert entry.cleaned == "darkmahou.*"
    assert entry.is_wildcard


def test_normalize_domain_invalid():
    assert normalize_domain("localhost") is None
    assert normalize_domain("127.0.0.1") is None
    assert normalize_domain("0.0.0.0") is None
    assert normalize_domain("invalid..domain") is None
    assert normalize_domain("singleword") is None
    assert normalize_domain("-starts-with-hyphen.com") is None
