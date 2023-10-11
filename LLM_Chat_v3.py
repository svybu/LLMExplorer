import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
import requests
from typing import Union
import openai
from datetime import date
# from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

# from langchain.llms import HuggingFaceHub
from translate import Translator

from api.database.db import SessionLocal
from htmlTemplates import css, bot_template, user_template
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.callbacks import get_openai_callback
from sqlalchemy.orm import Session
from api.database.models import ChatHistory, User, Document
from api.conf.config import settings

size = 50000000
acc = 0  # Сюди треба передати параметри користувача. Якщо прєм. то =1, якщо базовий то =0.
openai.api_key = settings.OPENAI_API_KEY

def get_token_from_url():
    params = st.experimental_get_query_params()
    token = params.get("token", [None])[0]
    return token

def generate_image_with_dalle(prompt):
    image_resp = openai.Image.create(prompt=prompt, n=1, size="512x512")
    image_url = image_resp.data[0]['url']
    return image_url

def verify_token_and_get_user_id(token: str) -> Union[int, None]:
    VERIFY_TOKEN_ENDPOINT = f"{settings.API_URL}/api/auth/get_user_id"

    try:
        response = requests.get(VERIFY_TOKEN_ENDPOINT, params={"token": token})
        if response.status_code == 200:
            return response.json().get("user_id")
    except Exception as e:
        st.error(f"Error verifying token: {e}")

    return None

def set_user_as_plus(user_id: int, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.plus = True
        db.commit()
        return True
    return False


def get_pdf_text(pdf_docs, selected_file_index):
    if selected_file_index >= 0 and selected_file_index < len(pdf_docs):
        pdf_reader = PdfReader(pdf_docs[selected_file_index])
        text = " ".join(page.extract_text() for page in pdf_reader.pages)
        return text
    else:
        return ""

def store_document(user_id: int, pdf_docs, selected_file_index: int, db: Session):
    content = get_pdf_text(pdf_docs, selected_file_index)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        st.error("User not found.")
        return

    max_size = settings.MAX_DOC_SIZE
    if len(content.encode('utf-8')) > max_size:
        st.warning(f"Document size exceeds the limit of {max_size / 1000} KB.")
        return

    current_docs = db.query(Document).filter(Document.user_id == user_id).all()
    if user.plus:
        if len(current_docs) >= settings.MAX_DOCS_PLUS:
            oldest_doc = min(current_docs, key=lambda x: x.uploaded_at)
            db.delete(oldest_doc)
    else:
        for doc in current_docs:
            db.delete(doc)

    new_document = Document(content=content, user_id=user_id)
    db.add(new_document)
    db.commit()

def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n", chunk_size=1000, chunk_overlap=200, length_function=len
    )
    return text_splitter.split_text(text)


def get_vectorstore(text_chunks):
    # embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    embeddings = OpenAIEmbeddings()
    return FAISS.from_texts(texts=text_chunks, embedding=embeddings)


def get_conversation_chain(vectorstore):
    # llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature": 0.5, "max_length": 1024})
    llm = ChatOpenAI()
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    return ConversationalRetrievalChain.from_llm(
        llm=llm, retriever=vectorstore.as_retriever(), memory=memory
    )



def handle_user_input(user_question, conversation_chain, chat_history, db: Session, user_id: int):
    chat_history.clear()
    with get_openai_callback() as cb:
        response = conversation_chain({"question": user_question})
        chat_history.extend(reversed(response["chat_history"]))
        st.write(cb)


        user_message = ""
        bot_message = ""

        for i, message in enumerate(chat_history):
            if i % 2 == 0:  # Якщо індекс повідомлення парний, це повідомлення від бота
                bot_message = message.content
            else:  # Інакше, це запит користувача
                user_message = message.content
                db_chat_history = ChatHistory(user_id=user_id, user_message=user_message, bot_message=bot_message)
                db.add(db_chat_history)
                user_message = ""
                bot_message = ""

        db.commit()

        # Вивести кожне повідомлення на екран
        for i, message in enumerate(chat_history):
            template = user_template if i % 2 != 0 else bot_template
            st.write(template.replace("{{MSG}}", message.content), unsafe_allow_html=True)


def clear_chat_history(chat_history):
    chat_history.clear()


def save_chat_history(chat_history, filename="chat_history.txt"):
    chat_history.clear()
    st.success("Chat history saved successfully")


def translate_text(text, source_language, target_language):
    translator = Translator(from_lang=source_language, to_lang=target_language)
    translated_text = translator.translate(text)
    return translated_text


def check_file_size(pdf_docs):
    for pdf in pdf_docs:
        file_size = pdf.getbuffer().nbytes
        if not acc:
            if file_size >= size:
                st.warning("You have to upload a file less than 50 MB")
                pdf_docs = None
    return pdf_docs


