import ast
from copy import deepcopy
from pathlib import Path
from typing import Annotated, Optional

import humps
import typer
from jinja2 import Environment

from enchante.utils import Config

app = typer.Typer()


current_path = Path(__file__).parent.resolve()


@app.command()
def init(
    root_dir: Path,
    alembic_dir: Annotated[
        Path, typer.Option(help="Set the name of the alembic directory")
    ] = Path("alembic"),
):
    Config(root_dir=root_dir, alembic_dir=alembic_dir)

    print("✅ Success!")


@app.command()
def create(
    name: str,
    table_name: Optional[str] = None,
):
    env = Environment()

    table_name = humps.decamelize(table_name or f"{name}s")
    object_name = humps.pascalize(name)
    print(f"🔄 Creating {table_name}...")

    config = Config.load_config()

    for template_path in (current_path / "./templates/table").glob("*.py.jinja"):
        rendered_template = env.from_string(template_path.read_text()).render(
            object=object_name,
            table_name=table_name,
        )
        path = (
            config.tables_path
            / table_name
            / str(template_path.name).replace(".jinja", "")
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        open(path, "w").write(rendered_template)

    with open(config.models_path, "a") as schemas:
        schemas.write(
            f"from .{config.tables_path.stem}.{table_name}.model import {object_name}"
        )

    with open(config.schemas_path, "a") as schemas:
        schemas.write(f"from .{config.tables_path.stem}.{table_name}.schema import *")

    print("✅ Success!")


def get_id(target: ast.Name | ast.Attribute | ast.Subscript):
    if isinstance(target, ast.Name):
        return target.id
    else:
        return target.value.id  # type: ignore


@app.command()
def sync():
    print("🔄 Syncing tables with schemas...")
    config = Config.load_config()

    for table in config.tables_path.iterdir():
        print(f"📃 Syncing {table.stem}...")
        model_path = table / "model.py"
        schema_path = table / "schema.py"

        model_ast = ast.parse(model_path.read_text())
        schema_ast = ast.parse(schema_path.read_text())

        model = [model for model in model_ast.body if isinstance(model, ast.ClassDef)][
            0
        ]
        schema = [
            schema
            for schema in schema_ast.body
            if isinstance(schema, ast.ClassDef) and schema.name == model.name
        ][0]

        schema_body = deepcopy(schema.body)

        for stmt in model.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(
                stmt.annotation, ast.Subscript
            ):
                annotation = ast.AnnAssign(
                    target=stmt.target,
                    annotation=stmt.annotation.slice,
                    simple=1,
                )
                for i, s_stmt in enumerate(schema_body):
                    if isinstance(s_stmt, ast.AnnAssign) and get_id(
                        s_stmt.target
                    ) == get_id(stmt.target):
                        schema_body[i] = annotation
                        break
                else:
                    schema_body.append(annotation)

        model_body_ids = [
            get_id(stmt.target)
            for stmt in model.body
            if isinstance(stmt, ast.AnnAssign)
        ]

        tmp_schema_body = list(schema_body)

        for stmt in tmp_schema_body:
            if isinstance(stmt, ast.AnnAssign):
                if get_id(stmt.target) not in model_body_ids:
                    schema_body.remove(stmt)

        schema.body = schema_body

        schema_path.write_text(ast.unparse(schema_ast))
    print("✅ Success!")


if __name__ == "__main__":
    app()
