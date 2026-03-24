import os
import sqlite3

try:
    import psycopg2
except ImportError:
    psycopg2 = None


# =========================
# COMPATIBILIDAD POSTGRES
# =========================
class CursorCompat:
    def __init__(self, cursor):
        self._cursor = cursor
        self.lastrowid = None

    def _adapt_query(self, query: str):
        """
        Convierte placeholders SQLite (?) a Postgres (%s)
        y añade RETURNING id a INSERTs cuando hace falta,
        para que app.py pueda seguir usando lastrowid.
        """
        q = query.strip()
        q_pg = q.replace("?", "%s")

        upper_q = q_pg.upper()
        if upper_q.startswith("INSERT INTO") and "RETURNING" not in upper_q:
            q_pg += " RETURNING id"

        return q_pg

    def execute(self, query, params=None):
        params = params or ()
        q_pg = self._adapt_query(query)

        self._cursor.execute(q_pg, params)

        if q_pg.strip().upper().startswith("INSERT INTO"):
            try:
                row = self._cursor.fetchone()
                if row:
                    self.lastrowid = row[0]
            except Exception:
                self.lastrowid = None

        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def rowcount(self):
        return self._cursor.rowcount


class ConnectionCompat:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return CursorCompat(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def execute(self, query, params=None):
        cur = self.cursor()
        return cur.execute(query, params or ())


# =========================
# CONEXIÓN
# =========================
def conectar():
    """
    Si existe DATABASE_URL -> usa Postgres (Render / producción)
    Si no existe -> usa SQLite local
    """
    database_url = os.getenv("DATABASE_URL")

    if database_url and psycopg2:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        return ConnectionCompat(conn)

    conn = sqlite3.connect("cafeteria.db", timeout=30)
    return conn


def es_postgres():
    return bool(os.getenv("DATABASE_URL")) and psycopg2 is not None


# =========================
# CREAR BASE DE DATOS
# =========================
def crear_bd():
    conn = conectar()
    c = conn.cursor()

    if es_postgres():
        # ---------------- USUARIOS ----------------
        c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios(
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE,
            password VARCHAR(100)
        )
        """)

        # ---------------- PRODUCTOS ----------------
        c.execute("""
        CREATE TABLE IF NOT EXISTS productos(
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(150) UNIQUE,
            precio NUMERIC DEFAULT 0,
            stock INTEGER DEFAULT 0,
            tipo VARCHAR(100) DEFAULT 'General',
            precio_pequeno NUMERIC DEFAULT 0,
            precio_grande NUMERIC DEFAULT 0,
            costo NUMERIC DEFAULT 0
        )
        """)

        # ---------------- SISTEMA VIEJO ----------------
        c.execute("""
        CREATE TABLE IF NOT EXISTS ventas(
            id SERIAL PRIMARY KEY,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total NUMERIC
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS detalle_venta(
            id SERIAL PRIMARY KEY,
            venta_id INTEGER REFERENCES ventas(id),
            producto_id INTEGER REFERENCES productos(id),
            cantidad INTEGER,
            subtotal NUMERIC
        )
        """)

        # ---------------- FACTURAS ----------------
        c.execute("""
        CREATE TABLE IF NOT EXISTS facturas(
            id SERIAL PRIMARY KEY,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total NUMERIC,
            pago_con NUMERIC DEFAULT 0,
            devuelta NUMERIC DEFAULT 0
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS detalle_factura(
            id SERIAL PRIMARY KEY,
            factura_id INTEGER REFERENCES facturas(id),
            producto VARCHAR(150),
            cantidad INTEGER,
            precio NUMERIC,
            subtotal NUMERIC
        )
        """)

        # ---------------- MOVIMIENTOS DE INVENTARIO ----------------
        c.execute("""
        CREATE TABLE IF NOT EXISTS movimientos_inventario(
            id SERIAL PRIMARY KEY,
            producto_id INTEGER REFERENCES productos(id),
            tipo_movimiento VARCHAR(100),
            cantidad INTEGER,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ---------------- CIERRES DE CAJA ----------------
        c.execute("""
        CREATE TABLE IF NOT EXISTS cierres_caja(
            id SERIAL PRIMARY KEY,
            fecha_cierre DATE,
            total_sistema NUMERIC,
            total_real NUMERIC,
            diferencia NUMERIC,
            estado VARCHAR(50),
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
            usuario VARCHAR(100) DEFAULT '',
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ---------------- ÍNDICES ----------------
        c.execute("CREATE INDEX IF NOT EXISTS idx_producto_nombre ON productos(nombre)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_factura_fecha ON facturas(fecha)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha)")

    else:
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
            precio_grande REAL DEFAULT 0,
            costo REAL DEFAULT 0
        )
        """)

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

        try:
            c.execute("ALTER TABLE productos ADD COLUMN costo REAL DEFAULT 0")
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


# =========================
# USUARIO ADMIN
# =========================
def crear_usuario_admin():
    conn = conectar()
    c = conn.cursor()

    if es_postgres():
        c.execute("""
            INSERT INTO usuarios (username, password)
            VALUES (%s, %s)
            ON CONFLICT (username) DO NOTHING
        """, ("admin", "1234"))
    else:
        c.execute("SELECT * FROM usuarios WHERE username = 'admin'")
        if not c.fetchone():
            c.execute(
                "INSERT INTO usuarios (username, password) VALUES (?, ?)",
                ("admin", "1234")
            )

    conn.commit()
    conn.close()