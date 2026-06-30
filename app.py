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

UPLOAD_FOLDER      = os.path.join('static', 'images')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
MAX_IMAGE_SIZE     = 5 * 1024 * 1024

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mysql = MySQL(app)


# ── Helpers ───────────────────────────────────────────────────────────────────

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
    today  = datetime.date.today()

    # ── Base KPIs (all time) ──────────────────────────────────────────────────
    cursor.execute("SELECT COALESCE(SUM(total),0) AS t FROM sales")
    total_sales = float(cursor.fetchone()['t'] or 0)

    
    cursor.execute("SELECT COUNT(DISTINCT customer_name) AS c FROM sales WHERE customer_name IS NOT NULL AND customer_name != ''")
    total_customers = int(cursor.fetchone()['c'] or 0)

    cursor.execute("SELECT COALESCE(AVG(total),0) AS a FROM sales")
    avg_order_value = float(cursor.fetchone()['a'] or 0)

    # ── Today KPIs ────────────────────────────────────────────────────────────
    cursor.execute("SELECT COUNT(*) AS c FROM sales WHERE DATE(created_at)=CURDATE()")
    orders_today = int(cursor.fetchone()['c'] or 0)

    cursor.execute("SELECT COUNT(DISTINCT customer_name) AS c FROM sales WHERE DATE(created_at)=CURDATE()")
    customers_today = int(cursor.fetchone()['c'] or 0)

    cursor.execute("SELECT COALESCE(SUM(total),0) AS t FROM sales WHERE DATE(created_at)=CURDATE()")
    revenue_today = float(cursor.fetchone()['t'] or 0)

    
    cursor.execute("SELECT COALESCE(AVG(total),0) AS a FROM sales WHERE DATE(created_at)=CURDATE()")
    avg_order_value_today = float(cursor.fetchone()['a'] or 0)

    # ── Period-over-period deltas (today vs yesterday) ────────────────────────
    cursor.execute("SELECT COALESCE(SUM(total),0) AS t FROM sales WHERE DATE(created_at)=CURDATE()-INTERVAL 1 DAY")
    revenue_yesterday = float(cursor.fetchone()['t'] or 0)

    cursor.execute("SELECT COUNT(*) AS c FROM sales WHERE DATE(created_at)=CURDATE()-INTERVAL 1 DAY")
    orders_yesterday = int(cursor.fetchone()['c'] or 0)

    cursor.execute("SELECT COUNT(DISTINCT customer_name) AS c FROM sales WHERE DATE(created_at)=CURDATE()-INTERVAL 1 DAY")
    customers_yesterday = int(cursor.fetchone()['c'] or 0)

    def pct_change(now, prev):
        if prev == 0:
            return None
        return round(((now - prev) / prev) * 100, 1)

    deltas = {
        "revenue":   pct_change(revenue_today,   revenue_yesterday),
        "orders":    pct_change(orders_today,     orders_yesterday),
        "customers": pct_change(customers_today,  customers_yesterday),
    }

    # ── Daily sales (last 30 days) ────────────────────────────────────────────
    cursor.execute("""
        SELECT DATE(created_at) AS day, SUM(total) AS total
        FROM sales WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY DATE(created_at) ORDER BY day
    """)
    daily_sales = [
        {"day": str(r["day"]), "label": r["day"].strftime("%b %d"), "total": float(r["total"] or 0)}
        for r in cursor.fetchall()
    ]

    # ── Weekly + monthly summaries ────────────────────────────────────────────
    cursor.execute("""
        SELECT DATE_FORMAT(created_at,'%Y-%m') AS month, SUM(total) AS total
        FROM sales GROUP BY month ORDER BY month
    """)
    monthly_sales = cursor.fetchall()

    # FIX #6: Wrap fromisocalendar in a specific ValueError/AttributeError catch
    # and log the offending row instead of silently swallowing it.
    cursor.execute("""
        SELECT YEAR(created_at) AS yr, WEEK(created_at,1) AS wk, SUM(total) AS total
        FROM sales GROUP BY yr,wk ORDER BY yr,wk
    """)
    weekly_sales = []
    for w in cursor.fetchall():
        try:
            mon = datetime.date.fromisocalendar(int(w['yr']), int(w['wk']), 1)
            sun = datetime.date.fromisocalendar(int(w['yr']), int(w['wk']), 7)
            weekly_sales.append({
                "week_range": f"{mon.strftime('%b %d')} – {sun.strftime('%b %d')}",
                "total": float(w['total'] or 0)
            })
        except (ValueError, AttributeError) as e:
            app.logger.warning(f"weekly_sales skip yr={w.get('yr')} wk={w.get('wk')}: {e}")

    # ── Product data ──────────────────────────────────────────────────────────
    cursor.execute("""
        SELECT p.name, SUM(si.quantity) AS total_sold
        FROM sale_items si JOIN products p ON si.product_id=p.id
        JOIN sales s ON si.sale_id=s.id
        GROUP BY p.name ORDER BY total_sold DESC
    """)
    product_data = [{'name': r['name'], 'total_sold': int(r['total_sold'] or 0)} for r in cursor.fetchall()]

    # ── Best sellers today ────────────────────────────────────────────────────
    cursor.execute("""
        SELECT p.name, SUM(si.quantity) AS total_sold
        FROM sale_items si JOIN products p ON si.product_id=p.id
        JOIN sales s ON si.sale_id=s.id
        WHERE DATE(s.created_at)=CURDATE()
        GROUP BY p.name ORDER BY total_sold DESC LIMIT 5
    """)
    best_sellers_today = cursor.fetchall()

    # ── Recent orders ─────────────────────────────────────────────────────────
    cursor.execute("""
        SELECT s.customer_name, p.name AS product_name, si.subtotal
        FROM sales s JOIN sale_items si ON s.id=si.sale_id
        JOIN products p ON si.product_id=p.id
        ORDER BY s.created_at DESC LIMIT 5
    """)
    recent_orders = cursor.fetchall()

    # ── Peak hours ────────────────────────────────────────────────────────────
    cursor.execute("""
        SELECT HOUR(created_at) AS hour, COUNT(*) AS total
        FROM sales GROUP BY hour ORDER BY hour
    """)
    peak_hours = [{'hour': int(r['hour']), 'total': int(r['total'])} for r in cursor.fetchall()]

    # ── Low stock ─────────────────────────────────────────────────────────────
    cursor.execute("SELECT name, stock, unit FROM ingredients WHERE stock<=20 ORDER BY stock ASC LIMIT 8")
    low_stock = cursor.fetchall()

    # ── 7-day sales forecast (trailing 14-day average projected forward) ──────
    cursor.execute("""
        SELECT DATE(created_at) AS day, SUM(total) AS total
        FROM sales
        WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
          AND DATE(created_at) < CURDATE()
        GROUP BY DATE(created_at)
    """)
    trailing = cursor.fetchall()
    if trailing:
        avg_daily = sum(float(r['total'] or 0) for r in trailing) / len(trailing)
    else:
        avg_daily = 0

    forecast = []
    for i in range(1, 8):
        d = today + datetime.timedelta(days=i)
        forecast.append({"day": d.strftime("%b %d"), "projected": round(avg_daily, 2)})

   
    cursor.execute("""
        SELECT DAYOFWEEK(created_at) AS dow,
               HOUR(created_at)     AS hr,
               COUNT(*)             AS cnt
        FROM sales
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 8 WEEK)
        GROUP BY dow, hr
        ORDER BY dow, hr
    """)
    heatmap_raw = cursor.fetchall()
    heatmap = [{'dow': int(r['dow']), 'hr': int(r['hr']), 'cnt': int(r['cnt'])} for r in heatmap_raw]

    # ── Repeat vs new customers (last 30 days) ────────────────────────────────
    cursor.execute("""
        SELECT customer_name, COUNT(*) AS visits
        FROM sales
        WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
          AND customer_name IS NOT NULL AND customer_name != ''
        GROUP BY customer_name
    """)
    cust_rows = cursor.fetchall()
    repeat_customers = sum(1 for r in cust_rows if int(r['visits']) > 1)
    new_customers    = sum(1 for r in cust_rows if int(r['visits']) == 1)
    total_named      = repeat_customers + new_customers

    # ── Slow-moving products (zero sales last 14 days) ────────────────────────
    cursor.execute("""
        SELECT p.name FROM products p
        WHERE p.id NOT IN (
            SELECT DISTINCT si.product_id FROM sale_items si
            JOIN sales s ON si.sale_id=s.id
            WHERE s.created_at >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
        )
        ORDER BY p.name
    """)
    slow_movers = [r['name'] for r in cursor.fetchall()]

    # ── Estimated days until stockout per ingredient ──────────────────────────
    cursor.execute("""
        SELECT i.id, i.name, i.stock, i.unit,
               COALESCE(SUM(r.quantity * si.quantity),0) AS used_14d
        FROM ingredients i
        LEFT JOIN recipes r     ON r.ingredient_id=i.id
        LEFT JOIN sale_items si ON si.product_id=r.product_id
        LEFT JOIN sales s       ON s.id=si.sale_id
            AND s.created_at >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
        GROUP BY i.id, i.name, i.stock, i.unit
        HAVING i.stock > 0
        ORDER BY i.stock ASC
    """)
    stockout_rows = cursor.fetchall()
    stockout_est = []
    for r in stockout_rows:
        used = float(r['used_14d'] or 0)
        daily_use = used / 14 if used > 0 else 0
        days_left = round(float(r['stock']) / daily_use) if daily_use > 0 else None
        stockout_est.append({
            "name":      r['name'],
            "stock":     float(r['stock']),
            "unit":      r['unit'],
            "daily_use": round(daily_use, 2),
            "days_left": days_left,
        })
    stockout_est.sort(key=lambda x: (x['days_left'] is None, x['days_left'] or 9999))

    # ── Revenue by category (all time) ───────────────────────────────────────
    cursor.execute("""
        SELECT p.category, SUM(si.subtotal) AS revenue
        FROM sale_items si JOIN products p ON si.product_id=p.id
        WHERE p.category IS NOT NULL AND p.category != ''
        GROUP BY p.category ORDER BY revenue DESC
    """)
    category_revenue = [{'category': r['category'], 'revenue': float(r['revenue'] or 0)} for r in cursor.fetchall()]

    return render_template(
        'dashboard.html',
        username=session['username'],
        total_sales=total_sales,
        total_customers=total_customers,
        avg_order_value=avg_order_value,
        avg_order_value_today=avg_order_value_today,   # FIX #3: added
        orders_today=orders_today,
        customers_today=customers_today,
        revenue_today=revenue_today,
        deltas=deltas,
        daily_sales=daily_sales,
        monthly_sales=monthly_sales,
        weekly_sales=weekly_sales,
        product_data=product_data,
        peak_hours=peak_hours,
        category_revenue=category_revenue,
        best_sellers_today=best_sellers_today,
        recent_orders=recent_orders,
        low_stock=low_stock,
        forecast=forecast,
        heatmap=heatmap,
        repeat_customers=repeat_customers,
        new_customers=new_customers,
        total_named=total_named,
        slow_movers=slow_movers,
        stockout_est=stockout_est,
    )


