import telebot
from dotenv import load_dotenv
import PyPDF2
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.llms import HuggingFaceHub
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import google.generativeai as genai
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain

os.environ["GOOGLE_API_KEY"] = ("AIzaSyBFGavIgm697DrT3iUnSrhrBlJmA1_BuCY")

def get_pdf_text():
    my_file = open("test_text.pdf", "rb")
    pdf_reader = PyPDF2.PdfReader(my_file)
    text=""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")


def get_conversational_chain():

    prompt_template = """
    This file contains descriptions of 19 programs, all numbered. Text written below a program name 
    refers to that program until the next program name. The names of the program instructors are listed after the word "Преподаватели".
   Answer the question as detailed as possible from the provided context, make sure to provide all the details \n\n
    Context:\n {context}?\n
    Question: \n{question}\n
    Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-pro",
                             temperature=0.3, max_length=10000)

    prompt = PromptTemplate(template = prompt_template, input_variables = ["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

    return chain

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question)

    chain = get_conversational_chain()

    response = chain(
        {"input_documents": docs, "question": user_question}
        , return_only_outputs=True)
    return response

# токен бота
bot = telebot.TeleBot("7287756507:AAHAPYC2W4YluwoSuoSW727iRjmoC0kZX9k")
@bot.message_handler(content_types=['text'])
def get_response(message):
    raw_text = get_pdf_text()
    text_chunks = get_text_chunks(raw_text)
    get_vector_store(text_chunks)
    response = user_input(message.text)
    print(response)
    bot.send_message(message.from_user.id, response['output_text'])

bot.polling(none_stop=True, interval=0)