from typing import TypedDict

CONFIG_FILENAME = ".enchante.yml"

ConfigDict = TypedDict("ConfigDict", {"root_dir": str, "alembic_dir": str})
