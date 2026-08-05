from extensions import mysql
import MySQLdb.cursors


class Product:
    """Represents a product in the Kape Tubong system."""

    def __init__(self, id, name, price, category, stock=0):
        self.id       = id
        self.name     = name
        self.price    = price
        self.category = category
        self.stock    = stock

    # ── READ ──────────────────────────────────────────────────────────────────

    @staticmethod
    def get_all():
        """Return all products ordered by name."""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM products ORDER BY name ASC")
        rows = cursor.fetchall()
        return [Product(r['id'], r['name'], r['price'], r['category'], r['stock']) for r in rows]

    @staticmethod
    def get_by_id(product_id):
        """Return a single Product by ID, or None if not found."""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        r = cursor.fetchone()
        if not r:
            return None
        return Product(r['id'], r['name'], r['price'], r['category'], r['stock'])

    # ── CREATE ─────────────────────────────────────────────────────────────────

    @staticmethod
    def create(name, price, category):
        """Insert a new product and return its new ID."""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "INSERT INTO products (name, price, stock, category) VALUES (%s, %s, %s, %s)",
            (name, price, 0, category)
        )
        mysql.connection.commit()
        return cursor.lastrowid

    # ── UPDATE ─────────────────────────────────────────────────────────────────

    def update(self):
        """Save name, price and category changes back to the database."""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "UPDATE products SET name=%s, price=%s, category=%s WHERE id=%s",
            (self.name, self.price, self.category, self.id)
        )
        mysql.connection.commit()

    # ── DELETE ─────────────────────────────────────────────────────────────────

    def delete(self):
        """Delete this product along with its recipes and sale items."""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("DELETE FROM recipes    WHERE product_id = %s", (self.id,))
        cursor.execute("DELETE FROM sale_items WHERE product_id = %s", (self.id,))
        cursor.execute("DELETE FROM products   WHERE id = %s",         (self.id,))
        mysql.connection.commit()

    # ── RECIPE ─────────────────────────────────────────────────────────────────

    def get_recipe(self):
        """Return list of ingredients for this product."""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT i.name, r.quantity, i.unit
            FROM recipes r
            JOIN ingredients i ON r.ingredient_id = i.id
            WHERE r.product_id = %s ORDER BY i.name ASC
        """, (self.id,))
        return cursor.fetchall()

    def save_recipe(self, ingredient_ids, ingredient_qtys):
        """Replace the recipe for this product with new ingredients."""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("DELETE FROM recipes WHERE product_id = %s", (self.id,))
        errors = []
        for ing_id, qty in zip(ingredient_ids, ingredient_qtys):
            ing_id = ing_id.strip(); qty = qty.strip()
            if not ing_id or not qty:
                continue
            try:
                qty_val = float(qty)
                if qty_val <= 0:
                    raise ValueError
            except ValueError:
                errors.append(f"Invalid qty for ingredient ID {ing_id}")
                continue
            cursor.execute(
                "INSERT INTO recipes (product_id, ingredient_id, quantity) VALUES (%s,%s,%s)",
                (self.id, ing_id, qty_val)
            )
        mysql.connection.commit()
        return errors

    def __repr__(self):
        return f"<Product {self.id}: {self.name} ₱{self.price}>"