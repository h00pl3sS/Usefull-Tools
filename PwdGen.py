import random
import string
import tkinter as tk
from tkinter import messagebox
import pyperclip

def generar_contrasena():
    # Requisitos
    mayuscula = random.choice(string.ascii_uppercase)
    numeros = random.choices(string.digits, k=4)
    caracter_especial = random.choice("!@#$%^&*()_+-=;:,.<>?")
    restantes = random.choices(string.ascii_lowercase, k=3)

    # Combinar y mezclar
    contrasena_lista = [mayuscula] + numeros + [caracter_especial] + restantes
    random.shuffle(contrasena_lista)
    
    contrasena = ''.join(contrasena_lista)
    
    # Actualizar la interfaz
    entrada_pass.delete(0, tk.END)
    entrada_pass.insert(0, contrasena)

def copiar_al_portapapeles():
    contrasena = entrada_pass.get()
    if contrasena:
        pyperclip.copy(contrasena)
        messagebox.showinfo("Éxito", "¡Contraseña copiada al portapapeles!")
    else:
        messagebox.showwarning("Atención", "Primero genera una contraseña")

# Configuración de la ventana principal
ventana = tk.Tk()
ventana.title("Generador de Passwords")
ventana.geometry("350x200")
ventana.resizable(False, False)

# Elementos visuales (Widgets)
tk.Label(ventana, text="Tu contraseña segura:", font=("Arial", 10, "bold")).pack(pady=10)

entrada_pass = tk.Entry(ventana, font=("Courier", 12), width=20, justify='center')
entrada_pass.pack(pady=5)

btn_generar = tk.Button(ventana, text="Generar Nueva", command=generar_contrasena, bg="#4CAF50", fg="white")
btn_generar.pack(pady=5, fill='x', padx=50)

btn_copiar = tk.Button(ventana, text="Copiar al Portapapeles", command=copiar_al_portapapeles, bg="#2196F3", fg="white")
btn_copiar.pack(pady=5, fill='x', padx=50)

# Iniciar la aplicación
ventana.mainloop()