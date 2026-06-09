"""
validate_prompts — CI gate for prompt template validity (ADR-146).

Checks:
  - Schema syntax (Pydantic validation of all variables_schema JSONFields)
  - Required variables (defaults cover all required=true)
  - Jinja2 syntax (system + user templates parseable by SandboxedEnvironment)
  - Duplicate active (>1 is_active=True per action_code)
  - Hub consistency (hub field set and valid HubChoices value)

Exit code: 0 if no ERRORs, 1 if at least one ERROR.
WARNINGs are printed but do not block CI.

Usage:
    python manage.py validate_prompts
    python manage.py validate_prompts --hub writing-hub
"""

from django.core.management.base import BaseCommand
from jinja2 import TemplateSyntaxError
from jinja2.sandbox import SandboxedEnvironment

from promptfw.contrib.django.models import HubChoices, PromptTemplate

_JINJA_ENV = SandboxedEnvironment()


class Command(BaseCommand):
    help = "Validate all prompt templates in the database (CI gate)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--hub",
            type=str,
            default="",
            help="Filter by hub name.",
        )

    def handle(self, *args, **options):
        hub = options["hub"]

        qs = PromptTemplate.objects.filter(deleted_at__isnull=True)
        if hub:
            qs = qs.filter(hub=hub)

        templates = list(qs)
        if not templates:
            self.stdout.write(self.style.WARNING("No templates found."))
            return

        errors = 0
        warnings = 0

        for tpl in templates:
            e, w = self._validate_template(tpl)
            errors += e
            warnings += w

        # Check duplicate active
        e = self._check_duplicate_active(qs)
        errors += e

        self.stdout.write("")
        self.stdout.write(f"Validated {len(templates)} template(s).")
        if errors:
            self.stderr.write(self.style.ERROR(f"  {errors} ERROR(s)"))
        if warnings:
            self.stdout.write(self.style.WARNING(f"  {warnings} WARNING(s)"))
        if not errors and not warnings:
            self.stdout.write(self.style.SUCCESS("  All checks passed."))

        if errors:
            raise SystemExit(1)

    def _validate_template(self, tpl: PromptTemplate) -> tuple[int, int]:
        """Validate a single template. Returns (errors, warnings)."""
        errors = 0
        warnings = 0
        prefix = f"[{tpl.action_code} v{tpl.version}]"

        # 1. Schema syntax (Pydantic validation)
        try:
            from promptfw.contrib.django.models import HAS_PYDANTIC

            if HAS_PYDANTIC and tpl.variables_schema:
                from promptfw.contrib.django.models import PromptVariablesSchema

                PromptVariablesSchema(variables=tpl.variables_schema)
        except Exception as e:
            self._error(f"{prefix} Schema syntax: {e}")
            errors += 1

        # 2. Required variables covered by defaults
        if tpl.variables_schema and tpl.is_active:
            for var_name, spec in tpl.variables_schema.items():
                if spec.get("required") and var_name not in (tpl.defaults or {}):
                    self._warning(f"{prefix} Required variable '{var_name}' has no default")
                    warnings += 1

        # 3. Jinja2 syntax
        for field_name in ("system_template", "user_template"):
            template_str = getattr(tpl, field_name, "")
            if template_str:
                try:
                    _JINJA_ENV.parse(template_str)
                except TemplateSyntaxError as e:
                    self._error(f"{prefix} Jinja2 {field_name}: {e}")
                    errors += 1

        # 4. Hub consistency
        if tpl.is_active:
            if not tpl.hub:
                self._warning(f"{prefix} No hub set")
                warnings += 1
            elif tpl.hub not in {c.value for c in HubChoices}:
                self._warning(f"{prefix} Invalid hub value: {tpl.hub}")
                warnings += 1

        return errors, warnings

    def _check_duplicate_active(self, qs) -> int:
        """Check for >1 is_active=True per action_code."""
        from django.db.models import Count

        errors = 0
        dupes = (
            qs.filter(is_active=True)
            .values("action_code")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
        )
        for d in dupes:
            self._error(f"[{d['action_code']}] Duplicate active: {d['cnt']} active versions")
            errors += 1
        return errors

    def _error(self, msg: str):
        self.stderr.write(self.style.ERROR(f"  ERROR: {msg}"))

    def _warning(self, msg: str):
        self.stdout.write(self.style.WARNING(f"  WARNING: {msg}"))
