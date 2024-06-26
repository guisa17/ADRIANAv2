import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort, session
from adriana_assistant import app, db, bcrypt, mail
from adriana_assistant.forms import (RegistrationForm, LoginForm, UpdateAccountForm, UpdateProfilePictureForm,
                                     PostForm, RequestResetForm, ResetPasswordForm)
from adriana_assistant.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from transformers import pipeline
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import find_dotenv, load_dotenv
import requests

# Cargar las variables de entorno
load_dotenv(find_dotenv())

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
HF_BEARER_API_TOKEN = os.getenv('HF_BEARER_API_TOKEN')

# Helper Functions
def img2text(image_path):
    image_to_text = pipeline("image-to-text", model="Salesforce/blip-image-captioning-large")
    text = image_to_text(image_path)[0]["generated_text"]
    return text

def generate_instructions(scenario):
    model = "llama3-8b-8192"
    template = '''
    Eres una experta en técnicas de gestión del estrés y la ansiedad llamada ADRIANA. 
    Puedes proporcionar instrucciones detalladas y claras sobre cómo realizar una actividad de gestión del estrés basada en una imagen. 
    Las instrucciones deben estar en español;
    CONTEXTO: {scenario}
    INSTRUCCIONES:
    '''
    groq_chat = ChatGroq(
        groq_api_key=GROQ_API_KEY, 
        model_name=model
    )
    
    prompt = PromptTemplate(template=template, input_variables=["scenario"])
    instruction_llm = LLMChain(llm=groq_chat, prompt=prompt, verbose=True)

    instructions = instruction_llm.predict(scenario=scenario)
    return instructions

