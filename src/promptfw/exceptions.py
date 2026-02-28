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
