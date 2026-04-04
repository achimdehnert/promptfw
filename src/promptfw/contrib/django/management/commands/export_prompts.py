"""
export_prompts — Export prompt templates from DB to YAML (ADR-146).

Usage:
    python manage.py export_prompts --hub writing-hub --output-dir prompts/
    python manage.py export_prompts --output prompts/all-prompts.yaml
"""

import yaml
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from promptfw.contrib.django.models import PromptTemplate


class Command(BaseCommand):
    help = "Export prompt templates from the database to YAML files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--hub",
            type=str,
            default="",
            help="Filter by hub name (e.g. writing-hub). Empty = all hubs.",
        )
        parser.add_argument(
            "--output",
            type=str,
            default="",
            help="Output YAML file path (single file with all prompts).",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default="",
            help="Output directory (one YAML file per action_code).",
        )
        parser.add_argument(
            "--include-inactive",
            action="store_true",
            help="Include inactive templates in export.",
        )

    def handle(self, *args, **options):
        hub = options["hub"]
        output = options["output"]
        output_dir = options["output_dir"]
        include_inactive = options["include_inactive"]

        if not output and not output_dir:
            raise CommandError("Specify --output or --output-dir.")

        qs = PromptTemplate.objects.filter(deleted_at__isnull=True)
        if hub:
            qs = qs.filter(hub=hub)
        if not include_inactive:
            qs = qs.filter(is_active=True)
        qs = qs.order_by("action_code", "-version")

        templates = list(qs)
        if not templates:
            self.stdout.write(self.style.WARNING("No templates found matching filters."))
            return

        if output:
            self._export_single_file(templates, Path(output))
        else:
            self._export_directory(templates, Path(output_dir))

        self.stdout.write(
            self.style.SUCCESS(f"Exported {len(templates)} prompt template(s).")
        )

    def _template_to_dict(self, tpl: PromptTemplate) -> dict:
        """Convert a PromptTemplate to a serializable dict."""
        data = {
            "action_code": tpl.action_code,
            "version": tpl.version,
            "name": tpl.name,
            "user_template": tpl.user_template,
        }
        if tpl.system_template:
            data["system_template"] = tpl.system_template
        if tpl.description:
            data["description"] = tpl.description
        if tpl.hub:
            data["hub"] = tpl.hub
        if tpl.domain:
            data["domain"] = tpl.domain
        if tpl.defaults:
            data["defaults"] = tpl.defaults
        if tpl.variables_schema:
            data["variables_schema"] = tpl.variables_schema
        if tpl.suggested_temperature is not None:
            data["suggested_temperature"] = tpl.suggested_temperature
        if tpl.suggested_max_tokens is not None:
            data["suggested_max_tokens"] = tpl.suggested_max_tokens
        if tpl.response_format:
            data["response_format"] = tpl.response_format
        if tpl.output_schema:
            data["output_schema"] = tpl.output_schema
        if tpl.tags:
            data["tags"] = tpl.tags
        if not tpl.is_active:
            data["is_active"] = False
        return data

    def _export_single_file(self, templates: list, output_path: Path):
        """Export all templates to a single YAML file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "prompts": [self._template_to_dict(tpl) for tpl in templates],
        }
        output_path.write_text(
            yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        self.stdout.write(f"  Written to {output_path}")

    def _export_directory(self, templates: list, output_dir: Path):
        """Export each template to a separate YAML file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        for tpl in templates:
            filename = f"{tpl.action_code.replace('.', '_')}_v{tpl.version}.yaml"
            path = output_dir / filename
            data = self._template_to_dict(tpl)
            path.write_text(
                yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            self.stdout.write(f"  Written: {path}")
