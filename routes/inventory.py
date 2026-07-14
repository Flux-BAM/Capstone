from flask import Blueprint, render_template, request, redirect, session, jsonify, flash
import MySQLdb.cursors
from extensions import mysql
from helpers import is_logged_in

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if not is_logged_in():
        return redirect('/')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        ingredient_id = request.form.get('ingredient_id')
        stock_raw     = request.form.get('stock', '').strip()
        try:
            stock = int(stock_raw)
            if stock < 0:
                flash("Stock cannot be negative.", "danger")
                return redirect('/inventory')
        except ValueError:
            flash("Invalid stock value.", "danger")
            return redirect('/inventory')

        cursor.execute("SELECT id, name FROM ingredients WHERE id = %s", (ingredient_id,))
        ingredient = cursor.fetchone()
        if not ingredient:
            flash("Ingredient not found.", "danger")
            return redirect('/inventory')

        try:
            cursor.execute("UPDATE ingredients SET stock = %s WHERE id = %s", (stock, ingredient_id))
            mysql.connection.commit()
            flash(f"Updated {ingredient['name']} stock to {stock}.", "success")
        except Exception:
            mysql.connection.rollback()
            flash("Failed to update stock.", "danger")

        return redirect('/inventory')

    cursor.execute("SELECT * FROM ingredients ORDER BY name ASC")
    ingredients = cursor.fetchall()
    return render_template("inventory.html", ingredients=ingredients, username=session['username'])


@inventory_bp.route('/inventory/update', methods=['POST'])
def inventory_update():
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    ingredient_id = request.form.get('ingredient_id')
    stock_raw     = (request.form.get('stock') or '').strip()

    try:
        stock = int(stock_raw)
        if stock < 0:
            return jsonify({"status": "error", "message": "Stock cannot be negative."}), 400
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Invalid stock value."}), 400

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id, name FROM ingredients WHERE id = %s", (ingredient_id,))
    ingredient = cursor.fetchone()
    if not ingredient:
        return jsonify({"status": "error", "message": "Ingredient not found."}), 404

    try:
        cursor.execute("UPDATE ingredients SET stock = %s WHERE id = %s", (stock, ingredient_id))
        mysql.connection.commit()
        return jsonify({
            "status": "success",
            "message": f"Updated {ingredient['name']} stock to {stock}.",
            "ingredient_id": int(ingredient_id),
            "stock": stock
        })
    except Exception:
        mysql.connection.rollback()
        return jsonify({"status": "error", "message": "Failed to update stock."}), 500


@inventory_bp.route('/inventory/usage')
def inventory_usage():
    if not is_logged_in():
        return jsonify({}), 401

    period = request.args.get('period', '7')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if period == '7':
        date_cond = "s.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
    elif period == '30':
        date_cond = "s.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
    else:
        date_cond = "1=1"

    cursor.execute(f"""
        SELECT
            i.id, i.name, i.unit,
            i.stock                                          AS current_stock,
            COALESCE(SUM(r.quantity * si.quantity), 0)       AS total_used,
            COUNT(DISTINCT s.id)                             AS order_count,
            COALESCE(
                SUM(r.quantity * si.quantity) / NULLIF(COUNT(DISTINCT s.id), 0),
                0
            )                                                AS avg_per_order
        FROM ingredients i
        LEFT JOIN recipes r      ON r.ingredient_id = i.id
        LEFT JOIN sale_items si  ON si.product_id   = r.product_id
        LEFT JOIN sales s        ON s.id            = si.sale_id
            AND {date_cond}
        GROUP BY i.id, i.name, i.unit, i.stock
        ORDER BY total_used DESC
    """)
    rows = cursor.fetchall()

    usage = [
        {
            "id":            r['id'],
            "name":          r['name'],
            "unit":          r['unit'],
            "current_stock": float(r['current_stock'] or 0),
            "total_used":    round(float(r['total_used'] or 0), 2),
            "order_count":   int(r['order_count'] or 0),
            "avg_per_order": round(float(r['avg_per_order'] or 0), 3),
        }
        for r in rows
    ]

    return jsonify({"usage": usage, "period": period})


