"""
PDFMerger Desktop Lite

A lightweight, local desktop PDF merger for Windows, macOS, and Linux.
Files are selected and processed on the user's machine. Nothing is uploaded.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk

try:
    from pypdf import PdfReader, PdfWriter, Transformation
except ImportError as exc:  # pragma: no cover - shown to desktop user
    raise SystemExit(
        "Missing dependency: pypdf\n\nInstall it with:\n  pip install -r requirements.txt"
    ) from exc


APP_NAME = "PDFMerger Desktop Lite"
APP_TAGLINE = "Local PDF merging. No uploads. No account."


PAGE_SIZES = {
    "Original size": None,
    "A5": (419.53, 595.28),
    "A4": (595.28, 841.89),
    "A3": (841.89, 1190.55),
    "Letter": (612.0, 792.0),
    "Legal": (612.0, 1008.0),
    "Tabloid": (792.0, 1224.0),
}


QUALITY_MODES = {
    "Best quality": {"compress_streams": False},
    "Balanced": {"compress_streams": True},
    "Small file": {"compress_streams": True},
}


@dataclass
class MergeOptions:
    page_size: str
    orientation: str
    quality: str


class PDFMergerDesktop:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("880x680")
        self.root.minsize(760, 560)
        self.root.configure(bg="#fffbeb")

        self.files: list[Path] = []
        self.drag_index: int | None = None
        self.is_busy = False

        self.page_size_var = tk.StringVar(value="Original size")
        self.orientation_var = tk.StringVar(value="Keep original")
        self.quality_var = tk.StringVar(value="Best quality")
        self.status_var = tk.StringVar(value="Add PDFs to begin.")

        self._build_styles()
        self._build_ui()

    def _build_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Root.TFrame", background="#fffbeb")
        style.configure("Panel.TFrame", background="#ffffff", relief="flat")
        style.configure("Title.TLabel", background="#fffbeb", foreground="#0f172a", font=("Segoe UI", 22, "bold"))
        style.configure("Tag.TLabel", background="#fffbeb", foreground="#78350f", font=("Segoe UI", 10, "bold"))
        style.configure("Body.TLabel", background="#fffbeb", foreground="#334155", font=("Segoe UI", 10))
        style.configure("PanelTitle.TLabel", background="#ffffff", foreground="#0f172a", font=("Segoe UI", 12, "bold"))
        style.configure("PanelText.TLabel", background="#ffffff", foreground="#334155", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=(10, 7))
        style.configure("Accent.TButton", font=("Segoe UI", 11, "bold"), padding=(16, 10))
        style.map("Accent.TButton", background=[("active", "#f59e0b")])
        style.configure("TCombobox", font=("Segoe UI", 10))
        style.configure("TRadiobutton", background="#ffffff", foreground="#334155", font=("Segoe UI", 10))
        style.configure("Horizontal.TProgressbar", troughcolor="#fff7cc", background="#f59e0b")

    def _build_ui(self) -> None:
        shell = ttk.Frame(self.root, style="Root.TFrame", padding=24)
        shell.pack(fill="both", expand=True)

        header = ttk.Frame(shell, style="Root.TFrame")
        header.pack(fill="x")

        title_area = ttk.Frame(header, style="Root.TFrame")
        title_area.pack(side="left", fill="x", expand=True)
        ttk.Label(title_area, text="PDFMerger", style="Title.TLabel").pack(anchor="w")
        ttk.Label(title_area, text=APP_TAGLINE, style="Tag.TLabel").pack(anchor="w", pady=(3, 0))

        ttk.Button(header, text="Add PDFs", command=self.add_files).pack(side="right", padx=(8, 0))
        ttk.Button(header, text="Add Folder", command=self.add_folder).pack(side="right")

        note = ttk.Label(
            shell,
            text="Files are read from your computer and merged locally. The app does not upload your PDFs.",
            style="Body.TLabel",
        )
        note.pack(anchor="w", pady=(18, 10))

        main = ttk.Frame(shell, style="Root.TFrame")
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=1)

        self._build_file_panel(main)
        self._build_settings_panel(main)
        self._build_footer(shell)

    def _build_file_panel(self, parent: ttk.Frame) -> None:
        panel = tk.Frame(parent, bg="#ffffff", highlightthickness=1, highlightbackground="#f5c36b")
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        panel.rowconfigure(1, weight=1)
        panel.columnconfigure(0, weight=1)

        top = tk.Frame(panel, bg="#ffffff")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        top.columnconfigure(0, weight=1)

        ttk.Label(top, text="Merge order", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            top,
            text="Drag rows, or use the controls below.",
            style="PanelText.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))

        list_wrap = tk.Frame(panel, bg="#ffffff")
        list_wrap.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 10))
        list_wrap.rowconfigure(0, weight=1)
        list_wrap.columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(
            list_wrap,
            activestyle="none",
            bd=0,
            bg="#fffbeb",
            fg="#0f172a",
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightbackground="#fde68a",
            selectbackground="#f59e0b",
            selectforeground="#111827",
        )
        scrollbar = ttk.Scrollbar(list_wrap, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.listbox.bind("<ButtonPress-1>", self._drag_start)
        self.listbox.bind("<B1-Motion>", self._drag_motion)
        self.listbox.bind("<ButtonRelease-1>", self._drag_end)
        self.listbox.bind("<Delete>", lambda _event: self.remove_selected())

        controls = tk.Frame(panel, bg="#ffffff")
        controls.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
        for text, command in (
            ("Move up", self.move_up),
            ("Move down", self.move_down),
            ("Remove", self.remove_selected),
            ("Clear", self.clear_all),
        ):
            ttk.Button(controls, text=text, command=command).pack(side="left", padx=(0, 8))

    def _build_settings_panel(self, parent: ttk.Frame) -> None:
        panel = tk.Frame(parent, bg="#ffffff", highlightthickness=1, highlightbackground="#f5c36b")
        panel.grid(row=0, column=1, sticky="nsew")
        panel.columnconfigure(0, weight=1)

        ttk.Label(panel, text="Output settings", style="PanelTitle.TLabel").pack(anchor="w", padx=16, pady=(16, 8))

        form = tk.Frame(panel, bg="#ffffff")
        form.pack(fill="x", padx=16)

        ttk.Label(form, text="Page size", style="PanelText.TLabel").pack(anchor="w", pady=(8, 4))
        ttk.Combobox(
            form,
            textvariable=self.page_size_var,
            values=list(PAGE_SIZES.keys()),
            state="readonly",
        ).pack(fill="x")

        ttk.Label(form, text="Orientation", style="PanelText.TLabel").pack(anchor="w", pady=(16, 4))
        for text in ("Keep original", "Portrait", "Landscape"):
            ttk.Radiobutton(form, text=text, value=text, variable=self.orientation_var).pack(anchor="w", pady=2)

        ttk.Label(form, text="Quality", style="PanelText.TLabel").pack(anchor="w", pady=(16, 4))
        for text in QUALITY_MODES:
            ttk.Radiobutton(form, text=text, value=text, variable=self.quality_var).pack(anchor="w", pady=2)

        divider = tk.Frame(panel, bg="#fde68a", height=1)
        divider.pack(fill="x", padx=16, pady=18)

        help_text = (
            "Best quality keeps source streams unchanged.\n"
            "Balanced and Small file compress PDF content streams when possible."
        )
        ttk.Label(panel, text=help_text, style="PanelText.TLabel", wraplength=260).pack(anchor="w", padx=16)

        ttk.Button(panel, text="Merge and save", style="Accent.TButton", command=self.merge).pack(
            side="bottom", fill="x", padx=16, pady=16
        )

    def _build_footer(self, parent: ttk.Frame) -> None:
        bottom = ttk.Frame(parent, style="Root.TFrame")
        bottom.pack(fill="x", pady=(14, 0))
        ttk.Label(bottom, textvariable=self.status_var, style="Body.TLabel").pack(anchor="w")
        self.progress = ttk.Progressbar(bottom, mode="determinate", style="Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(8, 0))

    def add_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Choose PDF files",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        self._add_paths(paths)

    def add_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choose a folder containing PDFs")
        if not folder:
            return
        paths = sorted(Path(folder).glob("*.pdf"))
        self._add_paths(paths)

    def _add_paths(self, paths) -> None:
        added = 0
        seen = {p.resolve() for p in self.files}
        for raw in paths:
            path = Path(raw)
            if path.suffix.lower() != ".pdf":
                continue
            resolved = path.resolve()
            if resolved not in seen and path.exists():
                self.files.append(path)
                seen.add(resolved)
                added += 1
        self._refresh_list()
        if added == 0 and paths:
            messagebox.showinfo(APP_NAME, "No new PDF files were added.")

    def _refresh_list(self) -> None:
        self.listbox.delete(0, tk.END)
        for index, path in enumerate(self.files, start=1):
            self.listbox.insert(tk.END, f"{index:02d}. {path.name}")
        count = len(self.files)
        self.status_var.set(f"{count} PDF file{'s' if count != 1 else ''} ready.")

    def selected_index(self) -> int | None:
        selection = self.listbox.curselection()
        return selection[0] if selection else None

    def move_up(self) -> None:
        index = self.selected_index()
        if index is None or index == 0:
            return
        self.files[index - 1], self.files[index] = self.files[index], self.files[index - 1]
        self._refresh_list()
        self.listbox.selection_set(index - 1)

    def move_down(self) -> None:
        index = self.selected_index()
        if index is None or index >= len(self.files) - 1:
            return
        self.files[index + 1], self.files[index] = self.files[index], self.files[index + 1]
        self._refresh_list()
        self.listbox.selection_set(index + 1)

    def remove_selected(self) -> None:
        index = self.selected_index()
        if index is None:
            return
        self.files.pop(index)
        self._refresh_list()
        if self.files:
            self.listbox.selection_set(min(index, len(self.files) - 1))

    def clear_all(self) -> None:
        if not self.files:
            return
        if messagebox.askyesno(APP_NAME, "Remove all files from the merge list?"):
            self.files.clear()
            self._refresh_list()

    def _drag_start(self, event) -> None:
        self.drag_index = self.listbox.nearest(event.y)

    def _drag_motion(self, event) -> None:
        if self.drag_index is None:
            return
        target = self.listbox.nearest(event.y)
        if target == self.drag_index or not 0 <= target < len(self.files):
            return
        self.files.insert(target, self.files.pop(self.drag_index))
        self.drag_index = target
        self._refresh_list()
        self.listbox.selection_set(target)

    def _drag_end(self, _event) -> None:
        self.drag_index = None

    def merge(self) -> None:
        if self.is_busy:
            return
        if len(self.files) < 2:
            messagebox.showwarning(APP_NAME, "Add at least two PDFs before merging.")
            return

        output = filedialog.asksaveasfilename(
            title="Save merged PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="PDFMerger-output.pdf",
        )
        if not output:
            return

        options = MergeOptions(
            page_size=self.page_size_var.get(),
            orientation=self.orientation_var.get(),
            quality=self.quality_var.get(),
        )
        self.is_busy = True
        self._set_controls_enabled(False)
        self.progress["value"] = 0
        self.status_var.set("Merging PDFs locally...")

        worker = threading.Thread(target=self._merge_worker, args=(Path(output), options), daemon=True)
        worker.start()

    def _merge_worker(self, output: Path, options: MergeOptions) -> None:
        try:
            writer = PdfWriter()
            total = len(self.files)
            for index, path in enumerate(self.files, start=1):
                reader = PdfReader(str(path))
                for page in reader.pages:
                    page = self._prepare_page(page, options)
                    writer.add_page(page)
                self._set_progress(int(index / total * 80), f"Added {index} of {total}: {path.name}")

            if QUALITY_MODES[options.quality]["compress_streams"]:
                for page in writer.pages:
                    try:
                        page.compress_content_streams()
                    except Exception:
                        pass
                self._set_progress(92, "Compressed content streams where possible.")

            with output.open("wb") as handle:
                writer.write(handle)

            size = self._format_size(output.stat().st_size)
            self.root.after(0, lambda: self._merge_done(output, size))
        except Exception as exc:  # pragma: no cover - UI path
            self.root.after(0, lambda: self._merge_failed(exc))

    def _prepare_page(self, page, options: MergeOptions):
        size = PAGE_SIZES[options.page_size]
        if size is None and options.orientation == "Keep original":
            return page

        current_w = float(page.mediabox.width)
        current_h = float(page.mediabox.height)
        target_w, target_h = size or (current_w, current_h)

        if options.orientation == "Landscape" and target_w < target_h:
            target_w, target_h = target_h, target_w
        elif options.orientation == "Portrait" and target_w > target_h:
            target_w, target_h = target_h, target_w

        if current_w <= 0 or current_h <= 0:
            return page

        scale = min(target_w / current_w, target_h / current_h)
        tx = (target_w - current_w * scale) / 2
        ty = (target_h - current_h * scale) / 2

        page.add_transformation(Transformation().scale(scale).translate(tx=tx, ty=ty))
        page.mediabox.lower_left = (0, 0)
        page.mediabox.upper_right = (target_w, target_h)
        page.cropbox.lower_left = (0, 0)
        page.cropbox.upper_right = (target_w, target_h)
        return page

    def _set_progress(self, value: int, message: str) -> None:
        self.root.after(0, lambda: (self.progress.configure(value=value), self.status_var.set(message)))

    def _merge_done(self, output: Path, size: str) -> None:
        self.progress["value"] = 100
        self.status_var.set(f"Saved {output.name} ({size}).")
        self.is_busy = False
        self._set_controls_enabled(True)
        messagebox.showinfo(APP_NAME, f"Merged PDF saved locally:\n\n{output}\n\nSize: {size}")

    def _merge_failed(self, exc: Exception) -> None:
        self.progress["value"] = 0
        self.status_var.set("Merge failed.")
        self.is_busy = False
        self._set_controls_enabled(True)
        messagebox.showerror(APP_NAME, f"Could not merge the selected PDFs:\n\n{exc}")

    def _set_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for child in self.root.winfo_children():
            self._set_child_state(child, state)

    def _set_child_state(self, widget, state: str) -> None:
        try:
            if isinstance(widget, (ttk.Button, ttk.Combobox, ttk.Radiobutton)):
                widget.configure(state=state)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_child_state(child, state)

    @staticmethod
    def _format_size(bytes_count: int) -> str:
        if bytes_count >= 1024 * 1024:
            return f"{bytes_count / (1024 * 1024):.2f} MB"
        return f"{bytes_count / 1024:.1f} KB"


def main() -> None:
    root = tk.Tk()
    PDFMergerDesktop(root)
    root.mainloop()


if __name__ == "__main__":
    main()
