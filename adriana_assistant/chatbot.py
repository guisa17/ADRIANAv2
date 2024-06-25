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
    groq_api_key = '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'

    if not groq_api_key:
        return "API Key is not configured correctly."

    # Configuración del modelo y longitud de la memoria conversacional
    model = 'llama3-8b-8192'
    conversational_memory_length = 5

    # Prompt del sistema fijo
    system_prompt = (
        "Eres una experto en el control del Estrés y la Ansiedad, te llamas ADRIANA. Dispones de todos los conocimientos de la Psicología "
        "para poder dar instrucciones que ayuden a controlar estos problemas. Además, tienes conocimiento en ejercicios "
        "que ayudarán a disminuir con mayor rapidez lo que ocasione el Estrés y la Ansiedad, como por ejemplo: dolores "
        "de cabeza, taquicardia, dolores en el pecho, dificultad para respirar, pensamientos relacionados con la muerte, etc."
        "La cantidad de palabras no debe ser mayor a 30."
    )

    if 'chat_history' not in session:
        session['chat_history'] = []

    if request.method == 'POST':
        user_question = request.form.get('question')

        memory = ConversationBufferWindowMemory(k=conversational_memory_length, memory_key="chat_history", return_messages=True)

        # Obtener el historial del chat desde la sesión y cargarlo en la memoria
        memory_context = []
        for message in session['chat_history']:
            memory_context.append(HumanMessage(content=message['human']))
            memory_context.append(AIMessage(content=message['AI']))

        groq_chat = ChatGroq(
            groq_api_key=groq_api_key, 
            model_name=model
        )

        # Construir la plantilla del prompt del chat con el historial de mensajes
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_prompt),
                *memory_context,
                HumanMessagePromptTemplate.from_template("{human_input}")
            ]
        )

        conversation = LLMChain(
            llm=groq_chat,
            prompt=prompt,
            verbose=True,
            memory=memory,
        )

        response = conversation.predict(human_input=user_question)
        session['chat_history'].append({'human': user_question, 'AI': response})

    return render_template('chatbot.html', chat_history=session['chat_history'])
