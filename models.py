from typing import Any

from pydantic import BaseModel, model_validator


class Attribute(BaseModel):
    name: str = None
    isPrimaryKey: bool = False
    composite: list[str] | None = None
    isMultiValued: bool = False
    derived: bool = False


class Entity(BaseModel):
    name: str = None
    attributes: list[Attribute] = []
    weak: bool = None


class Relationship(BaseModel):
    name: str = None
    entities: list[str] = []
    cardinalities: list[str] = []
    participations: list[str] = []
    identifying: bool = False

    @model_validator(mode="before")
    @classmethod
    def get_entities(cls, data: Any) -> Any:

        data = data.copy()
        entities = []

        if isinstance(data, dict):
            for key, value in list(data.items()):
                if key.startswith("entity"):
                    entities.append(value)
                    del data[key]

            data["entities"] = entities

        return data

    @model_validator(mode="before")
    @classmethod
    def get_cardinality(cls, data: Any) -> Any:
        if isinstance(data, dict) and "cardinality" in data:
            cardinalities = data["cardinality"].split(":")
            data["cardinalities"] = cardinalities

        return data

    # Participations
    @model_validator(mode="before")
    @classmethod
    def get_participations(cls, data: Any) -> Any:
        if isinstance(data, dict) and "participation" in data:
            participations = data["participation"].split(":")
            data["participations"] = participations
        return data


class Database(BaseModel):
    name: str | None = None
    entities: list[Entity] = []
    relationships: list[Relationship] = []
