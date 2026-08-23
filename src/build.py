#!/usr/bin/env python3
"""
Orquestrador de Compilação do Projeto listas_bloqueio.
Gera todas as listas multi-formato otimizadas para AdGuard Home, Pi-hole, Hosts e DNS Servers.
"""

import argparse
from pathlib import Path
import sys
from typing import Any, Dict

# Importação dos módulos internos
try:
    from src.parser import parse_file, parse_whitelist
    from src.deduplicator import deduplicate_and_optimize
    from src.exporter import (
        export_adguard,
        export_domains,
        export_hosts,
        export_pihole_regex,
        export_dnsmasq,
        export_unbound,
    )
except ImportError:
    # Caso executado diretamente de dentro da pasta src/
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.parser import parse_file, parse_whitelist
    from src.deduplicator import deduplicate_and_optimize
    from src.exporter import (
        export_adguard,
        export_domains,
        export_hosts,
        export_pihole_regex,
        export_dnsmasq,
        export_unbound,
    )

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def load_config(config_path: Path) -> Dict[str, Any]:
    """Carrega o arquivo de configuração YAML ou retorna os padrões do projeto."""
    default_config = {
        "metadata": {
            "title": "Lista de Telemetria e Bloqueios - FACRF",
            "description": "Bloqueio unificado e otimizado de telemetria, rastreadores, adnets e popups agressivos",
            "version": "1.3.0",
            "homepage": "https://github.com/facrf/listas_bloqueio",
            "license": "MIT",
            "redirect_ip": "0.0.0.0",
        },
        "files": {
            "blacklist": "config/blacklist.txt",
            "whitelist": "config/whitelist.txt",
            "output_dir": "output",
        },
    }

    if HAS_YAML and config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if loaded and isinstance(loaded, dict):
                    return loaded
        except Exception as e:
            print(f"[!] Aviso: Falha ao ler {config_path}: {e}. Usando configuração padrão.")

    return default_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Compilador e otimizador de listas de bloqueio DNS.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/sources.yaml"),
        help="Caminho para o arquivo sources.yaml",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Diretório de saída para os arquivos compilados",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    config_file = (project_root / args.config) if not args.config.is_absolute() else args.config

    config = load_config(config_file)
    metadata = config.get("metadata", {})
    files_cfg = config.get("files", {})

    blacklist_file = project_root / files_cfg.get("blacklist", "config/blacklist.txt")
    whitelist_file = project_root / files_cfg.get("whitelist", "config/whitelist.txt")
    
    if args.output_dir:
        output_dir = args.output_dir if args.output_dir.is_absolute() else (project_root / args.output_dir)
    else:
        output_dir = project_root / files_cfg.get("output_dir", "output")

    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"🚀 Iniciando compilação: {metadata.get('title', 'listas_bloqueio')}")
    print(f"📁 Raiz do Projeto: {project_root}")
    print("=" * 70)

    # 1. Leitura e parsing dos arquivos de entrada
    print(f"[*] Lendo blacklist manual: {blacklist_file.relative_to(project_root)}...")
    raw_blacklist_entries = parse_file(blacklist_file)
    raw_domains = [e.cleaned for e in raw_blacklist_entries if not e.is_wildcard]
    raw_wildcards = [e.cleaned for e in raw_blacklist_entries if e.is_wildcard]

    print(f"[*] Lendo whitelist: {whitelist_file.relative_to(project_root)}...")
    whitelist_domains = parse_whitelist(whitelist_file)

    # 2. Otimização e Deduplicação via Trie
    print("[*] Executando deduplicação e otimização por Trie de subdomínios...")
    opt_domains, opt_wildcards, redundancies = deduplicate_and_optimize(
        domains=raw_domains,
        wildcards=raw_wildcards,
        whitelist=whitelist_domains,
    )

    redirect_ip = metadata.get("redirect_ip", "0.0.0.0")

    # 3. Geração dos arquivos de saída
    outputs = {
        "adguard.txt": export_adguard(opt_domains, opt_wildcards, metadata),
        "pihole.txt": export_domains(opt_domains, metadata),
        "domains.txt": export_domains(opt_domains, metadata),
        "hosts.txt": export_hosts(opt_domains, metadata, redirect_ip=redirect_ip),
        "pihole-regex.txt": export_pihole_regex(opt_wildcards, metadata),
        "dnsmasq.conf": export_dnsmasq(opt_domains, metadata, redirect_ip=redirect_ip),
        "unbound.conf": export_unbound(opt_domains, metadata),
    }

    for filename, content in outputs.items():
        dest = output_dir / filename
        with open(dest, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [+] Gerado: {dest.relative_to(project_root)} ({len(content.splitlines())} linhas)")

    # 4. Atualizar blocklist.txt na raiz para compatibilidade retroativa
    root_blocklist = project_root / "blocklist.txt"
    with open(root_blocklist, "w", encoding="utf-8") as f:
        f.write(outputs["adguard.txt"])
    print(f"  [+] Atualizado para retrocompatibilidade: blocklist.txt")

    # 5. Resumo estatístico
    print("=" * 70)
    print("📊 RESUMO DA COMPILAÇÃO:")
    print(f"  • Total bruto de regras carregadas: {len(raw_blacklist_entries)}")
    print(f"  • Regras na Whitelist: {len(whitelist_domains)}")
    print(f"  • Redundâncias eliminadas (subdomínios/duplicatas): {redundancies}")
    print(f"  • Domínios FQDN únicos ativos: {len(opt_domains)}")
    print(f"  • Padrões Wildcard ativos: {len(opt_wildcards)}")
    print(f"  • Total de regras ativas (AdGuard): {len(opt_domains) + len(opt_wildcards)}")
    print("=" * 70)
    print("✅ Compilação concluída com sucesso!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
