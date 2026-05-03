from flask import Flask, render_template, request, redirect, session, jsonify, Response, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import MySQLdb.cursors
import csv
import io
import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'brewinsight'

# Image upload config
UPLOAD_FOLDER   = os.path.join('static', 'images')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
MAX_IMAGE_SIZE   = 5 * 1024 * 1024   # 5 MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mysql = MySQL(app)


# ── Helpers ──────────────────────────────────────────────────────────────────

def is_logged_in():
    return bool(session.get('loggedin'))


def parse_iso_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ── LOGIN ─────────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
def login():
    error = False
    register_success = request.args.get('register_success')
    register_error   = request.args.get('register_error')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['loggedin'] = True
            session['id']       = user['id']
            session['username'] = user['username']
            return redirect('/dashboard?login_success=true')
        else:
            error = True

    return render_template('login.html', error=error,
                           register_success=register_success,
                           register_error=register_error)


# ── REGISTER ──────────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        if cursor.fetchone():
            return redirect('/?register_error=1')

        cursor.execute("INSERT INTO users (username, password) VALUES (%s,%s)", (username, password))
        mysql.connection.commit()
        return redirect('/?register_success=1')

    return redirect('/')


# ── DASHBOARD ─────────────────────────────────────────────────────────────────

@app.route('/dashboard')
def dashboard():
    if not is_logged_in():
        return redirect('/')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("SELECT COALESCE(SUM(total), 0) as total FROM sales")
    total_sales = cursor.fetchone()['total'] or 0

    cursor.execute("""
        SELECT DATE(created_at) AS day, SUM(total) AS total
        FROM sales GROUP BY DATE(created_at) ORDER BY day
    """)
    daily_sales_rows = cursor.fetchall()
    daily_sales = [
        {"day": str(r["day"]), "label": r["day"].strftime("%b %d"), "total": float(r["total"] or 0)}
        for r in daily_sales_rows
    ]

    cursor.execute("""
        SELECT p.name, SUM(si.quantity) as total_sold
        FROM sale_items si JOIN products p ON si.product_id = p.id
        GROUP BY p.name
    """)
    product_data = cursor.fetchall()

    cursor.execute("""
        SELECT HOUR(created_at) as hour, COUNT(*) as total
        FROM sales GROUP BY hour ORDER BY hour
    """)
    peak_hours = cursor.fetchall() or []

    cursor.execute("""
        SELECT DATE_FORMAT(created_at, '%Y-%m') as month, SUM(total) as total
        FROM sales GROUP BY month ORDER BY month
    """)
    monthly_sales = cursor.fetchall()

    cursor.execute("""
        SELECT YEAR(created_at) as year, WEEK(created_at, 1) as week_number, SUM(total) as total
        FROM sales GROUP BY year, week_number ORDER BY year, week_number
    """)
    weekly_sales_raw = cursor.fetchall()

    weekly_sales = []
    for w in weekly_sales_raw:
        year  = w['year']
        week  = w['week_number']
        total = w['total']
        monday     = datetime.date.fromisocalendar(year, week, 1)
        sunday     = datetime.date.fromisocalendar(year, week, 7)
        week_range = f"{monday.strftime('%b %d')} - {sunday.strftime('%b %d')}"
        weekly_sales.append({"week_range": week_range, "total": total})

    cursor.execute("""
        SELECT p.name, SUM(si.quantity) as total_sold
        FROM sale_items si JOIN products p ON si.product_id = p.id
        JOIN sales s ON si.sale_id = s.id
        WHERE DATE(s.created_at) = CURDATE()
        GROUP BY p.name ORDER BY total_sold DESC LIMIT 5
    """)
    best_sellers_today = cursor.fetchall()

    cursor.execute("""
        SELECT s.customer_name, p.name as product_name, si.subtotal
        FROM sales s JOIN sale_items si ON s.id = si.sale_id
        JOIN products p ON si.product_id = p.id
        ORDER BY s.created_at DESC LIMIT 5
    """)
    recent_orders = cursor.fetchall()

    cursor.execute("""
        SELECT name, stock, unit FROM ingredients
        WHERE stock <= 20 ORDER BY stock ASC LIMIT 5
    """)
    low_stock = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) as total_customers FROM sales")
    total_customers = cursor.fetchone()['total_customers'] or 0

    cursor.execute("SELECT COUNT(*) as orders_today FROM sales WHERE DATE(created_at) = CURDATE()")
    orders_today = cursor.fetchone()['orders_today'] or 0

    cursor.execute("SELECT COUNT(DISTINCT customer_name) as customers_today FROM sales WHERE DATE(created_at) = CURDATE()")
    customers_today = cursor.fetchone()['customers_today'] or 0

    cursor.execute("SELECT COALESCE(AVG(total), 0) as avg_order_value FROM sales")
    avg_order_value = cursor.fetchone()['avg_order_value'] or 0

    return render_template(
        'dashboard.html',
        username=session['username'],
        total_sales=total_sales,
        product_data=product_data,
        daily_sales=daily_sales,
        monthly_sales=monthly_sales,
        weekly_sales=weekly_sales,
        peak_hours=peak_hours,
        best_sellers_today=best_sellers_today,
        total_customers=total_customers,
        orders_today=orders_today,
        customers_today=customers_today,
        avg_order_value=avg_order_value,
        recent_orders=recent_orders,
        low_stock=low_stock
    )


