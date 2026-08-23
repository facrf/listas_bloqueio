"""
Módulo de deduplicação e otimização de domínios via Árvore de Prefixos/Sufixos (Trie).
"""

from typing import Dict, List, Set, Tuple


class DomainTrieNode:
    def __init__(self) -> None:
        self.children: Dict[str, "DomainTrieNode"] = {}
        self.is_terminal: bool = False


class DomainTrie:
    """
    Estrutura Trie reversa para verificação eficiente de domínios e subdomínios.
    Exemplo: 'dqa.samsung.com' é armazenado como ['com', 'samsung', 'dqa'].
    """

    def __init__(self) -> None:
        self.root = DomainTrieNode()

    def insert(self, domain: str) -> bool:
        """
        Insere um domínio no Trie.
        Retorna True se for um novo domínio não coberto por um pai já existente,
        ou False se já estiver coberto por uma regra pai (ex: 'samsung.com' já cobre 'dqa.samsung.com').
        """
        labels = domain.split(".")[::-1]  # Inverter: ['com', 'samsung', 'dqa']
        curr = self.root

        for label in labels:
            if curr.is_terminal:
                # Já existe uma regra pai que cobre este subdomínio
                return False
            if label not in curr.children:
                curr.children[label] = DomainTrieNode()
            curr = curr.children[label]

        curr.is_terminal = True
        # Se este nó virou terminal, podemos podar quaisquer filhos que foram inseridos antes
        curr.children.clear()
        return True

    def is_covered(self, domain: str) -> bool:
        """Verifica se o domínio (ou um de seus pais) existe no Trie."""
        labels = domain.split(".")[::-1]
        curr = self.root
        for label in labels:
            if curr.is_terminal:
                return True
            if label not in curr.children:
                return False
            curr = curr.children[label]
        return curr.is_terminal


def deduplicate_and_optimize(
    domains: List[str],
    wildcards: List[str],
    whitelist: Set[str],
) -> Tuple[List[str], List[str], int]:
    """
    Remove duplicatas exatas, aplica a whitelist e elimina subdomínios redundantes.
    Retorna (dominios_otimizados, wildcards_otimizados, total_redundancias_removidas).
    """
    # 1. Deduplicação exata inicial
    unique_domains = sorted(set(domains), key=lambda d: (len(d.split(".")), d))
    unique_wildcards = sorted(set(wildcards), key=lambda w: (len(w.split(".")), w))

    # 2. Criar Trie da Whitelist para descarte rápido
    whitelist_trie = DomainTrie()
    for w in sorted(whitelist, key=lambda d: (len(d.split(".")), d)):
        whitelist_trie.insert(w)

    # 3. Filtrar entradas pela Whitelist
    filtered_domains = [d for d in unique_domains if not whitelist_trie.is_covered(d)]

    # 4. Trie de Bloqueio para Otimização de Subdomínios
    block_trie = DomainTrie()
    optimized_domains: List[str] = []
    redundancies_removed = 0

    # Processar domínios ordenados por menor profundidade primeiro (ex: 'samsung.com' antes de 'sub.samsung.com')
    sorted_by_depth = sorted(filtered_domains, key=lambda d: (len(d.split(".")), d))

    for domain in sorted_by_depth:
        if block_trie.insert(domain):
            optimized_domains.append(domain)
        else:
            redundancies_removed += 1

    # 5. Otimização de Wildcards
    # Se 'darkmahou.*' existir, 'sub.darkmahou.*' é redundante
    wildcard_trie = DomainTrie()
    optimized_wildcards: List[str] = []
    sorted_wildcards = sorted(unique_wildcards, key=lambda w: (len(w.split(".")), w))

    for wc in sorted_wildcards:
        # Remover o '.*' temporariamente para inserção na árvore
        base_wc = wc.rstrip(".*")
        if wildcard_trie.insert(base_wc):
            optimized_wildcards.append(wc)
        else:
            redundancies_removed += 1

    # Ordenação final determinística alfanumérica
    optimized_domains.sort()
    optimized_wildcards.sort()

    return optimized_domains, optimized_wildcards, redundancies_removed
