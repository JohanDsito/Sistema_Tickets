#tkinter fue la libreria escogida para realizar la interfaz grafica e interactiva de este programa
#datetime es la libreria encargada de manejar el tiempo de espera, hasta establecer que un boleta ha expirado
# ninguna de las 2 librerias requiere una instalacion previa ya que forman parte del paquete estandar de python

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta

# clase que gestiona la compra, la cancelación y la validación de los boletos, junto con la lista de espera y el historial de las cancelaciones

class TicketSystem:
    def __init__(self, total_tickets):
        self.total_tickets = total_tickets
        self.available_tickets = total_tickets
        self.tickets = {}
        self.waitlist = []
        self.history = []
        self.ticket_queue = []
        self.ref_expiry = timedelta(minutes=1) 
        self.undo_stack = []  

    #genera para cada compra un numero de refencia 

    def generate_reference(self):
        return f"Ticket{len(self.tickets) + 1:04d}"
    
    # intenta comprar un boleto si hay boletos disponibles, genera una referencia para el boleto y lo registra
    # si no hay boletos el usuario se añade a la lista de espera
    def buy_ticket(self, user):
        if self.available_tickets > 0:
            ref = self.generate_reference()
            self.tickets[ref] = {'user': user, 'valid': False, 'timestamp': datetime.now()}
            self.available_tickets -= 1
            return f"Boleto comprado el numero de referencia es: {ref}"
        else:
            if user not in self.waitlist:
                self.waitlist.append(user)  
            return "No hay boletos disponibles. Has sido añadido a la lista de espera"
        
    # cancela un boleto dado su numero de referencia devolviendo el boleto a estar otra vez disponible y registrando la cancelacion
    def cancel_ticket(self, ref):
        if ref in self.tickets:
            ticket = self.tickets.pop(ref)
            self.available_tickets += 1
            self.history.append((ref, ticket['user'], 'Cancelado'))
            self.undo_stack.append(('cancel', ref, ticket['user']))  
            return f"Boleto {ref} cancelado."
        else:
            return "Numero de referencia no encontrado"

    def validate_ticket(self, ref):
        if ref in self.tickets:
            ticket = self.tickets[ref]
            if ticket['valid']:
                return "Boleto ya validado."
            else:
                if datetime.now() - ticket['timestamp'] < self.ref_expiry:
                    ticket['valid'] = True
                    return "Boleto validado exitosamente"
                else:
                    del self.tickets[ref]
                    return "El boleto ha expirado"
        else:
            return "Numero de referencia no encontrado"

    def view_waitlist(self):
        if not self.waitlist:
            return "No hay usuarios en la lista de espera"
        return "\n".join([f"Usuario: {user}" for user in self.waitlist])


    def view_history(self):
        if not self.history:
            return "No hay boletos cancelados."
        return "\n".join([f"{ref} - Usuario: {user} - Estado: {status}" for ref, user, status in self.history])

    def view_users_tickets(self):
        user_tickets = {}
        for ref, info in self.tickets.items():
            if info['user'] not in user_tickets:
                user_tickets[info['user']] = []
            user_tickets[info['user']].append({'ref': ref, 'valid': info['valid']})

        result = ""
        for user, tickets in user_tickets.items():
            result += f"{user}:\n"
            for ticket in tickets:
                status = "Válido" if ticket['valid'] else "No válido"
                result += f"  - {ticket['ref']}: {status}\n"
        return result if result else "No hay usuarios con boletos."
    
# guarda las acciones recientes en la pila `undo_stack` para que se pueda deshacer la ultima accion de compra o cancelacion
    def undo_last_action(self):
        if not self.undo_stack:
            return "No hay acciones para deshacer."
        
        action = self.undo_stack.pop()
        if action[0] == 'buy':
            ref, user = action[1], action[2]
            if ref in self.tickets:
                return "El boleto ya fue utilizado o cancelado."
            self.tickets[ref] = {'user': user, 'valid': False, 'timestamp': datetime.now()}
            self.available_tickets -= 1
            return f"Accion deshecha: Boleto {ref} comprado nuevamente."

        elif action[0] == 'cancel':
            ref, user = action[1], action[2]
            if ref in self.tickets:
                return "El boleto ya ha sido validado."
            self.tickets[ref] = {'user': user, 'valid': False, 'timestamp': datetime.now()}
            self.available_tickets -= 1
            self.history = [entry for entry in self.history if entry[0] != ref]
            return f"Accion deshecha: Boleto {ref} en uso nuevamente."
        
        return "No se pudo deshacer la acción."

    def get_available_tickets(self):
        return self.available_tickets
    
