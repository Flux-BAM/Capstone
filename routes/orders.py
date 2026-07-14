from flask import Blueprint, render_template, request, redirect, session, jsonify, flash
import MySQLdb.cursors
from extensions import mysql
from helpers import is_logged_in, parse_iso_date

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/orders', methods=['GET', 'POST'])
def orders():
    if not is_logged_in():
        return redirect('/')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity   = int(request.form['quantity'])
        cursor.execute("SELECT price FROM products WHERE id=%s", (product_id,))
        product  = cursor.fetchone()
        price    = product['price']
        subtotal = quantity * price
        cursor.execute("INSERT INTO sales (total, created_at) VALUES (%s, NOW())", (subtotal,))
        sale_id = cursor.lastrowid
        cursor.execute("""
            INSERT INTO sale_items (sale_id, product_id, quantity, price, subtotal)
            VALUES (%s,%s,%s,%s,%s)
        """, (sale_id, product_id, quantity, price, subtotal))
        cursor.execute("UPDATE products SET stock = stock - %s WHERE id=%s", (quantity, product_id))
        mysql.connection.commit()
        return redirect('/orders')

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    return render_template('orders.html', products=products, username=session['username'])


@orders_bp.route('/submit_order', methods=['POST'])
def submit_order():
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid payload"}), 400

    customer = data.get('customer', '').strip()
    cart     = data.get('cart', [])

    if not customer:
        return jsonify({"status": "error", "message": "Customer name is required"}), 400
    if not isinstance(cart, list) or not cart:
        return jsonify({"status": "error", "message": "Cart is empty"}), 400

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        total = sum(float(item['subtotal']) for item in cart)
    except (KeyError, TypeError, ValueError):
        return jsonify({"status": "error", "message": "Invalid cart values"}), 400

    for item in cart:
        cursor.execute("SELECT ingredient_id, quantity FROM recipes WHERE product_id = %s", (item['id'],))
        for r in cursor.fetchall():
            cursor.execute("SELECT stock FROM ingredients WHERE id=%s", (r['ingredient_id'],))
            current = cursor.fetchone()['stock']
            if current < r['quantity'] * item['qty']:
                return jsonify({"status": "error", "message": "Not enough ingredients"}), 400

    try:
        cursor.execute("INSERT INTO sales (customer_name,total,created_at) VALUES (%s,%s,NOW())", (customer, total))
        sale_id = cursor.lastrowid
        for item in cart:
            cursor.execute("""
                INSERT INTO sale_items (sale_id,product_id,quantity,price,subtotal)
                VALUES (%s,%s,%s,%s,%s)
            """, (sale_id, item['id'], item['qty'], item['price'], item['subtotal']))
            cursor.execute("UPDATE products SET stock=stock-%s WHERE id=%s", (item['qty'], item['id']))
            cursor.execute("SELECT ingredient_id, quantity FROM recipes WHERE product_id = %s", (item['id'],))
            for r in cursor.fetchall():
                cursor.execute("UPDATE ingredients SET stock = stock - %s WHERE id = %s",
                               (r['quantity'] * item['qty'], r['ingredient_id']))
        mysql.connection.commit()
        return jsonify({"status": "success"})
    except Exception:
        mysql.connection.rollback()
        return jsonify({"status": "error", "message": "Failed to save order"}), 500


@orders_bp.route('/view_orders')
def view_orders():
    if not is_logged_in():
        return redirect('/')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    q         = (request.args.get('q') or '').strip()
    from_date = request.args.get('from')
    to_date   = request.args.get('to')
    page      = max(int(request.args.get('page', 1) or 1), 1)
    per_page  = 20
    offset    = (page - 1) * per_page

    where_clauses = []
    params = []

    if q:
        where_clauses.append("(sales.customer_name LIKE %s OR products.name LIKE %s)")
        like = f"%{q}%"
        params.extend([like, like])

    if from_date and to_date:
        parsed_from = parse_iso_date(from_date)
        parsed_to   = parse_iso_date(to_date)
        if not parsed_from or not parsed_to or parsed_from > parsed_to:
            flash("Invalid date range filter.", "danger")
            return redirect('/view_orders')
        where_clauses.append("DATE(sales.created_at) BETWEEN %s AND %s")
        params.extend([from_date, to_date])

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    cursor.execute(f"""
        SELECT COUNT(*) AS total_rows FROM sales
        JOIN sale_items ON sales.id = sale_items.sale_id
        JOIN products ON products.id = sale_items.product_id
        {where_sql}
    """, params)
    total_rows  = cursor.fetchone()['total_rows'] or 0
    total_pages = max((total_rows + per_page - 1) // per_page, 1)

    if page > total_pages:
        page   = total_pages
        offset = (page - 1) * per_page

    cursor.execute(f"""
        SELECT sale_items.id AS item_id, sales.created_at,
               sales.customer_name, products.name AS product_name,
               sale_items.quantity, sale_items.subtotal
        FROM sales
        JOIN sale_items ON sales.id = sale_items.sale_id
        JOIN products ON products.id = sale_items.product_id
        {where_sql}
        ORDER BY sales.created_at DESC
        LIMIT %s OFFSET %s
    """, params + [per_page, offset])
    orders = cursor.fetchall()

    cursor.execute(f"""
        SELECT COALESCE(SUM(sale_items.subtotal), 0) AS total_revenue
        FROM sales
        JOIN sale_items ON sales.id = sale_items.sale_id
        JOIN products ON products.id = sale_items.product_id
        {where_sql}
    """, params)
    total_revenue = float(cursor.fetchone()['total_revenue'] or 0)

    return render_template(
        'view_orders.html',
        orders=orders, total_revenue=total_revenue,
        page=page, per_page=per_page,
        total_rows=total_rows, total_pages=total_pages,
        q=q, from_date=from_date or '', to_date=to_date or ''
    )


@orders_bp.route('/done_order/<int:item_id>', methods=['POST'])
def done_order(item_id):
    if not is_logged_in():
        return redirect('/')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("DELETE FROM sale_items WHERE id = %s", (item_id,))
    mysql.connection.commit()
    return redirect('/view_orders')