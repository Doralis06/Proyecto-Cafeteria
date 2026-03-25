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
            nombre VARCHAR(150),
            tipo VARCHAR(100) DEFAULT 'General',
            presentacion VARCHAR(50) DEFAULT 'Normal',
            precio NUMERIC DEFAULT 0,
            precio_pequeno NUMERIC DEFAULT 0,
            precio_grande NUMERIC DEFAULT 0,
            precio_venta NUMERIC DEFAULT 0,
            stock INTEGER DEFAULT 0,
            inversion_total NUMERIC DEFAULT 0,
            costo_unitario NUMERIC DEFAULT 0,
            ganancia_unitaria NUMERIC DEFAULT 0
        )
        """)

        # Agregar columnas nuevas si la tabla ya existía
        try:
            c.execute("ALTER TABLE productos ADD COLUMN tipo VARCHAR(100) DEFAULT 'General'")
        except:
            pass

        try:
            c.execute("ALTER TABLE productos ADD COLUMN presentacion VARCHAR(50) DEFAULT 'Normal'")
        except:
            pass

        try:
            c.execute("ALTER TABLE productos ADD COLUMN precio NUMERIC DEFAULT 0")
        except:
            pass

        try:
            c.execute("ALTER TABLE productos ADD COLUMN precio_pequeno NUMERIC DEFAULT 0")
        except:
            pass

        try:
            c.execute("ALTER TABLE productos ADD COLUMN precio_grande NUMERIC DEFAULT 0")
        except:
            pass

        try:
            c.execute("ALTER TABLE productos ADD COLUMN precio_venta NUMERIC DEFAULT 0")
        except:
            pass

        try:
            c.execute("ALTER TABLE productos ADD COLUMN stock INTEGER DEFAULT 0")
        except:
            pass

        try:
            c.execute("ALTER TABLE productos ADD COLUMN inversion_total NUMERIC DEFAULT 0")
        except:
            pass

        try:
            c.execute("ALTER TABLE productos ADD COLUMN costo_unitario NUMERIC DEFAULT 0")
        except:
            pass

        try:
            c.execute("ALTER TABLE productos ADD COLUMN ganancia_unitaria NUMERIC DEFAULT 0")
        except:
            pass

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

        try:
            c.execute("ALTER TABLE facturas ADD COLUMN pago_con NUMERIC DEFAULT 0")
        except:
            pass

        try:
            c.execute("ALTER TABLE facturas ADD COLUMN devuelta NUMERIC DEFAULT 0")
        except:
            pass

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

        try:
            c.execute("ALTER TABLE cierres_caja ADD COLUMN observaciones TEXT DEFAULT ''")
        except:
            pass

        try:
            c.execute("ALTER TABLE cierres_caja ADD COLUMN usuario VARCHAR(100) DEFAULT ''")
        except:
            pass

        # ---------------- ÍNDICES ----------------
        c.execute("CREATE INDEX IF NOT EXISTS idx_producto_nombre ON productos(nombre)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_producto_tipo ON productos(tipo)")
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
            nombre TEXT,
            tipo TEXT DEFAULT 'General',
            presentacion TEXT DEFAULT 'Normal',
            precio REAL DEFAULT 0,
            precio_pequeno REAL DEFAULT 0,
            precio_grande REAL DEFAULT 0,
            precio_venta REAL DEFAULT 0,
            stock INTEGER DEFAULT 0,
            inversion_total REAL DEFAULT 0,
            costo_unitario REAL DEFAULT 0,
            ganancia_unitaria REAL DEFAULT 0
        )
        """)

        try:
            c.execute("ALTER TABLE productos ADD COLUMN tipo TEXT DEFAULT 'General'")
        except:
            pass

        try:
            c.execute("ALTER TABLE productos ADD COLUMN presentacion TEXT DEFAULT 'Normal'")
        except:
            pass

        try:
            c.execute("ALTER TABLE productos ADD COLUMN precio REAL DEFAULT 0")
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
            c.execute("ALTER TABLE productos ADD COLUMN precio_venta REAL DEFAULT 0")
        except:
            pass

        try:
            c.execute("ALTER TABLE productos ADD COLUMN stock INTEGER DEFAULT 0")
        except:
            pass

        try:
            c.execute("ALTER TABLE productos ADD COLUMN inversion_total REAL DEFAULT 0")
        except:
            pass

        try:
            c.execute("ALTER TABLE productos ADD COLUMN costo_unitario REAL DEFAULT 0")
        except:
            pass

        try:
            c.execute("ALTER TABLE productos ADD COLUMN ganancia_unitaria REAL DEFAULT 0")
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
        c.execute("CREATE INDEX IF NOT EXISTS idx_producto_tipo ON productos(tipo)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_factura_fecha ON facturas(fecha)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha)")

    conn.commit()
    conn.close()