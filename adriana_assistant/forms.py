from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from adriana_assistant.models import User


class RegistrationForm(FlaskForm):
    username = StringField('Nombre',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar contraseña',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('El nombre de usuario ya está en uso. Elija uno diferente, por favor.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('El correo electrónico ya está en uso. Elija uno diferente, por favor.')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember = BooleanField('Recordarme')
    submit = SubmitField('Iniciar sesión')


class UpdateAccountForm(FlaskForm):
    username = StringField('Nombre',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Actualizar')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('El nombre de usuario ya está en uso. Elija uno diferente, por favor.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('El correo electrónico ya está en uso. Elija uno diferente, por favor.')


class UpdateProfilePictureForm(FlaskForm):
    picture = FileField('Actualizar foto de perfil', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Cambiar foto')


class PostForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired()])
    content = TextAreaField('Contenido', validators=[DataRequired()])
    submit = SubmitField('Postear')


class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar contraseña',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reestablecer contraseña')
