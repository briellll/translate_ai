import os
import time
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import List

from translator.pipeline import run_translation
from translator.types import TranslationConfig, ProgressStats

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Tradutor AI Desktop")
        self.geometry("1100x800")
        try:
            self.minsize(960, 680)
        except Exception:
            pass
        self.input_path = ctk.StringVar()
        self.api_key = ctk.StringVar(value=os.getenv("OPENAI_API_KEY", ""))
        self.model = ctk.StringVar(value="gpt-4o-mini")
        self.chunk_chars = ctk.IntVar(value=4000)
        self.out_format = ctk.StringVar(value="pdf")
        self.output_dir = ctk.StringVar()
        self.status = ctk.StringVar(value="Pronto")
        self.progress = ctk.DoubleVar(value=0)
        self.total = 0
        self._cancel = threading.Event()
        self._preview_max = 2000
        self._build()

    def _build(self):
        container = ctk.CTkFrame(self, corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        grid = container
        row = 0
        ctk.CTkLabel(grid, text="Arquivo").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        ctk.CTkEntry(grid, textvariable=self.input_path, width=480).grid(row=row, column=1, sticky="we", padx=8, pady=6)
        ctk.CTkButton(grid, text="Selecionar", command=self.select_file).grid(row=row, column=2, padx=8, pady=6)
        row += 1
        ctk.CTkLabel(grid, text="Pasta de saída").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        ctk.CTkEntry(grid, textvariable=self.output_dir, width=480).grid(row=row, column=1, sticky="we", padx=8, pady=6)
        ctk.CTkButton(grid, text="Selecionar", command=self.select_output_dir).grid(row=row, column=2, padx=8, pady=6)
        row += 1
        ctk.CTkLabel(grid, text="API Key").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        ctk.CTkEntry(grid, textvariable=self.api_key, width=480, show="*").grid(row=row, column=1, sticky="we", padx=8, pady=6)
        row += 1
        row += 1
        ctk.CTkLabel(grid, text="Modelo").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        ctk.CTkEntry(grid, textvariable=self.model, width=320).grid(row=row, column=1, sticky="we", padx=8, pady=6)
        row += 1
        ctk.CTkLabel(grid, text="Chars por chunk").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        self._slider = ctk.CTkSlider(grid, from_=1000, to=10000, number_of_steps=18, command=lambda v: self.chunk_chars.set(int(v)), width=320)
        self._slider.grid(row=row, column=1, sticky="we", padx=8, pady=6)
        self._slider.set(self.chunk_chars.get())
        ctk.CTkLabel(grid, textvariable=self.chunk_chars).grid(row=row, column=2, sticky="w", padx=8, pady=6)
        row += 1
        ctk.CTkLabel(grid, text="Formato de saída").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        ctk.CTkOptionMenu(grid, variable=self.out_format, values=["pdf","epub","txt"]).grid(row=row, column=1, sticky="we", padx=8, pady=6)
        row += 1
        btns = ctk.CTkFrame(grid)
        btns.grid(row=row, column=0, columnspan=3, sticky="we", padx=8, pady=6)
        self._start_btn = ctk.CTkButton(btns, text="Iniciar", command=self.start, height=40)
        self._start_btn.pack(side="left", expand=True, fill="x", padx=(0,8))
        self._cancel_btn = ctk.CTkButton(btns, text="Cancelar", command=self.cancel, height=40, state="disabled")
        self._cancel_btn.pack(side="left", expand=True, fill="x")
        row += 1
        ctk.CTkLabel(grid, textvariable=self.status).grid(row=row, column=0, columnspan=3, sticky="we", padx=8, pady=6)
        row += 1
        pb = ctk.CTkProgressBar(grid)
        pb.grid(row=row, column=0, columnspan=3, sticky="we", padx=8, pady=6)
        pb.set(0)
        self._pb = pb
        for i in range(3):
            grid.columnconfigure(i, weight=1)

        row += 1
        legend = ctk.CTkFrame(grid, corner_radius=8)
        legend.grid(row=row, column=0, columnspan=3, sticky="we", padx=8, pady=(2,6))
        legend.columnconfigure(0, weight=0)
        legend.columnconfigure(1, weight=1)
        self._legend = legend
        names = [
            "Tempo decorrido",
            "Tempo estimado (ETA)",
            "Média por parte",
            "Velocidade (partes por minuto)",
            "Modelo",
            "Caracteres por chunk",
            "Total de partes",
        ]
        self._legend_fields = {}
        for i, nm in enumerate(names):
            ctk.CTkLabel(legend, text=f"{nm}:").grid(row=i, column=0, sticky="w", padx=8, pady=2)
            val = ctk.CTkLabel(legend, text="-", anchor="w")
            val.grid(row=i, column=1, sticky="we", padx=8, pady=2)
            self._legend_fields[nm] = val

        row += 1
        bottom = ctk.CTkFrame(grid, corner_radius=12)
        bottom.grid(row=row, column=0, columnspan=3, sticky="nsew", padx=8, pady=8)
        grid.rowconfigure(row, weight=1)
        bottom.columnconfigure(0, weight=1)
        bottom.rowconfigure(0, weight=1)
        preview_label = ctk.CTkLabel(bottom, text="Prévia traduzida (tempo real)")
        preview_label.grid(row=0, column=0, sticky="w", padx=8, pady=(8,4))
        preview_box = ctk.CTkTextbox(bottom, width=900, height=260)
        preview_box.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0,8))
        self._preview = preview_box
        act = ctk.CTkProgressBar(bottom)
        act.grid(row=2, column=0, sticky="we", padx=8, pady=(0,8))
        act.set(0)
        self._activity = act

    def select_file(self):
        path = filedialog.askopenfilename(title="Selecione PDF ou EPUB", filetypes=[("PDF","*.pdf"),("EPUB","*.epub")])
        if path:
            self.input_path.set(path)

    def select_output_dir(self):
        path = filedialog.askdirectory(title="Selecione a pasta de saída")
        if path:
            self.output_dir.set(path)

    def start(self):
        if getattr(self, "_running", False):
            return
        self._running = True
        self._cancel.clear()
        self._start_btn.configure(state="disabled")
        self._cancel_btn.configure(state="normal")
        self.status.set("Preparando...")
        threading.Thread(target=self._run_task, daemon=True).start()
        self._animate_activity()

    def _run_task(self):
        try:
            ip = self.input_path.get()
            if not ip:
                self._notify_error("Selecione um arquivo")
                return
            if not os.path.exists(ip):
                self._notify_error("Arquivo não encontrado")
                return
            base = os.path.splitext(os.path.basename(ip))[0]
            out_dir = self.output_dir.get()
            if not out_dir:
                self._notify_error("Selecione a pasta de saída")
                return
            cfg = TranslationConfig(
                input_path=ip,
                output_dir=out_dir,
                out_format=self.out_format.get(),
                chunk_chars=int(self.chunk_chars.get()),
                model=self.model.get(),
                api_key=self.api_key.get() or None,
            )
            def on_chunk_start(idx: int, total: int):
                self._ui(lambda: self._preview.delete("1.0", "end"))
                self._ui(lambda: (
                    self.status.set(f"Parte {idx}/{total}"),
                    self._legend_fields["Total de partes"].configure(text=str(total)),
                    self._legend_fields["Modelo"].configure(text=self.model.get()),
                    self._legend_fields["Caracteres por chunk"].configure(text=str(int(self.chunk_chars.get())))
                ))
            def on_token(tok: str):
                if self._cancel.is_set():
                    return
                self._ui(lambda t=tok: self._append_preview(t))
            def on_progress(stats: ProgressStats):
                prog = stats.idx / stats.total
                self._ui(lambda: (
                    self.progress.set(prog),
                    self._pb.set(prog),
                    self._legend_fields["Tempo decorrido"].configure(text=f"{int(stats.elapsed)} s"),
                    self._legend_fields["Tempo estimado (ETA)"].configure(text=f"{int(stats.eta)} s"),
                    self._legend_fields["Média por parte"].configure(text=f"{stats.avg_per_part:.1f} s"),
                    self._legend_fields["Velocidade (partes por minuto)"].configure(text=f"{stats.speed_parts_per_min:.2f}")
                ))
            out_path = run_translation(cfg, on_chunk_start=on_chunk_start, on_token=on_token, on_progress=on_progress, should_cancel=lambda: self._cancel.is_set())
            if not out_path:
                self._ui(lambda: self.status.set("Cancelado"))
                return
            self._ui(lambda: self.status.set(f"Concluído • {out_path}"))
            self._ui(lambda: messagebox.showinfo("Concluído", f"Arquivo salvo em:\n{out_path}"))
        except Exception as e:
            self._notify_error(str(e))
        finally:
            self._ui(lambda: self._start_btn.configure(state="normal"))
            self._ui(lambda: self._cancel_btn.configure(state="disabled"))
            self._running = False
            self._stop_activity = True

    def _ui(self, fn):
        try:
            self.after(0, fn)
        except Exception:
            pass

    def _notify_error(self, msg: str):
        self._ui(lambda: (self.status.set(f"Erro: {msg}"), messagebox.showerror("Erro", msg), self._start_btn.configure(state="normal"), self._cancel_btn.configure(state="disabled")))

    def cancel(self):
        if getattr(self, "_running", False):
            self._cancel.set()
            self.status.set("Cancelando...")

    def _animate_activity(self):
        self._stop_activity = False
        def tick(val=0.0, step=0.03):
            if self._stop_activity:
                return
            val += step
            if val > 1.0:
                val = 0.0
            try:
                self._activity.set(val)
            except Exception:
                pass
            self.after(50, lambda: tick(val, step))
        tick()

    def _append_preview(self, text: str):
        try:
            self._preview.insert("end", text)
            self._preview.see("end")
            current = self._preview.get("1.0", "end-1c")
            if len(current) >= self._preview_max:
                self._preview.delete("1.0", "end")
        except Exception:
            pass

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
