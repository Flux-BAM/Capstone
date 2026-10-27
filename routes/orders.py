from flask import Blueprint, render_template, request, redirect, session, jsonify, flash
from models.product import Product
from models.sale import Sale
from helpers import is_logged_in, parse_iso_date
from extensions import mysql
import MySQLdb.cursors

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/orders', methods=['GET', 'POST'])
def orders():
    if not is_logged_in():
        return redirect('/login')

    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity   = int(request.form['quantity'])

        # OOP: get Product object to access price
        product  = Product.get_by_id(product_id)
        subtotal = quantity * float(product.price)

        # OOP: Sale.create() handles the full transaction
        Sale.create('Walk-in', subtotal, [{
            'id':       product_id,
            'qty':      quantity,
            'price':    float(product.price),
            'subtotal': subtotal
        }])
        return redirect('/orders')

    # OOP: Product.get_all() returns list of Product objects
    all_products = Product.get_all()
    return render_template('orders.html', products=all_products, username=session['username'])


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

    try:
        total = sum(float(item['subtotal']) for item in cart)
    except (KeyError, TypeError, ValueError):
        return jsonify({"status": "error", "message": "Invalid cart values"}), 400

    # OOP: Sale.check_stock() validates ingredients before inserting
    stock_error = Sale.check_stock(cart)
    if stock_error:
        return jsonify({"status": "error", "message": stock_error}), 400

    try:
        # OOP: Sale.create() handles full transaction atomically
        Sale.create(customer, total, cart)
        return jsonify({"status": "success"})
    except Exception:
        return jsonify({"status": "error", "message": "Failed to save order"}), 500


@orders_bp.route('/view_orders')
def view_orders():
    if not is_logged_in():
        return redirect('/login')

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
        return redirect('/login')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("DELETE FROM sale_items WHERE id = %s", (item_id,))
    mysql.connection.commit()
    return redirect('/view_orders')