from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required
from models import User, db
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
import logging

auth = Blueprint('auth', __name__)

class SignupForm(FlaskForm):
    name = StringField('Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Sign Up')

class SigninForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class ResetPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Email already registered', 'error')
            return redirect(url_for('auth.signup'))

        try:
            new_user = User()
            new_user.name = form.name.data
            new_user.email = form.email.data
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()

            # Store the name in session
            session['user_name'] = form.name.data

            flash('Account created successfully! Please sign in.', 'success')
            return redirect(url_for('auth.signin'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"User registration error: {e}")
            flash('Registration failed. Please try again.', 'error')
            return redirect(url_for('auth.signup'))
    return render_template('signup.html', form=form)

@auth.route('/signin', methods=['GET', 'POST'])
def signin():
    form = SigninForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=True)
                # Store the user's name in session
                session['user_name'] = user.name
                session.permanent = True
                
                # Debug log for Mixpanel tracking consistency
                logging.info(f"🔐 User login successful: user_id={user.id}, email={user.email}")
                logging.debug(f"🔍 Session established for user_id={user.id} with 30-day persistence")
                logging.info(f"User {user.email} successfully authenticated")
                
                # Check if we should redirect to admin page
                next_page = request.args.get('next')
                if next_page and 'admin' in next_page and user.is_admin:
                    return redirect(next_page)
                elif next_page:
                    return redirect(next_page)
                else:
                    return redirect(url_for('dashboard'))
            else:
                logging.warning(f"Failed login attempt for email: {form.email.data}")
                flash('Invalid email or password', 'error')
        except Exception as e:
            logging.error(f"Login error: {e}")
            flash('Login failed. Please try again.', 'error')
    return render_template('signin.html', form=form)

@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # In a real application, send a password reset email here
            flash('If your email is registered, you will receive a reset link shortly', 'info')
        else:
            flash('If your email is registered, you will receive a reset link shortly', 'info')
        return redirect(url_for('auth.signin'))
    return render_template('reset_password.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_name', None)  # Clear the user's name from session
    return redirect(url_for('index'))