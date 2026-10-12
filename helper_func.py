from pydantic_core import ValidationError

from models import Database


def save(database, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(database.model_dump_json(indent=2))


def load(path):
    with open(path, encoding="utf-8") as f:
        content = f.read()
    try:
        return Database.model_validate_json(content)
    except ValidationError as e:
        print(f"\nThe JSON is not valid:\n{e}")
        return None


def ai_call(func, *args):
    try:
        result = func(*args)
    except (ConnectionError, TimeoutError, ValueError) as e:
        print(f"AI call failed: {e}")
        return None
    if result is None:
        print("The AI did not return a valid database.")
    return result


import os
import subprocess
import sys


def open_file(path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=True)
        else:
            subprocess.run(["xdg-open", path], check=True)
    except (OSError, subprocess.SubprocessError) as e:
        print(
            f"Couldn't open the file automatically ({e}). Please open {path} yourself."
        )