@inventory_bp.route('/inventory/servings')
def inventory_servings():
    if not is_logged_in():
        return jsonify({}), 401

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id, name, category FROM products ORDER BY name ASC")
    products = cursor.fetchall()

    servings = []
    for prod in products:
        cursor.execute("""
            SELECT r.ingredient_id, r.quantity, i.name AS ing_name, i.unit, i.stock
            FROM recipes r
            JOIN ingredients i ON r.ingredient_id = i.id
            WHERE r.product_id = %s
        """, (prod['id'],))
        recipe = cursor.fetchall()

        if not recipe:
            servings.append({
                "id": prod['id'], "name": prod['name'], "category": prod['category'] or '',
                "max_servings": None, "limiting_ingredient": None,
                "limiting_stock": None, "limiting_unit": None,
            })
            continue

        max_servings = None; limiting_ing = None; limiting_stock = None; limiting_unit = None

        for r in recipe:
            qty_per = float(r['quantity'] or 0)
            stock   = float(r['stock']    or 0)
            if qty_per <= 0: continue
            possible = int(stock / qty_per)
            if max_servings is None or possible < max_servings:
                max_servings = possible; limiting_ing = r['ing_name']
                limiting_stock = round(stock, 2); limiting_unit = r['unit']

        if max_servings is None:
            max_servings = 0

        servings.append({
            "id": prod['id'], "name": prod['name'], "category": prod['category'] or '',
            "max_servings": max_servings,
            "limiting_ingredient": limiting_ing   if max_servings is not None else None,
            "limiting_stock":      limiting_stock if max_servings is not None else None,
            "limiting_unit":       limiting_unit  if max_servings is not None else None,
        })

    servings.sort(key=lambda x: (
        0 if x['max_servings'] == 0
        else 1 if x['max_servings'] is not None and x['max_servings'] <= 5
        else 2 if x['max_servings'] is None
        else 3
    ))

    return jsonify({"servings": servings})


@inventory_bp.route('/add-ingredient', methods=['GET', 'POST'])
def add_ingredient():
    if not is_logged_in():
        return redirect('/')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM ingredients ORDER BY name ASC")
    ingredients = cursor.fetchall()

    if request.method == 'POST':
        name  = request.form.get('name', '').strip()
        unit  = request.form.get('unit', '').strip()
        stock = request.form.get('stock', '0').strip()

        if not name:
            flash("Ingredient name is required.", "danger")
            return render_template('add_ingredient.html', ingredients=ingredients)
        if not unit:
            flash("Unit is required.", "danger")
            return render_template('add_ingredient.html', ingredients=ingredients)

        try:
            stock = float(stock)
            if stock < 0: raise ValueError
        except ValueError:
            flash("Invalid stock value.", "danger")
            return render_template('add_ingredient.html', ingredients=ingredients)

        cursor.execute("SELECT id FROM ingredients WHERE name = %s", (name,))
        if cursor.fetchone():
            flash(f"'{name}' already exists.", "warning")
            return render_template('add_ingredient.html', ingredients=ingredients)

        try:
            cursor.execute("INSERT INTO ingredients (name, stock, unit) VALUES (%s,%s,%s)", (name, stock, unit))
            mysql.connection.commit()
            flash(f"'{name}' added successfully!", "success")
            return redirect('/add-ingredient')
        except Exception:
            mysql.connection.rollback()
            flash("Failed to save ingredient.", "danger")
            return render_template('add_ingredient.html', ingredients=ingredients)

    return render_template('add_ingredient.html', ingredients=ingredients)


@inventory_bp.route('/delete-ingredient/<int:ingredient_id>', methods=['POST'])
def delete_ingredient(ingredient_id):
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT name FROM ingredients WHERE id = %s", (ingredient_id,))
    ingredient = cursor.fetchone()
    if not ingredient:
        return jsonify({"status": "error", "message": "Ingredient not found."}), 404

    try:
        cursor.execute("DELETE FROM recipes     WHERE ingredient_id = %s", (ingredient_id,))
        cursor.execute("DELETE FROM ingredients WHERE id = %s",            (ingredient_id,))
        mysql.connection.commit()
        return jsonify({"status": "success", "message": f"'{ingredient['name']}' deleted."})
    except Exception:
        mysql.connection.rollback()
        return jsonify({"status": "error", "message": "Failed to delete ingredient."}), 500