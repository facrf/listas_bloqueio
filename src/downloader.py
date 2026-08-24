"""
Módulo de download e cache de feeds remotos de listas de bloqueio.
Implementa verificação de integridade, suporte a ETag / Last-Modified e modo offline.
"""

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Union
import urllib.error
import urllib.request


@dataclass
class CacheEntry:
    url: str
    filename: str
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    last_checked: float = 0.0
    status_code: int = 0


class FeedDownloader:
    """Gerenciador de downloads com suporte a cache inteligente e ETag."""

    DEFAULT_USER_AGENT = "listas_bloqueio/1.3.0 (+https://github.com/facrf/listas_bloqueio)"

    def __init__(self, cache_dir: Union[Path, str] = "data/cache", timeout: int = 15) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.cache_dir / "cache_index.json"
        self.timeout = timeout
        self.index: Dict[str, CacheEntry] = self._load_index()

    def _url_hash(self, url: str) -> str:
        """Gera hash SHA256 único para a URL do feed."""
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

    def _load_index(self) -> Dict[str, CacheEntry]:
        """Carrega índice de metadados do cache."""
        if not self.index_file.exists():
            return {}
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {k: CacheEntry(**v) for k, v in data.items()}
        except Exception as e:
            print(f"[!] Falha ao carregar cache_index.json ({e}). Criando novo índice.")
            return {}

    def _save_index(self) -> None:
        """Salva índice de metadados do cache em disco."""
        try:
            serializable = {k: asdict(v) for k, v in self.index.items()}
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(serializable, f, indent=2)
        except Exception as e:
            print(f"[!] Falha ao salvar cache_index.json: {e}")

    def download_feed(
        self,
        url: str,
        force: bool = False,
        offline: bool = False,
    ) -> Optional[Path]:
        """
        Baixa um feed remoto ou recupera do cache se não tiver sido modificado.
        Retorna o caminho local do arquivo baixado/em cache, ou None em caso de falha.
        """
        url = url.strip()
        if not url or not (url.startswith("http://") or url.startswith("https://")):
            return None

        url_key = self._url_hash(url)
        cached_entry = self.index.get(url_key)
        local_filename = f"feed_{url_key}.txt"
        local_path = self.cache_dir / local_filename

        # Modo Offline: usar cache existente se disponível
        if offline:
            if local_path.exists():
                print(f"  [cache/offline] {url} -> {local_path.name}")
                return local_path
            print(f"  [!] Modo offline ativo e cache inexistente para: {url}")
            return None

        # Preparar requisição HTTP
        headers = {"User-Agent": self.DEFAULT_USER_AGENT}
        if not force and cached_entry and local_path.exists():
            if cached_entry.etag:
                headers["If-None-Match"] = cached_entry.etag
            if cached_entry.last_modified:
                headers["If-Modified-Since"] = cached_entry.last_modified

        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                status = resp.getcode()
                etag = resp.headers.get("ETag")
                last_modified = resp.headers.get("Last-Modified")
                content = resp.read()

                # Gravar conteúdo baixado
                with open(local_path, "wb") as f:
                    f.write(content)

                self.index[url_key] = CacheEntry(
                    url=url,
                    filename=local_filename,
                    etag=etag,
                    last_modified=last_modified,
                    last_checked=time.time(),
                    status_code=status,
                )
                self._save_index()
                print(f"  [download/200] {url} ({len(content)} bytes) -> {local_path.name}")
                return local_path

        except urllib.error.HTTPError as e:
            if e.code == 304:  # Not Modified
                if local_path.exists():
                    if cached_entry:
                        cached_entry.last_checked = time.time()
                        self._save_index()
                    print(f"  [cache/304] {url} (não modificado) -> {local_path.name}")
                    return local_path
            # Outros erros HTTP
            print(f"  [!] Erro HTTP {e.code} ao baixar {url}: {e.reason}")
            if local_path.exists():
                print(f"  [fallback] Usando versão em cache anterior para {url}")
                return local_path
            return None

        except (urllib.error.URLError, TimeoutError, Exception) as e:
            print(f"  [!] Falha de conexão ao baixar {url}: {e}")
            if local_path.exists():
                print(f"  [fallback] Usando versão em cache anterior para {url}")
                return local_path
            return None


def fetch_all_sources(
    remote_urls: List[str],
    cache_dir: Union[Path, str] = "data/cache",
    force: bool = False,
    offline: bool = False,
    timeout: int = 15,
) -> List[Path]:
    """Baixa ou recupera do cache todas as URLs de feeds especificadas."""
    if not remote_urls:
        return []

    downloader = FeedDownloader(cache_dir=cache_dir, timeout=timeout)
    paths: List[Path] = []

    for url in remote_urls:
        path = downloader.download_feed(url, force=force, offline=offline)
        if path:
            paths.append(path)

    return paths
