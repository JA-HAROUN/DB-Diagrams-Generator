
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from models import Database

load_dotenv(override=True)

llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    temperature=0,
)

structured_llm = llm.with_structured_output(Database)

prompt = """
Design a database for the following description:

A university has students and courses. Each student has a unique ID,
a name, and an email. Each course has a unique code, a title, and
credit hours.

A student can enroll in many courses, and each course can have
many students. Store the grade a student receives in each course.

Follow the supplied Pydantic schema exactly.

Instructions:
- Return a Database object.
- Include all necessary entities, attributes, and relationships.
- Use the exact field names defined by the Pydantic models.
- For Attribute, use name, isPrimaryKey, composite,
  isMultiValued, and derived.
- For Entity, use name, attributes, and weak.
- For Relationship, use name, entities, cardinalities,
  participations, and identifying.
- entities must contain entity names.
- cardinalities and participations must be lists of strings,
  with one value per participating entity.
- Use the appropriate cardinalities and participation constraints.
- Represent the grade using an appropriate entity or relationship
  attribute.
- Do not invent additional fields.
"""

database = structured_llm.invoke(prompt)

# Convert the validated Pydantic object to JSON
json_output = database.model_dump_json(indent=2)

print(json_output)

with open("database.json", "w", encoding="utf-8") as file:
    file.write(json_output)

print("\nSaved to database.json")
