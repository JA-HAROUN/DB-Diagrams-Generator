from __future__ import annotations

from typing import Any

from pydantic import BaseModel, model_validator


class Attribute(BaseModel):
    name: str = ""
    isPrimaryKey: bool | None = None
    isPartialKey: bool | None = None
    composite: list[str] | list[Attribute] | None = None
    isMultiValued: bool | None = None
    derived: bool | None = None


class Entity(BaseModel):
    name: str = ""
    attributes: list[Attribute] = []
    weak: bool | None = None


class Relationship(BaseModel):
    name: str = ""
    entities: list[str] = []
    cardinalities: list[str] = []
    participations: list[str] = []
    attributes: list[Attribute] = []
    identifying: bool = False

    @model_validator(mode="before")
    @classmethod
    def reshape_input(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = data.copy()

        entities = [data.pop(k) for k in list(data) if k.startswith("entity")]
        if entities:
            data["entities"] = entities

        if isinstance(data.get("cardinality"), str):
            data["cardinalities"] = data.pop("cardinality").split(":")

        if isinstance(data.get("participation"), str):
            data["participations"] = data.pop("participation").split(":")

        return data


class Database(BaseModel):
    name: str | None = None
    entities: list[Entity] = []
    relationships: list[Relationship] = []
