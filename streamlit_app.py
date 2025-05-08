"""
Streamlit interface for the Generic Agent with Supabase, Ollama and A2A protocol integration.
"""

import os
import asyncio
import streamlit as st
from generic_agent import run_generic_agent
from a2a_protocol import A2AProtocol, AgentInfo
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Generic Agent Interface",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define CSS for the interface
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stTextInput>div>div>input {
        background-color: white;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
    }
    .chat-message.user {
        background-color: #e6f7ff;
    }
    .chat-message.assistant {
        background-color: #f0f0f0;
    }
    .chat-message .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        object-fit: cover;
        margin-right: 1rem;
    }
    .chat-message .message {
        flex-grow: 1;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("Generic Agent Interface")
st.subheader("Interact with a versatile agent powered by Supabase, Ollama, and A2A protocol")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # Model selection
    model = st.selectbox(
        "Ollama Model",
        ["llama2", "codellama", "mistral", "gemma", "deepseek"],
        index=0
    )
    
    # Table selection
    table_name = st.text_input("Supabase Table", value="knowledge_base")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get user input
prompt = st.chat_input("Ask something...")

# When user submits a question
if prompt:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response with a spinner
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🤔 Thinking...")
        
        try:
            # Call the generic agent
            with st.spinner("Processing..."):
                response = asyncio.run(run_generic_agent(
                    prompt,
                    table_name=table_name,
                    model=model
                ))
            
            # Update placeholder with response
            message_placeholder.markdown(response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        except Exception as e:
            message_placeholder.markdown(f"❌ Error: {str(e)}")
            st.error(f"An error occurred: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Generic Agent v1.0.0 | Powered by Supabase, Ollama & A2A Protocol")
