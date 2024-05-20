import operator
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generic, Sequence, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql._typing import (
    _ColumnExpressionArgument,
    _ColumnExpressionOrStrLabelArgument,
)

from .base import Base

Model = TypeVar("Model", bound=Base)
CreateModel = TypeVar("CreateModel", bound=BaseModel)
UIDType = UUID | str | int


@dataclass
class CRUD(Generic[Model, CreateModel]):
    model: type[Model]
    uid_key: str = "uid"

    def __dict_to_where(
        self,
        where: dict[str, Any],
    ):
        """Converts dict to where clause"""
        filters: list[_ColumnExpressionArgument[bool]] = []

        filter_available_operations = {
            "lt": operator.lt,
            "gt": operator.gt,
            "le": operator.le,
            "ge": operator.ge,
            "eq": operator.eq,
            "ne": operator.ne,
        }
        column_type_mappings = {
            "TIMESTAMP": lambda st: func.to_timestamp(st),
            "DATETIME": lambda st: func.to_timestamp(st),
        }

        for key, value in where.items():
            pattern = re.compile(
                rf"(\w+)(?:__({'|'.join(filter_available_operations.keys())}))"
            )

            if (match := pattern.fullmatch(key)) is not None:
                column = getattr(self.model, match.group(1))
                operand = filter_available_operations.get(match.group(2))
            else:
                column = getattr(self.model, key)
                operand = operator.eq

            if operand is None:
                raise Exception("Not an available operand")

            filters.append(
                operand(
                    column,
                    column_type_mappings.get(
                        str(column.type),
                        lambda st: cast(st, column.type) if st is not None else None,
                    )(value),
                ),
            )

        return filters

    def __list_to_order_by(self, order_by: list[str]):
        """Converts list to order_by clause"""
        filters: list[_ColumnExpressionOrStrLabelArgument] = []
        filter_available_operations = ["desc"]
        for key in order_by:
            pattern = re.compile(rf"(\w+)__({'|'.join(filter_available_operations)})")
            if (match := pattern.fullmatch(key)) is not None:
                column = getattr(self.model, match.group(1))
                filters.append(
                    getattr(
                        column,
                        match.group(2),
                    )()
                )
            else:
                filters.append(getattr(self.model, key))

        return filters

    ## Create
    async def create_new(self, db: AsyncSession, model: CreateModel) -> Model:
        """Creates new item"""
        db_item: Model = self.model(**model.model_dump())
        db.add(db_item)
        await db.commit()
        await db.refresh(db_item)

        return db_item

    ## READ

    async def get_all_where(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        where: dict[str, Any],
        order_by: list[str] = [],
    ) -> Sequence[Model]:
        return (
            (
                await db.scalars(
                    select(self.model)
                    .where(*self.__dict_to_where(where))
                    .offset(skip)
                    .limit(limit)
                    .order_by(*self.__list_to_order_by(order_by))
                )
            )
            .unique()
            .all()
        )

    async def get_all(self, db: AsyncSession, *, skip: int = 0, limit: int = 100):
        return await self.get_all_where(
            db,
            skip=skip,
            limit=limit,
            where={},
        )

    async def get_where(
        self, db: AsyncSession, *, where: dict[str, Any]
    ) -> Model | None:
        return (
            (await db.scalars(select(self.model).where(*self.__dict_to_where(where))))
            .unique()
            .first()
        )

    async def get(self, db: AsyncSession, uid: UIDType):
        return await self.get_where(db, where={self.uid_key: uid})

    ## UPDATE
    async def update_all_where(
        self,
        db: AsyncSession,
        *,
        where: dict[str, Any],
        update_values: dict[str, Any],
    ) -> Sequence[Model]:
        if "updated_at" in vars(self.model):
            update_values.update(updated_at=datetime.now())

        items_to_update = (
            (await db.scalars(select(self.model).where(*self.__dict_to_where(where))))
            .unique()
            .all()
        )

        if items_to_update is None:
            raise Exception(f"Item with values '{where}' is not found in {self.model}")

        for item in items_to_update:
            for key, value in update_values.items():
                setattr(item, key, value)

        await db.commit()
        await db.refresh(items_to_update)
        return items_to_update

    async def update_where(
        self,
        db: AsyncSession,
        *,
        where: dict[str, Any],
        update_values: dict[str, Any],
    ) -> Model:
        if "updated_at" in vars(self.model):
            update_values.update(updated_at=datetime.now())

        item_to_update = (
            (await db.scalars(select(self.model).where(*self.__dict_to_where(where))))
            .unique()
            .first()
        )

        if item_to_update is None:
            raise Exception(f"Item with values '{where}' is not found in {self.model}")

        for key, value in update_values.items():
            setattr(item_to_update, key, value)

        await db.commit()
        await db.refresh(item_to_update)
        return item_to_update

    async def update(
        self,
        db: AsyncSession,
        uid: UIDType,
        *,
        update_values: dict[str, Any],
    ):
        return await self.update_where(
            db,
            where={self.uid_key: uid},
            update_values=update_values,
        )

    ## DELETE
    async def delete_where(self, db: AsyncSession, *, where: dict[str, Any]) -> Model:
        item_to_delete: Model | None = (
            (await db.scalars(select(self.model).where(*self.__dict_to_where(where))))
            .unique()
            .first()
        )

        if item_to_delete is None:
            raise Exception(f"Item with values '{where}' is not found in {self.model}")

        await db.delete(item_to_delete)
        await db.commit()
        return item_to_delete

    async def delete(self, db: AsyncSession, uid: UIDType):
        return await self.delete_where(db, where={"uid": uid})
