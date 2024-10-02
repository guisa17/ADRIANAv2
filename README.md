# ADRIANA - Asistente de Gestión del Estrés y la Ansiedad

## Descripción

ADRIANA es una plataforma innovadora que combina inteligencia artificial con técnicas de psicología para ayudar a las personas a manejar el estrés y la ansiedad. La plataforma ofrece diversas funcionalidades, tales como un chatbot interactivo, una comunidad para compartir pensamientos y progreso personal, módulos de relajación y respiración guiados, entre otros.

## Funcionalidades Principales

- **Chatbot**: Interactúa en tiempo real para ofrecer apoyo emocional y técnicas de relajación.
- **Comunidad**: Comparte pensamientos y progreso personal con otros usuarios.
- **Módulos de Relajación**: Ejercicios y audios guiados para reducir el estrés.


## Requisitos

- Python 3.10 o superior
- Virtualenv
- Dependencias listadas en `requirements.txt`

## Instalación y Ejecución Local

Sigue estos pasos para configurar y ejecutar el proyecto de ADRIANA en tu máquina local.

1. **Clonar el repositorio**

   ```bash
   git clone https://github.com/guisa17/ADRIANAv2.git
   cd ADRIANA
   ```

2. Crea un entorno virtual:

    ```bash
    python -m venv venv
    ```

3. Activa el entorno virtual:

    - En Windows:

        ```bash
        venv\Scripts\activate
        ```

    - En macOS/Linux:

        ```bash
        source venv/bin/activate
        ```

4. Instala las dependencias:

    ```bash
    pip install -r requirements.txt
    ```

5. Configura las variables de entorno:

    Crea un archivo `.env` en el directorio raíz del proyecto con las siguientes variables:

    ```env
    GROQ_API_KEY=tu_groq_api_key
    HF_BEARER_API_TOKEN=tu_hf_bearer_api_token
    ```

## Ejecución

1. Realiza las migraciones de la base de datos:

    ```bash
    flask db init
    flask db migrate -m "Initial migration."
    flask db upgrade
    ```

2. Ejecuta la aplicación:

    ```bash
    python run.py
    ```

    La aplicación estará disponible en `http://127.0.0.1:5000`.

### Nota
Es posible visualizar el deployment de la aplicación en el siguiente enlace https://adrianav4.pythonanywhere.com/.
