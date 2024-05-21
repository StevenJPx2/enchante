import subprocess
from pathlib import Path
from typing import Annotated, Optional

import humps
import typer
import yaml
from jinja2 import Environment

from enchante.utils.types import CONFIG_FILENAME, ConfigDict

app = typer.Typer()


current_path = Path(__file__).parent.resolve()


@app.command()
def init(
    root_dir: Path,
    alembic_dir: Annotated[
        str, typer.Option(help="Set the name of the alembic directory")
    ] = "alembic",
):
    (root_dir / "tables").mkdir(parents=True, exist_ok=True)
    open(Path.cwd() / CONFIG_FILENAME, "w").write(
        yaml.safe_dump({"root_dir": str(root_dir), "alembic_dir": alembic_dir})
    )

    if not root_dir.is_dir():
        raise FileNotFoundError(f"Given root path ({root_dir}) is not a directory")

    subprocess.run(["alembic", "init", root_dir / alembic_dir])


@app.command()
def create(
    name: str,
    table_name: Optional[str] = None,
    root_dir: Optional[Path] = None,
):
    env = Environment()

    table_name = table_name or f"{name}s"
    config: ConfigDict = yaml.safe_load(open(Path.cwd() / CONFIG_FILENAME).read())

    for template_path in (current_path / "./templates/table").glob("*.py.jinja"):
        rendered_template = env.from_string(open(template_path).read()).render(
            object=humps.pascalize(name),
            table_name=humps.decamelize(table_name),
        )
        path = (
            Path(config["root_dir"])
            / "tables"
            / humps.decamelize(table_name)
            / str(template_path.name).replace(".jinja", "")
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        open(path, "w").write(rendered_template)


@app.command()
def sync():
    class User:
        pass

    table_data = {
        key: str(value.__args__[0])
        if not getattr(value.__args__[0], "__name__", None)
        else value.__args__[0].__name__
        for key, value in User.__annotations__.items()
    }


if __name__ == "__main__":
    app()
