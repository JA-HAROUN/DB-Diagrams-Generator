import html

from graphviz import Graph

from models import Database


# Drawing Functions
def make_label(text, underlined = False):
    safe = html.escape(text)
    return f"<<U>{safe}</U>>" if underlined else text

def composite_attribute_drawing(attribute, graph, entity):
    parent_id = f"{entity.name}_{attribute.name}"
    for subatt in attribute.composite:
        sub_id = f"{parent_id}_{subatt}"
        graph.node(name=f"{entity.name}_{attribute.name}_{subatt}", label=make_label(subatt, underlined=attribute.isPrimaryKey), shape="oval")
        graph.edge(parent_id, sub_id)

def attribute_drawing(attribute, graph, entity):
    attribute_id = f"{entity.name}_{attribute.name}"

    graph.node(
        name=attribute_id,
        label=make_label(attribute.name, underlined=attribute.isPrimaryKey),
        shape="oval",
        peripheries="2" if attribute.isMultiValued else "1"
    )

    # Composite Attribute
    if attribute.composite:
        composite_attribute_drawing(attribute, graph, entity)

    graph.edge(entity.name, attribute_id)

def entity_drawing(entity, graph):
    graph.node(
        name=entity.name,
        label=entity.name,
        shape="rectangle",
        peripheries = "2" if entity.weak else "1"
    )

    for attribute in entity.attributes:
        attribute_drawing(attribute, graph, entity)

def relationship_drawing(relationship, graph):
    entities = relationship.entities
    cardinalities = relationship.cardinalities
    participations = relationship.participations

    if len(participations) == 0:
        participations = ["partial"] * len(entities)
    
    graph.node(
        name=relationship.name,
        label=relationship.name,
        shape="diamond",
        peripheries = "2" if relationship.identifying else "1"
    )
    
    for entity, cardinality, participation in zip(entities, cardinalities, participations):
        graph.edge(
            entity,
            relationship.name,
            headlabel=cardinality,
            style = "bold" if (participation == "total") else "solid"
        )

def db_drawing(database, filename="er-diagram"):

    graph = Graph(format="png")
    graph.attr(splines="true")

    for entity in database.entities:
        entity_drawing(entity, graph)

    for relationship in database.relationships:
        relationship_drawing(relationship, graph)

    graph.render(filename=filename, cleanup=True, view=True)

# Testing
example = """
{
  "name": "University",
  "entities": [
    {
      "name": "Student",
      "attributes": [
        {
          "name": "id",
          "isPrimaryKey": true,
          "composite": null,
          "isMultiValued": false,
          "derived": false
        },
        {
          "name": "name",
          "isPrimaryKey": false,
          "composite": null,
          "isMultiValued": false,
          "derived": false
        },
        {
          "name": "email",
          "isPrimaryKey": false,
          "composite": null,
          "isMultiValued": false,
          "derived": false
        }
      ],
      "weak": false
    },
    {
      "name": "Course",
      "attributes": [
        {
          "name": "code",
          "isPrimaryKey": true,
          "composite": null,
          "isMultiValued": false,
          "derived": false
        },
        {
          "name": "title",
          "isPrimaryKey": false,
          "composite": null,
          "isMultiValued": false,
          "derived": false
        },
        {
          "name": "credit_hours",
          "isPrimaryKey": false,
          "composite": null,
          "isMultiValued": false,
          "derived": false
        }
      ],
      "weak": false
    },
    {
      "name": "Enrollment",
      "attributes": [
        {
          "name": "grade",
          "isPrimaryKey": false,
          "composite": null,
          "isMultiValued": false,
          "derived": false
        }
      ],
      "weak": true
    }
  ],
  "relationships": [
    {
      "name": "Student_Enrollment",
      "entities": [],
      "cardinalities": [
        "1",
        "N"
      ],
      "participations": [
        "Partial",
        "Total"
      ],
      "identifying": true
    },
    {
      "name": "Course_Enrollment",
      "entities": [],
      "cardinalities": [
        "1",
        "N"
      ],
      "participations": [
        "Partial",
        "Total"
      ],
      "identifying": true
    }
  ]
}
"""


db = Database.model_validate_json(example)

db_drawing(db)