# ── RANGE CONDITIONS ──────────────────────────────────────────────────────────

def build_range_conditions(range_type, table_alias=None, from_date=None, to_date=None):
    col = "created_at" if not table_alias else f"{table_alias}.created_at"
    if range_type == "all":
        return "1=1", []
    if range_type == "today":
        return f"DATE({col}) = CURDATE()", []
    if range_type == "7d":
        return f"{col} >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)", []
    if range_type == "30d":
        return f"{col} >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)", []
    if range_type == "custom":
        return f"DATE({col}) BETWEEN %s AND %s", [from_date, to_date]
    return "1=1", []


# ── ANALYTICS FILTER ─────────────────────────────────────────────────────────

@app.route('/analytics-filter')
def analytics_filter():
    if not is_logged_in():
        return jsonify({}), 401

    range_type = request.args.get('range', 'today')
    from_date  = request.args.get('from')
    to_date    = request.args.get('to')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if range_type == "custom":
        if not from_date or not to_date:
            range_type = "all"
        else:
            parsed_from = parse_iso_date(from_date)
            parsed_to   = parse_iso_date(to_date)
            if not parsed_from or not parsed_to:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
            if parsed_from > parsed_to:
                return jsonify({"error": "Start date must be before end date"}), 400

    date_cond, date_params = build_range_conditions(range_type, None,  from_date, to_date)
    sale_cond, sale_params = build_range_conditions(range_type, "s",   from_date, to_date)

    cursor.execute(f"SELECT COALESCE(SUM(total), 0) AS total FROM sales WHERE {date_cond}", date_params)
    total_sales = float(cursor.fetchone()['total'] or 0)

    cursor.execute(f"SELECT COUNT(*) AS cnt FROM sales WHERE {date_cond}", date_params)
    orders_today = int(cursor.fetchone()['cnt'] or 0)

    cursor.execute(f"SELECT COUNT(DISTINCT customer_name) AS cnt FROM sales WHERE {date_cond}", date_params)
    customers_today = int(cursor.fetchone()['cnt'] or 0)

    cursor.execute(f"""
        SELECT DATE(created_at) AS day, SUM(total) AS total
        FROM sales WHERE {date_cond}
        GROUP BY DATE(created_at) ORDER BY day
    """, date_params)
    daily_sales = [
        {"day": str(r["day"]), "label": r["day"].strftime("%b %d"), "total": float(r["total"] or 0)}
        for r in cursor.fetchall()
    ]

    cursor.execute(f"""
        SELECT p.name, SUM(si.quantity) AS total_sold
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        JOIN sales s ON si.sale_id = s.id
        WHERE {sale_cond}
        GROUP BY p.name ORDER BY total_sold DESC
    """, sale_params)
    product_data = [{'name': r['name'], 'total_sold': int(r['total_sold'] or 0)} for r in cursor.fetchall()]

    cursor.execute(f"""
        SELECT HOUR(created_at) AS hour, COUNT(*) AS total
        FROM sales WHERE {date_cond}
        GROUP BY hour ORDER BY hour
    """, date_params)
    peak_hours = [{'hour': int(r['hour']), 'total': int(r['total'])} for r in cursor.fetchall()]

    cursor.execute(f"""
        SELECT p.name, SUM(si.quantity) AS total_sold
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        JOIN sales s ON si.sale_id = s.id
        WHERE {sale_cond}
        GROUP BY p.name ORDER BY total_sold DESC LIMIT 5
    """, sale_params)
    best_sellers = [{'name': r['name'], 'total_sold': int(r['total_sold'] or 0)} for r in cursor.fetchall()]

    return jsonify({
        "total_sales":     total_sales,
        "orders_today":    orders_today,
        "customers_today": customers_today,
        "daily_sales":     daily_sales,
        "product_data":    product_data,
        "peak_hours":      peak_hours,
        "best_sellers":    best_sellers,
    })


