"""A complete little tray application in about sixty lines.

Run it twice: the second launch does not open a second copy, it asks the
first one to come back to the front. Close the window and it keeps running
in the tray; if there is no tray on this desktop it minimises instead of
disappearing.

    python examples/tk_demo.py
    python examples/tk_demo.py --background
"""

import tkinter as tk
from tkinter import ttk

from desktop_lifecycle import App, TrayUnavailable, create_tray

NAME = "desktop-lifecycle-demo"


def main() -> int:
    app = App(NAME).ensure_dirs()
    log_path = app.setup_logging(console=True)

    if not app.acquire():
        # Another copy is running and has been asked to show its window.
        print("Already running - requested the existing window.")
        return 0

    root = tk.Tk()
    root.title("desktop-lifecycle demo")
    root.geometry("420x180")
    root.protocol("WM_DELETE_WINDOW", root.withdraw)

    frame = ttk.Frame(root, padding=18)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="Running as a single instance", font=("Sans", 14, "bold")).pack(anchor="w")
    ttk.Label(frame, text=f"Log: {log_path}", wraplength=380).pack(anchor="w", pady=(6, 12))
    ttk.Label(frame, text=f"Session: {app.session}").pack(anchor="w")

    buttons = ttk.Frame(frame)
    buttons.pack(fill="x", pady=(16, 0))
    ttk.Button(buttons, text="Hide", command=root.withdraw).pack(side="left")
    ttk.Button(buttons, text="Quit", command=root.destroy).pack(side="left", padx=8)

    try:
        tray = create_tray(
            "desktop-lifecycle demo",
            icon="applications-system",
            items=[("Show window", root.deiconify)],
            on_show=root.deiconify,
            on_quit=root.destroy,
        )
    except TrayUnavailable as error:
        tray = None
        print(f"No tray icon on this desktop: {error}")

    if tray is not None:
        tray.set_label("Running")

    def tick() -> None:
        if app.poll_show_request():
            root.deiconify()
            root.lift()
        if tray is not None:
            tray.pump()
        root.after(100, tick)

    root.after(100, tick)
    if app.background_requested and tray is not None:
        root.withdraw()

    try:
        root.mainloop()
    finally:
        if tray is not None:
            tray.stop()
        app.release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
