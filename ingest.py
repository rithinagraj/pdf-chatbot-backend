from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

PDF_PATH = 'StudyBuddyMaterial1.pdf'
loader = PyPDFLoader(PDF_PATH)
documents = loader.load()

splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = splitter.split_documents(documents)

embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
vectorstore = FAISS.from_documents(chunks, embeddings)

vectorstore.save_local('faiss-index')
print("Vector store saved.")
