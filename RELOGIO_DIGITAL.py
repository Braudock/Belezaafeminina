import tkinter as tk
from tkinter import ttk, messagebox
import time
from datetime import datetime, timedelta
import locale
from playsound import playsound
import threading

# Configura idioma para português
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, 'pt_BR')

# Variáveis globais
alarm_list = []  # Lista de alarmes
tema_escuro = None
som_alarme = "alarme.mp3"  # Arquivo de som
alarme_tocando = None  # Hora do alarme tocando

# Janela principal
root = tk.Tk()
root.title("⏰ Relógio com Alarmes")
root.geometry("450x480")
root.minsize(350, 300)

style = ttk.Style()

# Frame principal
frame = ttk.Frame(root)
frame.pack(expand=True, fill="both", padx=10, pady=10)

label = ttk.Label(frame, text="", font=("Helvetica", 36))
label.pack(pady=(10, 5))

data_label = ttk.Label(frame, text="", font=("Helvetica", 14))
data_label.pack()

# Entrada de novo alarme
ttk.Label(frame, text="⏰ Novo Alarme (HH:MM):").pack(pady=(10, 2))
alarme_entry = ttk.Entry(frame, font=("Helvetica", 12), width=10, justify="center")
alarme_entry.pack()

# Lista de alarmes
lista_label = ttk.Label(frame, text="🔁 Alarmes Ativos:", font=("Helvetica", 10))
lista_label.pack(pady=(10, 0))

lista_alarm_frame = tk.Listbox(frame, height=5, font=("Helvetica", 11))
lista_alarm_frame.pack(pady=(0, 10), fill="x", padx=20)

# Soneca (aparece apenas durante o alarme)
btn_soneca = ttk.Button(frame, text="🔁 Soneca (5 min)", command=lambda: ativar_soneca())
btn_soneca.pack()
btn_soneca.pack_forget()

# Aplicar tema
def aplicar_tema(escuro: bool):
    global tema_escuro
    tema_escuro = escuro

    cor_bg = "black" if escuro else "white"
    cor_fg_hora = "#00FF7F" if escuro else "#1E90FF"
    cor_fg_data = "#FFD700" if escuro else "#FF8C00"

    root.configure(bg=cor_bg)
    style.configure("TLabel", background=cor_bg, foreground=cor_fg_hora)
    label.configure(background=cor_bg, foreground=cor_fg_hora)
    data_label.configure(background=cor_bg, foreground=cor_fg_data)
    lista_label.configure(background=cor_bg, foreground=cor_fg_data)

def alternar_tema():
    aplicar_tema(not tema_escuro)

btn_tema = ttk.Button(frame, text="🌗 Alternar Tema", command=alternar_tema)
btn_tema.pack()

# Adicionar alarme
def definir_alarme():
    hora = alarme_entry.get().strip()
    try:
        datetime.strptime(hora, '%H:%M')
        if hora not in alarm_list:
            alarm_list.append(hora)
            lista_alarm_frame.insert(tk.END, f"⏰ {hora}")
            alarme_entry.delete(0, tk.END)
        else:
            messagebox.showinfo("Alarme Existente", "Esse alarme já está ativo.")
    except ValueError:
        messagebox.showerror("Formato Inválido", "Use o formato HH:MM (24h)")

btn_alarme = ttk.Button(frame, text="➕ Adicionar Alarme", command=definir_alarme)
btn_alarme.pack(pady=(0, 10))

# Remover alarme selecionado
def remover_alarme():
    try:
        sel = lista_alarm_frame.curselection()
        if sel:
            idx = sel[0]
            hora = lista_alarm_frame.get(idx).replace("⏰ ", "")
            alarm_list.remove(hora)
            lista_alarm_frame.delete(idx)
    except:
        messagebox.showerror("Erro", "Não foi possível remover o alarme.")

btn_remover = ttk.Button(frame, text="⛔ Remover Alarme", command=remover_alarme)
btn_remover.pack()

# Tocar alarme
def tocar_alarme():
    try:
        threading.Thread(target=playsound, args=(som_alarme,), daemon=True).start()
    except:
        messagebox.showerror("Erro de Som", "Não foi possível tocar o som do alarme.")

# Ativar soneca (adiciona novo alarme +5min)
def ativar_soneca():
    global alarme_tocando
    if alarme_tocando:
        nova_hora = (datetime.strptime(alarme_tocando, '%H:%M') + timedelta(minutes=5)).strftime('%H:%M')
        if nova_hora not in alarm_list:
            alarm_list.append(nova_hora)
            lista_alarm_frame.insert(tk.END, f"⏰ {nova_hora}")
        alarme_tocando = None
        btn_soneca.pack_forget()

# Atualização do relógio
def tick():
    global alarme_tocando
    agora = time.strftime('%H:%M:%S')
    hoje = datetime.now().strftime('%A, %d/%m/%Y')
    hora_curta = time.strftime('%H:%M')

    label.config(text=agora)
    data_label.config(text=hoje)

    # Verifica alarmes
    if hora_curta in alarm_list:
        alarm_list.remove(hora_curta)
        for i in range(lista_alarm_frame.size()):
            if lista_alarm_frame.get(i).endswith(hora_curta):
                lista_alarm_frame.delete(i)
                break
        alarme_tocando = hora_curta
        tocar_alarme()
        messagebox.showwarning("Alarme", f"⏰ Alarme tocando: {hora_curta}")
        btn_soneca.pack(pady=(5, 10))

    # Tema automático
    hora = datetime.now().hour
    if hora >= 18 or hora < 6:
        if tema_escuro is not True:
            aplicar_tema(True)
    else:
        if tema_escuro is not False:
            aplicar_tema(False)

    root.after(1000, tick)

tick()
root.mainloop()