# Interfaz grafica para interactuar con el sistema de boletos, permitiendo comprar, cancelar y validar boletos
# ademas de ver la lista de espera y el historial
class TicketInterfaz:
    def __init__(self, root, ticket_system):
        self.ticket_system = ticket_system
        self.root = root
        self.root.title("Sistema de Tickets para Evento")
        self.root.geometry("750x400")
        self.root.configure(bg="LightSkyBlue2")
        self.create_widgets()

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 20), padding=12)
        style.configure("TLabel", font=("Helvetica", 12), background="#f0f0f0")
        style.configure("TEntry", font=("Helvetica", 12))

        # titulo
        title_label = tk.Label(self.root, text="Sistema de Tickets para Evento", font=("Helvetica", 16))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # etiquetas y entradas de texto
        ttk.Label(self.root, text="Usuario:", font=("Helvetica", 12)).grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        self.user_entry = ttk.Entry(self.root, font=("Helvetica", 12))
        self.user_entry.grid(row=1, column=1, padx=10, pady=5, columnspan=2, sticky=tk.EW)

        ttk.Label(self.root, text="Numero de referencia:", font=("Helvetica", 12)).grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        self.ref_entry = ttk.Entry(self.root, font=("Helvetica", 12))
        self.ref_entry.grid(row=2, column=1, padx=10, pady=5, columnspan=2, sticky=tk.EW)

        # botones
        tk.Button(self.root, text="Comprar Boleto", command=self.buy_ticket, bg="#3cff25", fg="black").grid(row=3, column=0, padx=10, pady=5)
        tk.Button(self.root, text="Cancelar Boleto", command=self.cancel_ticket, bg="#ff0000", fg="white").grid(row=3, column=1, padx=10, pady=5)
        tk.Button(self.root, text="Validar Boleto", command=self.validate_ticket, bg="#2196F3", fg="white").grid(row=3, column=2, padx=10, pady=5)
        tk.Button(self.root, text="Ver Lista de Espera", command=self.view_waitlist).grid(row=4, column=0, padx=10, pady=5)
        tk.Button(self.root, text="Ver Usuarios con Boletos", command=self.view_users_tickets).grid(row=5, column=0, padx=10, pady=5)
        tk.Button(self.root, text="Ver Historial de Cancelacion", command=self.view_history).grid(row=4, column=1, padx=10, pady=5)
        tk.Button(self.root, text="Limpiar", command=self.clear_entries).grid(row=4, column=2, padx=10, pady=5)
        tk.Button(self.root, text="Deshacer Ultima Accion", command=self.undo_last_action, bg="#f0f0f0").grid(row=5, column=1, padx=10, pady=5)

        # etiquetas de Informacion
        self.output_label = tk.Label(self.root, text="", font=("Helvetica", 12), bg="#f0f0f0")
        self.output_label.grid(row=8, column=0, columnspan=3, pady=10)

        # etiqueta para mostrar el nuimero de referencia
        self.ref_display = tk.Entry(self.root, font=("Helvetica", 12), state='readonly')
        self.ref_display.grid(row=9, column=0, columnspan=3, padx=10, pady=5, sticky=tk.EW)

        # etiqueta para mostrar los boletos disponibles
        self.available_tickets_label = tk.Label(self.root, text=f"Boletos disponibles: {self.ticket_system.get_available_tickets()}", font=("Helvetica", 12), bg="#f0f0f0")
        self.available_tickets_label.grid(row=7, column=0, columnspan=3, pady=10)

    def buy_ticket(self):
        username = self.user_entry.get()
        if username:
            ref = self.ticket_system.buy_ticket(username)
            self.ref_display.config(state='normal')
            self.ref_display.delete(0, tk.END)
            self.ref_display.insert(0, ref)
            self.ref_display.config(state='readonly')
            self.output_label.config(text=f"Boleto comprado. Numero de referencia: {ref}")
            self.update_available_tickets()
        else:
            self.output_label.config(text="Por favor ingrese un nombre de usuario.")

    def cancel_ticket(self):
        ref = self.ref_entry.get()
        if ref:
            message = self.ticket_system.cancel_ticket(ref)
            self.output_label.config(text=message)
            self.update_available_tickets()
        else:
            self.output_label.config(text="Por favor ingrese un número de referencia.")

    def validate_ticket(self):
        ref = self.ref_entry.get()
        if ref:
            message = self.ticket_system.validate_ticket(ref)
            self.output_label.config(text=message)
        else:
            self.output_label.config(text="Por favor ingrese un número de referencia.")

    def view_users_tickets(self):
        result = self.ticket_system.view_users_tickets()
        self.output_label.config(text=result)

    def view_waitlist(self):
        message = self.ticket_system.view_waitlist()
        self.output_label.config(text=message)

    def view_history(self):
        message = self.ticket_system.view_history()
        self.output_label.config(text=message)

    def clear_entries(self):
        self.user_entry.delete(0, tk.END)
        self.ref_entry.delete(0, tk.END)
        self.output_label.config(text="")
        self.ref_display.config(state='normal')
        self.ref_display.delete(0, tk.END)
        self.ref_display.config(state='readonly')

    def update_available_tickets(self):
        self.available_tickets_label.config(text=f"Boletos disponibles: {self.ticket_system.get_available_tickets()}")

    def undo_last_action(self):
        message = self.ticket_system.undo_last_action()
        self.output_label.config(text=message)
        self.update_available_tickets()

#iniciador 
if __name__ == "__main__":
    root = tk.Tk()
    ticket_system = TicketSystem(total_tickets=20) # establecer la cantidad total de boleos disponibles
    app = TicketInterfaz(root, ticket_system)
    root.mainloop()
