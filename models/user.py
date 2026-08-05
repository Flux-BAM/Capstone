from extensions import mysql
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb.cursors


class User:
    """Represents a system user (admin/staff)."""

    def __init__(self, id, username):
        self.id       = id
        self.username = username

    # ── READ ──────────────────────────────────────────────────────────────────

    @staticmethod
    def find_by_username(username):
        """
        Look up a user by username.
        Returns (User, hashed_password) tuple or (None, None) if not found.
        """
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        r = cursor.fetchone()
        if not r:
            return None, None
        return User(r['id'], r['username']), r['password']

    @staticmethod
    def exists(username):
        """Return True if a user with this username already exists."""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        return cursor.fetchone() is not None

    # ── CREATE ─────────────────────────────────────────────────────────────────

    @staticmethod
    def create(username, password):
        """Insert a new user with a hashed password."""
        hashed = generate_password_hash(password)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed)
        )
        mysql.connection.commit()

    # ── AUTH ───────────────────────────────────────────────────────────────────

    @staticmethod
    def verify_password(plain_password, hashed_password):
        """Return True if plain_password matches the hashed version."""
        return check_password_hash(hashed_password, plain_password)

    def __repr__(self):
        return f"<User {self.id}: {self.username}>"