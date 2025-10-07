import streamlit as st
from pypdf import PdfReader
import io
import requests
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


def get_openrouter_response(api_key, pdf_text, chat_history, question):
    """Gets a response from the OpenRouter API based on PDF text and chat history."""
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost:8501",  # Change to your Streamlit app URL when deployed
            "X-Title": "PDF Chatbot Assistant"
        }

        # Build the conversation context
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant. Your primary task is to answer questions using ONLY the information "
                    "contained in the provided PDF text.\n"
                    "First, find the relevant information in the PDF to formulate an answer in English.\n"
                    "Then, check if the user has requested the answer in a specific language (e.g., 'in Hindi', 'in Marathi', 'in Tamil').\n"
                    "If a specific language is requested, you MUST translate the English answer into that language. "
                    "If the information cannot be found, say 'Information not available' in the requested language (or in English by default).\n"
                    "Do not use any external knowledge."
                )
            },
            {"role": "system", "content": f"PDF Content:\n---\n{pdf_text}\n---"}
        ]

        # Add chat history
        for message in chat_history:
            messages.append({"role": message["role"], "content": message["content"]})

        # Add the latest user question
        messages.append({"role": "user", "content": question})

        payload = {
            "model": "mistralai/mistral-small-3.2-24b-instruct:free",  # You can change this to another model on OpenRouter
            "messages": messages,
            "temperature": 0.7,
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        return result["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"An error occurred while contacting OpenRouter: {e}"


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
    api_key = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    api_key = None
    st.error("OpenRouter API key not found. Please add it to your Streamlit secrets.")
    st.info("To add your secret, create a file in your project's root directory named `.streamlit/secrets.toml` with the following content:\n\n`OPENROUTER_API_KEY = 'YOUR_API_KEY_HERE'`")

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
                response = get_openrouter_response(
                    api_key, 
                    st.session_state.pdf_text, 
                    st.session_state.messages[:-1],
                    prompt
                )
            st.write_stream(stream_response(response))
        st.session_state.messages.append({"role": "assistant", "content": response})
