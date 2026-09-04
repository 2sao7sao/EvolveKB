"""Retrieval as evidence supply."""

from evolvekb.retrieval.base import EvidenceItem, EvidencePack, Retriever
from evolvekb.retrieval.registry import available_retrievers, get_retriever

# Importing the built-in modules triggers their @register_retriever decorators
# so get_retriever("bm25") etc. work without explicit class imports at call sites.
from evolvekb.retrieval import bm25, hybrid, keyword, semantic  # noqa: F401
# Contrib adapters are external / optional modes. Importing this module
# registers them under their declared names.
from evolvekb.retrieval import contrib  # noqa: F401

__all__ = [
    "EvidenceItem",
    "EvidencePack",
    "Retriever",
    "available_retrievers",
    "get_retriever",
]
