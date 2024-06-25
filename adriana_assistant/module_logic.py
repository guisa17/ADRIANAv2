import os
from transformers import pipeline
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
from dotenv import find_dotenv, load_dotenv
import requests

# Cargar las variables de entorno
load_dotenv(find_dotenv())

GROQ_API_KEY = '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'
HF_BEARER_API_TOKEN = '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'   

# Definir el pipeline para la tarea de imagen a texto
def img2text(image_path):
    image_to_text = pipeline("image-to-text", model="Salesforce/blip-image-captioning-large")
    text = image_to_text(image_path)[0]["generated_text"]
    return text

# Generar instrucciones basadas en la imagen
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

# Convertir texto a voz
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

# Procesar el módulo
def process_module(image_path):
    scenario = img2text(image_path)
    instructions = generate_instructions(scenario)
    text2speech(instructions)
    title = "Módulo de Gestión del Estrés"
    return title, scenario, instructions

# Cargar módulos preexistentes
def load_preexisting_modules():
    modules_dir = os.path.join('adriana_assistant', 'static', 'modules_data')

    # Verificar que el directorio existe
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

# Obtener detalles de un módulo específico
def get_module_details(module_name):
    modules_dir = os.path.join('adriana_assistant', 'static', 'modules_data')
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
