# -*- coding: utf-8 -*-
"""
Template-based exporter for IPTV channels.
Supports variable substitution and validation.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExportError:
    """Represents a field-level export error."""

    field: str
    message: str


@dataclass
class ComposeContent:
    """Container for compose file content and errors."""

    content: str
    errors: list[ExportError]


class TemplateRenderer:
    """Renders templates with channel data."""

    def render_docker_compose(
        self, channels: dict[str, dict], output_path: str
    ) -> list[ExportError]:
        """Render docker-compose.yml template with channel data.

        Generates a docker-compose.yml file with each channel as a service.
        Channel names are sanitized to valid service names.

        Args:
            channels: Dict mapping channel names to channel info dicts.
                Required keys in each info dict: 'media_url'
                Optional keys: 'resolution', 'fps'
            output_path: Path where the docker-compose.yml will be written.

        Returns:
            List of ExportError if validation fails, empty list on success.
        """
        errors = []

        if not channels:
            errors.append(
                ExportError(field="channels", message="No channels to export")
            )
            return errors

        compose_content = self._build_compose_content(channels)
        if compose_content.errors:
            return compose_content.errors

        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(compose_content.content)
        except OSError as e:
            errors.append(ExportError(field="output_path", message=str(e)))

        return errors

    def _build_compose_content(self, channels: dict[str, dict]) -> ComposeContent:
        """Build docker-compose.yml content from channels."""
        errors: list[ExportError] = []

        for name, info in channels.items():
            if not name or not isinstance(name, str):
                errors.append(
                    ExportError(
                        field="channel_name", message=f"Invalid channel name: {name}"
                    )
                )
            if not info.get("media_url"):
                errors.append(
                    ExportError(
                        field="media_url",
                        message=f"Missing media_url for channel: {name}",
                    )
                )

        if errors:
            return ComposeContent(content="", errors=errors)

        services = []
        for name, info in channels.items():
            service_name = _sanitize_service_name(name)
            safe_url = _escape_env_value(info.get("media_url", ""))
            safe_name = _escape_env_value(name)
            services.append(
                f"  {service_name}:\n"
                f"    image: mythtv/mythtv:combined\n"
                f"    container_name: {service_name}\n"
                f"    environment:\n"
                f"      - CHANNEL_URL={safe_url}\n"
                f"      - CHANNEL_NAME={safe_name}\n"
                f"    restart: unless-stopped\n"
            )

        content = "version: '3.8'\n\nservices:\n" + "".join(services)
        return ComposeContent(content=content, errors=[])

    def render_custom(
        self, template: str, channels: dict[str, dict], output_path: str
    ) -> list[ExportError]:
        """Render custom template with channel data.

        For each channel, the template is rendered with that channel's data.
        All placeholders ({{channel_name}}, {{media_url}}, {{resolution}}, {{fps}})
        are replaced for each channel.
        """
        errors: list[ExportError] = []

        if not template:
            errors.append(
                ExportError(field="template", message="Template content is empty")
            )
            return errors

        try:
            lines = []
            for name, info in channels.items():
                content = template
                content = content.replace("{{channel_name}}", name)
                content = content.replace("{{media_url}}", info.get("media_url", ""))
                content = content.replace(
                    "{{resolution}}", str(info.get("resolution", ""))
                )
                content = content.replace("{{fps}}", str(info.get("fps", "")))
                lines.append(content)

            result = "\n".join(lines)

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result)
        except OSError as e:
            errors.append(ExportError(field="output_path", message=str(e)))

        return errors


def _sanitize_service_name(name: str) -> str:
    """Convert channel name to valid docker-compose service name."""
    import re

    name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.lower()


def _escape_env_value(value: str) -> str:
    """Escape value for docker-compose environment variable."""
    return value.replace("\n", "\\n").replace('"', '\\"')
