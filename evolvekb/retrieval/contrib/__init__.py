"""Pluggable retrieval adapters contributed on top of the built-in modes.

Importing this sub-package triggers the ``@register_retriever`` decorators on
each contrib class, so the retriever is available to :func:`get_retriever`
by its ``name`` without any extra wiring. ``evolvekb.retrieval.__init__``
imports this module for the same reason.

To plug your own adapter in a downstream project:

1. Subclass :class:`evolvekb.retrieval.base.Retriever` (or implement the
   ``name`` + ``retrieve`` protocol directly).
2. Apply ``@register_retriever("your_mode")``.
3. Ensure the module is imported once at startup (entry point, settings,
   or an explicit ``import`` in your harness).
"""
from __future__ import annotations

from evolvekb.retrieval.contrib.tfidf import TFIDFRetriever

__all__ = ["TFIDFRetriever"]
