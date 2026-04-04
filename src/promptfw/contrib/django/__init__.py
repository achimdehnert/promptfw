"""
promptfw.contrib.django — DB-backed prompt management for Django.

Install: pip install iil-promptfw[django]
Config:  INSTALLED_APPS += ["promptfw.contrib.django"]

Usage::

    from promptfw.contrib.django import render_prompt, PromptNotFoundError

    messages = render_prompt("writing-hub.authoring.chapter-write", genre="thriller")
"""

__all__ = [
    "PromptTemplate",
    "render_prompt",
    "PromptNotFoundError",
    "PromptValidationError",
]


def __getattr__(name):
    """Lazy imports to avoid AppRegistryNotReady during django.setup()."""
    if name == "PromptTemplate":
        from promptfw.contrib.django.models import PromptTemplate

        return PromptTemplate
    if name in ("render_prompt", "PromptNotFoundError", "PromptValidationError"):
        from promptfw.contrib.django import resolution

        return getattr(resolution, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
