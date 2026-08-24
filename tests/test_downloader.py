"""
Testes unitários para o módulo de download e cache de feeds remotos.
"""

import io
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error

from src.downloader import CacheEntry, FeedDownloader, fetch_all_sources


def test_url_hash(tmp_path: Path):
    downloader = FeedDownloader(cache_dir=tmp_path)
    h1 = downloader._url_hash("https://example.com/list.txt")
    h2 = downloader._url_hash("https://example.com/list.txt")
    h3 = downloader._url_hash("https://example.com/other.txt")
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 16


def test_download_feed_invalid_url(tmp_path: Path):
    downloader = FeedDownloader(cache_dir=tmp_path)
    assert downloader.download_feed("") is None
    assert downloader.download_feed("ftp://invalid-proto.com") is None
    assert downloader.download_feed("not-a-url") is None


def test_download_feed_200_ok(tmp_path: Path):
    downloader = FeedDownloader(cache_dir=tmp_path)
    url = "https://example.com/blocklist.txt"
    sample_content = b"ad1.example.com\nad2.example.com\n"

    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.headers = {"ETag": '"abc123etag"', "Last-Modified": "Wed, 21 Oct 2025 07:28:00 GMT"}
    mock_resp.read.return_value = sample_content
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = downloader.download_feed(url)

    assert result is not None
    assert result.exists()
    assert result.read_bytes() == sample_content

    # Verificar se o índice de cache foi atualizado
    cached_entry = downloader.index.get(downloader._url_hash(url))
    assert cached_entry is not None
    assert cached_entry.etag == '"abc123etag"'
    assert cached_entry.status_code == 200


def test_download_feed_304_not_modified(tmp_path: Path):
    downloader = FeedDownloader(cache_dir=tmp_path)
    url = "https://example.com/blocklist.txt"
    url_key = downloader._url_hash(url)
    local_file = tmp_path / f"feed_{url_key}.txt"
    local_file.write_bytes(b"cached.domain.com\n")

    # Inserir entrada prévia no índice
    downloader.index[url_key] = CacheEntry(
        url=url,
        filename=local_file.name,
        etag='"etag123"',
        last_modified="Wed, 21 Oct 2025 07:28:00 GMT",
        last_checked=100.0,
        status_code=200,
    )
    downloader._save_index()

    # Simular resposta 304 Not Modified
    http_304 = urllib.error.HTTPError(url, 304, "Not Modified", {}, None)

    with patch("urllib.request.urlopen", side_effect=http_304):
        result = downloader.download_feed(url)

    assert result == local_file
    assert result.read_bytes() == b"cached.domain.com\n"


def test_download_feed_offline_mode(tmp_path: Path):
    downloader = FeedDownloader(cache_dir=tmp_path)
    url_cached = "https://example.com/cached.txt"
    url_uncached = "https://example.com/uncached.txt"

    cached_file = tmp_path / f"feed_{downloader._url_hash(url_cached)}.txt"
    cached_file.write_bytes(b"cached.com\n")

    # Cached deve retornar o caminho sem fazer chamada de rede
    with patch("urllib.request.urlopen") as mock_urlopen:
        res_cached = downloader.download_feed(url_cached, offline=True)
        res_uncached = downloader.download_feed(url_uncached, offline=True)
        mock_urlopen.assert_not_called()

    assert res_cached == cached_file
    assert res_uncached is None


def test_download_feed_fallback_on_network_error(tmp_path: Path):
    downloader = FeedDownloader(cache_dir=tmp_path)
    url = "https://example.com/failing.txt"
    cached_file = tmp_path / f"feed_{downloader._url_hash(url)}.txt"
    cached_file.write_bytes(b"old.cached.com\n")

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("DNS lookup failed")):
        res = downloader.download_feed(url)

    assert res == cached_file


def test_fetch_all_sources(tmp_path: Path):
    urls = ["https://example.com/list1.txt", "https://example.com/list2.txt"]

    def mock_urlopen_handler(req, timeout=15):
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.headers = {}
        mock_resp.read.return_value = b"feed.domain.com\n"
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=mock_urlopen_handler):
        paths = fetch_all_sources(urls, cache_dir=tmp_path)

    assert len(paths) == 2
    for p in paths:
        assert p.exists()
