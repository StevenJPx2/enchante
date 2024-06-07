import json
import subprocess
from pathlib import Path
from typing import Any, Self

import yaml
from pydantic import BaseModel

CONFIG_FILEPATH = Path.cwd() / ".enchante.yml"


class Config(BaseModel):
    root_dir: Path
    alembic_dir: Path

    def model_post_init(self, _):
        CONFIG_FILEPATH.touch()

        self.tables_path
        self.schemas_path
        self.models_path

        alembic_path = self.root_dir / self.alembic_dir

        if not alembic_path.exists():
            subprocess.run(["alembic", "init", alembic_path])

        self.save_config()

    @classmethod
    def load_config(cls) -> Self:
        if not CONFIG_FILEPATH.exists():
            print("❌ No config detected in this path.")
            raise SystemExit()

        loaded_values: dict[str, Any] = yaml.safe_load(CONFIG_FILEPATH.read_text())

        resolved_config = cls.model_validate(loaded_values)

        resolved_config.save_config()

        return resolved_config

    def save_config(self):
        CONFIG_FILEPATH.write_text(
            yaml.safe_dump(json.loads(self.model_dump_json())),
        )

    @property
    def tables_path(self):
        dir = self.root_dir / "tables"
        dir.mkdir(parents=True, exist_ok=True)
        return dir

    @property
    def schemas_path(self):
        file = self.root_dir / "schemas.py"
        file.touch()
        return file

    @property
    def models_path(self):
        file = self.root_dir / "models.py"
        file.touch()
        return file
