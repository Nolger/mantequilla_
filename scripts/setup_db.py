import mysql.connector
from dotenv import load_dotenv
from mysql.connector import errorcode
import os

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"), # O la IP/hostname de tu contenedor Docker si es diferente
    "port": os.getenv("DB_PORT"), # Puerto estándar de MySQL
    "user": os.getenv("DB_USER"), # Usuario de MySQL (debe coincidir con MYSQL_USER)
    "password": os.getenv("DB_PASSWORD"), # Contraseña del usuario (debe coincidir con MYSQL_PASSWORD)
    "database": os.getenv("DB_NAME") # Nombre de la base de datos (debe coincidir con MYSQL_DATABASE)
}

# --- DEFINICIÓN DE TABLAS (SQL CREATE STATEMENTS para MySQL) ---
TABLE_DEFINITIONS = [
    """
    CREATE TABLE IF NOT EXISTS Proveedores (
        id_proveedor VARCHAR(50) PRIMARY KEY,
        nombre VARCHAR(255) NOT NULL UNIQUE,
        telefono VARCHAR(20),
        correo VARCHAR(255) UNIQUE,
        producto_suministra TEXT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS Empleados (
        id_empleado VARCHAR(50) PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        apellido VARCHAR(100) NOT NULL,
        rol VARCHAR(50) NOT NULL CHECK (rol IN ('administrador', 'empleado', 'cocinero', 'mesero')),
        hash_contrasena VARCHAR(255) NOT NULL, 
        salt VARCHAR(64) NOT NULL, 
        estado VARCHAR(20) NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo'))
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS Mesa (
        id_mesa VARCHAR(20) PRIMARY KEY,
        capacidad INT NOT NULL CHECK (capacidad > 0),
        estado VARCHAR(20) NOT NULL DEFAULT 'libre' CHECK (estado IN ('libre', 'ocupada', 'reservada', 'mantenimiento')),
        ubicacion VARCHAR(100), -- Descripción textual de la ubicación
        pos_x INT DEFAULT 50,   -- Coordenada X para el canvas gráfico
        pos_y INT DEFAULT 50    -- Coordenada Y para el canvas gráfico
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """, # MODIFICACIÓN: Añadidos pos_x y pos_y
    """
    CREATE TABLE IF NOT EXISTS Cliente (
        id_cliente VARCHAR(50) PRIMARY KEY,
        nombre VARCHAR(255) NOT NULL,
        telefono VARCHAR(20),
        correo VARCHAR(255) UNIQUE,
        genero VARCHAR(50)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS Producto (
        id_producto VARCHAR(50) PRIMARY KEY,
        nombre VARCHAR(255) NOT NULL UNIQUE,
        descripcion TEXT,
        unidad_medida VARCHAR(20) NOT NULL CHECK (unidad_medida IN ('kg', 'litros', 'unidades', 'g', 'ml', 'botella', 'lata')),
        stock_minimo DECIMAL(10, 2) NOT NULL DEFAULT 0.00 CHECK (stock_minimo >= 0),
        proveedor_principal_ref VARCHAR(50),
        costo_unitario DECIMAL(10, 2) NOT NULL CHECK (costo_unitario >= 0),
        perecedero BOOLEAN NOT NULL DEFAULT FALSE,
        fecha_caducidad DATE,
        CONSTRAINT fk_proveedor_principal FOREIGN KEY (proveedor_principal_ref) REFERENCES Proveedores(id_proveedor) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS InventarioMadre (
        id_inventariomadre VARCHAR(50) PRIMARY KEY,
        descripcion TEXT NOT NULL,
        cantidad_actual DECIMAL(10, 2) NOT NULL DEFAULT 0.00 CHECK (cantidad_actual >= 0),
        unidad_medida VARCHAR(50),
        precio_unitario_estimado DECIMAL(10, 2) CHECK (precio_unitario_estimado >= 0),
        ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS Plato (
        id_plato VARCHAR(50) PRIMARY KEY,
        nombre_plato VARCHAR(255) NOT NULL UNIQUE,
        descripcion TEXT,
        categoria VARCHAR(50) NOT NULL CHECK (categoria IN ('entrada', 'principal', 'postre', 'bebida', 'acompañamiento', 'snack')),
        tiempo_preparacion_min INT CHECK (tiempo_preparacion_min >= 0),
        activo BOOLEAN NOT NULL DEFAULT TRUE,
        precio_venta DECIMAL(10, 2) NOT NULL CHECK (precio_venta >= 0),
        imagen_url VARCHAR(512)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS Ingrediente (
        id_ingrediente VARCHAR(50) PRIMARY KEY,
        id_producto VARCHAR(50) NOT NULL UNIQUE,
        cantidad_disponible DECIMAL(10, 3) NOT NULL DEFAULT 0.000 CHECK (cantidad_disponible >= 0),
        ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT fk_producto_ingrediente FOREIGN KEY (id_producto) REFERENCES Producto(id_producto) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS OrdenCompra (
        id_ordencompra VARCHAR(50) PRIMARY KEY,
        id_proveedor VARCHAR(50) NOT NULL,
        fecha_orden DATETIME DEFAULT CURRENT_TIMESTAMP,
        fecha_entrega_estimada DATE,
        estado_orden VARCHAR(50) NOT NULL DEFAULT 'pendiente' CHECK (estado_orden IN ('pendiente', 'procesando', 'enviada', 'recibida', 'recibida_parcial', 'cancelada')),
        total_orden DECIMAL(12, 2) CHECK (total_orden >= 0),
        observaciones TEXT,
        CONSTRAINT fk_proveedor_orden FOREIGN KEY (id_proveedor) REFERENCES Proveedores(id_proveedor) ON DELETE RESTRICT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS DetalleOrdenCompra (
        id_detalle_oc INT AUTO_INCREMENT PRIMARY KEY,
        id_ordencompra VARCHAR(50) NOT NULL,
        id_producto VARCHAR(50) NOT NULL,
        cantidad_solicitada DECIMAL(10, 2) NOT NULL CHECK (cantidad_solicitada > 0),
        cantidad_recibida DECIMAL(10, 2) DEFAULT 0.00 CHECK (cantidad_recibida >= 0),
        precio_unitario_compra DECIMAL(10, 2) NOT NULL CHECK (precio_unitario_compra >= 0),
        subtotal_detalle DECIMAL(12, 2) AS (cantidad_solicitada * precio_unitario_compra) STORED,
        CONSTRAINT fk_ordencompra_detalle FOREIGN KEY (id_ordencompra) REFERENCES OrdenCompra(id_ordencompra) ON DELETE CASCADE,
        CONSTRAINT fk_producto_detalle_oc FOREIGN KEY (id_producto) REFERENCES Producto(id_producto) ON DELETE RESTRICT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS Comanda (
        id_comanda VARCHAR(50) PRIMARY KEY,
        id_mesa VARCHAR(20) NOT NULL,
        id_empleado_mesero VARCHAR(50) NOT NULL,
        id_cliente VARCHAR(50),
        fecha_hora_apertura DATETIME DEFAULT CURRENT_TIMESTAMP,
        fecha_hora_cierre DATETIME NULL DEFAULT NULL,
        cantidad_personas INT NOT NULL DEFAULT 1 CHECK (cantidad_personas > 0),
        estado_comanda VARCHAR(50) NOT NULL DEFAULT 'abierta' CHECK (estado_comanda IN ('abierta', 'en preparacion', 'lista para servir', 'servida', 'facturada', 'cancelada')),
        observaciones TEXT,
        CONSTRAINT fk_mesa_comanda FOREIGN KEY (id_mesa) REFERENCES Mesa(id_mesa) ON DELETE RESTRICT,
        CONSTRAINT fk_empleado_comanda FOREIGN KEY (id_empleado_mesero) REFERENCES Empleados(id_empleado) ON DELETE RESTRICT,
        CONSTRAINT fk_cliente_comanda FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS Receta (
        id_receta INT AUTO_INCREMENT PRIMARY KEY,
        id_plato VARCHAR(50) NOT NULL,
        id_ingrediente VARCHAR(50) NOT NULL,
        cantidad_necesaria DECIMAL(10, 3) NOT NULL CHECK (cantidad_necesaria > 0),
        unidad_medida_receta VARCHAR(20) NOT NULL,
        instrucciones_paso TEXT,
        UNIQUE (id_plato, id_ingrediente),
        CONSTRAINT fk_plato_receta FOREIGN KEY (id_plato) REFERENCES Plato(id_plato) ON DELETE CASCADE,
        CONSTRAINT fk_ingrediente_receta FOREIGN KEY (id_ingrediente) REFERENCES Ingrediente(id_ingrediente) ON DELETE RESTRICT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS Merma (
        id_merma INT AUTO_INCREMENT PRIMARY KEY,
        id_ingrediente VARCHAR(50), 
        id_producto_directo VARCHAR(50), 
        cantidad_perdida DECIMAL(10, 3) NOT NULL CHECK (cantidad_perdida > 0),
        unidad_medida_merma VARCHAR(20) NOT NULL,
        fecha_merma DATE NOT NULL DEFAULT (CURRENT_DATE),
        motivo VARCHAR(100) NOT NULL CHECK (motivo IN ('caducidad', 'preparacion', 'mal estado', 'almacenamiento', 'daño', 'otro')),
        descripcion_motivo TEXT,
        id_empleado_responsable VARCHAR(50),
        CONSTRAINT chk_merma_source CHECK (id_ingrediente IS NOT NULL OR id_producto_directo IS NOT NULL),
        CONSTRAINT fk_ingrediente_merma FOREIGN KEY (id_ingrediente) REFERENCES Ingrediente(id_ingrediente) ON DELETE CASCADE,
        CONSTRAINT fk_producto_directo_merma FOREIGN KEY (id_producto_directo) REFERENCES Producto(id_producto) ON DELETE CASCADE,
        CONSTRAINT fk_empleado_merma FOREIGN KEY (id_empleado_responsable) REFERENCES Empleados(id_empleado) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS DetalleComanda (
        id_detalle_comanda INT AUTO_INCREMENT PRIMARY KEY,
        id_comanda VARCHAR(50) NOT NULL,
        id_plato VARCHAR(50) NOT NULL,
        cantidad INT NOT NULL CHECK (cantidad > 0),
        precio_unitario_momento DECIMAL(10, 2) NOT NULL,
        estado_plato VARCHAR(50) NOT NULL DEFAULT 'pendiente' CHECK (estado_plato IN ('pendiente', 'en preparacion', 'listo', 'entregado', 'cancelado')),
        observaciones_plato TEXT,
        hora_pedido DATETIME DEFAULT CURRENT_TIMESTAMP,
        hora_entrega_estimada DATETIME NULL DEFAULT NULL,
        hora_entrega_real DATETIME NULL DEFAULT NULL,
        subtotal_detalle DECIMAL(12, 2) AS (cantidad * precio_unitario_momento) STORED,
        CONSTRAINT fk_comanda_detalle FOREIGN KEY (id_comanda) REFERENCES Comanda(id_comanda) ON DELETE CASCADE,
        CONSTRAINT fk_plato_detalle FOREIGN KEY (id_plato) REFERENCES Plato(id_plato) ON DELETE RESTRICT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS Factura (
        id_factura VARCHAR(50) PRIMARY KEY,
        id_comanda VARCHAR(50) NOT NULL UNIQUE,
        id_cliente_factura VARCHAR(50),
        fecha_hora_emision DATETIME DEFAULT CURRENT_TIMESTAMP,
        subtotal DECIMAL(12, 2) NOT NULL CHECK (subtotal >= 0),
        impuestos DECIMAL(12, 2) NOT NULL DEFAULT 0.00 CHECK (impuestos >= 0),
        descuentos DECIMAL(12, 2) DEFAULT 0.00 CHECK (descuentos >=0),
        total_factura DECIMAL(12, 2) AS (subtotal + impuestos - descuentos) STORED,
        metodo_pago VARCHAR(50) CHECK (metodo_pago IN ('efectivo', 'tarjeta_credito', 'tarjeta_debito', 'transferencia', 'online', 'cortesia', 'otro')),
        referencia_pago VARCHAR(255),
        estado_factura VARCHAR(20) NOT NULL DEFAULT 'pendiente' CHECK (estado_factura IN ('pendiente', 'pagada', 'anulada', 'reembolsada')),
        CONSTRAINT fk_comanda_factura FOREIGN KEY (id_comanda) REFERENCES Comanda(id_comanda) ON DELETE RESTRICT,
        CONSTRAINT fk_cliente_factura FOREIGN KEY (id_cliente_factura) REFERENCES Cliente(id_cliente) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS InventarioPorcionamiento (
        id_porcionamiento INT AUTO_INCREMENT PRIMARY KEY,
        id_detalle_comanda INT NOT NULL,
        id_ingrediente VARCHAR(50) NOT NULL,
        cantidad_usada DECIMAL(10, 3) NOT NULL CHECK (cantidad_usada > 0),
        unidad_medida_usada VARCHAR(20) NOT NULL,
        costo_ingrediente_momento DECIMAL(10, 2) NOT NULL,
        costo_total_porcion DECIMAL(12, 2) AS (cantidad_usada * costo_ingrediente_momento) STORED,
        fecha_hora_porcionamiento DATETIME DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_detalle_comanda_porcion FOREIGN KEY (id_detalle_comanda) REFERENCES DetalleComanda(id_detalle_comanda) ON DELETE CASCADE,
        CONSTRAINT fk_ingrediente_porcion FOREIGN KEY (id_ingrediente) REFERENCES Ingrediente(id_ingrediente) ON DELETE RESTRICT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS MovimientoStock (
        id_movimiento INT AUTO_INCREMENT PRIMARY KEY,
        id_ingrediente VARCHAR(50) NOT NULL,
        fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        tipo_movimiento VARCHAR(50) NOT NULL COMMENT 'INGRESO, CONSUMO_COMANDA, MERMA, AJUSTE_MANUAL, INVENTARIO_INICIAL, etc.',
        cantidad_cambio DECIMAL(10, 3) NOT NULL COMMENT 'Positivo para aumento, negativo para disminución',
        cantidad_anterior DECIMAL(10, 3) NOT NULL,
        cantidad_nueva DECIMAL(10, 3) NOT NULL,
        id_referencia_origen VARCHAR(100) NULL COMMENT 'ID de OrdenCompra, Comanda, Merma, etc.',
        descripcion_motivo TEXT,
        id_empleado_responsable VARCHAR(50) NULL,
        CONSTRAINT fk_ingrediente_movimiento FOREIGN KEY (id_ingrediente) REFERENCES Ingrediente(id_ingrediente) ON DELETE CASCADE,
        CONSTRAINT fk_empleado_movimiento FOREIGN KEY (id_empleado_responsable) REFERENCES Empleados(id_empleado) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
]

def create_database_if_not_exists(config):
    """
    Crea la base de datos en MySQL si no existe.
    """
    db_name = config.pop("database") # Extraer dbname para conectar sin él primero
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**config) # Conectar sin especificar la base de datos
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print(f"Base de datos '{db_name}' verificada/creada exitosamente.")
        config["database"] = db_name # Añadir de nuevo para la creación de tablas
        return True
    except mysql.connector.Error as err:
        print(f"Error al crear la base de datos '{db_name}': {err}")
        config["database"] = db_name # Restaurar por si acaso para el mensaje de error
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def create_tables(db_config):
    """
    Crea las tablas en la base de datos MySQL especificada.
    """
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        print(f"\nConectado a la base de datos '{db_config['database']}'. Creando tablas...")

        for table_sql in TABLE_DEFINITIONS:
            try:
                # Extraer el nombre de la tabla del comando SQL (de forma simple)
                # Asume que la estructura es "CREATE TABLE IF NOT EXISTS NombreTabla ("
                parts = table_sql.split("CREATE TABLE IF NOT EXISTS ", 1)
                table_name = "Desconocida"
                if len(parts) > 1:
                    table_name = parts[1].split("(", 1)[0].strip().replace("`", "")

                cursor.execute(table_sql)
                print(f"Tabla '{table_name}' verificada/creada exitosamente.")
            except mysql.connector.Error as err:
                print(f"Error al crear tabla '{table_name}': {err}")
                # Podrías decidir si continuar con otras tablas o detenerte
                # conn.rollback() no es necesario para DDL en MySQL si autocommit está activado o si son sentencias individuales.
                # Si una tabla falla, las anteriores ya están creadas.

        # conn.commit() # No es estrictamente necesario para DDL si autocommit es el comportamiento por defecto o cada execute es una transacción.
        print("\nProceso de creación de tablas completado.")
        return True

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Error de acceso: Usuario o contraseña incorrectos.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print(f"La base de datos '{db_config['database']}' no existe.")
        else:
            print(f"Error de MySQL al conectar o crear tablas: {err}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("Conexión a la base de datos cerrada.")
    
if __name__ == "__main__":
    print("Iniciando script de configuración de la base de datos MySQL...")

    # 1. Crear la base de datos si no existe
    if not create_database_if_not_exists(DB_CONFIG.copy()): # Usar una copia para no modificar el original global
        print("No se pudo asegurar la existencia de la base de datos. Abortando creación de tablas.")
    else:
        # 2. Conectarse a la base de datos (ahora con el nombre) y crear las tablas
        if create_tables(DB_CONFIG):
            print("Configuración de la base de datos MySQL completada.")
        else:
            print("Falló la configuración de las tablas de la base de datos MySQL.")
