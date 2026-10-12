from graph import db_drawing
from models import Database

example = """
{
  "name": "Company",
  "entities": [
    {
      "name": "Employee",
      "weak": false,
      "attributes": [
        {"name": "ssn", "isPrimaryKey": true},
        {"name": "name", "composite": [{"name": "first"}, {"name": "last"}]},
        {"name": "phones", "isMultiValued": true},
        {"name": "age", "derived": true},
        {"name": "tags", "composite": ["a", "b"]},
        {"name": "address", "composite": [
          {"name": "street"},
          {"name": "city", "composite": [{"name": "zip"}]}
        ]}
      ]
    },
    {"name": "Project", "attributes": [{"name": "pno", "isPrimaryKey": true}, {"name": "title"}]},
    {"name": "Department", "attributes": [{"name": "dno", "isPrimaryKey": true}]},
    {"name": "Dependent", "weak": true, "attributes": [{"name": "dep_name", "isPartialKey": true}]}
  ],
  "relationships": [
    {
      "name": "Works_On",
      "entity1": "Employee", "entity2": "Project",
      "cardinality": "M:N",
      "participation": "total:partial",
      "attributes": [{"name": "hours"}]
    },
    {
      "name": "Has_Dependent",
      "entity1": "Employee", "entity2": "Dependent",
      "cardinality": "1:N",
      "participation": "partial:total",
      "identifying": true
    },
    {
      "name": "Supplies",
      "entity1": "Employee", "entity2": "Project", "entity3": "Department",
      "cardinality": "1:M:N"
    },
    {
      "name": "Works_For",
      "entities": ["Employee", "Department"],
      "cardinalities": ["N", "1"],
      "participations": ["total", "total"]
    }
  ]
}
"""

db = Database.model_validate_json(example)
emp, proj, dept, dep = db.entities
works_on, has_dep, supplies, works_for = db.relationships

# Entities
assert db.name == "Company"
assert emp.weak is False and dep.weak is True and proj.weak is None  # weak / default

# Attribute flags
ssn, name, phones, age, tags, address = emp.attributes
assert ssn.isPrimaryKey is True
assert phones.isMultiValued is True
assert age.derived is True
assert proj.attributes[1].isPrimaryKey is None  # default
assert dep.attributes[0].isPartialKey is True
assert ssn.isPartialKey is None  # default

# Composite: list[Attribute], list[str], nested, none
assert name.composite[0].name == "first"
assert tags.composite == ["a", "b"]
assert address.composite[1].composite[0].name == "zip"  # recursion
assert ssn.composite is None

# Relationship: entityN keys -> entities list
assert works_on.entities == ["Employee", "Project"]
assert supplies.entities == ["Employee", "Project", "Department"]  # ternary

# "1:N" strings -> lists
assert works_on.cardinalities == ["M", "N"]
assert supplies.cardinalities == ["1", "M", "N"]
assert works_on.participations == ["total", "partial"]
assert supplies.participations == []  # missing -> default

# Other fields
assert has_dep.identifying is True and works_on.identifying is False
assert works_on.attributes[0].name == "hours"

# Already-shaped input must NOT be overwritten
assert works_for.entities == ["Employee", "Department"]
assert works_for.cardinalities == ["N", "1"]

# Round trip
assert Database.model_validate(db.model_dump()) == db
print("All model tests passed")

# Visual check:
#   Employee_ssn      -> solid underline (primary key)
#   Dependent dep_name -> dashed underline (partial key)
#   phones            -> double oval (multivalued)
#   age               -> dashed oval (derived)
#   Dependent         -> double rectangle (weak)
#   Has_Dependent     -> double diamond (identifying)
#   Works_On (Employee side), Has_Dependent (Dependent side),
#   Works_For (both sides) -> double lines (total participation)
db_drawing(db)
