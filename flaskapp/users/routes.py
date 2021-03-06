from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_user, logout_user, login_required
from flaskapp.users.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm, \
    ChangeEmailForm, ChangePasswordForm
from flaskapp.models import User
from flaskapp import bcrypt, db
from .utils import send_reset_email
from flaskapp.budget.routes import update_funds

users = Blueprint('users', __name__)


@users.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('budget.main'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('budget.main'))
        else:
            flash('Niepowodzenie. Nieprawidłowy e-mail lub hasło.', 'danger')
    return render_template('login.html', title="Strona Główna", form=form)


@users.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('budget.main'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = User(email=form.email.data, password=hash)
            db.session.add(user)
            db.session.commit()
            flash('Konto zostało założone pomyślnie. Możesz się zalogować.', 'success')
            return redirect(url_for('users.login'))
        else:
            flash('Ten adres email został już przypisany do konta.', 'danger')
            redirect(url_for('users.register'))
    return render_template('register.html', title='Zarejestruj się', form=form)


@users.route('/logout')
def logout():
    logout_user()
    flash('Zostałeś wylogowany.', 'success')
    return redirect(url_for('users.login'))


@users.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('budget.main'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('Jeżeli ten e-mail jest przypisany do konta został na niego wysłany link do zmiany hasła', 'info')
        return redirect(url_for('users.login'))
    return render_template('forgot-password.html', title='Przypomnij hasło', form=form)


@users.route('/reset-password/<string:token>', methods=['GET', 'POST'])
def reset_password_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('budget.main'))
    user = User.verify_reset_token(token)
    if not User:
        flash('Link jest niepoprawny lub utracił ważność.', 'warning')
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Twoje hasło zostało zmienione! Możesz się teraz zalogować.', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_password.html', title='Reset hasła', form=form)


@users.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
    funds = update_funds()
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if bcrypt.check_password_hash(current_user.password, form.password.data):
            current_user.email = form.email.data
            db.session.commit()
            flash('Pomyślnie zmieniono adres e-mail.', 'success')
            return redirect(url_for('budget.main'))
        else:
            flash('To nie jest twoje obecne hasło.', 'danger')
            return redirect(url_for('users.change_email'))
    return render_template('change-email.html', title='Zmień e-mail', funds=funds, form=form)


@users.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    funds = update_funds()
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if bcrypt.check_password_hash(current_user.password, form.old_password.data):
            current_user.password = bcrypt.generate_password_hash(form.new_password.data)
            db.session.commit()
            flash('Pomyślnie zmieniono hasło.', 'success')
            return redirect(url_for('budget.main'))
        else:
            flash('To nie jest twoje obecne hasło.', 'danger')
            return redirect(url_for('users.change_password'))
    return render_template('change-password.html', title='Zmień hasło', funds=funds, form=form)
