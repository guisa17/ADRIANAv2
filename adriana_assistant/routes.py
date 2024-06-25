import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from adriana_assistant import app, db, bcrypt, mail
from adriana_assistant.forms import (RegistrationForm, LoginForm, UpdateAccountForm, UpdateProfilePictureForm,
                             PostForm, RequestResetForm, ResetPasswordForm)
from adriana_assistant.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from .module_logic import process_module, load_preexisting_modules, get_module_details


@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    latest_posts = Post.query.order_by(Post.date_posted.desc()).limit(5).all()
    return render_template('home.html', posts=posts, latest_posts=latest_posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    picture_form = UpdateProfilePictureForm()
    if form.validate_on_submit() and picture_form.picture.data is None:
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Los datos de tu cuenta han sido actualizados.', 'success')
        return redirect(url_for('account'))
    if picture_form.validate_on_submit() and picture_form.picture.data:
        picture_file = save_picture(picture_form.picture.data)
        current_user.image_file = picture_file
        db.session.commit()
        flash('Tu foto de perfil ha sido actualizada.', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form, picture_form=picture_form)

@app.route("/remove_picture", methods=['POST'])
@login_required
def remove_picture():
    current_user.image_file = 'default.jpg'
    db.session.commit()
    flash('Tu foto de perfil ha sido eliminada.', 'success')
    return redirect(url_for('account'))


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Tu publicación se ha realizado con éxito.', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='Nueva publicación',
                           form=form, legend='Crea una nueva publicación')


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))


@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


# MODULOS
@app.route("/modules")
def modules():
    preexisting_modules = load_preexisting_modules()
    return render_template('modules.html', title='Módulos', modules=preexisting_modules)

@app.route("/modules/upload", methods=['GET', 'POST'])
def upload_module():
    if request.method == 'POST':
        image_file = request.files['image']
        if image_file:
            # Directorio donde se guardarán las imágenes subidas
            upload_folder = os.path.join(app.root_path, 'static/uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            # Guardar la imagen en la carpeta temporal
            image_path = os.path.join(upload_folder, image_file.filename)
            image_file.save(image_path)

            # Procesar la imagen para obtener la descripción y el audio
            title, scenario, instructions = process_module(image_path)
            audio_path = os.path.join(upload_folder, 'audio-es.wav')

            return render_template('module_detail.html', title=title, scenario=scenario, instructions=instructions, image_file=image_file.filename, audio_file='audio-es.wav')

    return redirect(url_for('modules'))

@app.route("/modules/<module_name>")
def module_detail(module_name):
    module = get_module_details(module_name)
    if module:
        return render_template('module_detail.html', title=module['title'], description=module['description'], module_name=module_name)
    else:
        return redirect(url_for('modules'))