def main():
    st.set_page_config(page_title="LLMExplorer", page_icon=":robot_face:")
    st.write(css, unsafe_allow_html=True)
    token = get_token_from_url()
    user_id = None
    acc = 0

    if token:
        user_id = verify_token_and_get_user_id(token)
        if user_id:
            acc = 1

    load_dotenv()

    db = SessionLocal()

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.header("LLMExplorer :robot_face:")

    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.plus:
            mode = st.radio(
                "Choose your mode",
                ("Query Documents", "DALL·E Image Generation")
            )

            if mode == "DALL·E Image Generation":
                if user.last_image_generated_date == date.today():
                    if user.images_generated_today >= settings.MAX_IMAGES:
                        st.warning(f"You have reached the limit of {settings.MAX_IMAGES} images for today.")
                        return
                else:
                    user.images_generated_today = 0
                    user.last_image_generated_date = date.today()
                st.subheader("Generate images with DALL·E")
                description = st.text_input("Enter your description for image generation:")
                if st.button("Generate Image"):
                    image_url = generate_image_with_dalle(description)
                    st.image(image_url)
                    user.images_generated_today += 1
                    db.commit()
            else:
                user_question = st.text_input("Ask a question about your documents:")

                if user_question:
                    if st.session_state.conversation is None:
                        st.warning("Please process your PDF documents first.")
                    else:
                        handle_user_input(
                            user_question,
                            st.session_state.conversation,
                            st.session_state.chat_history,
                            db,
                            user_id
                        )


    with st.sidebar:
        logout_url = f'{settings.API_URL}/api/auth/logout/'
        st.markdown(f'<a href="{logout_url}" target="_blank"><button style="margin-top: 20px">Logout</button></a>',
                    unsafe_allow_html=True)

        st.subheader("Your documents")

        pdf_docs = st.file_uploader("Upload your PDFs here", accept_multiple_files=True)
        pdf_docs = check_file_size(pdf_docs)

        if pdf_docs:
            selected_file = st.selectbox(
                "Select a PDF file:", [pdf.name for pdf in pdf_docs]
            )
            selected_file_index = [pdf.name for pdf in pdf_docs].index(selected_file)
        else:
            selected_file_index = -1

        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user and not user.plus:
                if st.button("Make Me Plus"):
                    if set_user_as_plus(user_id, db):
                        st.success("You are now a Plus user!")
                    else:
                        st.error("Failed to update your status.")

        if st.button("Process"):
            if pdf_docs:
                with st.spinner("Processing..."):
                    raw_text = get_pdf_text(pdf_docs, selected_file_index)
                    text_chunks = get_text_chunks(raw_text)
                    vectorstore = get_vectorstore(text_chunks)
                    st.session_state.conversation = get_conversation_chain(vectorstore)

                    user = db.query(User).filter(User.id == user_id).first()
                    if user and user.plus:
                        store_document(user_id, pdf_docs, selected_file_index, db)
            else:
                st.warning("Please upload PDF documents before processing.")

        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.plus:
                saved_docs = db.query(Document).filter(Document.user_id == user_id).all()
                if saved_docs:
                    selected_saved_doc_content = st.selectbox(
                        "Select a saved document to view:",
                        [(f"{doc.content[:50]}...") for doc in saved_docs]
                    )
                    selected_saved_doc = next(
                        doc.id for doc in saved_docs if doc.content.startswith(selected_saved_doc_content[:50]))

                    st.text("Document content:")
                    st.text_area("Document Content:", value=selected_saved_doc_content, disabled=True)

                    # Додавання кнопки для обробки вибраного документа
                    if st.button("Process Selected Saved Document"):
                        raw_text = selected_saved_doc_content
                        text_chunks = get_text_chunks(raw_text)
                        vectorstore = get_vectorstore(text_chunks)
                        st.session_state.conversation = get_conversation_chain(vectorstore)

        if st.button("Clear Chat History"):
            clear_chat_history(st.session_state.chat_history)
            st.success("Chat history cleared successfully.")

        if st.button("Save Chat History"):
            if st.session_state.chat_history:
                save_chat_history(st.session_state.chat_history)

        st.subheader("Translation")
        text_to_translate = st.text_area("Enter text to translate:")
        source_language = st.selectbox("Select source language:", ["en", "fr", "es", "de", "ru", "uk"])
        target_language = st.selectbox("Select target language:", ["en", "fr", "es", "de", "ru", "uk"])
        if st.button("Translate"):
            if text_to_translate and source_language and target_language:
                translated_text = translate_text(text_to_translate, source_language, target_language)
                st.write(f"Translated Text ({source_language} to {target_language}): {translated_text}")


if __name__ == "__main__":
    main()
