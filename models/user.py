from extensions import mysql
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb.cursors


class User:
    """Represents a customer, staff member, or administrator."""

    def __init__(self, id, username, role="staff"):
        self.id = id
        self.username = username
        self.role = role or "staff"

    @staticmethod
    def find_by_username(username):
        """Return (User, password_hash), or (None, None). Requires role migration."""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id, username, password, role FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if not row:
            return None, None
        return User(row['id'], row['username'], row['role']), row['password']

    @staticmethod
    def exists(username):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        return cursor.fetchone() is not None

    @staticmethod
    def create(username, password, role="staff"):
        """Create an account with a hashed password. Public registration must pass role='customer'."""
        hashed = generate_password_hash(password)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (username, hashed, role)
        )
        mysql.connection.commit()
        return cursor.lastrowid

    @staticmethod
    def create_customer(username, password):
        # Never accept a role from a public registration form.
        return User.create(username, password, role="customer")

    @staticmethod
    def verify_password(plain_password, hashed_password):
        return check_password_hash(hashed_password, plain_password)

    def __repr__(self):
        return f"<User {self.id}: {self.username} ({self.role})>"
