"""
Módulo de parsing, higienização e validação de regras de bloqueio.
"""

from dataclasses import dataclass
import ipaddress
from pathlib import Path
import re
from typing import List, Optional, Set, Tuple


@dataclass(frozen=True)
class RuleEntry:
    raw: str
    cleaned: str
    is_wildcard: bool
    is_whitelist: bool = False


# Regex para validar caracteres de domínio ou wildcard
VALID_LABEL_REGEX = re.compile(r"^[a-z0-9_-]+$", re.IGNORECASE)
VALID_WILDCARD_LABEL_REGEX = re.compile(r"^[a-z0-9_*-]+$", re.IGNORECASE)


def clean_line(line: str) -> Optional[str]:
    """Remove espaços, quebras de linha e comentários inline."""
    line = line.strip()
    if not line:
        return None
    # Ignorar comentários de linha inteira
    if line.startswith(("#", "!", ";", "//")):
        return None
    # Remover comentários inline (evitando quebrar URLs como https://)
    for separator in ("#", "!", ";"):
        if separator in line:
            line = line.split(separator)[0].strip()
    if " //" in line:
        line = line.split(" //")[0].strip()
    return line if line else None


def normalize_domain(raw_line: str) -> Optional[RuleEntry]:
    """
    Normaliza e valida uma linha de regra para formato de domínio canônico ou wildcard.
    Suporta:
    - FQDN puro: ads.example.com
    - Formato ABP/AdGuard: ||ads.example.com^, ||example.*^, @@||whitelist.com^
    - Formato Hosts: 0.0.0.0 ads.example.com, 127.0.0.1 ads.example.com
    - URLs: http://ads.example.com/path -> ads.example.com
    - IDN (Punycode): xn--...
    """
    cleaned = clean_line(raw_line)
    if not cleaned:
        return None

    is_whitelist = False
    # Identificar se é regra de whitelist AdGuard (@@)
    if cleaned.startswith("@@"):
        is_whitelist = True
        cleaned = cleaned[2:].strip()

    # Formato Hosts (ex: 0.0.0.0 dominio.com ou 127.0.0.1 dominio.com)
    parts = cleaned.split()
    if len(parts) >= 2:
        try:
            ipaddress.ip_address(parts[0])
            # Primeiro token é IP válido, pegar o segundo token como domínio
            cleaned = parts[1].strip()
        except ValueError:
            pass

    # Formato ABP (remover || no início e ^ ou modificadores $ no final)
    if cleaned.startswith("||"):
        cleaned = cleaned[2:]

    # Remover modificadores AdGuard/uBlock como $important, $third-party, etc.
    if "$" in cleaned:
        cleaned = cleaned.split("$")[0].strip()

    if cleaned.endswith("^"):
        cleaned = cleaned[:-1]

    # Remover protocolos http:// ou https://
    cleaned = re.sub(r"^https?://", "", cleaned, flags=re.IGNORECASE)

    # Remover caminhos (/path...) e portas (:8080)
    if "/" in cleaned:
        cleaned = cleaned.split("/")[0].strip()
    if ":" in cleaned:
        cleaned = cleaned.split(":")[0].strip()

    # Remover pontos no início ou final
    cleaned = cleaned.strip(".")

    if not cleaned:
        return None

    # Converter para minúsculas
    cleaned = cleaned.lower()

    # Verificar se é localhost ou IP direto
    if cleaned in ("localhost", "local", "broadcasthost") or cleaned.startswith("0.0.0.0"):
        return None
    try:
        ipaddress.ip_address(cleaned)
        # Se for apenas um IP, não é domínio FQDN para listas DNS padrão
        return None
    except ValueError:
        pass

    # Suporte a IDN (Internationalized Domain Names) -> Punycode
    try:
        # Se contiver wildcard, converter apenas as partes não-wildcard
        if "*" in cleaned:
            labels = cleaned.split(".")
            encoded_labels = []
            for lbl in labels:
                if lbl == "*":
                    encoded_labels.append("*")
                else:
                    encoded_labels.append(lbl.encode("idna").decode("ascii"))
            cleaned = ".".join(encoded_labels)
        else:
            cleaned = cleaned.encode("idna").decode("ascii")
    except Exception:
        # Falha na conversão de IDN, descartar domínio inválido
        return None

    # Validação estrutural de tamanho (RFC 1035: total <= 253, label <= 63)
    if len(cleaned) > 253 or ".." in cleaned:
        return None

    is_wildcard = "*" in cleaned
    labels = cleaned.split(".")

    # Um domínio válido precisa de no mínimo 2 labels (ex: site.com ou site.*)
    if len(labels) < 2:
        return None

    for label in labels:
        if not label or len(label) > 63:
            return None
        # Validar caracteres por label
        regex_check = VALID_WILDCARD_LABEL_REGEX if is_wildcard else VALID_LABEL_REGEX
        if not regex_check.match(label):
            return None
        # Labels normais não devem começar nem terminar com hífen
        if label != "*" and (label.startswith("-") or label.endswith("-")):
            return None

    return RuleEntry(
        raw=raw_line.strip(),
        cleaned=cleaned,
        is_wildcard=is_wildcard,
        is_whitelist=is_whitelist,
    )


from typing import List, Optional, Set, Tuple, Union


def parse_file(file_path: Union[Path, str]) -> List[RuleEntry]:
    """Lê um arquivo de regras e retorna uma lista de RuleEntry válidas."""
    path = Path(file_path)
    entries: List[RuleEntry] = []
    if not path.exists():
        return entries

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            entry = normalize_domain(line)
            if entry:
                entries.append(entry)
    return entries


def parse_whitelist(file_path: Union[Path, str]) -> Set[str]:
    """Lê arquivo de whitelist e retorna conjunto de domínios permitidos."""
    entries = parse_file(file_path)
    return {e.cleaned for e in entries if not e.is_wildcard}
