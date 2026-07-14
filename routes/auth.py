from flask import Blueprint, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb.cursors
from extensions import mysql

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/', methods=['GET', 'POST'])
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


@auth_bp.route('/register', methods=['GET', 'POST'])
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


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/?logout_success=true')