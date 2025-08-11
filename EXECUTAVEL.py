import tkinter as tk
from tkinter import filedialog
import datetime
import threading
import time
import subprocess

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Atualizador On Page - Mercado Livre")
        self.root.geometry("600x500")
        self.running = False
        self.script_path = ""

        # Frame amarelo superior
        top_frame = tk.Frame(root, bg="yellow")
        top_frame.pack(fill=tk.X)

        self.title_label = tk.Label(top_frame, text="Painel de Atualização On Page", 
                                    font=("Arial", 15, "bold"), bg="yellow")
        self.title_label.pack(pady=10)

        self.clock_label = tk.Label(top_frame, font=("Arial", 12, "bold"), fg="yellow", bg="black")
        self.clock_label.pack(side=tk.RIGHT, padx=10)
        self.update_clock()

        # Frame principal para botões e text area
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)

        # Botão iniciar
        self.start_button = tk.Button(btn_frame, text="▶ Iniciar", bg="green", fg="white",
                                      font=("Arial", 12, "bold"), width=15, height=2,
                                      command=self.start_loop)
        self.start_button.grid(row=0, column=0, padx=10)

        # Botão parar
        self.stop_button = tk.Button(btn_frame, text="■ Parar", bg="red", fg="white",
                                     font=("Arial", 12, "bold"), width=15, height=2,
                                     command=self.stop_loop)
        self.stop_button.grid(row=0, column=1, padx=10)

        # Área de texto com scroll para logs
        self.log = tk.Text(root, height=15, width=70, font=("Courier", 10))
        self.log.pack(padx=10, pady=10)

        # Adicionando rolagem manualmente
        scrollbar = tk.Scrollbar(self.log)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log.yview)

        # Botão para selecionar script
        self.select_button = tk.Button(root, text="Selecionar Script .py",
                                       font=("Arial", 10), command=self.select_script)
        self.select_button.pack()

    def update_clock(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.clock_label.config(text=now)
        self.root.after(1000, self.update_clock)

    def write_log(self, msg):
        self.log.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log.see(tk.END)  # Garante que o texto mais recente apareça

    def select_script(self):
        path = filedialog.askopenfilename(filetypes=[("Python Scripts", "*.py")])
        if path:
            self.script_path = path
            self.write_log(f"Script selecionado: {path}")

    def start_loop(self):
        if not self.script_path:
            self.write_log("⚠️ Nenhum script selecionado.")
            return
        if not self.running:
            self.running = True
            self.write_log("Iniciando execução a cada 5 minutos.")
            threading.Thread(target=self.loop_execution, daemon=True).start()

    def stop_loop(self):
        if self.running:
            self.running = False
            self.write_log("Execução interrompida.")

    def loop_execution(self):
        while self.running:
            self.write_log("Executando script...")
            try:
                result = subprocess.run(["python", self.script_path], capture_output=True, text=True)
                self.write_log(result.stdout.strip())
                if result.stderr:
                    self.write_log(f"ERRO: {result.stderr.strip()}")
            except Exception as e:
                self.write_log(f"Erro: {e}")

            # Espera 5 minutos (300 segundos)
            for _ in range(300):
                if not self.running:
                    break
                time.sleep(1)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
