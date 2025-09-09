import streamlit as st
from PyPDF2 import PdfReader
import io

# --- Helper Functions ---

def extract_text_from_pdf(pdf_file):
    """
    Extracts text from an uploaded PDF file.
    """
    try:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        return text
    except Exception as e:
        st.error(f"Error reading the PDF file: {e}")
        return None

def find_answer_in_text(text, question):
    """
    A simple keyword-based search to find answers in the text.
    This is a placeholder and should be replaced with a real QA model (e.g., using Gemini, OpenAI, etc.).
    """
    # Convert text and question to lowercase for case-insensitive search
    text_lower = text.lower()
    question_lower = question.lower()
    
    # Split text into sentences
    sentences = text.split('.')
    
    # Find sentences containing keywords from the question
    question_keywords = set(question_lower.split())
    
    relevant_sentences = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in question_keywords):
            relevant_sentences.append(sentence.strip())
            
    if relevant_sentences:
        # Join the first few relevant sentences to form an answer
        answer = ". ".join(relevant_sentences[:3]) + "."
        return answer
    else:
        return "I'm sorry, I couldn't find an answer to your question in the document."

# --- Streamlit App ---

# Set page configuration
st.set_page_config(page_title="PDF Chatbot", page_icon="📄", layout="wide")

# Custom CSS for a better look and feel
st.markdown("""
<style>
    .stApp {
        background-color: #F0F2F6;
    }
    .stChatMessage {
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .st-chat-message-user {
        background-color: #DCF8C6;
    }
    .st-chat-message-assistant {
        background-color: #FFFFFF;
    }
    .stSidebar {
        background-color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)


# --- Main UI ---

st.title("📄 PDF Chatbot Assistant")
st.write("Upload a PDF document and ask any question about its content.")

# Initialize session state variables
if 'pdf_text' not in st.session_state:
    st.session_state.pdf_text = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- Sidebar for PDF Upload ---
with st.sidebar:
    st.header("Upload Your PDF")
    uploaded_file = st.file_uploader("Drag and drop a PDF file here", type=["pdf"])

    if uploaded_file:
        if st.button("Process Document"):
            with st.spinner("Extracting text from the document..."):
                # Read the uploaded file as bytes
                file_bytes = io.BytesIO(uploaded_file.getvalue())
                extracted_text = extract_text_from_pdf(file_bytes)
                
                if extracted_text:
                    st.session_state.pdf_text = extracted_text
                    st.session_state.chat_history = [
                        {"role": "assistant", "content": "I've processed the document. What would you like to know?"}
                    ]
                    st.success("Document processed successfully!")
                else:
                    st.error("Failed to extract text. The PDF might be empty or corrupted.")
    st.markdown("---")
    st.info("This is a demo app. The question-answering is based on simple keyword matching.")


# --- Chat Interface ---

# Display previous messages
if st.session_state.chat_history:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Handle new user input
if st.session_state.pdf_text:
    user_question = st.chat_input("Ask a question about the PDF content...")
    if user_question:
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_question)
            
        # Generate and display assistant's response
        with st.chat_message("assistant"):
            with st.spinner("Searching for the answer..."):
                answer = find_answer_in_text(st.session_state.pdf_text, user_question)
                st.markdown(answer)
        
        # Add assistant response to history
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
else:
    st.info("Please upload and process a PDF using the sidebar to start the chat.")
