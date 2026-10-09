from models import Database

# 1. Read JSON
print("Hello to our ER Diagram Generator")
print("Please give us your JSON file path: ")
path = input()

with open(path, "r") as file:
    data = file.read()

    DB = Database.model_validate_json(data)

print(DB)

# 2. Get Models

# 3. Draw Model

"""
TODO:
    1. Logic to get the json file from the user -> File Picker
    2. Use the json data to send it to db_drawing()
    3. Display the generated ER diagram
    4. Allow the user to save the generated diagram => Already saved in the file

    ### Relationship Must Have ability to add ATTRIBUTES
    
    5. ADD AI LOGIC

FUTURE_RELEASES:
    1. n-ary relations -> Done
    2. Participation types -> Done
    3. Composite Attribute of Composite Attribute (hierarchical)
    4. Weak & Strong Entities -> Done
    5. GUI For the App
    6. Relational Diagram OUTPUT
    7. Export to other formats (PDF, SVG, etc.)
    8. Export SQL output if needed
    9. Make the API Key inputable not just hardcoded
"""