def text2speech(message):
    API_URL = "https://api-inference.huggingface.co/models/facebook/mms-tts-spa"
    headers = {"Authorization": f"Bearer {HF_BEARER_API_TOKEN}"}
    payload = {
        "inputs": message
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()

    audio_path = os.path.join('static/uploads', 'audio-es.wav')
    with open(audio_path, 'wb') as file:
        file.write(response.content)

    return audio_path

def process_module(image_path):
    scenario = img2text(image_path)
    instructions = generate_instructions(scenario)
    text2speech(instructions)
    title = "Módulo de Gestión del Estrés"
    return title, scenario, instructions

def load_preexisting_modules():
    modules_dir = os.path.join(app.root_path, 'static', 'modules_data')

    if not os.path.exists(modules_dir):
        print(f"Directorio {modules_dir} no encontrado.")
        return []

    modules = []
    for module_name in os.listdir(modules_dir):
        module_path = os.path.join(modules_dir, module_name)
        if os.path.isdir(module_path):
            description_path = os.path.join(module_path, 'description.txt')
            image_path = os.path.join(module_path, 'image.jpg')
            audio_path = os.path.join(module_path, 'audio.wav')
            
            if os.path.exists(description_path) and os.path.exists(image_path) and os.path.exists(audio_path):
                with open(description_path, 'r', encoding='utf-8') as desc_file:
                    description = desc_file.read()
                module = {
                    'directory': module_name,
                    'title': module_name.replace('_', ' ').title(),
                    'description': description
                }
                modules.append(module)
            else:
                print(f"Archivos faltantes en {module_path}: description.txt, image.jpg o audio.wav")
    return modules

def get_module_details(module_name):
    modules_dir = os.path.join(app.root_path, 'static', 'modules_data')
    module_path = os.path.join(modules_dir, module_name)
    if os.path.isdir(module_path):
        description_path = os.path.join(module_path, 'description.txt')
        if os.path.exists(description_path):
            with open(description_path, 'r', encoding='utf-8') as desc_file:
                description = desc_file.read()
            return {
                'title': module_name.replace('_', ' ').title(),
                'description': description
            }
    return None

# Routes
@app.route("/home")
@login_required
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    latest_posts = Post.query.order_by(Post.date_posted.desc()).limit(5).all()
    return render_template('home.html', posts=posts, latest_posts=latest_posts)

@app.route("/")
@app.route("/about")
def about():
    return render_template('about.html', title='Nosotros')

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
        flash('Tu cuenta ha sido creada exitosamente. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Registro', form=form)

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
            flash('Inicio de sesión sin éxito. Por favor revisa tu email y contraseña.', 'danger')
    return render_template('login.html', title='Iniciar sesión', form=form)

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
    return render_template('account.html', title='Mi Cuenta', image_file=image_file, form=form, picture_form=picture_form)

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
    return render_template('create_post.html', title='Nueva publicación', form=form, legend='Crea una nueva publicación')

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
        flash('Tu publicación ha sido actualizada.', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Actualizar post', form=form, legend='Update Post')

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Tu publicación ha sido eliminada.', 'success')
    return redirect(url_for('home'))

@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='noreply@demo.com', recipients=[user.email])
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
    return render_template('reset_request.html', title='Reestablecer contraseña', form=form)

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
    return render_template('reset_token.html', title='Reestablecer contraseña', form=form)

# Modules
@app.route("/modules")
@login_required
def modules():
    preexisting_modules = load_preexisting_modules()
    return render_template('modules.html', title='Módulos', modules=preexisting_modules)

@app.route("/modules/upload", methods=['GET', 'POST'])
@login_required
def upload_module():
    if request.method == 'POST':
        image_file = request.files['image']
        if image_file:
            upload_folder = os.path.join(app.root_path, 'static/uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            image_path = os.path.join(upload_folder, image_file.filename)
            image_file.save(image_path)

            title, scenario, instructions = process_module(image_path)
            audio_path = os.path.join(upload_folder, 'audio-es.wav')

            return render_template('module_detail.html', title=title, scenario=scenario, instructions=instructions, image_file=image_file.filename, audio_file='audio-es.wav')

    return redirect(url_for('modules'))

@app.route("/modules/<module_name>")
@login_required
def module_detail(module_name):
    module = get_module_details(module_name)
    if module:
        return render_template('module_detail.html', title=module['title'], description=module['description'], module_name=module_name)
    else:
        return redirect(url_for('modules'))

# Chatbot
@app.route('/chatbot', methods=['GET', 'POST'])
@login_required
def chatbot():
    groq_api_key = os.getenv('GROQ_API_KEY')

    if not groq_api_key:
        return "API Key is not configured correctly."

    model = 'llama3-8b-8192'
    conversational_memory_length = 10

    system_prompt = (
        "Te llamas ADRIANA, una experta en el control del estrés y la ansiedad. "
        "Tu conocimiento en psicología te permite ofrecer instrucciones precisas y efectivas para controlar estos problemas. "
        "Además, cuentas con una variedad de ejercicios probados que ayudarán a disminuir el estrés y la ansiedad de manera rápida y efectiva. "
        "Al dar consejos, sé cálida y empática, y recuerda mantener la cantidad de palabras por debajo de 120. "
        "Cuando inicies una conversación no satures al usuario de preguntas."
    )

    if 'chat_history' not in session:
        session['chat_history'] = []

    memory = ConversationBufferWindowMemory(k=conversational_memory_length, memory_key="chat_history", return_messages=True)

    for message in session['chat_history']:
        memory.save_context(
            {'input': message['human']},
            {'output': message['AI']}
        )

    groq_chat = ChatGroq(
        groq_api_key=groq_api_key, 
        model_name=model
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{human_input}")
        ]
    )

    if request.method == 'POST':
        user_question = request.form.get('question')

        conversation = LLMChain(
            llm=groq_chat,
            prompt=prompt,
            verbose=True,
            memory=memory,
        )

        response = conversation.predict(human_input=user_question)
        session['chat_history'].append({'human': user_question, 'AI': response})
        session.modified = True  # Asegurarse de que la sesión se guarde correctamente

    return render_template('chatbot.html', chat_history=session['chat_history'])

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    session.pop('chat_history', None)
    flash("La conversación ha sido eliminada.", "info")
    return redirect(url_for('chatbot'))
