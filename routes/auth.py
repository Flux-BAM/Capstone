from flask import Blueprint, render_template, request, redirect, session, url_for
from models.user import User


auth_bp = Blueprint('auth', __name__)


def role_home(role):
    if role == 'customer':
        return url_for('customer_dashboard')
    return url_for('analytics.dashboard')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('loggedin') and session.get('role') in ('staff', 'admin', 'customer'):
        return redirect(role_home(session['role']))

    error = False
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user, hashed = User.find_by_username(username) if username else (None, None)

        if user and User.verify_password(password, hashed) and user.role in ('customer', 'staff', 'admin'):
            session.clear()
            session.permanent = True
            session['loggedin'] = True
            session['id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(role_home(user.role))
        error = True

    return render_template('login.html', error=error)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('loggedin'):
        return redirect(role_home(session.get('role')))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not re_valid_username(username):
            error = 'Username must be 3–50 characters and contain only letters, numbers, dots, underscores, or hyphens.'
        elif len(password) < 8:
            error = 'Password must be at least 8 characters long.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif User.exists(username):
            error = 'That username is already taken. Please choose another.'
        else:
            try:
                User.create_customer(username, password)
                return redirect(url_for('auth.login', registered='1'))
            except Exception:
                # Do not expose database details to a public user.
                error = 'We could not create your account right now. Please try again.'

    return render_template('register.html', error=error)


def re_valid_username(username):
    import re
    return bool(re.fullmatch(r'[A-Za-z0-9_.-]{3,50}', username))


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('public_home', logout_success='true'))
