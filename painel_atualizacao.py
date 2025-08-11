import sys
import threading
import subprocess
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from datetime import datetime
import time
import os
import multiprocessing  # IMPORTANTE para evitar duplicação

class PainelAtualizacaoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Atualizador")
        self.root.geometry("650x600")
        self.root.resizable(False, False)
        
        # Cores e fontes
        self.COR_FUNDO = "#f0f0f0"
        self.COR_HEADER = "#ffeb3b"
        self.COR_HEADER_TEXTO = "#000000"
        self.COR_LOG_FUNDO = "#ffffff"
        self.COR_LOG_TEXTO = "#000000"
        self.COR_BOTAO_START = "#4caf50"
        self.COR_BOTAO_STOP = "#f44336"
        self.COR_BOTAO_CLOSE = "#ff9800"
        self.COR_BOTAO_TEXTO = "#ffffff"
        self.FONTE_TITULO = ("Helvetica", 16, "bold")
        self.FONTE_DATA = ("Helvetica", 12, "bold")
        self.FONTE_BOTAO = ("Helvetica", 12, "bold")
        self.FONTE_LABEL = ("Helvetica", 10)
        self.FONTE_LOG = ("Consolas", 10)

        self.root.configure(bg=self.COR_FUNDO)

        # Estados
        self.script_path = None
        self._loop_thread = None
        self._stop_event = threading.Event()
        self.active_process = None

        self._criar_widgets()
        self._update_time()

    def _criar_widgets(self):
        header = tk.Frame(self.root, bg=self.COR_HEADER, height=50)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        tk.Label(header, text="Painel de Atualização", bg=self.COR_HEADER,
                 fg=self.COR_HEADER_TEXTO, font=self.FONTE_TITULO).place(relx=0.03, rely=0.5, anchor='w')
        self.time_label = tk.Label(header, text="", bg=self.COR_HEADER, fg=self.COR_HEADER_TEXTO, font=self.FONTE_DATA)
        self.time_label.place(relx=0.97, rely=0.5, anchor='e')

        config_frame = tk.Frame(self.root, bg=self.COR_FUNDO, pady=10)
        config_frame.pack(fill=tk.X, padx=20)
        tk.Button(config_frame, text="Selecionar Script (.py)", command=self._selecionar_script,
                  font=self.FONTE_LABEL).grid(row=0, column=0, sticky='w', pady=(0, 5))
        self.script_label = tk.Label(config_frame, text="Nenhum script selecionado", font=self.FONTE_LABEL,
                                     bg=self.COR_FUNDO, fg="#555")
        self.script_label.grid(row=1, column=0, columnspan=2, sticky='w')
        tk.Label(config_frame, text="Intervalo (minutos):", font=self.FONTE_LABEL,
                 bg=self.COR_FUNDO).grid(row=2, column=0, sticky='w', pady=(10, 0))
        self.interval_entry = tk.Entry(config_frame, width=10, font=self.FONTE_LABEL)
        self.interval_entry.grid(row=2, column=1, sticky='w', pady=(10, 0))
        self.interval_entry.insert(0, "5")

        btn_frame = tk.Frame(self.root, bg=self.COR_FUNDO)
        btn_frame.pack(pady=15)

        self.start_btn = tk.Button(btn_frame, text="Iniciar Loop", command=self.start_loop, width=12, height=2,
                                   bg=self.COR_BOTAO_START, fg=self.COR_BOTAO_TEXTO, font=self.FONTE_BOTAO,
                                   relief=tk.RAISED, borderwidth=2, cursor="hand2")
        self.start_btn.grid(row=0, column=0, padx=10)

        self.stop_btn = tk.Button(btn_frame, text="Parar Loop", command=self.stop_loop, width=12, height=2,
                                  bg=self.COR_BOTAO_STOP, fg=self.COR_BOTAO_TEXTO, font=self.FONTE_BOTAO,
                                  relief=tk.RAISED, borderwidth=2, state=tk.DISABLED, cursor="hand2")
        self.stop_btn.grid(row=0, column=1, padx=10)

        self.close_script_btn = tk.Button(btn_frame, text="Fechar Script", command=self.close_external_script, width=12, height=2,
                                          bg=self.COR_BOTAO_CLOSE, fg=self.COR_BOTAO_TEXTO, font=self.FONTE_BOTAO,
                                          relief=tk.RAISED, borderwidth=2, state=tk.DISABLED, cursor="hand2")
        self.close_script_btn.grid(row=0, column=2, padx=10)

        self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, font=self.FONTE_LOG,
                                                   bg=self.COR_LOG_FUNDO, fg=self.COR_LOG_TEXTO,
                                                   relief=tk.SOLID, bd=1)
        self.text_area.pack(padx=20, pady=(0, 20), fill=tk.BOTH, expand=True)
        self.text_area.config(state=tk.DISABLED)

    def _selecionar_script(self):
        path = filedialog.askopenfilename(title="Selecione o script Python", filetypes=[("Python files", "*.py")])
        if path:
            if os.path.abspath(path) == os.path.abspath(sys.argv[0]):
                messagebox.showerror("Erro", "Você não pode selecionar o próprio painel como script.")
                return
            self.script_path = path
            self.script_label.config(text=f"Script: {os.path.basename(path)}")
            self._log(f"Script selecionado: {path}")

    def _update_time(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=now)
        self.root.after(1000, self._update_time)

    def _run_script(self):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self._log(f"[{timestamp}] 🚀 Tentando executar {os.path.basename(self.script_path)}...")

        self.close_external_script()

        try:
            self.active_process = subprocess.Popen([sys.executable, self.script_path])
            self._log(f"[{timestamp}] ✅ Script iniciado como um novo processo (PID: {self.active_process.pid}).")
            self.close_script_btn.config(state=tk.NORMAL)
        except Exception as exc:
            self._log(f"❌ Falha crítica ao iniciar o processo: {exc}")
            self.active_process = None

    def close_external_script(self):
        if self.active_process and self.active_process.poll() is None:
            self._log(f"▶️ Tentando fechar o script externo (PID: {self.active_process.pid})...")
            self.active_process.terminate()
            self.active_process = None
            self.close_script_btn.config(state=tk.DISABLED)
            self._log("✅ Sinal de término enviado ao script.")
            return True
        return False

    def _log(self, msg):
        def append_message():
            self.text_area.config(state=tk.NORMAL)
            self.text_area.insert(tk.END, msg + "\n")
            self.text_area.see(tk.END)
            self.text_area.config(state=tk.DISABLED)
        self.root.after(0, append_message)

    def _loop(self, intervalo_segundos):
        while not self._stop_event.is_set():
            self._run_script()
            self._log(f"--- Próxima execução em {int(intervalo_segundos / 60)} minutos ---\n")
            if self._stop_event.wait(intervalo_segundos):
                break
        self._log(f"[{datetime.now().strftime('%H:%M:%S')}] 🛑 Loop interrompido pelo usuário.")
        self.root.after(0, self._reset_ui_states)

    def start_loop(self):
        if not self.script_path:
            messagebox.showerror("Erro", "Por favor, selecione um script para executar.")
            return

        try:
            intervalo_minutos = float(self.interval_entry.get())
            if intervalo_minutos <= 0: raise ValueError
            intervalo_segundos = intervalo_minutos * 60
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira um número válido e positivo para o intervalo.")
            return
        if self._loop_thread and self._loop_thread.is_alive():
            messagebox.showwarning("Aviso", "O loop de atualização já está em execução.")
            return

        self._stop_event.clear()
        self._loop_thread = threading.Thread(target=self._loop, args=(intervalo_segundos,), daemon=True)
        self._loop_thread.start()

        self._log(f"[{datetime.now().strftime('%H:%M:%S')}] ▶️ Loop iniciado.")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

    def stop_loop(self):
        if not self._loop_thread or not self._loop_thread.is_alive(): return
        self._stop_event.set()

    def _reset_ui_states(self):
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

# ✅ Função principal
def main():
    root = tk.Tk()
    app = PainelAtualizacaoApp(root)

    def on_closing():
        if messagebox.askokcancel("Sair", "Deseja fechar o atualizador?"):
            app.stop_loop()
            app.close_external_script()
            if app._loop_thread:
                app._loop_thread.join(timeout=1)
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

# ✅ Corrigido para pyinstaller
if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
