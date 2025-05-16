# app/views/cook_dashboard_view.py
import tkinter as tk
from tkinter import ttk, messagebox

# Importar modelos necesarios
try:
    from ..models import order_model, recipe_model, stock_model # stock_model es opcional aquí
except ImportError:
    try:
        from models import order_model, recipe_model, stock_model
    except ImportError:
        print("Error crítico: No se pudieron importar los modelos en CookDashboardView.")
        order_model = recipe_model = stock_model = None

class CookDashboardView(tk.Tk):
    def __init__(self, cook_user_info):
        super().__init__()

        if not order_model or not recipe_model: # stock_model es opcional
            self.withdraw()
            messagebox.showerror("Error Crítico de Módulo",
                                 "No se pudieron cargar modelos esenciales para el dashboard de Cocina.")
            self.destroy()
            return

        self.cook_user_info = cook_user_info
        self.title(f"Panel de Cocina - Restaurante (Cocinero: {self.cook_user_info.get('nombre', 'Cocinero')})")
        self.geometry("900x700")

        style = ttk.Style(self)
        if 'clam' in style.theme_names(): style.theme_use('clam')

        self.selected_dish_detail_id = None # Para el id_detalle_comanda del plato seleccionado
        self.selected_dish_id_for_recipe = None # Para el id_plato para ver receta

        self._create_main_widgets()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.load_pending_dishes()

    def _create_main_widgets(self):
        main_notebook = ttk.Notebook(self)
        main_notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # --- Pestaña: Pedidos para Cocina ---
        kitchen_orders_tab = ttk.Frame(main_notebook, padding="10")
        main_notebook.add(kitchen_orders_tab, text='Pedidos para Cocina')
        self._create_kitchen_orders_widgets(kitchen_orders_tab)

        # --- Pestaña: Consultar Recetas ---
        recipes_tab = ttk.Frame(main_notebook, padding="10")
        main_notebook.add(recipes_tab, text='Consultar Recetas')
        self._create_recipes_lookup_widgets(recipes_tab)
        
        # --- (Opcional) Pestaña: Alertas de Stock ---
        # ...

        # --- Botón de Cerrar Sesión ---
        logout_button_frame = ttk.Frame(self) # Frame para el botón
        logout_button_frame.pack(fill=tk.X, padx=10, pady=(0,10))
        logout_btn = ttk.Button(logout_button_frame, text="Cerrar Sesión", command=self._logout)
        logout_btn.pack(side=tk.RIGHT)


    def _create_kitchen_orders_widgets(self, parent_tab):
        # Frame para la lista de platos pendientes y acciones
        orders_panel = ttk.Frame(parent_tab)
        orders_panel.pack(expand=True, fill=tk.BOTH)

        # Treeview para mostrar los platos
        cols = ("id_detalle", "id_comanda", "plato_nombre", "cantidad", "estado_plato", "observaciones", "hora_pedido")
        self.pending_dishes_treeview = ttk.Treeview(orders_panel, columns=cols, show="headings", selectmode="browse", height=15)
        
        self.pending_dishes_treeview.heading("id_detalle", text="ID Detalle")
        self.pending_dishes_treeview.heading("id_comanda", text="Comanda")
        self.pending_dishes_treeview.heading("plato_nombre", text="Plato")
        self.pending_dishes_treeview.heading("cantidad", text="Cant.")
        self.pending_dishes_treeview.heading("estado_plato", text="Estado Actual")
        self.pending_dishes_treeview.heading("observaciones", text="Observaciones")
        self.pending_dishes_treeview.heading("hora_pedido", text="Hora Pedido")

        self.pending_dishes_treeview.column("id_detalle", width=70, anchor="center")
        self.pending_dishes_treeview.column("id_comanda", width=100, anchor="w")
        self.pending_dishes_treeview.column("plato_nombre", width=180, anchor="w")
        self.pending_dishes_treeview.column("cantidad", width=50, anchor="center")
        self.pending_dishes_treeview.column("estado_plato", width=120, anchor="w")
        self.pending_dishes_treeview.column("observaciones", width=200, anchor="w")
        self.pending_dishes_treeview.column("hora_pedido", width=120, anchor="w")

        tree_scroll = ttk.Scrollbar(orders_panel, orient=tk.VERTICAL, command=self.pending_dishes_treeview.yview)
        self.pending_dishes_treeview.configure(yscrollcommand=tree_scroll.set)
        
        self.pending_dishes_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.pending_dishes_treeview.bind("<<TreeviewSelect>>", self._on_dish_selected_for_status_update)

        # Frame para botones de acción
        action_buttons_frame = ttk.Frame(parent_tab, padding=(0,10))
        action_buttons_frame.pack(fill=tk.X)

        self.update_to_preparing_btn = ttk.Button(action_buttons_frame, text="Marcar EN PREPARACIÓN",
                                                  command=lambda: self._update_selected_dish_status('en preparacion'),
                                                  state=tk.DISABLED)
        self.update_to_preparing_btn.pack(side=tk.LEFT, padx=5)

        self.update_to_ready_btn = ttk.Button(action_buttons_frame, text="Marcar LISTO para Servir",
                                              command=lambda: self._update_selected_dish_status('listo'),
                                              state=tk.DISABLED)
        self.update_to_ready_btn.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = ttk.Button(action_buttons_frame, text="Refrescar Pedidos", command=self.load_pending_dishes)
        refresh_btn.pack(side=tk.RIGHT, padx=5)

    def _create_recipes_lookup_widgets(self, parent_tab):
        # Frame para la búsqueda y visualización de recetas
        recipe_panel = ttk.Frame(parent_tab)
        recipe_panel.pack(expand=True, fill=tk.BOTH)
        recipe_panel.columnconfigure(0, weight=1) # Para que el Text se expanda

        search_frame = ttk.Frame(recipe_panel, padding=(0,5))
        search_frame.pack(fill=tk.X)
        
        ttk.Label(search_frame, text="Buscar Plato por ID o Nombre:").pack(side=tk.LEFT, padx=5)
        self.recipe_search_var = tk.StringVar()
        self.recipe_search_entry = ttk.Entry(search_frame, textvariable=self.recipe_search_var, width=30)
        self.recipe_search_entry.pack(side=tk.LEFT, padx=5)
        # Podrías tener un botón de búsqueda o hacerla dinámica al escribir
        # O un Combobox con todos los platos para seleccionar
        
        # Por simplicidad, mostraremos la receta del plato seleccionado en la otra pestaña
        # O podríamos tener un Treeview de platos aquí también
        
        self.recipe_display_text = tk.Text(recipe_panel, height=20, width=80, wrap=tk.WORD, font=("Consolas", 10), state=tk.DISABLED)
        recipe_scroll = ttk.Scrollbar(recipe_panel, orient=tk.VERTICAL, command=self.recipe_display_text.yview)
        self.recipe_display_text.configure(yscrollcommand=recipe_scroll.set)
        
        self.recipe_display_text.pack(pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)
        recipe_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Botón para mostrar la receta del plato seleccionado en la pestaña de "Pedidos para Cocina"
        show_recipe_btn = ttk.Button(search_frame, text="Ver Receta del Plato Seleccionado (en Pedidos)", 
                                     command=self._show_recipe_for_selected_dish_from_orders)
        show_recipe_btn.pack(side=tk.LEFT, padx=10)


    def load_pending_dishes(self):
        if not order_model: return
        for item in self.pending_dishes_treeview.get_children():
            self.pending_dishes_treeview.delete(item)
        
        self.selected_dish_detail_id = None
        self.update_to_preparing_btn.config(state=tk.DISABLED)
        self.update_to_ready_btn.config(state=tk.DISABLED)

        # Esta función necesita ser creada en order_model.py
        # Debería devolver detalles de platos 'pendiente' o 'en preparacion'
        pending_items = order_model.get_dishes_for_kitchen_view() # <--- NUEVA FUNCIÓN EN EL MODELO
        
        if pending_items:
            for item in pending_items:
                hora_pedido_f = item.get('hora_pedido', '').strftime('%H:%M:%S (%d/%m)') if item.get('hora_pedido') else 'N/A'
                self.pending_dishes_treeview.insert("", tk.END, 
                    iid=item['id_detalle_comanda'], # Usar id_detalle_comanda como iid
                    values=(
                        item.get('id_detalle_comanda', ''),
                        item.get('id_comanda', ''),
                        item.get('nombre_plato', 'Desconocido'),
                        item.get('cantidad', 0),
                        item.get('estado_plato', 'pendiente'),
                        item.get('observaciones_plato', ''),
                        hora_pedido_f
                ))
        elif pending_items == []:
            # messagebox.showinfo("Cocina", "No hay platos pendientes en este momento.") # Puede ser molesto
            print("No hay platos pendientes para cocina.")
        else: # None indica error
            messagebox.showerror("Error", "No se pudieron cargar los platos para la cocina.")

    def _on_dish_selected_for_status_update(self, event=None):
        selected = self.pending_dishes_treeview.selection()
        if selected:
            item_data = self.pending_dishes_treeview.item(selected[0])
            self.selected_dish_detail_id = item_data['values'][0] # id_detalle_comanda
            current_status = item_data['values'][4] # estado_plato
            
            # Guardar id_plato para la función de ver receta
            # Necesitaríamos que get_dishes_for_kitchen_view() también devuelva id_plato
            # Supongamos que lo hace y está en la posición 7 (o un índice dedicado)
            # Por ahora, lo dejaremos así y lo mejoraremos si es necesario.
            # Para obtener el id_plato, podríamos hacer una consulta adicional si no viene en 'values'
            # o modificar get_dishes_for_kitchen_view.

            if current_status == 'pendiente':
                self.update_to_preparing_btn.config(state=tk.NORMAL)
                self.update_to_ready_btn.config(state=tk.DISABLED)
            elif current_status == 'en preparacion':
                self.update_to_preparing_btn.config(state=tk.DISABLED)
                self.update_to_ready_btn.config(state=tk.NORMAL)
            else: # listo, entregado, cancelado
                self.update_to_preparing_btn.config(state=tk.DISABLED)
                self.update_to_ready_btn.config(state=tk.DISABLED)
        else:
            self.selected_dish_detail_id = None
            self.update_to_preparing_btn.config(state=tk.DISABLED)
            self.update_to_ready_btn.config(state=tk.DISABLED)

    def _update_selected_dish_status(self, new_status):
        if not self.selected_dish_detail_id or not order_model:
            messagebox.showwarning("Sin Selección", "Seleccione un plato de la lista primero.")
            return

        if messagebox.askyesno("Confirmar Cambio de Estado", 
                               f"¿Marcar el plato seleccionado como '{new_status.upper()}'?"):
            result = order_model.update_order_item_status(self.selected_dish_detail_id, new_status)
            if result is not None and result > 0:
                messagebox.showinfo("Éxito", f"Estado del plato actualizado a '{new_status}'.")
                self.load_pending_dishes() # Recargar la lista
            else:
                messagebox.showerror("Error", "No se pudo actualizar el estado del plato.")
                
    def _show_recipe_for_selected_dish_from_orders(self):
        selected_items = self.pending_dishes_treeview.selection()
        if not selected_items:
            messagebox.showwarning("Sin Selección", "Seleccione un plato en la pestaña 'Pedidos para Cocina' para ver su receta.")
            return

        item_values = self.pending_dishes_treeview.item(selected_items[0], "values")
        # Necesitamos el id_plato. Asumimos que get_dishes_for_kitchen_view fue modificado para devolverlo.
        # Si no, tendríamos que hacer una consulta a DetalleComanda para obtener el id_plato
        # usando el id_detalle_comanda (item_values[0]).

        # SIMULACIÓN: Vamos a buscar el id_plato desde el nombre del plato por ahora.
        # ESTO NO ES IDEAL Y DEBERÍA MEJORARSE obteniendo el id_plato directamente.
        dish_name_for_recipe = item_values[2] # Nombre del plato
        
        # Búsqueda simple de id_plato por nombre (esto requiere que los nombres de plato sean únicos)
        # En un sistema real, es mejor tener el ID.
        found_dish_id = None
        if recipe_model: # Usamos recipe_model o menu_model para buscar
            # Esto es ineficiente, idealmente ya tendrías el id_plato
            all_dishes_temp = order_model.db.fetch_all("SELECT id_plato, nombre_plato FROM Plato WHERE nombre_plato = %s", (dish_name_for_recipe,))
            if all_dishes_temp:
                found_dish_id = all_dishes_temp[0]['id_plato']
        
        if not found_dish_id:
            messagebox.showerror("Error Receta", f"No se pudo determinar el ID del plato '{dish_name_for_recipe}' para buscar su receta.")
            return

        self.display_recipe(found_dish_id, dish_name_for_recipe)


    def display_recipe(self, dish_id, dish_name):
        if not recipe_model: return
        self.recipe_display_text.config(state=tk.NORMAL)
        self.recipe_display_text.delete("1.0", tk.END)

        recipe_items = recipe_model.get_recipe_for_dish(dish_id)
        
        display_str = f"--- RECETA PARA: {dish_name.upper()} (ID: {dish_id}) ---\n\n"
        if recipe_items:
            for item in recipe_items:
                display_str += (
                    f"Ingrediente: {item.get('nombre_ingrediente', 'N/A')} (ID: {item.get('id_ingrediente')})\n"
                    f"Cantidad:    {item.get('cantidad_necesaria')} {item.get('unidad_medida_receta')}\n"
                    f"Instrucción: {item.get('instrucciones_paso', 'Ninguna')}\n"
                    f"--------------------------------------------------\n"
                )
        elif recipe_items == []:
            display_str += "Este plato no tiene una receta definida en el sistema."
        else: # None
            display_str += "Error al cargar la receta para este plato."
            
        self.recipe_display_text.insert("1.0", display_str)
        self.recipe_display_text.config(state=tk.DISABLED)


    def _logout(self):
        if messagebox.askokcancel("Cerrar Sesión", "¿Está seguro de que desea cerrar la sesión?"):
            self.destroy()
            # main_app.py se encargará de volver al login

    def _on_closing(self):
        if messagebox.askokcancel("Salir", "¿Está seguro de que desea salir de la aplicación?"):
            self.destroy()


# Para probar esta vista de forma aislada
if __name__ == '__main__':
    if not order_model or not recipe_model:
        root_error = tk.Tk()
        root_error.withdraw()
        messagebox.showerror("Error Crítico", "No se pueden cargar los modelos para probar CookDashboardView.")
        root_error.destroy()
    else:
        # Simular información del cocinero logueado
        test_cook_info = {
            "id_empleado": "COCINERO01", # Asegúrate que este empleado exista y tenga rol 'cocinero'
            "nombre": "Chef",
            "apellido": "Principal",
            "rol": "cocinero"
        }
        root = tk.Tk()
        root.title("Prueba Dashboard Cocina")
        
        # Crear algunos datos de prueba para que se muestren platos
        # (esto se haría en un script de setup de pruebas más completo)
        print("Asegúrate de tener comandas con platos en estado 'pendiente' o 'en preparacion' para verlos aquí.")

        cook_dashboard = CookDashboardView(root, test_cook_info)
        cook_dashboard.pack(expand=True, fill=tk.BOTH)
        root.mainloop()