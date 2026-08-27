from flask import Flask
import os
from extensions import mysql
from routes.auth      import auth_bp
from routes.analytics import analytics_bp
from routes.products  import products_bp
from routes.inventory import inventory_bp
from routes.orders    import orders_bp

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

app.config['MYSQL_HOST']     = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER']     = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB']       = os.environ.get('MYSQL_DB', 'brewinsight')

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')

mysql.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(products_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(orders_bp)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)