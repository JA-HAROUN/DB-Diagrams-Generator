from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from models import Database

load_dotenv(override=True)

MODEL = "gemini-3.8-flash"

INSTRUCTIONS = """
Design an ER database for the description above.

Format rules:
- Return a Database object using the exact field names of the schema.
- Attribute: name, isPrimaryKey, isPartialKey, composite,
  isMultiValued, derived.
- Entity: name, attributes, weak.
- Relationship: name, entities, cardinalities, participations,
  attributes, identifying.
- Relationship.entities must contain entity names spelled exactly as
  in the entities list.
- cardinalities: one value per entity, only "1", "N" or "M".
- participations: one value per entity, only "total" or "partial".
- Do not invent additional fields.

Modeling rules (decide these yourself from the description):
- Every strong entity needs a primary key attribute (isPrimaryKey=true).
  If the description gives no obvious key, add a sensible ID.
- WEAK ENTITY: an entity that cannot be uniquely identified by its own
  attributes and exists only in relation to an owner entity (e.g. a
  dependent of an employee, a room in a building). Set weak=true and
  connect it to its owner with an identifying relationship
  (identifying=true). The weak entity participates "total" in that
  relationship with cardinality "N" on its side and "1" on the owner's
  side.
- PARTIAL KEY: a weak entity has NO primary key. Instead, mark the
  attribute that distinguishes its instances among those of the same
  owner (e.g. a dependent's name) with isPartialKey=true and
  isPrimaryKey=false. Never set isPartialKey=true on a strong entity,
  and never set isPrimaryKey=true on a weak entity.
- PARTICIPATION: "total" if every instance of the entity must take part
  in the relationship (it cannot exist without it, or words like "must",
  "every", "each ... has"). Otherwise "partial".
- CARDINALITY: for each entity, give how many instances of THAT entity
  can be linked to one instance of the other side. A department with many
  employees is Department "1", Employee "N". A many-to-many is "M" and
  "N". For a ternary relationship use "1", "M", "N" as appropriate.
- COMPOSITE: an attribute that has meaningful parts (name -> first, last;
  address -> street, city). List the parts in composite.
- MULTIVALUED: an attribute that can hold several values per instance
  (phone numbers, emails, skills). Set isMultiValued=true.
- DERIVED: an attribute computable from others (age from birth date,
  total from items). Set derived=true.
- RELATIONSHIP ATTRIBUTE: a fact that belongs to the pairing and not to
  either entity (grade, hours worked, enrollment date). Put it in the
  Relationship's attributes.
- If a many-to-many link has no attributes, it is still a relationship,
  not a new entity.
- When the description is ambiguous, choose the most reasonable
  interpretation instead of leaving fields empty.
"""

import os

llm = ChatGoogleGenerativeAI(model=MODEL, temperature=0)
structured_llm = llm.with_structured_output(Database)


def get_structured_llm(model: str | None = None):
    load_dotenv(override=True)
    m = model or os.getenv("GEMINI_MODEL", MODEL)
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        active_llm = ChatGoogleGenerativeAI(model=m, temperature=0, google_api_key=api_key)
    else:
        active_llm = ChatGoogleGenerativeAI(model=m, temperature=0)
    return active_llm.with_structured_output(Database)


def generate_database(description: str, model: str | None = None) -> Database | None:
    client = get_structured_llm(model)
    return client.invoke(f"{description}\n{INSTRUCTIONS}")


def refine_database(current: Database, feedback: str, model: str | None = None) -> Database | None:
    prompt = f"""
    Here is the current ER database as JSON:

    {current.model_dump_json(indent=2)}

    Apply ONLY this change and keep everything else exactly as it is:
    {feedback}
    {INSTRUCTIONS}
    """

    client = get_structured_llm(model)
    return client.invoke(prompt)
