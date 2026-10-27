from flask import Blueprint, render_template, request, redirect, session, jsonify, Response
import MySQLdb.cursors
import csv
import io
import datetime
from extensions import mysql
from helpers import is_logged_in, parse_iso_date, build_range_conditions

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/dashboard')
def dashboard():
    if not is_logged_in():
        return redirect('/login')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    today  = datetime.date.today()

    cursor.execute("SELECT COALESCE(SUM(total),0) AS t FROM sales")
    total_sales = float(cursor.fetchone()['t'] or 0)

    cursor.execute("SELECT COUNT(DISTINCT customer_name) AS c FROM sales WHERE customer_name IS NOT NULL AND customer_name != ''")
    total_customers = int(cursor.fetchone()['c'] or 0)

    cursor.execute("SELECT COALESCE(AVG(total),0) AS a FROM sales")
    avg_order_value = float(cursor.fetchone()['a'] or 0)

    cursor.execute("SELECT COUNT(*) AS c FROM sales WHERE DATE(created_at)=CURDATE()")
    orders_today = int(cursor.fetchone()['c'] or 0)

    cursor.execute("SELECT COUNT(DISTINCT customer_name) AS c FROM sales WHERE DATE(created_at)=CURDATE()")
    customers_today = int(cursor.fetchone()['c'] or 0)

    cursor.execute("SELECT COALESCE(SUM(total),0) AS t FROM sales WHERE DATE(created_at)=CURDATE()")
    revenue_today = float(cursor.fetchone()['t'] or 0)

    cursor.execute("SELECT COALESCE(AVG(total),0) AS a FROM sales WHERE DATE(created_at)=CURDATE()")
    avg_order_value_today = float(cursor.fetchone()['a'] or 0)

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

    cursor.execute("""
        SELECT DATE(created_at) AS day, SUM(total) AS total
        FROM sales WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY DATE(created_at) ORDER BY day
    """)
    daily_sales = [
        {"day": str(r["day"]), "label": r["day"].strftime("%b %d"), "total": float(r["total"] or 0)}
        for r in cursor.fetchall()
    ]

    cursor.execute("""
        SELECT DATE_FORMAT(created_at,'%Y-%m') AS month, SUM(total) AS total
        FROM sales GROUP BY month ORDER BY month
    """)
    monthly_sales = cursor.fetchall()

    cursor.execute("""
        SELECT YEAR(created_at) AS yr, WEEK(created_at,1) AS wk, SUM(total) AS total
        FROM sales GROUP BY yr,wk ORDER BY yr,wk
    """)
    weekly_sales = []
    from flask import current_app
    for w in cursor.fetchall():
        try:
            mon = datetime.date.fromisocalendar(int(w['yr']), int(w['wk']), 1)
            sun = datetime.date.fromisocalendar(int(w['yr']), int(w['wk']), 7)
            weekly_sales.append({
                "week_range": f"{mon.strftime('%b %d')} – {sun.strftime('%b %d')}",
                "total": float(w['total'] or 0)
            })
        except (ValueError, AttributeError) as e:
            current_app.logger.warning(f"weekly_sales skip yr={w.get('yr')} wk={w.get('wk')}: {e}")

    cursor.execute("""
        SELECT p.name, SUM(si.quantity) AS total_sold
        FROM sale_items si JOIN products p ON si.product_id=p.id
        JOIN sales s ON si.sale_id=s.id
        GROUP BY p.name ORDER BY total_sold DESC
    """)
    product_data = [{'name': r['name'], 'total_sold': int(r['total_sold'] or 0)} for r in cursor.fetchall()]

    cursor.execute("""
        SELECT p.name, SUM(si.quantity) AS total_sold
        FROM sale_items si JOIN products p ON si.product_id=p.id
        JOIN sales s ON si.sale_id=s.id
        WHERE DATE(s.created_at)=CURDATE()
        GROUP BY p.name ORDER BY total_sold DESC LIMIT 5
    """)
    best_sellers_today = cursor.fetchall()

    cursor.execute("""
        SELECT s.customer_name, p.name AS product_name, si.subtotal
        FROM sales s JOIN sale_items si ON s.id=si.sale_id
        JOIN products p ON si.product_id=p.id
        ORDER BY s.created_at DESC LIMIT 5
    """)
    recent_orders = cursor.fetchall()

    cursor.execute("""
        SELECT HOUR(created_at) AS hour, COUNT(*) AS total
        FROM sales GROUP BY hour ORDER BY hour
    """)
    peak_hours = [{'hour': int(r['hour']), 'total': int(r['total'])} for r in cursor.fetchall()]

    cursor.execute("SELECT name, stock, unit FROM ingredients WHERE stock<=20 ORDER BY stock ASC LIMIT 8")
    low_stock = cursor.fetchall()

    cursor.execute("""
        SELECT DATE(created_at) AS day, SUM(total) AS total
        FROM sales
        WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
          AND DATE(created_at) < CURDATE()
        GROUP BY DATE(created_at)
    """)
    trailing = cursor.fetchall()
    avg_daily = sum(float(r['total'] or 0) for r in trailing) / len(trailing) if trailing else 0

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
    heatmap = [{'dow': int(r['dow']), 'hr': int(r['hr']), 'cnt': int(r['cnt'])} for r in cursor.fetchall()]

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
        avg_order_value_today=avg_order_value_today,
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


@analytics_bp.route('/analytics-filter')
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

    cursor.execute(f"SELECT COALESCE(SUM(total),0) AS t FROM sales WHERE {date_cond}", date_params)
    total_sales = float(cursor.fetchone()['t'] or 0)

    cursor.execute(f"SELECT COUNT(*) AS c FROM sales WHERE {date_cond}", date_params)
    orders_today = int(cursor.fetchone()['c'] or 0)

    cursor.execute(f"SELECT COUNT(DISTINCT customer_name) AS c FROM sales WHERE {date_cond}", date_params)
    customers_today = int(cursor.fetchone()['c'] or 0)

    cursor.execute(f"SELECT COALESCE(AVG(total),0) AS a FROM sales WHERE {date_cond}", date_params)
    avg_order = float(cursor.fetchone()['a'] or 0)

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
        return "1=0", []

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

    cursor.execute(f"""
        SELECT p.name, SUM(si.quantity) AS total_sold
        FROM sale_items si JOIN products p ON si.product_id=p.id
        JOIN sales s ON si.sale_id=s.id WHERE {sale_cond}
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
        SELECT p.category, SUM(si.subtotal) AS revenue
        FROM sale_items si JOIN products p ON si.product_id=p.id
        JOIN sales s ON si.sale_id=s.id WHERE {sale_cond}
          AND p.category IS NOT NULL AND p.category != ''
        GROUP BY p.category ORDER BY revenue DESC
    """, sale_params)
    category_revenue = [{'category': r['category'], 'revenue': float(r['revenue'] or 0)} for r in cursor.fetchall()]

    cursor.execute(f"""
        SELECT p.name, SUM(si.quantity) AS total_sold
        FROM sale_items si JOIN products p ON si.product_id=p.id
        JOIN sales s ON si.sale_id=s.id WHERE {sale_cond}
        GROUP BY p.name ORDER BY total_sold DESC LIMIT 5
    """, sale_params)
    best_sellers = [{'name': r['name'], 'total_sold': int(r['total_sold'] or 0)} for r in cursor.fetchall()]

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


@analytics_bp.route('/export-csv')
def export_csv():
    if not is_logged_in():
        return redirect('/login')

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


@analytics_bp.route('/live-data')
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


@analytics_bp.route('/notifications')
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