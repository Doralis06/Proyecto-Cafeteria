import sqlite3
from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from database import crear_bd, crear_usuario_admin, conectar

app = Flask(__name__)
app.secret_key = "clave_super_segura"

crear_bd()
crear_usuario_admin()


def conectar_seguro():
    conn = conectar()
    try:
        conn.execute("PRAGMA foreign_keys = ON")
    except Exception:
        pass
    return conn


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if "usuario" in session:
        return redirect("/dashboard")

    conn = None
    try:
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()

            conn = conectar_seguro()
            c = conn.cursor()

            c.execute(
                "SELECT * FROM usuarios WHERE username=? AND password=?",
                (username, password)
            )
            user = c.fetchone()

            if user:
                session.permanent = True
                session["usuario"] = username
                return redirect("/dashboard")
            else:
                return render_template("login.html", error="Usuario o contraseña incorrectos")

        return render_template("login.html")

    except Exception as e:
        return f"Error en login: {e}"

    finally:
        if conn:
            conn.close()


@app.before_request
def proteger_rutas():
    if request.path.startswith("/static/"):
        return None

    rutas_libres = ["/"]
    if request.path not in rutas_libres and "usuario" not in session:
        return redirect("/")


@app.route("/dashboard")
def dashboard():
    if "usuario" not in session:
        return redirect("/")
    return render_template("dashboard.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- INVENTARIO ----------------
@app.route("/productos", methods=["GET", "POST"])
def productos():
    if "usuario" not in session:
        return redirect("/")

    conn = None
    mensaje = None
    tipo_mensaje = None

    try:
        conn = conectar_seguro()
        c = conn.cursor()

        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            tipo = request.form.get("tipo", "").strip()
            stock = int(request.form.get("stock") or 0)
            inversion_total = float(request.form.get("inversion_total") or 0)

            precio = float(request.form.get("precio") or 0)
            precio_pequeno = float(request.form.get("precio_pequeno") or 0)
            precio_grande = float(request.form.get("precio_grande") or 0)

            if not nombre:
                return redirect(url_for("productos", error="Debe escribir el nombre del producto"))
            if not tipo:
                return redirect(url_for("productos", error="Debe seleccionar el tipo de producto"))
            if stock <= 0:
                return redirect(url_for("productos", error="El stock debe ser mayor que 0"))

            costo_unitario = inversion_total / stock if stock > 0 else 0

            if tipo == "Jugos":
                precio = 0
            else:
                precio_pequeno = 0
                precio_grande = 0

            c.execute("SELECT id, stock, inversion_total FROM productos WHERE nombre = ?", (nombre,))
            existente = c.fetchone()

            if existente:
                producto_id = existente[0]
                stock_actual = int(existente[1] or 0)
                inversion_actual = float(existente[2] or 0)

                nuevo_stock = stock_actual + stock
                nueva_inversion_total = inversion_actual + inversion_total
                nuevo_costo_unitario = nueva_inversion_total / nuevo_stock if nuevo_stock > 0 else 0

                c.execute("""
                    UPDATE productos
                    SET precio = ?, stock = ?, tipo = ?, precio_pequeno = ?, precio_grande = ?,
                        inversion_total = ?, costo_unitario = ?
                    WHERE id = ?
                """, (
                    precio, nuevo_stock, tipo, precio_pequeno, precio_grande,
                    nueva_inversion_total, nuevo_costo_unitario, producto_id
                ))

                conn.commit()
                return redirect(url_for("productos", ok="actualizado"))
            else:
                c.execute("""
                    INSERT INTO productos (
                        nombre, precio, stock, tipo,
                        precio_pequeno, precio_grande,
                        inversion_total, costo_unitario
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    nombre, precio, stock, tipo,
                    precio_pequeno, precio_grande,
                    inversion_total, costo_unitario
                ))

                conn.commit()
                return redirect(url_for("productos", ok="guardado"))

        ok = request.args.get("ok")
        error = request.args.get("error")

        if ok == "guardado":
            mensaje = "Producto agregado correctamente."
            tipo_mensaje = "ok"
        elif ok == "actualizado":
            mensaje = "El producto ya existía. Se actualizó y se sumó el stock."
            tipo_mensaje = "info"
        elif error:
            mensaje = error
            tipo_mensaje = "error"

        c.execute("SELECT * FROM productos ORDER BY tipo, nombre")
        productos = c.fetchall()

        return render_template(
            "productos.html",
            productos=productos,
            mensaje=mensaje,
            tipo_mensaje=tipo_mensaje
        )

    except Exception as e:
        return f"Error en productos: {e}"

    finally:
        if conn:
            conn.close()


@app.route("/eliminar_producto/<int:id>")
def eliminar_producto(id):
    if "usuario" not in session:
        return redirect("/")

    conn = None
    try:
        conn = conectar_seguro()
        c = conn.cursor()

        c.execute("SELECT * FROM productos WHERE id = ?", (id,))
        producto = c.fetchone()

        if not producto:
            return "❌ Producto no encontrado"

        c.execute("DELETE FROM productos WHERE id = ?", (id,))
        conn.commit()

        return redirect("/productos")

    except sqlite3.IntegrityError as e:
        return f"No se puede eliminar este producto porque está relacionado con otros datos. Error: {e}"

    except Exception as e:
        return f"Error al eliminar producto: {e}"

    finally:
        if conn:
            conn.close()


@app.route("/editar_producto/<int:id>")
def editar_producto(id):
    if "usuario" not in session:
        return redirect("/")

    conn = None
    try:
        conn = conectar_seguro()
        c = conn.cursor()

        c.execute("""
            SELECT id, nombre, precio, stock, tipo,
                   COALESCE(precio_pequeno, 0),
                   COALESCE(precio_grande, 0),
                   COALESCE(inversion_total, 0),
                   COALESCE(costo_unitario, 0)
            FROM productos
            WHERE id = ?
        """, (id,))
        producto = c.fetchone()

        if not producto:
            return "❌ Producto no encontrado"

        producto = list(producto)

        while len(producto) < 9:
            producto.append(0)

        mensaje = request.args.get("mensaje")
        tipo_mensaje = request.args.get("tipo", "error")

        return render_template(
            "editar_producto.html",
            producto=producto,
            mensaje=mensaje,
            tipo_mensaje=tipo_mensaje
        )

    except Exception as e:
        return f"Error al cargar el producto para editar: {e}"

    finally:
        if conn:
            conn.close()


@app.route("/actualizar_producto/<int:id>", methods=["POST"])
def actualizar_producto(id):
    if "usuario" not in session:
        return redirect("/")

    conn = None
    try:
        conn = conectar_seguro()
        c = conn.cursor()

        c.execute("SELECT id FROM productos WHERE id = ?", (id,))
        existe = c.fetchone()

        if not existe:
            return "❌ Producto no encontrado"

        nombre = request.form.get("nombre", "").strip()
        tipo = request.form.get("tipo", "").strip()
        stock = int(request.form.get("stock") or 0)
        inversion_total = float(request.form.get("inversion_total") or 0)

        precio = float(request.form.get("precio") or 0)
        precio_pequeno = float(request.form.get("precio_pequeno") or 0)
        precio_grande = float(request.form.get("precio_grande") or 0)

        if not nombre:
            return redirect(url_for("editar_producto", id=id, mensaje="Debe escribir el nombre del producto", tipo="error"))

        if not tipo:
            return redirect(url_for("editar_producto", id=id, mensaje="Debe seleccionar el tipo de producto", tipo="error"))

        if stock <= 0:
            return redirect(url_for("editar_producto", id=id, mensaje="El stock debe ser mayor que 0", tipo="error"))

        costo_unitario = inversion_total / stock if stock > 0 else 0

        if tipo == "Jugos":
            precio = 0
        else:
            precio_pequeno = 0
            precio_grande = 0

        c.execute("SELECT id FROM productos WHERE nombre = ? AND id != ?", (nombre, id))
        repetido = c.fetchone()

        if repetido:
            return redirect(url_for(
                "editar_producto",
                id=id,
                mensaje=f"Ya existe otro producto con el nombre '{nombre}'",
                tipo="error"
            ))

        c.execute("""
            UPDATE productos
            SET nombre = ?,
                precio = ?,
                stock = ?,
                tipo = ?,
                precio_pequeno = ?,
                precio_grande = ?,
                inversion_total = ?,
                costo_unitario = ?
            WHERE id = ?
        """, (
            nombre, precio, stock, tipo, precio_pequeno, precio_grande,
            inversion_total, costo_unitario, id
        ))

        conn.commit()
        return redirect(url_for("productos", ok="editado"))

    except Exception as e:
        return f"Error al actualizar el producto: {e}"

    finally:
        if conn:
            conn.close()


# ---------------- FACTURACIÓN ----------------
@app.route("/facturacion")
def facturacion():
    if "usuario" not in session:
        return redirect("/")

    conn = None
    try:
        conn = conectar_seguro()
        c = conn.cursor()

        c.execute("SELECT * FROM productos ORDER BY tipo, nombre")
        productos = c.fetchall()

        return render_template("facturacion.html", productos=productos)

    except Exception as e:
        return f"Error en facturación: {e}"

    finally:
        if conn:
            conn.close()


@app.route("/api/facturar", methods=["POST"])
def facturar():
    conn = None
    try:
        data = request.get_json()

        productos = data.get("productos", [])
        pago_con = float(data.get("pago_con") or 0)

        if not productos:
            return jsonify({"error": "No hay productos para facturar."}), 400

        conn = conectar_seguro()
        c = conn.cursor()

        total = 0
        for p in productos:
            total += float(p["precio"]) * int(p["cantidad"])

        if pago_con < total:
            return jsonify({
                "error": f"El monto pagado no es suficiente. Faltan RD$ {(total - pago_con):.2f}"
            }), 400

        devuelta = pago_con - total

        c.execute(
            "INSERT INTO facturas(total, pago_con, devuelta) VALUES (?, ?, ?)",
            (total, pago_con, devuelta)
        )
        factura_id = c.lastrowid

        for p in productos:
            nombre_detalle = p["nombre"]
            nombre_base = p["producto_base"]
            cantidad = int(p["cantidad"])
            precio = float(p["precio"])
            subtotal = cantidad * precio

            c.execute("""
                INSERT INTO detalle_factura(factura_id, producto, cantidad, precio, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (factura_id, nombre_detalle, cantidad, precio, subtotal))

            c.execute("SELECT stock FROM productos WHERE nombre = ?", (nombre_base,))
            fila_stock = c.fetchone()

            if not fila_stock:
                conn.rollback()
                return jsonify({"error": f"No se encontró el producto base '{nombre_base}' en inventario."}), 400

            stock_actual = int(fila_stock[0])

            if cantidad > stock_actual:
                conn.rollback()
                return jsonify({"error": f"No hay suficiente stock para '{nombre_base}'."}), 400

            c.execute("""
                UPDATE productos
                SET stock = stock - ?
                WHERE nombre = ?
            """, (cantidad, nombre_base))

        conn.commit()

        return jsonify({
            "ok": True,
            "factura_id": factura_id,
            "total": total,
            "pago_con": pago_con,
            "devuelta": devuelta,
            "mensaje": "✅ Factura realizada correctamente"
        })

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": f"Ocurrió un error al facturar: {str(e)}"}), 500

    finally:
        if conn:
            conn.close()


@app.route("/factura/<int:id>")
def ver_factura(id):
    if "usuario" not in session:
        return redirect("/")

    conn = None
    try:
        conn = conectar_seguro()
        c = conn.cursor()

        c.execute("SELECT * FROM facturas WHERE id=?", (id,))
        factura = c.fetchone()

        c.execute("SELECT * FROM detalle_factura WHERE factura_id=?", (id,))
        detalles = c.fetchall()

        return render_template("factura.html", factura=factura, detalles=detalles)

    except Exception as e:
        return f"Error al ver factura: {e}"

    finally:
        if conn:
            conn.close()


# ---------------- REPORTES ----------------
@app.route("/reportes", methods=["GET", "POST"])
def reportes():
    if "usuario" not in session:
        return redirect("/")

    conn = None
    try:
        conn = conectar_seguro()
        c = conn.cursor()

        fecha_buscar = request.form.get("fecha_buscar") if request.method == "POST" else request.args.get("fecha_buscar")

        query = """
            SELECT id, fecha_cierre, total_sistema, total_real, diferencia, estado, usuario, creado_en, observaciones
            FROM cierres_caja
        """
        params = []

        if fecha_buscar:
            query += " WHERE fecha_cierre = ?"
            params.append(fecha_buscar)

        query += " ORDER BY fecha_cierre DESC, creado_en DESC"

        c.execute(query, params)
        reportes = c.fetchall()

        total_reportado = sum(float(r[2] or 0) for r in reportes) if reportes else 0
        total_real = sum(float(r[3] or 0) for r in reportes) if reportes else 0

        return render_template(
            "reportes.html",
            reportes=reportes,
            fecha_buscar=fecha_buscar,
            total_reportado=total_reportado,
            total_real=total_real
        )

    except Exception as e:
        return f"Error en reportes: {e}"

    finally:
        if conn:
            conn.close()


@app.route("/reporte/<int:id>")
def ver_reporte(id):
    if "usuario" not in session:
        return redirect("/")

    conn = None
    try:
        conn = conectar_seguro()
        try:
            conn.row_factory = lambda cursor, row: {
                col[0]: row[idx] for idx, col in enumerate(cursor.description)
            }
        except Exception:
            pass

        c = conn.cursor()

        c.execute("""
            SELECT *
            FROM cierres_caja
            WHERE id = ?
        """, (id,))
        reporte = c.fetchone()

        if not reporte:
            return "❌ No se encontró el reporte"

        fecha_cierre = reporte["fecha_cierre"] if isinstance(reporte, dict) else reporte[1]

        c.execute("""
            SELECT id, fecha, total
            FROM facturas
            WHERE DATE(fecha) = ?
            ORDER BY fecha DESC
        """, (fecha_cierre,))
        facturas = c.fetchall()

        return render_template("reporte_detalle.html", reporte=reporte, facturas=facturas)

    except Exception as e:
        return f"Error al ver reporte: {e}"

    finally:
        if conn:
            conn.close()


@app.route("/eliminar_reporte/<int:id>")
def eliminar_reporte(id):
    if "usuario" not in session:
        return redirect("/")

    conn = None
    try:
        conn = conectar_seguro()
        c = conn.cursor()

        c.execute("SELECT id FROM cierres_caja WHERE id = ?", (id,))
        existe = c.fetchone()

        if not existe:
            return "❌ El reporte no existe."

        c.execute("DELETE FROM cierres_caja WHERE id = ?", (id,))
        conn.commit()

        return redirect("/reportes")

    except Exception as e:
        if conn:
            conn.rollback()
        return f"Error al eliminar el reporte: {e}"

    finally:
        if conn:
            conn.close()


@app.route("/api/grafica_ventas")
def grafica_ventas():
    if "usuario" not in session:
        return jsonify({"fechas": [], "totales": []})

    conn = None
    try:
        conn = conectar_seguro()
        c = conn.cursor()

        c.execute("""
            SELECT DATE(fecha), SUM(total)
            FROM facturas
            GROUP BY DATE(fecha)
            ORDER BY DATE(fecha)
        """)

        datos = c.fetchall()
        fechas = [d[0] for d in datos]
        totales = [d[1] for d in datos]

        return jsonify({"fechas": fechas, "totales": totales})

    except Exception:
        return jsonify({"fechas": [], "totales": []})

    finally:
        if conn:
            conn.close()


@app.route("/graficas")
def graficas():
    if "usuario" not in session:
        return redirect("/")
    return render_template("graficas.html")


@app.route("/ventas", methods=["GET", "POST"])
def ventas():
    if "usuario" not in session:
        return redirect("/")

    conn = None
    try:
        conn = conectar_seguro()
        c = conn.cursor()

        fecha_inicio = request.form.get("fecha_inicio") if request.method == "POST" else request.args.get("fecha_inicio")
        fecha_fin = request.form.get("fecha_fin") if request.method == "POST" else request.args.get("fecha_fin")

        query = "SELECT * FROM facturas"
        params = []

        if fecha_inicio and fecha_fin:
            query += " WHERE DATE(fecha) BETWEEN ? AND ?"
            params = [fecha_inicio, fecha_fin]
        elif fecha_inicio:
            query += " WHERE DATE(fecha) = ?"
            params = [fecha_inicio]

        query += " ORDER BY fecha DESC"

        c.execute(query, params)
        ventas = c.fetchall()

        total = sum(float(v[2]) for v in ventas) if ventas else 0

        return render_template(
            "ventas.html",
            ventas=ventas,
            total=total,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )

    except Exception as e:
        return f"Error en ventas: {e}"

    finally:
        if conn:
            conn.close()


@app.route("/eliminar_venta/<int:id>")
def eliminar_venta(id):
    if "usuario" not in session:
        return redirect("/")

    conn = None
    try:
        conn = conectar_seguro()
        c = conn.cursor()

        c.execute("""
            SELECT producto, cantidad
            FROM detalle_factura
            WHERE factura_id = ?
        """, (id,))
        detalles = c.fetchall()

        if not detalles:
            return "❌ No se encontró la venta o no tiene detalles."

        for detalle in detalles:
            nombre_detalle = detalle[0]
            cantidad = int(detalle[1])

            if " (" in nombre_detalle:
                nombre_base = nombre_detalle.split(" (")[0]
            else:
                nombre_base = nombre_detalle

            c.execute("""
                UPDATE productos
                SET stock = stock + ?
                WHERE nombre = ?
            """, (cantidad, nombre_base))

        c.execute("DELETE FROM detalle_factura WHERE factura_id = ?", (id,))
        c.execute("DELETE FROM facturas WHERE id = ?", (id,))

        conn.commit()
        return redirect("/ventas")

    except Exception as e:
        if conn:
            conn.rollback()
        return f"Error al eliminar la venta: {e}"

    finally:
        if conn:
            conn.close()


@app.route("/estadisticas")
def estadisticas():
    if "usuario" not in session:
        return redirect("/")

    conn = None
    try:
        conn = conectar_seguro()
        c = conn.cursor()

        c.execute("SELECT SUM(total) FROM facturas")
        total = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM facturas")
        cantidad = c.fetchone()[0]

        c.execute("""
            SELECT DATE(fecha), SUM(total)
            FROM facturas
            GROUP BY DATE(fecha)
            ORDER BY DATE(fecha)
        """)
        datos = c.fetchall()

        fechas = [d[0] for d in datos]
        totales = [d[1] for d in datos]

        return render_template(
            "estadisticas.html",
            total=total,
            cantidad=cantidad,
            fechas=fechas,
            totales=totales
        )

    except Exception as e:
        return f"Error en estadísticas: {e}"

    finally:
        if conn:
            conn.close()


@app.route("/ganancias")
def ganancias():
    if "usuario" not in session:
        return redirect("/")

    conn = None
    try:
        conn = conectar_seguro()
        c = conn.cursor()

        c.execute("SELECT COALESCE(SUM(total), 0) FROM facturas")
        total_vendido = float(c.fetchone()[0] or 0)

        c.execute("""
            SELECT nombre, precio, stock, tipo,
                   COALESCE(precio_pequeno, 0),
                   COALESCE(precio_grande, 0),
                   COALESCE(inversion_total, 0),
                   COALESCE(costo_unitario, 0)
            FROM productos
        """)
        productos = c.fetchall()

        productos_dict = {}
        valor_inventario = 0.0

        for p in productos:
            nombre = p[0]
            stock = int(p[2] or 0)
            costo_unitario = float(p[7] or 0)

            productos_dict[nombre] = {
                "costo_unitario": costo_unitario
            }

            valor_inventario += stock * costo_unitario

        c.execute("""
            SELECT producto, cantidad, precio, subtotal
            FROM detalle_factura
        """)
        detalles = c.fetchall()

        costo_total_vendido = 0.0
        ingreso_total_detalle = 0.0

        for d in detalles:
            nombre_detalle = d[0]
            cantidad = int(d[1] or 0)
            subtotal = float(d[3] or 0)

            ingreso_total_detalle += subtotal

            if " (" in nombre_detalle:
                nombre_base = nombre_detalle.split(" (")[0]
            else:
                nombre_base = nombre_detalle

            costo_producto = 0.0
            if nombre_base in productos_dict:
                costo_producto = float(productos_dict[nombre_base]["costo_unitario"] or 0)

            costo_total_vendido += costo_producto * cantidad

        ganancia_total = ingreso_total_detalle - costo_total_vendido

        if ganancia_total > 0:
            capital_reinversion = ganancia_total * 0.60
            ahorro_reserva = ganancia_total * 0.20
            fondo_imprevistos = ganancia_total * 0.20
        else:
            capital_reinversion = 0
            ahorro_reserva = 0
            fondo_imprevistos = 0

        return render_template(
            "ganancias.html",
            total_vendido=total_vendido,
            ingreso_total_detalle=ingreso_total_detalle,
            costo_total_vendido=costo_total_vendido,
            ganancia_total=ganancia_total,
            valor_inventario=valor_inventario,
            capital_reinversion=capital_reinversion,
            ahorro_reserva=ahorro_reserva,
            fondo_imprevistos=fondo_imprevistos
        )

    except Exception as e:
        return f"Error en ganancias: {e}"

    finally:
        if conn:
            conn.close()


# ---------------- CAJA ----------------
@app.route("/caja", methods=["GET", "POST"])
def caja():
    if "usuario" not in session:
        return redirect("/")

    conn = None
    try:
        fecha = request.form.get("fecha") if request.method == "POST" else request.args.get("fecha")

        conn = conectar_seguro()
        c = conn.cursor()

        if not fecha:
            c.execute("SELECT DATE('now')")
            fecha = c.fetchone()[0]

        c.execute("""
            SELECT id, fecha, total
            FROM facturas
            WHERE DATE(fecha) = ?
            ORDER BY fecha DESC
        """, (fecha,))
        facturas = c.fetchall()

        c.execute("""
            SELECT COUNT(*), COALESCE(SUM(total), 0)
            FROM facturas
            WHERE DATE(fecha) = ?
        """, (fecha,))
        resumen = c.fetchone()

        cantidad_facturas = resumen[0]
        total_sistema = float(resumen[1] or 0)

        cant_5 = 0
        cant_10 = 0
        cant_25 = 0
        cant_50 = 0
        cant_100 = 0
        cant_200 = 0
        cant_500 = 0
        cant_1000 = 0
        cant_2000 = 0

        observaciones = ""
        total_real = 0.0
        diferencia = None
        estado = None
        cierre_guardado = False
        ultimo_cierre_id = None

        if request.method == "POST":
            cant_5 = int(request.form.get("cant_5") or 0)
            cant_10 = int(request.form.get("cant_10") or 0)
            cant_25 = int(request.form.get("cant_25") or 0)
            cant_50 = int(request.form.get("cant_50") or 0)
            cant_100 = int(request.form.get("cant_100") or 0)
            cant_200 = int(request.form.get("cant_200") or 0)
            cant_500 = int(request.form.get("cant_500") or 0)
            cant_1000 = int(request.form.get("cant_1000") or 0)
            cant_2000 = int(request.form.get("cant_2000") or 0)
            observaciones = request.form.get("observaciones", "").strip()

            total_real = (
                cant_5 * 5 +
                cant_10 * 10 +
                cant_25 * 25 +
                cant_50 * 50 +
                cant_100 * 100 +
                cant_200 * 200 +
                cant_500 * 500 +
                cant_1000 * 1000 +
                cant_2000 * 2000
            )

            diferencia = round(total_real - total_sistema, 2)

            if diferencia == 0:
                estado = "cuadrada"
            elif diferencia > 0:
                estado = "sobrante"
            else:
                estado = "faltante"

            guardar = request.form.get("guardar_cierre")

            if guardar == "si":
                c.execute("""
                    INSERT INTO cierres_caja(
                        fecha_cierre, total_sistema, total_real, diferencia, estado,
                        cant_5, cant_10, cant_25, cant_50, cant_100,
                        cant_200, cant_500, cant_1000, cant_2000,
                        observaciones, usuario
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fecha, total_sistema, total_real, diferencia, estado,
                    cant_5, cant_10, cant_25, cant_50, cant_100,
                    cant_200, cant_500, cant_1000, cant_2000,
                    observaciones, session.get("usuario", "")
                ))
                ultimo_cierre_id = c.lastrowid
                conn.commit()
                cierre_guardado = True

        c.execute("""
            SELECT id, fecha_cierre, total_sistema, total_real, diferencia, estado, usuario, creado_en
            FROM cierres_caja
            ORDER BY creado_en DESC
            LIMIT 10
        """)
        cierres = c.fetchall()

        return render_template(
            "caja.html",
            fecha=fecha,
            facturas=facturas,
            cantidad_facturas=cantidad_facturas,
            total_sistema=total_sistema,
            cant_5=cant_5,
            cant_10=cant_10,
            cant_25=cant_25,
            cant_50=cant_50,
            cant_100=cant_100,
            cant_200=cant_200,
            cant_500=cant_500,
            cant_1000=cant_1000,
            cant_2000=cant_2000,
            observaciones=observaciones,
            total_real=total_real,
            diferencia=diferencia,
            estado=estado,
            cierre_guardado=cierre_guardado,
            ultimo_cierre_id=ultimo_cierre_id,
            cierres=cierres
        )

    except Exception as e:
        return f"Error en caja: {e}"

    finally:
        if conn:
            conn.close()


@app.route("/cierre/<int:id>")
def ver_cierre(id):
    if "usuario" not in session:
        return redirect("/")

    conn = None
    try:
        conn = conectar_seguro()
        try:
            conn.row_factory = lambda cursor, row: {
                col[0]: row[idx] for idx, col in enumerate(cursor.description)
            }
        except Exception:
            pass

        c = conn.cursor()

        c.execute("SELECT * FROM cierres_caja WHERE id = ?", (id,))
        cierre = c.fetchone()

        if not cierre:
            return "❌ No se encontró el cierre"

        return render_template("cierre_detalle.html", cierre=cierre)

    except Exception as e:
        return f"Error al ver cierre: {e}"

    finally:
        if conn:
            conn.close()


# ---------------- EJECUCIÓN ----------------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)