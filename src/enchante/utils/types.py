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
    tables: dict[str, str] = {}
    config_file: Path = CONFIG_FILEPATH

    @classmethod
    def new(cls, root_dir: Path, alembic_dir: Path):
        config = cls(root_dir=root_dir, alembic_dir=alembic_dir)
        config.config_file.touch()

        config.tables_path
        config.schemas_path
        config.models_path

        subprocess.run(["alembic", "init", root_dir / alembic_dir])

        config.save_config()

        return config

    @classmethod
    def load_config(cls) -> Self:
        loaded_values: dict[str, Any] = yaml.safe_load(CONFIG_FILEPATH.read_text())

        resolved_config = cls.model_validate(loaded_values)

        resolved_config.save_config()

        return resolved_config

    def save_config(self):
        self.config_file.write_text(yaml.safe_dump(json.loads(self.model_dump_json())))

    def add_table(self, name: str, *, table_name: str):
        self.tables[table_name] = name
        self.load_config()

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
