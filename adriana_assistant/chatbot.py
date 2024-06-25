import os
from flask import Blueprint, render_template, request, session
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    groq_api_key = os.getenv('GROQ_API_KEY')

    if not groq_api_key:
        return "API Key is not configured correctly."

    # Configuración del modelo y longitud de la memoria conversacional
    model = 'llama3-8b-8192'
    conversational_memory_length = 20

    # Prompt del sistema fijo
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

    # Cargar el historial del chat desde la sesión en la memoria
    for message in session['chat_history']:
        memory.save_context(
            {'input': message['human']},
            {'output': message['AI']}
        )

    groq_chat = ChatGroq(
        groq_api_key=groq_api_key, 
        model_name=model
    )

    # Construir la plantilla del prompt del chat con el historial de mensajes
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

    return render_template('chatbot.html', chat_history=session['chat_history'])
