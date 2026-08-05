from extensions import mysql
import MySQLdb.cursors
import datetime


class Sale:
    """Represents a sales transaction."""

    def __init__(self, id, customer_name, total, created_at=None):
        self.id            = id
        self.customer_name = customer_name
        self.total         = total
        self.created_at    = created_at or datetime.datetime.now()

    # ── CREATE ─────────────────────────────────────────────────────────────────

    @staticmethod
    def create(customer_name, total, cart):
        """
        Insert a new sale, all its items, and deduct stock from
        products and ingredients. Returns the new sale ID.
        """
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "INSERT INTO sales (customer_name, total, created_at) VALUES (%s, %s, NOW())",
            (customer_name, total)
        )
        sale_id = cursor.lastrowid
        for item in cart:
            cursor.execute("""
                INSERT INTO sale_items (sale_id, product_id, quantity, price, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """, (sale_id, item['id'], item['qty'], item['price'], item['subtotal']))
            cursor.execute(
                "UPDATE products SET stock = stock - %s WHERE id = %s",
                (item['qty'], item['id'])
            )
            cursor.execute(
                "SELECT ingredient_id, quantity FROM recipes WHERE product_id = %s",
                (item['id'],)
            )
            for r in cursor.fetchall():
                cursor.execute(
                    "UPDATE ingredients SET stock = stock - %s WHERE id = %s",
                    (r['quantity'] * item['qty'], r['ingredient_id'])
                )
        mysql.connection.commit()
        return sale_id

    @staticmethod
    def check_stock(cart):
        """
        Check if all items in cart have enough ingredient stock.
        Returns an error message string, or None if all good.
        """
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        for item in cart:
            cursor.execute(
                "SELECT ingredient_id, quantity FROM recipes WHERE product_id = %s",
                (item['id'],)
            )
            for r in cursor.fetchall():
                cursor.execute(
                    "SELECT stock FROM ingredients WHERE id = %s",
                    (r['ingredient_id'],)
                )
                current = cursor.fetchone()['stock']
                if current < r['quantity'] * item['qty']:
                    return "Not enough ingredients"
        return None

    # ── READ ──────────────────────────────────────────────────────────────────

    @staticmethod
    def get_today_revenue():
        """Return total revenue for today."""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT COALESCE(SUM(total),0) AS t FROM sales WHERE DATE(created_at)=CURDATE()"
        )
        return float(cursor.fetchone()['t'] or 0)

    @staticmethod
    def get_today_count():
        """Return number of orders placed today."""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT COUNT(*) AS c FROM sales WHERE DATE(created_at)=CURDATE()"
        )
        return int(cursor.fetchone()['c'] or 0)

    @staticmethod
    def get_today_customers():
        """Return number of distinct customers today."""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT COUNT(DISTINCT customer_name) AS c FROM sales WHERE DATE(created_at)=CURDATE()"
        )
        return int(cursor.fetchone()['c'] or 0)

    def __repr__(self):
        return f"<Sale {self.id}: {self.customer_name} ₱{self.total}>"