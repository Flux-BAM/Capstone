from extensions import mysql
import MySQLdb.cursors


class Ingredient:
    """Represents a stock ingredient used in product recipes."""

    def __init__(self, id, name, stock, unit):
        self.id    = id
        self.name  = name
        self.stock = stock
        self.unit  = unit

    # ── READ ──────────────────────────────────────────────────────────────────

    @staticmethod
    def get_all():
        """Return all ingredients ordered by name."""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM ingredients ORDER BY name ASC")
        rows = cursor.fetchall()
        return [Ingredient(r['id'], r['name'], r['stock'], r['unit']) for r in rows]

    @staticmethod
    def get_by_id(ingredient_id):
        """Return a single Ingredient by ID, or None if not found."""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM ingredients WHERE id = %s", (ingredient_id,))
        r = cursor.fetchone()
        if not r:
            return None
        return Ingredient(r['id'], r['name'], r['stock'], r['unit'])

    @staticmethod
    def get_all_for_select():
        """Return raw dicts for dropdown selects (id, name, unit only)."""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id, name, unit FROM ingredients ORDER BY name ASC")
        return cursor.fetchall()

    @staticmethod
    def exists(name):
        """Check if an ingredient with this name already exists."""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id FROM ingredients WHERE name = %s", (name,))
        return cursor.fetchone() is not None

    # ── CREATE ─────────────────────────────────────────────────────────────────

    @staticmethod
    def create(name, stock, unit):
        """Insert a new ingredient."""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "INSERT INTO ingredients (name, stock, unit) VALUES (%s, %s, %s)",
            (name, stock, unit)
        )
        mysql.connection.commit()

    # ── UPDATE ─────────────────────────────────────────────────────────────────

    def update_stock(self, new_stock):
        """Update stock level for this ingredient."""
        self.stock = new_stock
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "UPDATE ingredients SET stock = %s WHERE id = %s",
            (self.stock, self.id)
        )
        mysql.connection.commit()

    # ── DELETE ─────────────────────────────────────────────────────────────────

    def delete(self):
        """Delete this ingredient and remove it from all recipes."""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("DELETE FROM recipes     WHERE ingredient_id = %s", (self.id,))
        cursor.execute("DELETE FROM ingredients WHERE id = %s",            (self.id,))
        mysql.connection.commit()

    # ── HELPERS ────────────────────────────────────────────────────────────────

    def is_low_stock(self):
        """Return True if stock is at or below 20."""
        return self.stock <= 20

    def is_out_of_stock(self):
        """Return True if stock is zero."""
        return self.stock == 0

    def is_critical(self):
        """Return True if stock is critically low (5 or below)."""
        return 0 < self.stock <= 5

    def __repr__(self):
        return f"<Ingredient {self.id}: {self.name} {self.stock}{self.unit}>"