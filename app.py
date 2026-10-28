from flask import Flask, render_template, request, redirect, session, url_for
import os
from extensions import mysql
from routes.auth      import auth_bp
from routes.analytics import analytics_bp
from routes.products  import products_bp
from routes.inventory import inventory_bp
from routes.orders    import orders_bp
from models.product import Product

app = Flask(__name__)
# Set FLASK_SECRET_KEY to a long, random value in Railway production.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("RAILWAY_ENVIRONMENT") is not None,
    PERMANENT_SESSION_LIFETIME=60 * 60 * 8,  # 8 hours
)

# Public pages are available without an account. Every other route is guarded
# server-side according to the authenticated account's role.
@app.before_request
def enforce_role_access():
    endpoint = request.endpoint
    public_endpoints = {"public_home", "auth.login", "auth.register", "auth.logout", "static"}
    if endpoint is None or endpoint in public_endpoints:
        return None

    if not session.get("loggedin") or not session.get("id") or not session.get("role"):
        return redirect(url_for("auth.login", next=request.path))

    role = session.get("role")
    if role == "customer":
        if endpoint == "customer_dashboard":
            return None
        # Customers cannot access staff POS, inventory, analytics, or API routes.
        return redirect(url_for("customer_dashboard"))

    if role in ("staff", "admin"):
        if endpoint == "customer_dashboard":
            return redirect(url_for("analytics.dashboard"))
        return None

    session.clear()
    return redirect(url_for("auth.login"))


app.config['MYSQL_HOST']     = os.environ.get('MYSQLHOST', 'localhost')
app.config['MYSQL_USER']     = os.environ.get('MYSQLUSER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQLPASSWORD', '')
app.config['MYSQL_DB']       = os.environ.get('MYSQLDATABASE', 'brewinsight')
app.config['MYSQL_PORT'] = int(os.environ.get('MYSQLPORT', 3306))

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')

mysql.init_app(app)



@app.route('/')
def public_home():
    # Public, read-only customer menu. Product data comes from the same
    # database used by the staff POS.
    products = Product.get_all()
    menu_products = []
    for product in products:
        image_url = None
        for ext in ('jpg', 'jpeg', 'png', 'webp'):
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{product.id}.{ext}')
            if os.path.isfile(image_path):
                image_url = f'/static/images/{product.id}.{ext}'
                break
        menu_products.append({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'category': product.category or 'Other',
            'image_url': image_url,
        })
    categories = sorted({p['category'] for p in menu_products}, key=str.lower)
    return render_template('landing.html', products=menu_products, categories=categories)


@app.route('/customer')
def customer_dashboard():
    # Customer account page is read-only; ordering/payment are not enabled.
    from flask import flash
    products = Product.get_all()
    menu_products = []
    for product in products:
        image_url = None
        for ext in ('jpg', 'jpeg', 'png', 'webp'):
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{product.id}.{ext}')
            if os.path.isfile(image_path):
                image_url = f'/static/images/{product.id}.{ext}'
                break
        menu_products.append({
            'id': product.id, 'name': product.name, 'price': product.price,
            'category': product.category or 'Other', 'image_url': image_url,
        })
    categories = sorted({p['category'] for p in menu_products}, key=str.lower)
    return render_template('customer_dashboard.html', products=menu_products,
                           categories=categories, username=session.get('username'))


# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(products_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(orders_bp)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)