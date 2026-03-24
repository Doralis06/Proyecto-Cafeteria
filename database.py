import os
import psycopg2
from urllib.parse import urlparse

def conectar():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("No se encontró DATABASE_URL")

    return psycopg2.connect(database_url)

    # ---------------- USUARIOS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # ---------------- PRODUCTOS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS productos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE,
        precio REAL DEFAULT 0,
        stock INTEGER DEFAULT 0,
        tipo TEXT DEFAULT 'General',
        precio_pequeno REAL DEFAULT 0,
        precio_grande REAL DEFAULT 0
    )
    """)

    # Si la tabla ya existía, estas columnas se agregan sin romper nada
    try:
        c.execute("ALTER TABLE productos ADD COLUMN tipo TEXT DEFAULT 'General'")
    except:
        pass

    try:
        c.execute("ALTER TABLE productos ADD COLUMN precio_pequeno REAL DEFAULT 0")
    except:
        pass

    try:
        c.execute("ALTER TABLE productos ADD COLUMN precio_grande REAL DEFAULT 0")
    except:
        pass

    # ---------------- SISTEMA VIEJO ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS ventas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
        total REAL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS detalle_venta(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER,
        producto_id INTEGER,
        cantidad INTEGER,
        subtotal REAL,
        FOREIGN KEY (venta_id) REFERENCES ventas(id),
        FOREIGN KEY (producto_id) REFERENCES productos(id)
    )
    """)

    # ---------------- FACTURAS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS facturas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
        total REAL,
        pago_con REAL DEFAULT 0,
        devuelta REAL DEFAULT 0
    )
    """)

    # Si la tabla facturas ya existía de antes, estas columnas se agregan sin romper nada
    try:
        c.execute("ALTER TABLE facturas ADD COLUMN pago_con REAL DEFAULT 0")
    except:
        pass

    try:
        c.execute("ALTER TABLE facturas ADD COLUMN devuelta REAL DEFAULT 0")
    except:
        pass

    c.execute("""
    CREATE TABLE IF NOT EXISTS detalle_factura(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        factura_id INTEGER,
        producto TEXT,
        cantidad INTEGER,
        precio REAL,
        subtotal REAL,
        FOREIGN KEY (factura_id) REFERENCES facturas(id)
    )
    """)

    # ---------------- MOVIMIENTOS DE INVENTARIO ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS movimientos_inventario(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER,
        tipo_movimiento TEXT,
        cantidad INTEGER,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (producto_id) REFERENCES productos(id)
    )
    """)

    # ---------------- CIERRES DE CAJA ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS cierres_caja(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_cierre DATE,
        total_sistema REAL,
        total_real REAL,
        diferencia REAL,
        estado TEXT,
        cant_5 INTEGER DEFAULT 0,
        cant_10 INTEGER DEFAULT 0,
        cant_25 INTEGER DEFAULT 0,
        cant_50 INTEGER DEFAULT 0,
        cant_100 INTEGER DEFAULT 0,
        cant_200 INTEGER DEFAULT 0,
        cant_500 INTEGER DEFAULT 0,
        cant_1000 INTEGER DEFAULT 0,
        cant_2000 INTEGER DEFAULT 0,
        observaciones TEXT DEFAULT '',
        usuario TEXT DEFAULT '',
        creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Si la tabla ya existía de antes, estas columnas se agregan sin romper nada
    try:
        c.execute("ALTER TABLE cierres_caja ADD COLUMN observaciones TEXT DEFAULT ''")
    except:
        pass

    try:
        c.execute("ALTER TABLE cierres_caja ADD COLUMN usuario TEXT DEFAULT ''")
    except:
        pass

    # ---------------- ÍNDICES ----------------
    c.execute("CREATE INDEX IF NOT EXISTS idx_producto_nombre ON productos(nombre)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_factura_fecha ON facturas(fecha)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha)")

    conn.commit()
    conn.close()


def crear_usuario_admin():
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    if not c.fetchone():
        c.execute(
            "INSERT INTO usuarios (username, password) VALUES (?, ?)",
            ("admin", "1234")
        )

    conn.commit()
    conn.close()