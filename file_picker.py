import tkinter as tk
from tkinter import filedialog


def pick_file():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    path = filedialog.askopenfilename(
        title="Select a JSON file",
        filetypes=[("JSON files", "*.json")],
    )
    root.destroy()
    return path or None


if __name__ == "__main__":
    print(pick_file())
