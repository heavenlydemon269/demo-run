import streamlit as st
from pypdf import PdfReader
import io
import google.generativeai as genai
import time

# --- Helper Functions ---

def get_pdfs_text(pdf_docs_bytes):
    """Extracts text from a list of PDF files."""
    text = ""
    for pdf_bytes in pdf_docs_bytes:
        try:
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        except Exception as e:
            st.error(f"Error reading a PDF: {e}")
    return text

def get_gemini_response(api_key, pdf_text, chat_history, question):
    """Gets a response from the Gemini API based on PDF text and chat history."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Construct the context and history for the model
        prompt_parts = [
            "You are a helpful AI assistant. Your primary task is to answer questions using ONLY the information contained in the provided PDF text.",
            "First, find the relevant information in the PDF to formulate an answer in English.",
            "Then, check if the user has requested the answer in a specific language (e.g., 'in Hindi', 'in Marathi', 'in Tamil').",
            "If a specific language is requested, you MUST translate the English answer you formulated into that language. The final response should ONLY be in the requested language.",
            "If the information to answer the question cannot be found in the PDF, state that the information is not available, and say this in the language the user requested (or in English if no language was specified).",
            "Do not use any external knowledge.",
            f"PDF Content:\n---\n{pdf_text}\n---\n",
            "Now, here is the conversation history:",
        ]

        # Add the existing chat history to the prompt
        for message in chat_history:
             prompt_parts.append(f"{message['role'].capitalize()}: {message['content']}")
        
        # Add the new user question
        prompt_parts.append(f"User: {question}")
        prompt_parts.append("Assistant:")

        response = model.generate_content("\n".join(prompt_parts))
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"

def stream_response(text):
    """Yields text word by word for a streaming effect."""
    for word in text.split():
        yield word + " "
        time.sleep(0.05)

# --- Streamlit App ---

st.set_page_config(page_title="PDF Chatbot Assistant", layout="wide")

st.title("📄 PDF Chatbot Assistant")
st.write("Upload one or more PDF documents and ask any question about their content.")

# --- API Key Configuration ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    api_key = None
    st.error("Gemini API key not found. Please add it to your Streamlit secrets.")
    st.info("To add your secret, create a file in your project's root directory named `.streamlit/secrets.toml` with the following content:\n\n`GEMINI_API_KEY = 'YOUR_API_KEY_HERE'`")

# --- Sidebar for PDF Upload ---
with st.sidebar:
    st.header("Configuration")
    uploaded_files = st.file_uploader("Upload your PDF(s)", type="pdf", accept_multiple_files=True)
    
    if uploaded_files:
        st.success(f"{len(uploaded_files)} PDF(s) uploaded successfully!")
        if st.button("Process Documents"):
            with st.spinner("Processing documents..."):
                pdf_docs_bytes = [file.getvalue() for file in uploaded_files]
                # Store PDF text in session state
                st.session_state.pdf_text = get_pdfs_text(pdf_docs_bytes)
                # Initialize chat history
                st.session_state.messages = [{"role": "assistant", "content": "I've processed the documents. What would you like to know?"}]
            st.success("Documents processed!")

# --- Main Chat Interface ---

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question about the PDF(s)"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    if not api_key:
        st.warning("API Key not configured. Please add it to your Streamlit secrets to continue.")
    elif "pdf_text" not in st.session_state or not st.session_state.pdf_text:
        st.warning("Please upload and process at least one PDF document first.")
    else:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_gemini_response(
                    api_key, 
                    st.session_state.pdf_text, 
                    st.session_state.messages[:-1],
                    prompt
                )
            st.write_stream(stream_response(response))
        st.session_state.messages.append({"role": "assistant", "content": response})

