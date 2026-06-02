"""
seed_prompts — Import prompt templates from files or YAML into DB (ADR-146).

Usage:
    python manage.py seed_prompts --from-dir templates/prompts/ --hub writing-hub
    python manage.py seed_prompts --from-yaml prompts/export.yaml --hub travel-beat
"""

import yaml
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from promptfw.contrib.django.models import PromptTemplate


class Command(BaseCommand):
    help = "Import prompt templates from .jinja2 files or YAML into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--from-dir",
            type=str,
            help="Directory containing .jinja2 frontmatter files to import.",
        )
        parser.add_argument(
            "--from-yaml",
            type=str,
            help="YAML file containing prompt template definitions.",
        )
        parser.add_argument(
            "--hub",
            type=str,
            default="",
            help="Hub name to assign (e.g. writing-hub, travel-beat).",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing templates (default: skip).",
        )

    def handle(self, *args, **options):
        from_dir = options["from_dir"]
        from_yaml = options["from_yaml"]
        hub = options["hub"]
        overwrite = options["overwrite"]

        if not from_dir and not from_yaml:
            raise CommandError("Specify --from-dir or --from-yaml.")

        if from_dir and from_yaml:
            raise CommandError("Specify only one of --from-dir or --from-yaml.")

        if from_dir:
            count = self._import_from_dir(Path(from_dir), hub, overwrite)
        else:
            count = self._import_from_yaml(Path(from_yaml), hub, overwrite)

        self.stdout.write(self.style.SUCCESS(f"Imported {count} prompt template(s)."))

    def _import_from_dir(self, directory: Path, hub: str, overwrite: bool) -> int:
        """Import .jinja2 frontmatter files from directory."""
        if not directory.is_dir():
            raise CommandError(f"Directory not found: {directory}")

        count = 0
        for path in sorted(directory.rglob("*.jinja2")):
            action_code = self._path_to_action_code(path, directory, hub)
            content = path.read_text(encoding="utf-8")

            # Parse frontmatter if present
            system_template = ""
            user_template = content
            if content.lstrip().startswith("---"):
                parts = self._parse_frontmatter(content)
                system_template = parts.get("system", "")
                user_template = parts.get("user", content)

            if self._upsert(action_code, system_template, user_template, hub, overwrite):
                count += 1
                self.stdout.write(f"  + {action_code}")
            else:
                self.stdout.write(f"  = {action_code} (exists, skipped)")

        return count

    def _import_from_yaml(self, yaml_path: Path, hub: str, overwrite: bool) -> int:
        """Import prompt templates from YAML file."""
        if not yaml_path.is_file():
            raise CommandError(f"YAML file not found: {yaml_path}")

        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "prompts" not in data:
            raise CommandError("YAML must have a top-level 'prompts' key with a list.")

        count = 0
        for entry in data["prompts"]:
            action_code = entry["action_code"]
            system_template = entry.get("system_template", "")
            user_template = entry.get("user_template", "")
            entry_hub = entry.get("hub", hub)

            if not user_template:
                self.stderr.write(
                    self.style.WARNING(f"  ! {action_code}: no user_template, skipped")
                )
                continue

            if self._upsert(
                action_code,
                system_template,
                user_template,
                entry_hub,
                overwrite,
                defaults=entry.get("defaults", {}),
                variables_schema=entry.get("variables_schema", {}),
                name=entry.get("name", ""),
                description=entry.get("description", ""),
                domain=entry.get("domain", ""),
                suggested_temperature=entry.get("suggested_temperature"),
                suggested_max_tokens=entry.get("suggested_max_tokens"),
                response_format=entry.get("response_format", ""),
                tags=entry.get("tags", []),
            ):
                count += 1
                self.stdout.write(f"  + {action_code}")
            else:
                self.stdout.write(f"  = {action_code} (exists, skipped)")

        return count

    def _upsert(
        self,
        action_code: str,
        system_template: str,
        user_template: str,
        hub: str,
        overwrite: bool,
        **extra,
    ) -> bool:
        """Create or update a PromptTemplate. Returns True if created/updated."""
        existing = PromptTemplate.objects.filter(
            action_code=action_code, is_active=True, deleted_at__isnull=True
        ).first()

        if existing and not overwrite:
            return False

        if existing and overwrite:
            existing.system_template = system_template
            existing.user_template = user_template
            if hub:
                existing.hub = hub
            for k, v in extra.items():
                if v is not None and v != "" and v != [] and v != {}:
                    setattr(existing, k, v)
            existing.save()
            return True

        PromptTemplate.objects.create(
            action_code=action_code,
            system_template=system_template,
            user_template=user_template,
            hub=hub,
            **{k: v for k, v in extra.items() if v is not None},
        )
        return True

    def _path_to_action_code(self, path: Path, base_dir: Path, hub: str) -> str:
        """Convert file path to action_code: hub.relative.path (without .jinja2)."""
        relative = path.relative_to(base_dir).with_suffix("")
        parts = list(relative.parts)
        code = ".".join(parts)
        if hub and not code.startswith(hub):
            code = f"{hub}.{code}"
        return code

    def _parse_frontmatter(self, content: str) -> dict:
        """Parse YAML frontmatter from .jinja2 file content."""
        # Strip leading Jinja2 comments before frontmatter
        lines = content.split("\n")
        start = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("{#") or stripped == "":
                continue
            if stripped == "---":
                start = i
                break
            break

        # Find frontmatter boundaries
        if lines[start].strip() != "---":
            return {"user": content}

        end = None
        for i in range(start + 1, len(lines)):
            if lines[i].strip() == "---":
                end = i
                break

        if end is None:
            return {"user": content}

        frontmatter_text = "\n".join(lines[start + 1 : end])
        body = "\n".join(lines[end + 1 :]).strip()

        try:
            meta = yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError:
            return {"user": content}

        return {
            "system": meta.get("system", meta.get("system_prompt", "")),
            "user": body or content,
        }