# ── RANGE CONDITIONS ──────────────────────────────────────────────────────────

def build_range_conditions(range_type, table_alias=None, from_date=None, to_date=None):
    col = "created_at" if not table_alias else f"{table_alias}.created_at"
    if range_type == "all":    return "1=1", []
    if range_type == "today":  return f"DATE({col}) = CURDATE()", []
    if range_type == "7d":     return f"{col} >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)", []
    if range_type == "30d":    return f"{col} >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)", []
    if range_type == "custom": return f"DATE({col}) BETWEEN %s AND %s", [from_date, to_date]
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
                return jsonify({"error": "Invalid date format"}), 400
            if parsed_from > parsed_to:
                return jsonify({"error": "Start date must be before end date"}), 400

    date_cond, date_params = build_range_conditions(range_type, None, from_date, to_date)
    sale_cond, sale_params = build_range_conditions(range_type, "s",  from_date, to_date)

    # ── Core metrics ──────────────────────────────────────────────────────────
    cursor.execute(f"SELECT COALESCE(SUM(total),0) AS t FROM sales WHERE {date_cond}", date_params)
    total_sales = float(cursor.fetchone()['t'] or 0)

    cursor.execute(f"SELECT COUNT(*) AS c FROM sales WHERE {date_cond}", date_params)
    orders_today = int(cursor.fetchone()['c'] or 0)

    cursor.execute(f"SELECT COUNT(DISTINCT customer_name) AS c FROM sales WHERE {date_cond}", date_params)
    customers_today = int(cursor.fetchone()['c'] or 0)

    # FIX #3: avg_order is now scoped to the selected range, matching the
    # range-aware label shown in the frontend KPI strip.
    cursor.execute(f"SELECT COALESCE(AVG(total),0) AS a FROM sales WHERE {date_cond}", date_params)
    avg_order = float(cursor.fetchone()['a'] or 0)

    # ── Period-over-period (previous equal window) ────────────────────────────
    def prev_condition(range_type, from_date, to_date):
        if range_type == "today":
            return "DATE(created_at) = CURDATE() - INTERVAL 1 DAY", []
        if range_type == "7d":
            return "created_at BETWEEN DATE_SUB(CURDATE(), INTERVAL 14 DAY) AND DATE_SUB(CURDATE(), INTERVAL 7 DAY)", []
        if range_type == "30d":
            return "created_at BETWEEN DATE_SUB(CURDATE(), INTERVAL 60 DAY) AND DATE_SUB(CURDATE(), INTERVAL 30 DAY)", []
        if range_type == "custom" and from_date and to_date:
            try:
                f = datetime.datetime.strptime(from_date, "%Y-%m-%d").date()
                t = datetime.datetime.strptime(to_date,   "%Y-%m-%d").date()
                delta = (t - f).days + 1
                prev_to   = f - datetime.timedelta(days=1)
                prev_from = prev_to - datetime.timedelta(days=delta - 1)
                return "DATE(created_at) BETWEEN %s AND %s", [str(prev_from), str(prev_to)]
            except Exception:
                pass
        return "1=0", []  # all-time has no prev

    prev_cond, prev_params = prev_condition(range_type, from_date, to_date)
    cursor.execute(f"SELECT COALESCE(SUM(total),0) AS t FROM sales WHERE {prev_cond}", prev_params)
    prev_revenue = float(cursor.fetchone()['t'] or 0)
    cursor.execute(f"SELECT COUNT(*) AS c FROM sales WHERE {prev_cond}", prev_params)
    prev_orders = int(cursor.fetchone()['c'] or 0)
    cursor.execute(f"SELECT COUNT(DISTINCT customer_name) AS c FROM sales WHERE {prev_cond}", prev_params)
    prev_customers = int(cursor.fetchone()['c'] or 0)

    def pct(now, prev):
        if prev == 0: return None
        return round(((now - prev) / prev) * 100, 1)

    deltas = {
        "revenue":   pct(total_sales,     prev_revenue),
        "orders":    pct(orders_today,    prev_orders),
        "customers": pct(customers_today, prev_customers),
    }

    # ── Daily sales chart ─────────────────────────────────────────────────────
    if range_type == "all":
        cursor.execute("""
            SELECT DATE_FORMAT(created_at, '%Y-%m-01') AS day,
                   DATE_FORMAT(created_at, '%b %Y')    AS label,
                   SUM(total) AS total
            FROM sales
            GROUP BY DATE_FORMAT(created_at, '%Y-%m')
            ORDER BY day
        """)
    else:
        cursor.execute(f"""
            SELECT DATE(created_at) AS day, SUM(total) AS total
            FROM sales WHERE {date_cond}
            GROUP BY DATE(created_at) ORDER BY day
        """, date_params)

    daily_rows = cursor.fetchall()
    daily_sales = [
        {
            "day":   str(r["day"]),
            "label": r["label"] if "label" in r else r["day"].strftime("%b %d"),
            "total": float(r["total"] or 0),
        }
        for r in daily_rows
    ]

    # ── Product data ──────────────────────────────────────────────────────────
    cursor.execute(f"""
        SELECT p.name, SUM(si.quantity) AS total_sold
        FROM sale_items si JOIN products p ON si.product_id=p.id
        JOIN sales s ON si.sale_id=s.id WHERE {sale_cond}
        GROUP BY p.name ORDER BY total_sold DESC
    """, sale_params)
    product_data = [{'name': r['name'], 'total_sold': int(r['total_sold'] or 0)} for r in cursor.fetchall()]

    # ── Peak hours ────────────────────────────────────────────────────────────
    cursor.execute(f"""
        SELECT HOUR(created_at) AS hour, COUNT(*) AS total
        FROM sales WHERE {date_cond}
        GROUP BY hour ORDER BY hour
    """, date_params)
    peak_hours = [{'hour': int(r['hour']), 'total': int(r['total'])} for r in cursor.fetchall()]

    # ── Category revenue ──────────────────────────────────────────────────────
    cursor.execute(f"""
        SELECT p.category, SUM(si.subtotal) AS revenue
        FROM sale_items si JOIN products p ON si.product_id=p.id
        JOIN sales s ON si.sale_id=s.id WHERE {sale_cond}
          AND p.category IS NOT NULL AND p.category != ''
        GROUP BY p.category ORDER BY revenue DESC
    """, sale_params)
    category_revenue = [{'category': r['category'], 'revenue': float(r['revenue'] or 0)} for r in cursor.fetchall()]

    # ── Best sellers ──────────────────────────────────────────────────────────
    cursor.execute(f"""
        SELECT p.name, SUM(si.quantity) AS total_sold
        FROM sale_items si JOIN products p ON si.product_id=p.id
        JOIN sales s ON si.sale_id=s.id WHERE {sale_cond}
        GROUP BY p.name ORDER BY total_sold DESC LIMIT 5
    """, sale_params)
    best_sellers = [{'name': r['name'], 'total_sold': int(r['total_sold'] or 0)} for r in cursor.fetchall()]

    # ── Repeat vs new (within range) ─────────────────────────────────────────
    cursor.execute(f"""
        SELECT customer_name, COUNT(*) AS visits FROM sales
        WHERE {date_cond} AND customer_name IS NOT NULL AND customer_name != ''
        GROUP BY customer_name
    """, date_params)
    cust_rows = cursor.fetchall()
    repeat_customers = sum(1 for r in cust_rows if int(r['visits']) > 1)
    new_customers    = sum(1 for r in cust_rows if int(r['visits']) == 1)

    return jsonify({
        "total_sales":      total_sales,
        "orders_today":     orders_today,
        "customers_today":  customers_today,
        "avg_order":        round(avg_order, 2),
        "deltas":           deltas,
        "daily_sales":      daily_sales,
        "product_data":     product_data,
        "peak_hours":       peak_hours,
        "category_revenue": category_revenue,
        "best_sellers":     best_sellers,
        "repeat_customers": repeat_customers,
        "new_customers":    new_customers,
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

    return jsonify({"total_sales": total_sales, "orders_today": orders_today, "customers_today": customers_today})


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
        orders=orders, total_revenue=total_revenue,
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


# ── INVENTORY — USAGE HISTORY ─────────────────────────────────────────────────

@app.route('/inventory/usage')
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
            i.id,
            i.name,
            i.unit,
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


# ── INVENTORY — ESTIMATED SERVINGS ────────────────────────────────────────────

@app.route('/inventory/servings')
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
                "id":                  prod['id'],
                "name":                prod['name'],
                "category":            prod['category'] or '',
                "max_servings":        None,
                "limiting_ingredient": None,
                "limiting_stock":      None,
                "limiting_unit":       None,
            })
            continue

        max_servings   = None
        limiting_ing   = None
        limiting_stock = None
        limiting_unit  = None

        for r in recipe:
            qty_per = float(r['quantity'] or 0)
            stock   = float(r['stock']    or 0)
            if qty_per <= 0:
                continue
            possible = int(stock / qty_per)
            if max_servings is None or possible < max_servings:
                max_servings   = possible
                limiting_ing   = r['ing_name']
                limiting_stock = round(stock, 2)
                limiting_unit  = r['unit']

        if max_servings is None:
            max_servings = 0

        servings.append({
            "id":                  prod['id'],
            "name":                prod['name'],
            "category":            prod['category'] or '',
            "max_servings":        max_servings,
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
    cursor.execute("SELECT id, name, unit FROM ingredients ORDER BY name ASC")
    ingredients = cursor.fetchall()

    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        price    = request.form.get('price', '0')
        category = request.form.get('category', '').strip()

        if not name:
            flash("Product name is required.", "danger")
            return render_template('add_product.html', ingredients=ingredients)
        if not category:
            flash("Please select a category.", "danger")
            return render_template('add_product.html', ingredients=ingredients)

        try:
            price = float(price)
        except ValueError:
            flash("Invalid price value.", "danger")
            return render_template('add_product.html', ingredients=ingredients)

        try:
            cursor.execute(
                "INSERT INTO products (name, price, stock, category) VALUES (%s, %s, %s, %s)",
                (name, price, 0, category)
            )
            mysql.connection.commit()
            product_id = cursor.lastrowid
        except Exception:
            mysql.connection.rollback()
            flash("Failed to save product.", "danger")
            return render_template('add_product.html', ingredients=ingredients)

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            if not allowed_file(image_file.filename):
                flash("Invalid image format. Use JPG, PNG, or WEBP.", "warning")
            else:
                image_file.seek(0, 2); size = image_file.tell(); image_file.seek(0)
                if size > MAX_IMAGE_SIZE:
                    flash("Image too large (max 5 MB).", "warning")
                else:
                    ext       = image_file.filename.rsplit('.', 1)[1].lower()
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{product_id}.{ext}")
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    image_file.save(save_path)
                    if ext != 'jpg':
                        try:
                            from PIL import Image as PILImage
                            img = PILImage.open(save_path).convert("RGB")
                            img.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{product_id}.jpg"), "JPEG", quality=90)
                            os.remove(save_path)
                        except ImportError:
                            pass

        ingredient_ids  = request.form.getlist('ingredient_id[]')
        ingredient_qtys = request.form.getlist('ingredient_qty[]')
        recipe_errors   = []

        for ing_id, qty in zip(ingredient_ids, ingredient_qtys):
            ing_id = ing_id.strip(); qty = qty.strip()
            if not ing_id or not qty: continue
            try:
                qty_val = float(qty)
                if qty_val <= 0: raise ValueError
            except ValueError:
                recipe_errors.append(f"Invalid qty for ingredient ID {ing_id}"); continue
            try:
                cursor.execute(
                    "INSERT INTO recipes (product_id, ingredient_id, quantity) VALUES (%s,%s,%s)",
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
        cursor.execute("DELETE FROM recipes    WHERE product_id = %s", (product_id,))
        cursor.execute("DELETE FROM sale_items WHERE product_id = %s", (product_id,))
        cursor.execute("DELETE FROM products   WHERE id = %s",         (product_id,))
        mysql.connection.commit()

        for ext in ['jpg', 'jpeg', 'png', 'webp']:
            p = os.path.join(app.config['UPLOAD_FOLDER'], f"{product_id}.{ext}")
            if os.path.exists(p): os.remove(p)

        return jsonify({"status": "success", "message": f"'{product['name']}' deleted."})
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


        # ── GET RECIPE ────────────────────────────────────────────────────────────────

@app.route('/get-recipe/<int:product_id>')
def get_recipe(product_id):
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT name FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    if not product:
        return jsonify({"status": "error", "message": "Product not found"}), 404

    cursor.execute("""
        SELECT i.name, r.quantity, i.unit
        FROM recipes r
        JOIN ingredients i ON r.ingredient_id = i.id
        WHERE r.product_id = %s
        ORDER BY i.name ASC
    """, (product_id,))
    rows = cursor.fetchall()

    ingredients = [
        {
            "name":     r["name"],
            "quantity": r["quantity"],
            "unit":     r["unit"]
        }
        for r in rows
    ]

    return jsonify({
        "product":     product["name"],
        "ingredients": ingredients
    })


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
        cursor.execute("DELETE FROM recipes     WHERE ingredient_id = %s", (ingredient_id,))
        cursor.execute("DELETE FROM ingredients WHERE id = %s",            (ingredient_id,))
        mysql.connection.commit()
        return jsonify({"status": "success", "message": f"'{ingredient['name']}' deleted."})
    except Exception:
        mysql.connection.rollback()
        return jsonify({"status": "error", "message": "Failed to delete ingredient."}), 500


# ── EDIT PRODUCT (GET) ────────────────────────────────────────────────────────

@app.route('/edit-product/<int:product_id>', methods=['GET'])
def edit_product(product_id):
    if not is_logged_in():
        return redirect('/')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    if not product:
        flash("Product not found.", "danger")
        return redirect('/products')

    cursor.execute("SELECT id, name, unit FROM ingredients ORDER BY name ASC")
    ingredients = cursor.fetchall()

    cursor.execute("""
        SELECT r.ingredient_id, r.quantity, i.name AS ingredient_name, i.unit
        FROM recipes r JOIN ingredients i ON r.ingredient_id = i.id
        WHERE r.product_id = %s ORDER BY i.name ASC
    """, (product_id,))
    recipe = cursor.fetchall()

    return render_template('edit_product.html', product=product, ingredients=ingredients, recipe=recipe)


# ── EDIT PRODUCT (POST) ───────────────────────────────────────────────────────

@app.route('/edit-product/<int:product_id>', methods=['POST'])
def edit_product_save(product_id):
    if not is_logged_in():
        return redirect('/')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    if not product:
        flash("Product not found.", "danger")
        return redirect('/products')

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
        flash("Invalid price.", "danger")
        return redirect(f'/edit-product/{product_id}')

    try:
        cursor.execute("UPDATE products SET name=%s, price=%s, category=%s WHERE id=%s", (name, price, category, product_id))
        mysql.connection.commit()
    except Exception:
        mysql.connection.rollback()
        flash("Failed to update product.", "danger")
        return redirect(f'/edit-product/{product_id}')

    image_file = request.files.get('image')
    if image_file and image_file.filename:
        if not allowed_file(image_file.filename):
            flash("Invalid image format.", "warning")
        else:
            image_file.seek(0, 2); size = image_file.tell(); image_file.seek(0)
            if size > MAX_IMAGE_SIZE:
                flash("Image too large (max 5 MB).", "warning")
            else:
                ext       = image_file.filename.rsplit('.', 1)[1].lower()
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{product_id}.{ext}")
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                for old_ext in ['jpg', 'jpeg', 'png', 'webp']:
                    op = os.path.join(app.config['UPLOAD_FOLDER'], f"{product_id}.{old_ext}")
                    if os.path.exists(op): os.remove(op)
                image_file.save(save_path)
                if ext != 'jpg':
                    try:
                        from PIL import Image as PILImage
                        img = PILImage.open(save_path).convert("RGB")
                        img.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{product_id}.jpg"), "JPEG", quality=90)
                        os.remove(save_path)
                    except ImportError:
                        pass

    ingredient_ids  = request.form.getlist('ingredient_id[]')
    ingredient_qtys = request.form.getlist('ingredient_qty[]')

    try:
        cursor.execute("DELETE FROM recipes WHERE product_id = %s", (product_id,))
        recipe_errors = []
        for ing_id, qty in zip(ingredient_ids, ingredient_qtys):
            ing_id = ing_id.strip(); qty = qty.strip()
            if not ing_id or not qty: continue
            try:
                qty_val = float(qty)
                if qty_val <= 0: raise ValueError
            except ValueError:
                recipe_errors.append(f"Invalid qty for ingredient ID {ing_id}"); continue
            cursor.execute(
                "INSERT INTO recipes (product_id, ingredient_id, quantity) VALUES (%s,%s,%s)",
                (product_id, ing_id, qty_val)
            )
        mysql.connection.commit()

        if recipe_errors:
            flash("Product updated, but some recipe rows had errors: " + "; ".join(recipe_errors), "warning")
        else:
            flash(f"'{name}' updated successfully!", "success")
    except Exception:
        mysql.connection.rollback()
        flash("Product details saved, but failed to update recipe.", "warning")

    return redirect('/products')


# ── NOTIFICATIONS ─────────────────────────────────────────────────────────────

@app.route('/notifications')
def notifications():
    if not is_logged_in():
        return jsonify({"notifications": []}), 401

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    items  = []
    now    = datetime.datetime.now()

    cursor.execute("SELECT name, unit FROM ingredients WHERE stock = 0 ORDER BY name ASC")
    for i in cursor.fetchall():
        items.append({"level": "danger", "title": f"{i['name']} is OUT OF STOCK",
                      "message": f"Stock is 0 {i['unit']}. Orders requiring this ingredient will be blocked.", "time": "Right now"})

    cursor.execute("SELECT name, stock, unit FROM ingredients WHERE stock > 0 AND stock <= 5 ORDER BY stock ASC")
    for i in cursor.fetchall():
        items.append({"level": "danger", "title": f"{i['name']} is critically low",
                      "message": f"Only {i['stock']} {i['unit']} left. Restock immediately.", "time": "Right now"})

    cursor.execute("SELECT name, stock, unit FROM ingredients WHERE stock > 5 AND stock <= 20 ORDER BY stock ASC")
    for i in cursor.fetchall():
        items.append({"level": "warn", "title": f"{i['name']} is running low",
                      "message": f"{i['stock']} {i['unit']} remaining. Consider restocking soon.", "time": "Right now"})

    cursor.execute("""
        SELECT p.name FROM products p
        LEFT JOIN recipes r ON p.id = r.product_id
        WHERE r.product_id IS NULL ORDER BY p.name ASC
    """)
    for p in cursor.fetchall():
        items.append({"level": "warn", "title": f"'{p['name']}' has no recipe",
                      "message": "Ingredient stock won't be deducted when this product is ordered.", "time": "Setup issue"})

    cursor.execute("SELECT COUNT(*) as cnt FROM sales WHERE DATE(created_at) = CURDATE()")
    orders_today = cursor.fetchone()['cnt'] or 0

    cursor.execute("""
        SELECT AVG(daily_count) as avg FROM (
            SELECT DATE(created_at) as day, COUNT(*) as daily_count
            FROM sales WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) AND DATE(created_at) < CURDATE()
            GROUP BY day
        ) t
    """)
    avg_orders = float((cursor.fetchone()['avg'] or 0))
    if avg_orders > 0 and orders_today < avg_orders * 0.5 and now.hour >= 12:
        items.append({"level": "info", "title": "Slow day detected",
                      "message": f"Only {orders_today} orders vs your {avg_orders:.0f} daily average.", "time": now.strftime('%I:%M %p')})

    cursor.execute("""
        SELECT HOUR(created_at) as hour, COUNT(*) as total FROM sales
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY hour ORDER BY total DESC LIMIT 1
    """)
    peak_row = cursor.fetchone()
    if peak_row and peak_row['hour'] == now.hour:
        items.append({"level": "success", "title": f"Peak hour now ({now.strftime('%I %p').lstrip('0')})",
                      "message": "Historically your busiest hour. Ensure stock and staff are ready.", "time": now.strftime('%I:%M %p')})

    cursor.execute("""
        SELECT p.name, SUM(si.quantity) as total_sold FROM sale_items si
        JOIN products p ON si.product_id = p.id JOIN sales s ON si.sale_id = s.id
        WHERE DATE(s.created_at) = CURDATE() GROUP BY p.name ORDER BY total_sold DESC LIMIT 1
    """)
    top = cursor.fetchone()
    if top and top['total_sold']:
        items.append({"level": "tip", "title": f"Top seller today: {top['name']}",
                      "message": f"Sold {top['total_sold']} unit(s). Keep ingredients stocked.", "time": now.strftime('%I:%M %p')})

    if orders_today == 0 and now.hour >= 10:
        items.append({"level": "info", "title": "No orders yet today",
                      "message": "No sales recorded today. Check if the POS is working correctly.", "time": now.strftime('%I:%M %p')})

    cursor.execute("SELECT COALESCE(SUM(total),0) as t FROM sales WHERE DATE(created_at) = CURDATE()")
    today_rev = float(cursor.fetchone()['t'] or 0)
    cursor.execute("""
        SELECT AVG(daily_total) as avg FROM (
            SELECT DATE(created_at) as day, SUM(total) as daily_total FROM sales
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) AND DATE(created_at) < CURDATE()
            GROUP BY day
        ) t
    """)
    avg_rev = float((cursor.fetchone()['avg'] or 0))
    if avg_rev > 0 and today_rev >= avg_rev * 1.5:
        items.append({"level": "success", "title": "Strong sales day! 🎉",
                      "message": f"Revenue ₱{today_rev:,.2f} is {(today_rev/avg_rev*100-100):.0f}% above your daily average.", "time": now.strftime('%I:%M %p')})

    cursor.execute("SELECT id, name FROM products")
    for prod in cursor.fetchall():
        cursor.execute("""
            SELECT r.quantity, i.stock, i.name as ing_name, i.unit FROM recipes r
            JOIN ingredients i ON r.ingredient_id = i.id WHERE r.product_id = %s
        """, (prod['id'],))
        recipe = cursor.fetchall()
        if not recipe: continue
        max_s = None; lim = None
        for r in recipe:
            if float(r['quantity'] or 0) > 0:
                p = int(float(r['stock']) / float(r['quantity']))
                if max_s is None or p < max_s: max_s = p; lim = r
        if max_s is not None and 0 < max_s <= 5:
            items.append({"level": "warn", "title": f"'{prod['name']}' can only be made {max_s}×",
                          "message": f"Limited by {lim['ing_name']} ({lim['stock']} {lim['unit']} left).", "time": "Right now"})
        elif max_s == 0:
            items.append({"level": "danger", "title": f"'{prod['name']}' CANNOT be made",
                          "message": f"{lim['ing_name']} has {lim['stock']} {lim['unit']} — not enough for 1 serving.", "time": "Right now"})

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