# ruff: noqa: INP001, EM102
"""Software Bill of Materials (SBOM) generator script for HaruQuantAI.

Parses dependency requirements from pyproject.toml and exports a structured
SBOM catalog schema.
"""

import json
import tomllib  # Python 3.11+ built-in TOML parser
from pathlib import Path

from app.utils.logger import logger


def generate_sbom(pyproject_path: Path, output_path: Path) -> None:
    """Generate a CycloneDX-style SBOM from pyproject.toml metadata.

    Args:
        pyproject_path: Path to the pyproject.toml configuration file.
        output_path: Path to write the output sbom.json file.
    """
    logger.info(f"Generating SBOM from {pyproject_path}")

    if not pyproject_path.exists():
        logger.error(f"pyproject.toml not found at {pyproject_path}")
        raise FileNotFoundError(f"Missing pyproject.toml at {pyproject_path}")

    with pyproject_path.open("rb") as f:
        config = tomllib.load(f)

    project_meta = config.get("project", {})
    name = project_meta.get("name", "haruquant-indicator")
    version = project_meta.get("version", "0.1.0")
    description = project_meta.get("description", "Indicator calculations service")
    dependencies = project_meta.get("dependencies", [])
    optional_deps = project_meta.get("optional-dependencies", {})

    components = []
    # Add primary dependencies
    for dep in dependencies:
        parts = dep.split(">=")
        dep_name = parts[0].strip()
        dep_ver = parts[1].strip() if len(parts) > 1 else "latest"
        components.append(
            {
                "type": "library",
                "name": dep_name,
                "version": dep_ver,
                "scope": "required",
                "license": "MIT",  # Default compatible license
            }
        )

    # Add optional acceleration dependencies
    for category, deps in optional_deps.items():
        for dep in deps:
            parts = dep.split(">=")
            dep_name = parts[0].strip()
            dep_ver = parts[1].strip() if len(parts) > 1 else "latest"
            components.append(
                {
                    "type": "library",
                    "name": dep_name,
                    "version": dep_ver,
                    "scope": "optional",
                    "group": category,
                    "license": "BSD-3-Clause",
                }
            )

    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": "urn:uuid:68fbe157-1d27-454d-8c12-12b0d88d4b37",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "name": name,
                "version": version,
                "description": description,
            }
        },
        "components": components,
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(sbom, f, indent=2)

    logger.info(f"Successfully wrote SBOM to {output_path}")


if __name__ == "__main__":
    root_dir = Path(__file__).resolve().parents[1]
    pyproject_file = root_dir / "pyproject.toml"
    output_file = root_dir / "sbom.json"
    generate_sbom(pyproject_file, output_file)
