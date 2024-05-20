# enchante
Simplify your DB management

---
## Motivation

Imagine you're creating an API that connects to your SQL DB via SQLAlchemy. One of the biggest pain points is to create a structure that makes logical sense along with being easy to scale (as in add more tables easily).
Well, that's where `enchante` comes in! Using the power of Pydantic, SQLAlchemy and Alembic, it'll be much easier to initialise and make changes to your database.

This CLI helps with creating and scaffolding the structure of your db architecture as python code.

### Folder structure
```
db/
├─ migrations/
├─ [table_name]/
│  ├─ __init__.py
│  ├─ crud.py
│  ├─ model.py
│  ├─ schema.py
enchante.toml
```
## Why not `...`?
<details>
  <summary>
    Why not <a href="https://sqlmodel.tiangolo.com/">SQLModel</a> instead of
    Pydantic + SQLALchemy?
  </summary>
  SQLModel still has a long way to go
  <a href="https://github.com/tiangolo/sqlmodel/issues/654">
    with their current roadmap </a
  >, but they're making good progress!
</details>


## How to use
1. First run `enchante init <root_dir>`
2. Now you can run `enchante create <object_name>`

## Development 

---
License: [MIT](https://github.com/StevenJPx2/enchante/blob/main/LICENSE)
