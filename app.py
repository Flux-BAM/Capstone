from flask import Flask, render_template
import os
from extensions import mysql
from routes.auth      import auth_bp
from routes.analytics import analytics_bp
from routes.products  import products_bp
from routes.inventory import inventory_bp
from routes.orders    import orders_bp
from models.product import Product

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

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


# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(products_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(orders_bp)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)