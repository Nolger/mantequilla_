import mysql.connector
from mysql.connector import errorcode
import os # Para leer variables de entorno (opcional)
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
# Intenta leer desde variables de entorno, o usa valores por defecto.
# Esto es útil si configuras estas variables en tu docker-compose.yml o archivo .env
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "admin_restaurante"),
    "password": os.getenv("DB_PASSWORD", "password123"),
    "database": os.getenv("DB_NAME", "restaurant_db")
}

def get_db_connection():
    """
    Establece y devuelve una conexión a la base de datos MySQL.
    Returns:
        mysql.connector.connection_cext.CMySQLConnection: Objeto de conexión o None si falla.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        # print("Conexión a la base de datos establecida exitosamente.")
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Error de acceso: Usuario o contraseña incorrectos.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print(f"La base de datos '{DB_CONFIG['database']}' no existe.")
        else:
            print(f"Error al conectar con la base de datos: {err}")
        return None

class DatabaseConnection:
    """
    Clase para manejar la conexión a la base de datos usando un context manager.
    Esto asegura que la conexión se cierre automáticamente.
    """
    def __init__(self):
        self.connection = None
        self.cursor = None

    def __enter__(self):
        self.connection = get_db_connection()
        if self.connection:
            self.cursor = self.connection.cursor(dictionary=True) # Devuelve filas como diccionarios
            return self.cursor
        else:
            # Si la conexión falla, __enter__ debería idealmente levantar una excepción
            # o devolver un objeto que indique el fallo para que el bloque 'with' no proceda.
            raise mysql.connector.Error("No se pudo establecer la conexión a la base de datos.")


    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            if exc_type is not None: # Si ocurrió una excepción dentro del bloque 'with'
                print(f"Ocurrió una excepción: {exc_val}. Haciendo rollback...")
                self.connection.rollback()
            else:
                self.connection.commit() # Confirmar cambios si no hubo excepciones
            
            if self.cursor:
                self.cursor.close()
            self.connection.close()
            # print("Conexión a la base de datos cerrada.")

# --- FUNCIONES DE OPERACIONES COMUNES ---

def fetch_all(query, params=None):
    """
    Ejecuta una consulta SELECT y devuelve todas las filas.
    Args:
        query (str): La consulta SQL a ejecutar.
        params (tuple, optional): Parámetros para la consulta SQL. Defaults to None.
    Returns:
        list: Una lista de diccionarios, donde cada diccionario representa una fila.
              None si ocurre un error.
    """
    results = None
    try:
        with DatabaseConnection() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error al ejecutar fetch_all: {err}")
        print(f"Consulta: {query}, Parámetros: {params}")
    return results

def fetch_one(query, params=None):
    """
    Ejecuta una consulta SELECT y devuelve una sola fila.
    Args:
        query (str): La consulta SQL a ejecutar.
        params (tuple, optional): Parámetros para la consulta SQL. Defaults to None.
    Returns:
        dict: Un diccionario que representa la fila, o None si no se encuentra o hay error.
    """
    result = None
    try:
        with DatabaseConnection() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Error al ejecutar fetch_one: {err}")
        print(f"Consulta: {query}, Parámetros: {params}")
    return result

def execute_query(query, params=None):
    """
    Ejecuta una consulta de modificación (INSERT, UPDATE, DELETE).
    Args:
        query (str): La consulta SQL a ejecutar.
        params (tuple, optional): Parámetros para la consulta SQL. Defaults to None.
    Returns:
        int: El ID de la última fila insertada (para INSERTs con AUTO_INCREMENT),
             o el número de filas afectadas por UPDATE/DELETE.
             None si ocurre un error.
    """
    result_id_or_count = None
    try:
        with DatabaseConnection() as cursor:
            cursor.execute(query, params)
            if cursor.lastrowid: # Para INSERTs
                result_id_or_count = cursor.lastrowid
            else: # Para UPDATE/DELETE
                result_id_or_count = cursor.rowcount
            # El commit se maneja en __exit__ de DatabaseConnection
    except mysql.connector.Error as err:
        print(f"Error al ejecutar execute_query: {err}")
        print(f"Consulta: {query}, Parámetros: {params}")
        # El rollback se maneja en __exit__ de DatabaseConnection
    return result_id_or_count


# --- EJEMPLOS DE USO (SOLO PARA PRUEBAS DIRECTAS DE ESTE ARCHIVO) ---
if __name__ == "__main__":
    print("Probando el módulo db.py...")

    # Ejemplo 1: Listar todos los proveedores
    print("\n--- Listando todos los Proveedores ---")
    proveedores = fetch_all("SELECT id_proveedor, nombre, correo FROM Proveedores")
    if proveedores is not None:
        if proveedores:
            for prov in proveedores:
                print(f"ID: {prov['id_proveedor']}, Nombre: {prov['nombre']}, Correo: {prov['correo']}")
        else:
            print("No se encontraron proveedores.")
    else:
        print("Error al listar proveedores.")

    # Ejemplo 2: Obtener un producto específico por ID (asumiendo que P001 existe)
    print("\n--- Obteniendo Producto con ID P001 ---")
    id_producto_buscar = "P001" # Cambia esto a un ID que exista en tu tabla Producto
    producto = fetch_one("SELECT * FROM Producto WHERE id_producto = %s", (id_producto_buscar,))
    if producto:
        print(f"Producto encontrado: {producto}")
    elif producto is None and not isinstance(producto, list): # fetch_one devuelve None si no hay error pero no hay resultado
        print(f"No se encontró el producto con ID {id_producto_buscar}.")
    else: # Si producto es None pero hubo un error, el mensaje de error ya se imprimió
        pass


    # Ejemplo 3: Insertar un nuevo empleado (¡CUIDADO CON LOS DATOS DE PRUEBA!)
    # Nota: Este es un ejemplo simple. En una aplicación real, el hash y salt se generarían de forma segura.
    print("\n--- Insertando un nuevo Empleado (ejemplo) ---")
    # Comprueba primero si el empleado ya existe para no causar error de clave duplicada
    empleado_existente = fetch_one("SELECT id_empleado FROM Empleados WHERE id_empleado = %s", ("EMP00_TEST",))
    if not empleado_existente:
        nuevo_empleado_query = """
        INSERT INTO Empleados (id_empleado, nombre, apellido, rol, hash_contrasena, salt, estado)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        # Datos de ejemplo (el hash y salt deberían ser generados de forma segura)
        empleado_params = ("EMP00_TEST", "Usuario", "DePrueba", "empleado", "hash_ejemplo_seguro", "salt_ejemplo_unico", "activo")
        
        last_id = execute_query(nuevo_empleado_query, empleado_params) # execute_query devuelve lastrowid para INSERT
        
        if last_id is not None: # Para INSERT, last_id será el ID autoincrementado si lo hay, o 0 si no.
                               # En este caso, id_empleado no es autoincrementado, así que lastrowid puede ser 0.
                               # Verificamos si rowcount (que también se puede obtener de cursor) es > 0.
                               # Sin embargo, la función execute_query ya devuelve el lastrowid o rowcount.
                               # Para INSERTs sin AUTO_INCREMENT, rowcount es más indicativo.
            # Para este caso específico, como id_empleado no es AUTO_INCREMENT, lastrowid no es tan útil.
            # Una mejor comprobación sería si la función no devolvió None.
             print(f"Empleado 'EMP00_TEST' insertado o ya existía (o error). Resultado de execute_query: {last_id}")
             # Para confirmar, podemos intentar buscarlo:
             empleado_insertado = fetch_one("SELECT * FROM Empleados WHERE id_empleado = %s", ("EMP00_TEST",))
             if empleado_insertado:
                 print(f"Empleado confirmado en DB: {empleado_insertado}")
             else:
                 print("El empleado no se pudo confirmar en la DB después del intento de inserción.")

        else:
            print("Error al insertar el empleado 'EMP00_TEST'.")
    else:
        print("El empleado 'EMP00_TEST' ya existe. No se intentó la inserción.")

    # Ejemplo 4: Actualizar el estado de un empleado
    print("\n--- Actualizando estado del Empleado EMP00_TEST ---")
    update_query = "UPDATE Empleados SET estado = %s WHERE id_empleado = %s"
    rows_affected = execute_query(update_query, ("inactivo", "EMP00_TEST"))
    if rows_affected is not None:
        print(f"Filas afectadas por la actualización: {rows_affected}")
        empleado_actualizado = fetch_one("SELECT id_empleado, estado FROM Empleados WHERE id_empleado = %s", ("EMP00_TEST",))
        if empleado_actualizado:
            print(f"Estado actual del empleado: {empleado_actualizado['estado']}")
    else:
        print("Error al actualizar el empleado.")

    # Ejemplo 5: Eliminar el empleado de prueba
    # print("\n--- Eliminando Empleado EMP00_TEST ---")
    # delete_query = "DELETE FROM Empleados WHERE id_empleado = %s"
    # rows_deleted = execute_query(delete_query, ("EMP00_TEST",))
    # if rows_deleted is not None:
    #     print(f"Filas eliminadas: {rows_deleted}")
    # else:
    #     print("Error al eliminar el empleado.")

    print("\nPruebas del módulo db.py completadas.")