# 🛡️ Listas de Bloqueio DNS — FACRF

[![Build & Validate](https://github.com/facrf/listas_bloqueio/actions/workflows/build.yml/badge.svg)](https://github.com/facrf/listas_bloqueio/actions/workflows/build.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![AdGuard Home](https://img.shields.io/badge/AdGuard_Home-Supported-brightgreen.svg)](https://adguard.com/adguard-home.html)
[![Pi-hole](https://img.shields.io/badge/Pi--hole-Supported-brightgreen.svg)](https://pi-hole.net/)

Filtros unificados e otimizados para bloqueio de **telemetria invasiva** (Samsung, Microsoft, Meta/Facebook, Google/SDKs mobile), **redes de anúncios abusivas**, **redirecionamentos/pop-ups** e **sites de streaming/trackers**.

As listas são validadas contra RFCs, normalizadas com suporte a IDN (Punycode) e deduplicadas via árvore de sufixos (*Trie*), garantindo **máxima performance e compatibilidade sem quebras de navegação**.

---

## 🔗 Links Diretos (Raw URLs para uso no DNS)

Basta copiar o link correspondente à sua plataforma e adicionar ao seu gerenciador de DNS:

| Plataforma / Formato | Arquivo | URL Direta (Raw) |
| :--- | :--- | :--- |
| **AdGuard Home / ABP** | [`output/adguard.txt`](output/adguard.txt) | `https://raw.githubusercontent.com/facrf/listas_bloqueio/main/output/adguard.txt` |
| **Pi-hole (Gravity Adlist)** | [`output/pihole.txt`](output/pihole.txt) | `https://raw.githubusercontent.com/facrf/listas_bloqueio/main/output/pihole.txt` |
| **Pi-hole (Regex Rules)** | [`output/pihole-regex.txt`](output/pihole-regex.txt) | `https://raw.githubusercontent.com/facrf/listas_bloqueio/main/output/pihole-regex.txt` |
| **Arquivo Hosts** | [`output/hosts.txt`](output/hosts.txt) | `https://raw.githubusercontent.com/facrf/listas_bloqueio/main/output/hosts.txt` |
| **Dnsmasq** | [`output/dnsmasq.conf`](output/dnsmasq.conf) | `https://raw.githubusercontent.com/facrf/listas_bloqueio/main/output/dnsmasq.conf` |
| **Unbound DNS** | [`output/unbound.conf`](output/unbound.conf) | `https://raw.githubusercontent.com/facrf/listas_bloqueio/main/output/unbound.conf` |
| **Retrocompatibilidade** | [`blocklist.txt`](blocklist.txt) | `https://raw.githubusercontent.com/facrf/listas_bloqueio/main/blocklist.txt` |

---

## 📖 Como Usar

### 🟢 1. No AdGuard Home
1. Acesse o painel web do seu **AdGuard Home**.
2. Vá em **Filtros (Filters)** > **Listas de bloqueio de DNS (DNS blocklists)**.
3. Clique em **Adicionar lista de bloqueio (Add blocklist)** > **Adicionar uma lista personalizada (Add custom list)**.
4. Insira um nome (ex: `FACRF Blocklist`) e cole a URL:
   ```text
   https://raw.githubusercontent.com/facrf/listas_bloqueio/main/output/adguard.txt
   ```
5. Clique em **Salvar**.

---

### 🔴 2. No Pi-hole

#### Adlist Regular (Domínios FQDN):
1. Acesse o painel web do seu **Pi-hole**.
2. Vá em **Adlists**.
3. No campo **Address**, adicione:
   ```text
   https://raw.githubusercontent.com/facrf/listas_bloqueio/main/output/pihole.txt
   ```
4. Clique em **Add** e depois atualize o Gravity em **Tools** > **Update Gravity** (ou execute `pihole -g` no terminal).

#### Regras Regex (Wildcards):
1. No painel do Pi-hole, vá em **Domains** > **RegEx filter**.
2. Adicione as expressões contidas no arquivo [`output/pihole-regex.txt`](output/pihole-regex.txt) para bloquear domínios que variam de TLD (ex: `(^|\.)darkmahou\.[a-z0-9-]+$`).

---

## 🏗️ Estrutura do Projeto

```text
listas_bloqueio/
├── config/
│   ├── blacklist.txt        # Regras manuais categorizadas e comentadas
│   ├── whitelist.txt        # Exceções globais (permite evitar falsos positivos)
│   └── sources.yaml         # Metadados e configurações do build
├── src/
│   ├── parser.py            # Validação FQDN, higienização e suporte IDN
│   ├── deduplicator.py      # Algoritmo Trie para poda de subdomínios redundantes
│   ├── downloader.py        # Gerenciador de cache com suporte a ETag/304
│   ├── exporter.py          # Gerador multi-formato (AdGuard, Pi-hole, Hosts, Unbound)
│   └── build.py             # Orquestrador CLI de compilação
├── output/                  # Listas compiladas e prontas para consumo
├── tests/                   # Testes unitários automatizados (pytest)
├── .github/workflows/       # CI/CD para compilação automática a cada push
├── pyproject.toml           # Configuração de build e integração pytest
├── AGENTS.md                # Governança e regras de arquitetura para IAs
└── README.md                # Documentação do projeto
```

---

## 🛠️ Desenvolvimento Local

### 1. Requisitos
- Python 3.10+
- `pip install pyyaml pytest`

### 2. Executar os Testes Unitários
```bash
pytest -v
```

### 3. Compilar as Listas
```bash
# Compilação padrão (com download/verificação de cache de feeds externos)
python3 src/build.py

# Compilação offline (usa apenas cache local e listas manuais)
python3 src/build.py --offline

# Forçar novo download de feeds remotos
python3 src/build.py --force-download
```

---

## ⚖️ Licença

Este projeto está licenciado sob a licença [MIT](LICENSE).
