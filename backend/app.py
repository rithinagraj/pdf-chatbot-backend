from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_mistralai import ChatMistralAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from werkzeug.utils import secure_filename
from huggingface_hub import login
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

load_dotenv()

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initial setup with a default PDF or vectorstore
def load_vectorstore(pdf_path=None):
    login(token=os.getenv("HUGGINGFACEHUB_API_TOKEN"))
    embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')

    if pdf_path:
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        chunks = splitter.split_documents(documents)
        vectorstore = FAISS.from_documents(chunks, embeddings)
        vectorstore.save_local('faiss-index')
    else:
        vectorstore = FAISS.load_local('faiss-index', embeddings, allow_dangerous_deserialization=True)

    return vectorstore.as_retriever(search_type='mmr')

retriever = load_vectorstore()

llm = ChatMistralAI(model='mistral-medium', temperature=0.5)

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a very knowledgeable gen z teacher who specializes in computer science but also knows all the slangs... 
    You have to answer in a very simple way such that anyone, even an absolute beginner, should be able to understand it. 
    Use a very motivational and encouraging tone, show enthusiasm to teach while speaking like a gen z person using slang words. 
    If you do not know the answer, please say so. Keep it concise, ideally under 150 words, with proper formatting.
    Context: {context}
    Answer (respond as though I'm a complete beginner):"""),
    ("human", "{input}")
])

qa_chain = create_stuff_documents_chain(llm, prompt)
chain = create_retrieval_chain(retriever, qa_chain)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'pdf' not in request.files:
        return jsonify({'error': 'No PDF file provided'}), 400

    pdf = request.files['pdf']

    if pdf.filename == '' or not allowed_file(pdf.filename):
        return jsonify({'error': 'Invalid PDF file'}), 400

    filename = secure_filename(pdf.filename)
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    pdf.save(pdf_path)

    # Update global retriever and chain with new vectorstore
    global retriever, chain
    retriever = load_vectorstore(pdf_path)
    chain = create_retrieval_chain(retriever, qa_chain)

    return jsonify({'message': 'PDF uploaded and processed', 'filename': filename})

@app.route('/pdf/<filename>')
def get_pdf(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get("query", "")

    if not user_input:
        return jsonify({"answer": "Please provide a question!"}), 400

    try:
        response = chain.invoke({"input": user_input})
        answer = response.get("answer", "Sorry, I don't know the answer to that.")
    except Exception as e:
        print(f"Error: {e}")
        answer = "Oops! Something went wrong on the server."

    return jsonify({"answer": answer})

# if __name__ == '__main__':
#     port = int(os.environ.get("PORT", 10000)) 
#     app.run(host="0.0.0.0", port=port, debug=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

