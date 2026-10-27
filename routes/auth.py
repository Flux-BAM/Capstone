from flask import Blueprint, render_template, request, redirect, session
from models.user import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = False
    register_success = request.args.get('register_success')
    register_error   = request.args.get('register_error')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # OOP: use User model to find and verify the user
        user, hashed = User.find_by_username(username)
        if user and User.verify_password(password, hashed):
            session['loggedin'] = True
            session['id']       = user.id
            session['username'] = user.username
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
        password = request.form['password']

        # OOP: use User model to check existence and create
        if User.exists(username):
            return redirect('/login?register_error=1')
        User.create(username, password)
        return redirect('/login?register_success=1')
    return redirect('/login')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/?logout_success=true')