# AGENTS.md — Regras, Diretrizes e Governança para Agentes de IA

Este documento define o escopo, arquitetura, padrões técnicos e regras de governança para qualquer agente de inteligência artificial (incluindo Antigravity, Claude, ChatGPT, Cursor, Copilot ou ferramentas autônomas) que atue neste repositório.

---

## 🔒 1. Restrição Estrita de Escopo (Workspace Boundary)

> [!IMPORTANT]
> **ISOLAMENTO ABSOLUTO DE DIRETÓRIO**:
> Qualquer agente atuando neste projeto **DEVE OPERAR EXCLUSIVAMENTE** dentro do diretório raiz deste projeto:
> ```
> /storage/www/projetos/utils/listas_bloqueio/
> ```
> e em suas respectivas **subpastas**.
>
> - **NUNCA** crie, edite, inspecione, mova ou exclua arquivos fora desta pasta raiz.
> - **NUNCA** execute comandos de gravação ou manipulação de arquivos em diretórios do sistema operacional como `/tmp/`, `/home/`, `/var/`, `/etc/`, `/storage/www/projetos/utils/` (fora desta pasta) ou qualquer outro caminho externo.
> - Todos os comandos executados via terminal (`run_command`) devem ter o diretório de trabalho (`Cwd`) configurado estritamente para `/storage/www/projetos/utils/listas_bloqueio` ou uma de suas subpastas.
> - Arquivos temporários, rascunhos, caches ou dados de teste devem ser criados exclusivamente em subpastas locais dedicadas (ex.: `scratch/`, `cache/`, `tmp/`), devidamente ignoradas pelo `.gitignore`.

---

## 📌 2. Visão Geral e Propósito do Projeto

O projeto **`listas_bloqueio`** é um ecossistema de utilitários e automações dedicado ao gerenciamento, download, agregação, validação, deduplicação, normalização e exportação de listas de bloqueio (*blocklists*, *threat intelligence feeds*, filtros de DNS/IP/Domínios/URLs e regras para firewall/adblock).

### Objetivos Principais:
- **Download & Agregação**: Obtenção automatizada de listas de fontes confiáveis (adblock, malware, phishing, telemetria, rastreadores, spam, botnets).
- **Normalização & Higienização**: Limpeza de sintaxe, conversão para minúsculas, remoção de comentários, suporte a IDN (Punycode), validação estrita de domínios (RFC 1035), endereços IPv4/IPv6 e blocos CIDR (RFC 4632 / RFC 4291).
- **Deduplicação & Otimização**: Algoritmos eficientes para consolidação e remoção de redundâncias (ex.: eliminação de subdomínios quando o domínio raiz já estiver na lista, agregação de sub-redes CIDR).
- **Exportação Multi-formato**: Geração de saídas compatíveis com:
  - Formato `hosts` (`0.0.0.0 dominio.com` / `127.0.0.1 dominio.com`)
  - Formatos DNS (Pi-hole, AdGuard Home, Unbound, BIND, Dnsmasq, CoreDNS, PowerDNS)
  - Formatos de Firewall (iptables, nftables, pfSense, OPNsense, MikroTik, IPSet, CIDR lists)
  - Formatos estruturados (Plain text, JSON, CSV, YAML)
  - Formatos de Extensões de Navegador (Adblock Plus / uBlock Origin rule syntax)

---

## 🏗️ 3. Estrutura Recomendada de Pastas

Ao criar ou organizar arquivos neste projeto, siga a seguinte estrutura modular:

```text
/storage/www/projetos/utils/listas_bloqueio/
├── AGENTS.md             # Este arquivo (regras e diretrizes para LLMs)
├── README.md             # Documentação principal para humanos
├── .gitignore            # Regras de exclusão do Git
├── .env.example          # Modelo de variáveis de ambiente e configurações
├── config/               # Arquivos de configuração e fontes de feeds (YAML/JSON/TOML)
│   ├── sources.yaml      # Lista de URLs e metadados das fontes externas
│   ├── whitelist.txt     # Domínios e IPs permitidos globalmente (exceções)
│   └── blacklist.txt     # Domínios e IPs bloqueados manualmente
├── src/                  # Código-fonte principal (scripts/módulos de processamento)
├── output/               # Listas finais processadas e formatadas prontas para consumo
├── tests/                # Testes unitários e de integração
├── docs/                 # Documentação detalhada e especificações de formatos
├── data/                 # Armazenamento de dados locais (quando aplicável)
│   └── cache/            # Caches de downloads temporários (ignorado no Git)
└── scratch/              # Área temporária para rascunhos de desenvolvimento (ignorado no Git)
```

---

## 🛠️ 4. Padrões Técnicos e Boas Práticas

### 1. Segurança e Privacidade
- **Zero Credenciais**: Nunca exponha senhas, chaves de API, tokens de acesso ou dados sensíveis nos arquivos versionados.
- Utilize `.env` para configurações locais e sempre mantenha um `.env.example` atualizado.
- Valide URLs e conteúdos baixados para evitar injeções ou processamento de arquivos corrompidos.

### 2. Eficiência de Memória e Processamento
- Listas de bloqueio podem conter centenas de milhares ou milhões de entradas.
- Utilize estruturas de dados com busca em tempo constante ou logarítmico (ex.: `Set`, `HashSet`, árvores de prefixo/Trie, Bloom Filters).
- Prefira processamento via *streaming* (linha por linha / iteradores) em vez de carregar arquivos gigantes inteiramente na memória quando não for estritamente necessário.
- Implemente suporte a *cache com verificação de ETag/Last-Modified* para evitar downloads redundantes de feeds externos.

### 3. Validação Estrita de Dados
- **Domínios**: Validar formato de FQDN, caracteres válidos (`[a-z0-9-_.]`), comprimento máximo de labels e conversão Punycode quando necessário.
- **Endereços IP**: Validar sintaxe IPv4 (0.0.0.0 a 255.255.255.255) e IPv6 com suporte a notação CIDR válida.
- **Whitelisting**: Garantir que as listas de liberação (*whitelist*) tenham precedência obrigatória sobre qualquer regra de bloqueio gerada.

### 4. Idempotência e Reprodutibilidade
- A execução do pipeline com as mesmas entradas deve gerar sempre saídas idênticas e ordenadas deterministicamente (ordem alfanumérica consistente).
- Inclusão de cabeçalhos nos arquivos exportados contendo metadados (data/hora de geração UTC, versão, quantidade de entradas ativas, licença/fontes).

---

## 🤖 5. Regras Operacionais para Agentes de IA

1. **Inspeção Prévia**: Antes de modificar ou refatorar qualquer arquivo existente, leia seu conteúdo completo para preservar contexto e convenções.
2. **Edições Não Destrutivas**: Ao atualizar código ou documentação, preserve comentários essenciais, docstrings e regras pré-existentes, a menos que haja instrução explícita em contrário.
3. **Respeito ao `.gitignore`**: Não adicione arquivos de cache, saídas temporárias massivas ou binários ao controle de versão.
4. **Mensagens e Logs Claros**: Qualquer script criado deve conter mensagens de log informativas e tratamento adequado de exceções/erros.
5. **Autonomia com Responsabilidade**: Se surgirem dúvidas sobre preferências de arquitetura ou bibliotecas não especificadas, proponha soluções robustas mantendo a simplicidade e a portabilidade.

---

*Documento ativo de governança e operação técnica do projeto `listas_bloqueio`.*