# ── EXPORT CSV ────────────────────────────────────────────────────────────────

@app.route('/export-csv')
def export_csv():
    if not is_logged_in():
        return redirect('/')

    range_type = request.args.get('range', 'today')
    from_date  = request.args.get('from')
    to_date    = request.args.get('to')

    if range_type == "custom":
        parsed_from = parse_iso_date(from_date)
        parsed_to   = parse_iso_date(to_date)
        if not parsed_from or not parsed_to or parsed_from > parsed_to:
            return jsonify({"error": "Invalid custom date range"}), 400

    date_cond, params = build_range_conditions(range_type, None, from_date, to_date)

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(f"""
        SELECT created_at, customer_name, total
        FROM sales WHERE {date_cond} ORDER BY created_at DESC
    """, params)
    rows = cursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["created_at", "customer_name", "total"])
    for row in rows:
        writer.writerow([row.get("created_at"), row.get("customer_name") or "Walk-in", row.get("total") or 0])

    csv_data = output.getvalue()
    output.close()

    filename = f"sales_{range_type}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(csv_data, mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={filename}"})


# ── LIVE DATA ─────────────────────────────────────────────────────────────────

@app.route('/live-data')
def live_data():
    if not is_logged_in():
        return jsonify({}), 401

    range_type = request.args.get('range', 'today')
    from_date  = request.args.get('from')
    to_date    = request.args.get('to')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    date_cond, params = build_range_conditions(range_type, None, from_date, to_date)

    cursor.execute(f"SELECT COALESCE(SUM(total), 0) AS total FROM sales WHERE {date_cond}", params)
    total_sales = float(cursor.fetchone()['total'] or 0)

    cursor.execute(f"SELECT COUNT(*) AS cnt FROM sales WHERE {date_cond}", params)
    orders_today = int(cursor.fetchone()['cnt'] or 0)

    cursor.execute(f"SELECT COUNT(DISTINCT customer_name) AS cnt FROM sales WHERE {date_cond}", params)
    customers_today = int(cursor.fetchone()['cnt'] or 0)

    return jsonify({
        "total_sales":     total_sales,
        "orders_today":    orders_today,
        "customers_today": customers_today,
    })


# ── POS ───────────────────────────────────────────────────────────────────────

@app.route('/orders', methods=['GET', 'POST'])
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


# ── SUBMIT ORDER ──────────────────────────────────────────────────────────────

@app.route('/submit_order', methods=['POST'])
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


# ── VIEW ORDERS ───────────────────────────────────────────────────────────────

@app.route('/view_orders')
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
        orders=orders,
        total_revenue=total_revenue,
        page=page, per_page=per_page,
        total_rows=total_rows, total_pages=total_pages,
        q=q, from_date=from_date or '', to_date=to_date or ''
    )


# ── DONE ORDER ────────────────────────────────────────────────────────────────

@app.route('/done_order/<int:item_id>', methods=['POST'])
def done_order(item_id):
    if not is_logged_in():
        return redirect('/')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("DELETE FROM sale_items WHERE id = %s", (item_id,))
    mysql.connection.commit()
    return redirect('/view_orders')


# ── INVENTORY ─────────────────────────────────────────────────────────────────

