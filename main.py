from pydantic import ValidationError

from ai import generate_database, refine_database
from file_picker import pick_file
from graph import db_drawing
from helper_func import ai_call, load, open_file, save
from models import Database

# 1. Read JSON
print("Hi There, Welcome to our ER Diagram Generator")
print("Generate from Description or from a file? (1 = Description, 2 = JSON file)")
choice = input().strip()

while choice not in ("1", "2"):
    print("Invalid choice. Please enter 1 or 2.")
    choice = input().strip()

database = None
json_path = "database.json"

if choice == "1":
    description = input("Describe your database:\n")
    database = ai_call(generate_database, description)

    if database:
        save(database, "generated_database.json")

else:
    path = pick_file()
    if not path:
        print("No file selected.")
    else:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()

            try:
                database = Database.model_validate_json(content)
            except ValidationError as e:
                print(f"Error validating JSON: {e}")
                database = None

while database is not None:
    print("\n" + database.model_dump_json(indent=2))
    print(f"""
            What now?
            1. Looks good, draw the diagram
            2. I edited the file myself ({json_path}), reload it
            3. Tell the AI what to change
            4. Rewrite the description from scratch
            (3 and 4 overwrite {json_path}, so save your manual edits first.)""")
    action = input("> ").strip()

    if action == "1":
        db_drawing(database)
        break
    elif action == "2":
        open_file(json_path)
        input(f"Edit and save {json_path}, then press Enter...")
        reloaded = load(json_path)
        if reloaded:
            database = reloaded
        else:
            print("Keeping the previous version. Fix the file and choose 2 again.")
    elif action == "3":
        change = input("What should change?\n")
        updated = ai_call(refine_database, database, change)
        if updated:
            database = updated
            save(database, json_path)
    elif action == "4":
        description = input("New description:\n")
        updated = ai_call(generate_database, description)
        if updated:
            database = updated
            save(database, json_path)
    else:
        print("Please enter 1, 2, 3 or 4.")
