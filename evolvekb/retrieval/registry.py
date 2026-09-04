from __future__ import annotations

from typing import Any, Callable

from evolvekb.retrieval.base import Retriever


# Pluggable retriever registry. Built-in retrievers (keyword, bm25, semantic, hybrid)
# self-register via the @register_retriever decorator on their class. External packages
# or contrib modules can register additional retrievers at import time, or at runtime via
# register_retriever_class(). get_retriever() resolves a name to an instance, optionally
# forwarding mode-level config from settings as keyword arguments to the class constructor.
_REGISTRY: dict[str, type[Retriever]] = {}


def register_retriever(name: str) -> Callable[[type[Retriever]], type[Retriever]]:
    """Class decorator that registers a Retriever subclass under ``name``.

    Re-importing the same class is a no-op so test reloads and entry-point double loads
    do not raise. Registering a different class under an existing name is an error.
    """

    def decorator(cls: type[Retriever]) -> type[Retriever]:
        existing = _REGISTRY.get(name)
        if existing is not None and existing is not cls:
            raise ValueError(f"retriever '{name}' already registered with {existing}")
        _REGISTRY[name] = cls
        return cls

    return decorator


def register_retriever_class(name: str, cls: type[Retriever]) -> None:
    """Register a retriever class at runtime (e.g. from a plugin entry point).

    Same idempotency / collision rules as :func:`register_retriever`.
    """

    existing = _REGISTRY.get(name)
    if existing is not None and existing is not cls:
        raise ValueError(f"retriever '{name}' already registered with {existing}")
    _REGISTRY[name] = cls


def unregister_retriever(name: str) -> None:
    """Remove a retriever from the registry. Mainly for tests."""

    _REGISTRY.pop(name, None)


def get_retriever(name: str | None = None, *, config: dict[str, Any] | None = None) -> Retriever:
    """Resolve a retriever name to an instance.

    ``config`` is forwarded to the retriever constructor as keyword arguments, so an
    external adapter can read its own mode-level settings without hard-coding keys.
    """

    mode = (name or "keyword").strip().lower()
    cls = _REGISTRY.get(mode)
    if cls is None:
        raise ValueError(
            f"Unknown retriever '{name}'. Registered: {sorted(_REGISTRY)}. "
            "Did you forget to import the contrib module that registers it?"
        )
    if config:
        return cls(**config)
    return cls()


def available_retrievers() -> list[str]:
    """Return all registered retriever names in deterministic order."""

    return sorted(_REGISTRY)
