"""promptfw exceptions."""


class PromptfwError(Exception):
    """Base exception for promptfw."""


class TemplateNotFoundError(PromptfwError):
    """Raised when a template ID or pattern has no match in the registry."""

    def __init__(self, pattern: str) -> None:
        super().__init__(f"No template found for pattern '{pattern}'")
        self.pattern = pattern


class TemplateRenderError(PromptfwError):
    """Raised when Jinja2 rendering fails (e.g. missing variable)."""

    def __init__(self, template_id: str, cause: str) -> None:
        super().__init__(f"Failed to render template '{template_id}': {cause}")
        self.template_id = template_id
        self.cause = cause


class LLMResponseError(PromptfwError):
    """Raised when an LLM response cannot be parsed (e.g. missing JSON).

    Distinct from TemplateRenderError which covers Jinja2 rendering failures.
    Callers that catch TemplateRenderError for rendering errors will NOT
    accidentally catch LLM response parsing failures.
    """

    def __init__(self, cause: str, preview: str = "") -> None:
        msg = f"LLM response error: {cause}"
        if preview:
            msg += f" | preview: {preview!r}"
        super().__init__(msg)
        self.cause = cause
        self.preview = preview
