# ABOUTME: Configuration loader for sources, QA thresholds, cluster params, and voices.
# ABOUTME: Reads YAML and Markdown configs from the config/ directory.
"""Configuration loading for the Newsroom CLI."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from newsroom.models import (
    ClusterConfig,
    FeedSource,
    QAConfig,
    VoiceConstitution,
)


class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""


def _read_yaml(file_path: Path) -> dict:
    """Read and parse a YAML file, raising ConfigError on failure."""
    if not file_path.exists():
        msg = f"Config file not found: {file_path}"
        raise ConfigError(msg)
    text = file_path.read_text()
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        msg = f"Expected YAML mapping in {file_path}, got {type(data).__name__}"
        raise ConfigError(msg)
    return data


def load_sources(beat: str, config_dir: Path) -> list[FeedSource]:
    """Load RSS feed sources for a given beat from config/sources.yaml."""
    file_path = config_dir / "sources.yaml"
    data = _read_yaml(file_path)
    if beat not in data:
        available = ", ".join(sorted(data.keys()))
        msg = f"Beat '{beat}' not found in {file_path} (available: {available})"
        raise ConfigError(msg)
    beat_data = data[beat]
    if not isinstance(beat_data, dict) or "rss" not in beat_data:
        msg = f"Missing 'rss' list under beat '{beat}' in {file_path}"
        raise ConfigError(msg)
    rss_entries = beat_data["rss"]
    try:
        return [FeedSource(**entry) for entry in rss_entries]
    except (ValidationError, TypeError) as exc:
        msg = f"Invalid feed source entry in {file_path}: {exc}"
        raise ConfigError(msg) from exc


def load_qa_config(config_dir: Path) -> QAConfig:
    """Load QA check thresholds and phrase lists from config/qa.yaml."""
    file_path = config_dir / "qa.yaml"
    data = _read_yaml(file_path)
    try:
        return QAConfig(**data)
    except ValidationError as exc:
        msg = f"Invalid QA config in {file_path}: {exc}"
        raise ConfigError(msg) from exc


def load_cluster_config(config_dir: Path) -> ClusterConfig:
    """Load TF-IDF and clustering parameters from config/cluster.yaml."""
    file_path = config_dir / "cluster.yaml"
    data = _read_yaml(file_path)
    try:
        return ClusterConfig(**data)
    except ValidationError as exc:
        msg = f"Invalid cluster config in {file_path}: {exc}"
        raise ConfigError(msg) from exc


_VOICE_SECTIONS = {
    "Beliefs": "beliefs",
    "Tone": "tone",
    "Forbidden Moves": "forbidden_moves",
    "Taboo Phrases": "taboo_phrases",
    "Required Habits": "required_habits",
}


def _parse_voice_markdown(text: str, file_path: Path) -> dict[str, list[str]]:
    """Parse a voice constitution markdown into section→bullet-list mapping.

    Sections are H2 headers matched exactly. Only '- ' (hyphen-space) bullets
    are recognized. Non-bullet content, blank lines, numbered lists, and
    asterisk bullets are ignored. A single layer of matched surrounding quote
    characters (`"..."` or `'...'`) is stripped from each bullet's text.
    """
    sections: dict[str, list[str]] = {}
    current_section: str | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            header = stripped[3:].strip()
            if header in _VOICE_SECTIONS:
                current_section = header
                sections[current_section] = []
            else:
                current_section = None
            continue
        if current_section is not None and stripped.startswith("- "):
            bullet_text = stripped[2:].strip()
            is_quoted = (
                len(bullet_text) >= 2
                and bullet_text[0] == bullet_text[-1]
                and bullet_text[0] in "\"'"
            )
            if is_quoted:
                bullet_text = bullet_text[1:-1]
            if bullet_text:
                sections[current_section].append(bullet_text)

    missing = [name for name in _VOICE_SECTIONS if name not in sections]
    if missing:
        msg = (
            f"Voice constitution in {file_path} missing required "
            f"section(s): {', '.join(missing)}"
        )
        raise ConfigError(msg)

    return {field: sections[header] for header, field in _VOICE_SECTIONS.items()}


def load_voice(beat: str, config_dir: Path) -> VoiceConstitution:
    """Load and parse the voice constitution markdown for a given beat."""
    file_path = config_dir / "voices" / f"{beat}.md"
    if not file_path.exists():
        msg = f"Voice file not found: {file_path}"
        raise ConfigError(msg)
    text = file_path.read_text()
    fields = _parse_voice_markdown(text, file_path)
    return VoiceConstitution(**fields)
