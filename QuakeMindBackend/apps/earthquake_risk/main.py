import tkinter as tk
try:
    import customtkinter as ctk
except ImportError:
    ctk = None
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from gui_app import App

def main():
    if ctk:
        # CustomTkinter ana penceresi
        root = ctk.CTk()
    else:
        root = tk.Tk()
        
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
