import html

from graphviz import Graph

from models import Attribute


# Drawing Functions
def make_label(text, underlined=False, dashed_underline=False):
    safe = html.escape(text)
    if dashed_underline:
        return (
            '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="0">'
            f'<TR><TD SIDES="B" STYLE="dashed">{safe}</TD></TR></TABLE>>'
        )
    if underlined:
        return f"<<U>{safe}</U>>"
    return f"<{safe}>"


def attribute_drawing(attribute, graph, component_name):
    attribute_id = f"{component_name}_{attribute.name}"

    graph.node(
        name=attribute_id,
        label=make_label(
            attribute.name,
            underlined=attribute.isPrimaryKey,
            dashed_underline=attribute.isPartialKey,
        ),
        shape="oval",
        peripheries="2" if attribute.isMultiValued else "1",
        style="dashed" if attribute.derived else "solid",
    )

    graph.edge(component_name, attribute_id, len="0.5")

    # Composite Attribute
    if attribute.composite:
        for subatt in attribute.composite:
            if isinstance(subatt, str):
                subatt = Attribute(name=subatt)
            attribute_drawing(subatt, graph, attribute_id)


def entity_drawing(entity, graph):
    graph.node(
        name=entity.name,
        label=entity.name,
        shape="rectangle",
        peripheries="2" if entity.weak else "1",
    )

    for attribute in entity.attributes:
        attribute_drawing(attribute, graph, entity.name)


def relationship_drawing(relationship, graph):
    entities = relationship.entities
    cardinalities = relationship.cardinalities
    participations = relationship.participations
    attributes = relationship.attributes

    if len(participations) == 0:
        participations = ["partial"] * len(entities)

    graph.node(
        name=relationship.name,
        label=relationship.name,
        shape="diamond",
        peripheries="2" if relationship.identifying else "1",
    )

    for entity, cardinality, participation in zip(
        entities, cardinalities, participations
    ):
        graph.edge(
            entity,
            relationship.name,
            taillabel=cardinality,
            labeldistance="2",
            len="1.5",
            color=(
                "black:invis:black" if (participation.lower() == "total") else "black"
            ),
        )

    for attribute in attributes:
        attribute_drawing(attribute, graph, relationship.name)


def db_drawing(database, filename="er-diagram", format="png", view=True):

    graph = Graph(format=format, engine="neato")
    graph.attr(overlap="false", sep="+12", splines="true")

    if database.name:
        graph.attr(
            label=database.name,
            labelloc="t",
            labeljust="c",
            fontsize="28",
        )

    graph.attr("graph", fontname="Helvetica", dpi="450")
    graph.attr("node", fontname="Helvetica", fontsize="12")
    graph.attr("edge", fontname="Helvetica", fontsize="11", penwidth="1.2")

    for entity in database.entities:
        entity_drawing(entity, graph)

    for relationship in database.relationships:
        relationship_drawing(relationship, graph)

    return graph.render(filename=filename, cleanup=True, view=view)