@app.route('/inventory', methods=['GET', 'POST'])
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
            flash("Invalid stock value. Please enter a whole number.", "danger")
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
            flash("Failed to update stock. Please try again.", "danger")

        return redirect('/inventory')

    cursor.execute("SELECT * FROM ingredients ORDER BY name ASC")
    ingredients = cursor.fetchall()
    return render_template("inventory.html", ingredients=ingredients, username=session['username'])


@app.route('/inventory/update', methods=['POST'])
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


# ── PRODUCTS LIST ─────────────────────────────────────────────────────────────

@app.route('/products')
def products():
    if not is_logged_in():
        return redirect('/')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM products ORDER BY name ASC")
    products = cursor.fetchall()

    return render_template('products.html', products=products, username=session['username'])


# ── ADD PRODUCT ───────────────────────────────────────────────────────────────

@app.route('/add-product', methods=['GET', 'POST'])
def add_product():
    if not is_logged_in():
        return redirect('/')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Always fetch ingredients for the recipe builder
    cursor.execute("SELECT id, name, unit FROM ingredients ORDER BY name ASC")
    ingredients = cursor.fetchall()

    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        price    = request.form.get('price', '0')
        stock    = request.form.get('stock', '0')
        category = request.form.get('category', '').strip()

        # Validation
        if not name:
            flash("Product name is required.", "danger")
            return render_template('add_product.html', ingredients=ingredients)
        if not category:
            flash("Please select a category.", "danger")
            return render_template('add_product.html', ingredients=ingredients)

        try:
            price = float(price)
            stock = int(stock)
        except ValueError:
            flash("Invalid price or stock value.", "danger")
            return render_template('add_product.html', ingredients=ingredients)

        # Insert product first to get the new ID
        try:
            cursor.execute(
                "INSERT INTO products (name, price, stock, category) VALUES (%s, %s, %s, %s)",
                (name, price, 0, category)
            )
            mysql.connection.commit()
            product_id = cursor.lastrowid
        except Exception as e:
            mysql.connection.rollback()
            flash("Failed to save product. Please try again.", "danger")
            return render_template('add_product.html', ingredients=ingredients)

        # Handle image upload — save as {product_id}.jpg
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            if not allowed_file(image_file.filename):
                flash("Invalid image format. Use JPG, PNG, or WEBP.", "warning")
            else:
                image_file.seek(0, 2)   # seek to end
                size = image_file.tell()
                image_file.seek(0)      # reset

                if size > MAX_IMAGE_SIZE:
                    flash("Image too large (max 5 MB).", "warning")
                else:
                    # Always save as {id}.jpg so the POS template works with existing pattern
                    ext      = image_file.filename.rsplit('.', 1)[1].lower()
                    filename = f"{product_id}.{ext}"
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    image_file.save(save_path)

                    # If extension is not jpg, also save a .jpg copy so the POS img tag works
                    if ext != 'jpg':
                        try:
                            from PIL import Image as PILImage
                            img = PILImage.open(save_path).convert("RGB")
                            jpg_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{product_id}.jpg")
                            img.save(jpg_path, "JPEG", quality=90)
                            os.remove(save_path)  # remove original non-jpg
                        except ImportError:
                            # Pillow not installed — just rename/keep as-is
                            pass

        # Handle recipe rows
        ingredient_ids  = request.form.getlist('ingredient_id[]')
        ingredient_qtys = request.form.getlist('ingredient_qty[]')

        recipe_errors = []
        for ing_id, qty in zip(ingredient_ids, ingredient_qtys):
            ing_id = ing_id.strip()
            qty    = qty.strip()
            if not ing_id or not qty:
                continue
            try:
                qty_val = float(qty)
                if qty_val <= 0:
                    raise ValueError
            except ValueError:
                recipe_errors.append(f"Invalid quantity for ingredient ID {ing_id}")
                continue

            try:
                cursor.execute(
                    "INSERT INTO recipes (product_id, ingredient_id, quantity) VALUES (%s, %s, %s)",
                    (product_id, ing_id, qty_val)
                )
            except Exception:
                recipe_errors.append(f"Could not link ingredient ID {ing_id}")

        mysql.connection.commit()

        if recipe_errors:
            flash("Product saved, but some recipe rows had errors: " + "; ".join(recipe_errors), "warning")
        else:
            flash(f"Product '{name}' created successfully!", "success")

        return redirect('/products')

    return render_template('add_product.html', ingredients=ingredients)


