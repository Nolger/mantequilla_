# app/models/menu_model.py
import datetime
import uuid # Para generar IDs
import random
import string
import traceback

# Ajusta las rutas de importación según tu estructura de proyecto.
try:
    from app import db # Si db.py está en app/
except ImportError:
    try:
        from .. import db
    except ImportError:
        try:
            import db # Si está en el mismo nivel o app está en PYTHONPATH
        except ImportError:
            print("Error CRÍTICO: No se pudo importar el módulo db.py en menu_model.py.")
            db = None

def generate_dish_id(length=10):
    """Genera un ID único para un nuevo plato. Ejemplo: PLATO-AB12C"""
    chars_to_generate = length - 6 # Para "PLATO-"
    if chars_to_generate < 1: chars_to_generate = 4
    characters = string.ascii_uppercase + string.digits
    random_id_part = ''.join(random.choice(characters) for _ in range(chars_to_generate))
    return f"PLATO-{random_id_part}"

def create_dish(dish_data_dict):
    """
    Crea un nuevo plato en el menú. El ID del plato se genera automáticamente.
    Args:
        dish_data_dict (dict): Datos del plato. Debe incluir:
            'nombre_plato', 'categoria', 'precio_venta'.
            Opcional: 'descripcion', 'tiempo_preparacion_min', 'activo', 'imagen_url'.
    Returns:
        str: El ID del plato creado, o None si falla.
    """
    if not db:
        print("Error: Módulo db no disponible en menu_model.")
        return None
    
    # Campos requeridos desde la vista (el ID se genera aquí)
    required_fields_from_view = ['nombre_plato', 'categoria', 'precio_venta']
    for field in required_fields_from_view:
        if field not in dish_data_dict or dish_data_dict[field] is None or str(dish_data_dict[field]).strip() == "":
            # Considerar precio_venta = 0 como válido si es necesario
            if field == 'precio_venta' and isinstance(dish_data_dict.get(field), (int, float)) and dish_data_dict.get(field) >= 0:
                pass # Precio 0 es válido
            else:
                print(f"Error de validación en menu_model: Falta el campo '{field}' o está vacío para el plato.")
                return None
    
    generated_id = generate_dish_id()
    print(f"INFO: ID de plato generado para nuevo plato: {generated_id}")

    query_string = """
    INSERT INTO Plato (id_plato, nombre_plato, descripcion, categoria, 
                       tiempo_preparacion_min, activo, precio_venta, imagen_url)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        generated_id, # Usar el ID generado
        dish_data_dict['nombre_plato'],
        dish_data_dict.get('descripcion', ''),
        dish_data_dict['categoria'],
        dish_data_dict.get('tiempo_preparacion_min') if dish_data_dict.get('tiempo_preparacion_min', 0) > 0 else None,
        dish_data_dict.get('activo', True),
        dish_data_dict['precio_venta'],
        dish_data_dict.get('imagen_url')
    )
    
    try:
        result_db = db.execute_query(query_string, params)
        if result_db is not None: # Para INSERT, puede ser lastrowid o rowcount
            print(f"Plato '{generated_id}' ('{dish_data_dict['nombre_plato']}') creado exitosamente.")
            return generated_id # Devolver el ID generado
        else:
            print(f"No se pudo crear el plato '{dish_data_dict['nombre_plato']}'. db.execute_query devolvió None.")
            return None
    except Exception as e:
        print(f"Excepción al crear plato '{dish_data_dict.get('nombre_plato', 'Nombre Desconocido')}': {e}")
        traceback.print_exc()
        return None


def get_dish_by_id(dish_id_value):
    if not db:
        print("Error: Módulo db no disponible en menu_model.")
        return None
    if not dish_id_value: # No buscar si el ID es None o vacío
        return None
    query_string = "SELECT * FROM Plato WHERE id_plato = %s"
    return db.fetch_one(query_string, (dish_id_value,))

def get_all_dishes_list():
    if not db: return None
    query_string = "SELECT * FROM Plato ORDER BY categoria, nombre_plato"
    return db.fetch_all(query_string)

def get_active_dishes():
    if not db:
        print("Error: Módulo db no disponible en menu_model.")
        return None
    query_string = """
        SELECT id_plato, nombre_plato, precio_venta, categoria, descripcion, tiempo_preparacion_min, imagen_url
        FROM Plato 
        WHERE activo = TRUE 
        ORDER BY categoria, nombre_plato
    """ # Devolver más campos si son útiles para la vista de toma de comandas
    return db.fetch_all(query_string)

def update_dish_details(dish_id_value, data_to_update_dict):
    if not db: return None
    if not dish_id_value:
        print("Error en menu_model: Se requiere ID de plato para actualizar.")
        return None
    if not data_to_update_dict:
        print("Modelo: No se proporcionaron datos para actualizar el plato.")
        return 0

    allowed_fields = {'nombre_plato', 'descripcion', 'categoria', 
                      'tiempo_preparacion_min', 'activo', 'precio_venta', 'imagen_url'}
    
    set_clauses_list = []
    parameters_list = []

    for key, value in data_to_update_dict.items():
        if key in allowed_fields:
            # Manejar tiempo_preparacion_min para que sea NULL si es 0 o None
            if key == 'tiempo_preparacion_min' and (value is None or int(value) <= 0):
                current_value = None
            else:
                current_value = value
            
            set_clauses_list.append(f"`{key}` = %s")
            parameters_list.append(current_value)

    if not set_clauses_list:
        print("Modelo (menu): Ningún campo válido para actualizar fue proporcionado.")
        return 0

    query_string = f"UPDATE Plato SET {', '.join(set_clauses_list)} WHERE id_plato = %s"
    parameters_list.append(dish_id_value)
    
    try:
        return db.execute_query(query_string, tuple(parameters_list))
    except Exception as e:
        print(f"Excepción al actualizar plato '{dish_id_value}': {e}")
        traceback.print_exc()
        return None


def delete_dish_by_id(dish_id_value):
    if not db: return None
    if not dish_id_value:
        print("Error en menu_model: Se requiere ID de plato para eliminar.")
        return None
    # La restricción FK en Receta (ON DELETE CASCADE) debería eliminar las recetas asociadas.
    # La restricción FK en DetalleComanda (ON DELETE RESTRICT) impedirá borrar si está en una comanda.
    query_string = "DELETE FROM Plato WHERE id_plato = %s"
    return db.execute_query(query_string, (dish_id_value,))


# --- Ejemplo de uso y pruebas ---
if __name__ == '__main__':
    if not db:
        print("No se pueden ejecutar las pruebas del modelo de menú: módulo db no cargado.")
    else:
        print("Probando el Modelo de Menú (menu_model.py)...")

        # Prueba de generación de ID
        print(f"ID de plato generado de ejemplo: {generate_dish_id()}")

        test_dish_nombre = "Hamburguesa de Prueba AutoID"
        test_dish_id_creado = None

        # 1. Crear un nuevo plato (ID se autogenerará)
        print(f"\n--- Creando plato: {test_dish_nombre} ---")
        dish_data = {
            'nombre_plato': test_dish_nombre,
            'categoria': 'principal',
            'precio_venta': 13.50,
            'descripcion': 'Carne jugosa, queso cheddar, vegetales frescos.',
            'tiempo_preparacion_min': 12,
            'activo': True
        }
        test_dish_id_creado = create_dish(dish_data) # create_dish ahora devuelve el ID
        
        if test_dish_id_creado:
            print(f"Plato '{test_dish_nombre}' creado con ID: {test_dish_id_creado}.")
            created_dish = get_dish_by_id(test_dish_id_creado)
            print(f"Verificación: {created_dish}")
        else:
            print(f"Fallo al crear plato '{test_dish_nombre}'.")

        # 2. Listar todos los platos
        # ... (resto de tus pruebas existentes, adaptadas si es necesario) ...
        # ... Asegúrate de usar test_dish_id_creado para actualizar y eliminar ...

        if test_dish_id_creado: # Solo si se creó
            print(f"\n--- Actualizando plato: {test_dish_id_creado} ---")
            update_data = {
                'nombre_plato': f"{test_dish_nombre} DELUXE",
                'precio_venta': 15.00,
                'activo': False
            }
            update_count = update_dish_details(test_dish_id_creado, update_data)
            # ...

            print(f"\n--- Eliminando plato: {test_dish_id_creado} ---")
            delete_count = delete_dish_by_id(test_dish_id_creado)
            # ...

        print("\nPruebas del Modelo de Menú (CRUD) completadas.")