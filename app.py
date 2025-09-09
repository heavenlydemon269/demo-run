import streamlit as st
from pypdf import PdfReader
import io
import google.generativeai as genai
import time

# --- Helper Functions ---

def get_pdf_text(pdf_bytes):
    """Extracts text from a PDF file."""
    try:
        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def get_gemini_response(api_key, pdf_text, chat_history, question):
    """Gets a response from the Gemini API based on PDF text and chat history."""
    try:
        genai.configure(api_key=api_key)
        # Updated model name to the latest recommended version
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        # Construct the context and history for the model
        # The prompt tells the model how to behave and includes the PDF text and chat history
        prompt_parts = [
            "You are a helpful AI assistant. Your task is to answer questions based ONLY on the provided text from a PDF document and the ongoing conversation history.",
            "Do not answer any questions that are outside the scope of the provided document text.",
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
st.write("Upload a PDF document and ask any question about its content.")

# --- Sidebar for API Key and PDF Upload ---
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Enter your Google Gemini API Key:", type="password")
    
    uploaded_file = st.file_uploader("Upload your PDF", type="pdf")
    
    if uploaded_file:
        st.success("PDF uploaded successfully!")
        if st.button("Process Document"):
            with st.spinner("Processing document..."):
                pdf_bytes = uploaded_file.getvalue()
                # Store PDF text in session state
                st.session_state.pdf_text = get_pdf_text(pdf_bytes)
                # Initialize chat history
                st.session_state.messages = [{"role": "assistant", "content": "I've processed the document. What would you like to know?"}]
            st.success("Document processed!")

# --- Main Chat Interface ---

# Initialize session state for messages if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask a question about the PDF"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Check for prerequisites
    if not api_key:
        st.warning("Please enter your Gemini API key in the sidebar.")
    elif "pdf_text" not in st.session_state or not st.session_state.pdf_text:
        st.warning("Please upload and process a PDF document first.")
    else:
        # Get and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_gemini_response(
                    api_key, 
                    st.session_state.pdf_text, 
                    st.session_state.messages[:-1], # Pass history excluding the current user message
                    prompt
                )
            # Use the streaming effect
            st.write_stream(stream_response(response))
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