# ── DELETE PRODUCT ────────────────────────────────────────────────────────────

@app.route('/delete-product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("SELECT name FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    if not product:
        return jsonify({"status": "error", "message": "Product not found."}), 404

    try:
        
        cursor.execute("DELETE FROM recipes WHERE product_id = %s", (product_id,))
        cursor.execute("DELETE FROM sale_items WHERE product_id = %s", (product_id,))  
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))

        mysql.connection.commit()

        return jsonify({"status": "success", "message": f"{product['name']} deleted"})
    
    except Exception as e:
        mysql.connection.rollback()
        print("DELETE ERROR:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# ── ADD INGREDIENT ────────────────────────────────────────────────────────────

@app.route('/add-ingredient', methods=['GET', 'POST'])
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
            flash("Unit of measurement is required.", "danger")
            return render_template('add_ingredient.html', ingredients=ingredients)

        try:
            stock = float(stock)
            if stock < 0:
                raise ValueError
        except ValueError:
            flash("Invalid stock value.", "danger")
            return render_template('add_ingredient.html', ingredients=ingredients)

        # Check for duplicate name
        cursor.execute("SELECT id FROM ingredients WHERE name = %s", (name,))
        if cursor.fetchone():
            flash(f"Ingredient '{name}' already exists.", "warning")
            return render_template('add_ingredient.html', ingredients=ingredients)

        try:
            cursor.execute(
                "INSERT INTO ingredients (name, stock, unit) VALUES (%s, %s, %s)",
                (name, stock, unit)
            )
            mysql.connection.commit()
            flash(f"Ingredient '{name}' added successfully!", "success")
            return redirect('/add-ingredient')
        except Exception:
            mysql.connection.rollback()
            flash("Failed to save ingredient. Please try again.", "danger")
            return render_template('add_ingredient.html', ingredients=ingredients)

    return render_template('add_ingredient.html', ingredients=ingredients)


# ── DELETE INGREDIENT ─────────────────────────────────────────────────────────

@app.route('/delete-ingredient/<int:ingredient_id>', methods=['POST'])
def delete_ingredient(ingredient_id):
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT name FROM ingredients WHERE id = %s", (ingredient_id,))
    ingredient = cursor.fetchone()
    if not ingredient:
        return jsonify({"status": "error", "message": "Ingredient not found."}), 404

    try:
        # Remove from recipes first
        cursor.execute("DELETE FROM recipes WHERE ingredient_id = %s", (ingredient_id,))
        cursor.execute("DELETE FROM ingredients WHERE id = %s", (ingredient_id,))
        mysql.connection.commit()
        return jsonify({"status": "success", "message": f"'{ingredient['name']}' deleted."})
    except Exception:
        mysql.connection.rollback()
        return jsonify({"status": "error", "message": "Failed to delete ingredient."}), 500
    


    # ── EDIT PRODUCT (GET) ───────────────────────────────────────────────────────
# Add these two routes to your app.py, right after the add_product route.

@app.route('/edit-product/<int:product_id>', methods=['GET'])
def edit_product(product_id):
    if not is_logged_in():
        return redirect('/')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch product
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    if not product:
        flash("Product not found.", "danger")
        return redirect('/products')

    # Fetch all ingredients for the recipe builder dropdown
    cursor.execute("SELECT id, name, unit FROM ingredients ORDER BY name ASC")
    ingredients = cursor.fetchall()

    # Fetch existing recipe for this product
    cursor.execute("""
        SELECT r.ingredient_id, r.quantity, i.name as ingredient_name, i.unit
        FROM recipes r
        JOIN ingredients i ON r.ingredient_id = i.id
        WHERE r.product_id = %s
        ORDER BY i.name ASC
    """, (product_id,))
    recipe = cursor.fetchall()

    return render_template(
        'edit_product.html',
        product=product,
        ingredients=ingredients,
        recipe=recipe
    )


# ── EDIT PRODUCT (POST — save changes) ───────────────────────────────────────

@app.route('/edit-product/<int:product_id>', methods=['POST'])
def edit_product_save(product_id):
    if not is_logged_in():
        return redirect('/')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Make sure product exists
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    if not product:
        flash("Product not found.", "danger")
        return redirect('/products')

    # ── Collect form data ──
    name     = request.form.get('name', '').strip()
    price    = request.form.get('price', '0').strip()
    category = request.form.get('category', '').strip()

    if not name:
        flash("Product name is required.", "danger")
        return redirect(f'/edit-product/{product_id}')
    if not category:
        flash("Please select a category.", "danger")
        return redirect(f'/edit-product/{product_id}')

    try:
        price = float(price)
    except ValueError:
        flash("Invalid price value.", "danger")
        return redirect(f'/edit-product/{product_id}')

    # ── Update product row ──
    try:
        cursor.execute(
            "UPDATE products SET name = %s, price = %s, category = %s WHERE id = %s",
            (name, price, category, product_id)
        )
        mysql.connection.commit()
    except Exception:
        mysql.connection.rollback()
        flash("Failed to update product details.", "danger")
        return redirect(f'/edit-product/{product_id}')

    # ── Handle image replacement ──
    image_file = request.files.get('image')
    if image_file and image_file.filename:
        if not allowed_file(image_file.filename):
            flash("Invalid image format. Use JPG, PNG, or WEBP.", "warning")
        else:
            image_file.seek(0, 2)
            size = image_file.tell()
            image_file.seek(0)

            if size > MAX_IMAGE_SIZE:
                flash("Image too large (max 5 MB).", "warning")
            else:
                ext      = image_file.filename.rsplit('.', 1)[1].lower()
                filename = f"{product_id}.{ext}"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

                # Remove old images for this product (all extensions)
                for old_ext in ['jpg', 'jpeg', 'png', 'webp']:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{product_id}.{old_ext}")
                    if os.path.exists(old_path):
                        os.remove(old_path)

                image_file.save(save_path)

                # Convert to JPG if not already
                if ext != 'jpg':
                    try:
                        from PIL import Image as PILImage
                        img = PILImage.open(save_path).convert("RGB")
                        jpg_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{product_id}.jpg")
                        img.save(jpg_path, "JPEG", quality=90)
                        os.remove(save_path)
                    except ImportError:
                        pass  # Pillow not installed — keep original extension

    # ── Replace recipe rows ──
    # We always replace all recipe rows with whatever is submitted.
    # This is the simplest and safest approach — no partial updates.
    ingredient_ids  = request.form.getlist('ingredient_id[]')
    ingredient_qtys = request.form.getlist('ingredient_qty[]')

    try:
        # Delete all existing recipe rows for this product
        cursor.execute("DELETE FROM recipes WHERE product_id = %s", (product_id,))

        # Re-insert from form
        recipe_errors = []
        for ing_id, qty in zip(ingredient_ids, ingredient_qtys):
            ing_id = ing_id.strip()
            qty    = qty.strip()
            if not ing_id or not qty:
                continue
            try:
                qty_val = float(qty)
                if qty_val <= 0:
                    raise ValueError
            except ValueError:
                recipe_errors.append(f"Invalid qty for ingredient ID {ing_id}")
                continue

            cursor.execute(
                "INSERT INTO recipes (product_id, ingredient_id, quantity) VALUES (%s, %s, %s)",
                (product_id, ing_id, qty_val)
            )

        mysql.connection.commit()

        if recipe_errors:
            flash(f"Product updated, but some recipe rows had errors: {'; '.join(recipe_errors)}", "warning")
        else:
            flash(f"'{name}' updated successfully!", "success")

    except Exception:
        mysql.connection.rollback()
        flash("Product details saved, but failed to update recipe. Please try again.", "warning")

    return redirect('/products')



#------------Notifications----------------------------------------

@app.route('/notifications')
def notifications():
    if not is_logged_in():
        return jsonify({"notifications": []}), 401

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    items  = []
    now    = datetime.datetime.now()

    # ── 1. OUT OF STOCK ingredients ──────────────────────────────────────────
    cursor.execute("""
        SELECT name, unit FROM ingredients
        WHERE stock = 0
        ORDER BY name ASC
    """)
    out_of_stock = cursor.fetchall()
    for i in out_of_stock:
        items.append({
            "level":   "danger",
            "title":   f"{i['name']} is OUT OF STOCK",
            "message": f"Stock is 0 {i['unit']}. Restock immediately — orders requiring this ingredient will be blocked.",
            "time":    "Right now"
        })

    # ── 2. CRITICALLY LOW stock (≤5) ─────────────────────────────────────────
    cursor.execute("""
        SELECT name, stock, unit FROM ingredients
        WHERE stock > 0 AND stock <= 5
        ORDER BY stock ASC
    """)
    critical_low = cursor.fetchall()
    for i in critical_low:
        items.append({
            "level":   "danger",
            "title":   f"{i['name']} is critically low",
            "message": f"Only {i['stock']} {i['unit']} left. Restock before running out completely.",
            "time":    "Right now"
        })

    # ── 3. LOW stock (6–20) ───────────────────────────────────────────────────
    cursor.execute("""
        SELECT name, stock, unit FROM ingredients
        WHERE stock > 5 AND stock <= 20
        ORDER BY stock ASC
    """)
    low_stock = cursor.fetchall()
    for i in low_stock:
        items.append({
            "level":   "warn",
            "title":   f"{i['name']} is running low",
            "message": f"{i['stock']} {i['unit']} remaining. Consider restocking soon.",
            "time":    "Right now"
        })

    # ── 4. PRODUCTS WITH NO RECIPE ────────────────────────────────────────────
    cursor.execute("""
        SELECT p.name FROM products p
        LEFT JOIN recipes r ON p.id = r.product_id
        WHERE r.product_id IS NULL
        ORDER BY p.name ASC
    """)
    no_recipe = cursor.fetchall()
    for p in no_recipe:
        items.append({
            "level":   "warn",
            "title":   f"'{p['name']}' has no recipe",
            "message": "This product has no ingredient recipe. Ingredient stock won't be deducted when it's ordered.",
            "time":    "Setup issue"
        })

    # ── 5. SLOW DAY ALERT ─────────────────────────────────────────────────────
    # Compare today's orders to the daily average over the last 30 days
    cursor.execute("""
        SELECT COUNT(*) as orders_today
        FROM sales
        WHERE DATE(created_at) = CURDATE()
    """)
    orders_today = cursor.fetchone()['orders_today'] or 0

    cursor.execute("""
        SELECT AVG(daily_count) as avg_orders
        FROM (
            SELECT DATE(created_at) as day, COUNT(*) as daily_count
            FROM sales
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
              AND DATE(created_at) < CURDATE()
            GROUP BY day
        ) as daily_totals
    """)
    avg_row    = cursor.fetchone()
    avg_orders = float(avg_row['avg_orders'] or 0)

    if avg_orders > 0 and orders_today < avg_orders * 0.5 and now.hour >= 12:
        items.append({
            "level":   "info",
            "title":   "Slow day detected",
            "message": f"Only {orders_today} orders so far today vs your {avg_orders:.0f} daily average. Consider a promotion or check if anything is unavailable.",
            "time":    f"As of {now.strftime('%I:%M %p')}"
        })

    # ── 6. PEAK HOUR ALERT ────────────────────────────────────────────────────
    # Check if the current hour is historically the busiest
    current_hour = now.hour
    cursor.execute("""
        SELECT HOUR(created_at) as hour, COUNT(*) as total
        FROM sales
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY hour
        ORDER BY total DESC
        LIMIT 1
    """)
    peak_row = cursor.fetchone()
    if peak_row and peak_row['hour'] == current_hour:
        hour_label = now.strftime("%I %p").lstrip("0")
        items.append({
            "level":   "success",
            "title":   f"You're in your peak hour ({hour_label})",
            "message": "This is historically your busiest hour. Make sure stock and staff are ready.",
            "time":    now.strftime("%I:%M %p")
        })

    # ── 7. TOP SELLER TODAY ───────────────────────────────────────────────────
    cursor.execute("""
        SELECT p.name, SUM(si.quantity) as total_sold
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        JOIN sales s ON si.sale_id = s.id
        WHERE DATE(s.created_at) = CURDATE()
        GROUP BY p.name
        ORDER BY total_sold DESC
        LIMIT 1
    """)
    top_seller = cursor.fetchone()
    if top_seller and top_seller['total_sold']:
        items.append({
            "level":   "tip",
            "title":   f"Top seller today: {top_seller['name']}",
            "message": f"Sold {top_seller['total_sold']} unit(s) so far. Make sure ingredients for this product are well stocked.",
            "time":    f"As of {now.strftime('%I:%M %p')}"
        })

    # ── 8. NO SALES TODAY (late in the day) ───────────────────────────────────
    if orders_today == 0 and now.hour >= 10:
        items.append({
            "level":   "info",
            "title":   "No orders yet today",
            "message": "No sales have been recorded today. If the store is open, check if the POS is working correctly.",
            "time":    f"As of {now.strftime('%I:%M %p')}"
        })

    # ── 9. REVENUE MILESTONE ──────────────────────────────────────────────────
    cursor.execute("SELECT COALESCE(SUM(total), 0) as total FROM sales WHERE DATE(created_at) = CURDATE()")
    today_revenue = float(cursor.fetchone()['total'] or 0)

    cursor.execute("""
        SELECT AVG(daily_total) as avg_revenue
        FROM (
            SELECT DATE(created_at) as day, SUM(total) as daily_total
            FROM sales
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
              AND DATE(created_at) < CURDATE()
            GROUP BY day
        ) as daily_rev
    """)
    avg_rev_row = cursor.fetchone()
    avg_revenue = float(avg_rev_row['avg_revenue'] or 0)

    if avg_revenue > 0 and today_revenue >= avg_revenue * 1.5:
        items.append({
            "level":   "success",
            "title":   "Strong sales day! 🎉",
            "message": f"Today's revenue ₱{today_revenue:,.2f} is {(today_revenue/avg_revenue*100 - 100):.0f}% above your daily average. Great work!",
            "time":    f"As of {now.strftime('%I:%M %p')}"
        })

    # ── 10. PRODUCTS WITH LOW INGREDIENT STOCK (can make < 5 servings) ────────
    cursor.execute("SELECT id, name FROM products")
    all_products = cursor.fetchall()

    for prod in all_products:
        cursor.execute("""
            SELECT r.quantity, i.stock, i.name as ing_name, i.unit
            FROM recipes r
            JOIN ingredients i ON r.ingredient_id = i.id
            WHERE r.product_id = %s
        """, (prod['id'],))
        recipe_items = cursor.fetchall()

        if not recipe_items:
            continue  # already caught by no-recipe check

        # How many servings can we make?
        max_servings = None
        limiting_ing = None
        for r in recipe_items:
            if r['quantity'] > 0:
                possible = int(float(r['stock']) / float(r['quantity']))
                if max_servings is None or possible < max_servings:
                    max_servings = possible
                    limiting_ing = r

        if max_servings is not None and 0 < max_servings <= 5:
            items.append({
                "level":   "warn",
                "title":   f"'{prod['name']}' can only be made {max_servings}x",
                "message": f"Limited by {limiting_ing['ing_name']} ({limiting_ing['stock']} {limiting_ing['unit']} left). Restock to keep selling this product.",
                "time":    "Right now"
            })
        elif max_servings == 0:
            items.append({
                "level":   "danger",
                "title":   f"'{prod['name']}' CANNOT be made",
                "message": f"Ingredients are depleted — {limiting_ing['ing_name']} has {limiting_ing['stock']} {limiting_ing['unit']} left, not enough for even 1 serving.",
                "time":    "Right now"
            })

    # Sort: danger first, then warn, then others
    level_order = {"danger": 0, "warn": 1, "info": 2, "tip": 3, "success": 4}
    items.sort(key=lambda x: level_order.get(x["level"], 5))

    return jsonify({"notifications": items})


# ── LOGOUT ────────────────────────────────────────────────────────────────────

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/?logout_success=true')


if __name__ == '__main__':
    app.run(debug=True)
