import streamlit as st
from PyPDF2 import PdfReader
import io
import google.generativelanguage as genai
import time

# --- Helper Functions ---

def extract_text_from_pdf(pdf_file):
    """
    Extracts text from an uploaded PDF file.
    """
    try:
        # Create a file-like object from the uploaded file's bytes
        pdf_file_object = io.BytesIO(pdf_file.read())
        pdf_reader = PdfReader(pdf_file_object)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        return text
    except Exception as e:
        st.error(f"Error reading the PDF file: {e}")
        return None

def get_gemini_response(api_key, context, question):
    """
    Generates a response from the Gemini API based on the PDF context and user question.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are a helpful assistant that answers questions based on the provided context from a PDF document.
        Your goal is to provide a clear and concise answer.
        If the answer is not available in the text, you must state that you cannot find the answer in the document.
        Do not provide information from outside the given context.

        CONTEXT:
        {context}

        QUESTION:
        {question}

        ANSWER:
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # A more user-friendly error message
        st.error("An error occurred while generating the response. Please check your API key and try again.")
        # Log the full error for debugging
        print(f"Gemini API Error: {e}") 
        return "Sorry, I encountered an error. Please check the console for more details."


# --- Streamlit App ---

# Set page configuration
st.set_page_config(page_title="PDF Chatbot with Gemini", page_icon="📄", layout="wide")

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

st.title("📄 PDF Chatbot with Gemini")
st.write("Upload a PDF document and ask any question about its content.")

# Initialize session state variables
if 'pdf_text' not in st.session_state:
    st.session_state.pdf_text = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

# --- Sidebar for PDF Upload and API Key ---
with st.sidebar:
    st.header("Configuration")
    
    # API Key Input
    api_key_input = st.text_input(
        "Enter your Gemini API Key", 
        type="password", 
        value=st.session_state.api_key,
        help="You can get your free API key from Google AI Studio."
    )
    if api_key_input:
        st.session_state.api_key = api_key_input

    st.markdown("---")
    st.header("Upload Your PDF")
    uploaded_file = st.file_uploader("Drag and drop a PDF file here", type=["pdf"])

    if uploaded_file:
        if st.button("Process Document"):
            if not st.session_state.api_key:
                st.warning("Please enter your Gemini API key first.")
            else:
                with st.spinner("Extracting text from the document..."):
                    extracted_text = extract_text_from_pdf(uploaded_file)
                
                if extracted_text:
                    st.session_state.pdf_text = extracted_text
                    st.session_state.chat_history = [
                        {"role": "assistant", "content": "I've processed the document. What would you like to know?"}
                    ]
                    st.success("Document processed successfully!")
                else:
                    st.error("Failed to extract text. The PDF might be empty or corrupted.")
    st.markdown("---")
    st.info("This chatbot uses the Gemini API for question-answering.")


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
            with st.spinner("Thinking..."):
                answer = get_gemini_response(st.session_state.api_key, st.session_state.pdf_text, user_question)
                
                # Simulate typing effect
                message_placeholder = st.empty()
                full_response = ""
                for chunk in answer.split():
                    full_response += chunk + " "
                    time.sleep(0.05)
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)

        # Add assistant response to history
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
else:
    st.info("Please provide an API key and process a PDF using the sidebar to start the chat.")

