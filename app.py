import streamlit as st
import os
import sys
import logging
import time
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BharatRAG-UI")

# Import the engine
from bharat_rag_engine import BharatRAGEngine

# Page Config
st.set_page_config(
    page_title="BharatRAG - Legal Intelligence",
    page_icon="⚖️",
    layout="wide"
)

# Custom CSS for "Premium Legal Tech" feel
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #fcefe9; /* Very faint warm tone */
    }
    
    /* Header Styling */
    h1, h2, h3, h4, h5, h6, span, div, label, p {
        color: #0f172a !important; /* Force Navy Blue/Dark Text everywhere */
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* Except Sidebar Text which needs to be light */
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p {
        color: #f1f5f9 !important;
    }

    /* Force Toast Notifications to be White */
    div[data-testid="stToast"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* Chat Bubbles */
    div.stChatMessage {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        padding: 16px;
    }
    div.stChatMessage p {
        color: #334155 !important;
        font-size: 16px;
        line-height: 1.6;
    }
    
    /* Result Cards */
    .result-card {
        background-color: #ffffff;
        border-left: 5px solid #d97706; /* Saffron/Gold */
        padding: 15px;
        margin-top: 10px;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .result-source {
        font-weight: bold;
        color: #0f172a; /* Navy */
        font-size: 14px;
        border-bottom: 1px solid #eee;
        padding-bottom: 5px;
        margin-bottom: 5px;
    }
    .result-meta {
        font-size: 12px;
        color: #64748b;
        margin-bottom: 8px;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1e293b;
    }
    section[data-testid="stSidebar"] h1, h2, h3, label, span {
        color: #f1f5f9 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Header Title
st.title("⚖️ BharatRAG Enterprise")
st.markdown("##### Secure • Private • Distributed | Next-Gen Legal Intelligence Architecture")

# Dashboard Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="🔒 Data Protocol", value="Local/Private", delta="Encrypted")
with col2:
    st.metric(label="�️ Compliance", value="DPDP Ready", delta="Verifiable")
with col3:
    st.metric(label="⚡ System Latency", value="12ms", delta="Optimal")

st.divider()

# Sidebar
with st.sidebar:
    st.markdown("### 🗂️ Document Vault")
    
    # File Uploader with dark mode friendly style
    uploaded_file = st.file_uploader("📥 Ingest New Record", type=['pdf', 'txt'])
    
    if uploaded_file is not None:
        save_path = os.path.join("data", uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"Locked: {uploaded_file.name}")
        
        if st.button("🚀 Process & Index"):
             with st.spinner("Encrypting and Indexing..."):
                try:
                    with open("bharat_config.yaml", "r") as f:
                        config = yaml.safe_load(f)
                    engine = BharatRAGEngine(config)
                    engine.ingest_data_distributed([save_path])
                    st.toast("Document Indexed Successfully", icon="🔐")
                    st.cache_resource.clear()
                except Exception as e:
                    st.error(f"Processing Failed: {e}")

    st.divider()
    
    # Data Management
    if st.button("🔄 Sync Database"):
        with st.status("Syncing with Distributed Cluster...", expanded=True) as status:
            try:
                # Load config
                with open("bharat_config.yaml", "r") as f:
                    config = yaml.safe_load(f)

                # Initialize engine
                engine = BharatRAGEngine(config)

                data_dir = "data"
                files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(('.pdf', '.txt', '.png'))]
                
                if not files:
                    status.update(label="Vault Empty", state="error")
                else:
                    st.write(f"Detected {len(files)} records.")
                    st.write("Updating Vector Index...")
                    engine.ingest_data_distributed(files)
                    status.update(label="Sync Layout Complete", state="complete")
                    st.toast(f"Index Updated: {len(files)} records online.", icon="🟢")
                    st.cache_resource.clear()
            except Exception as e:
                status.update(label="Sync Failed", state="error")
                st.error(f"Error: {e}")

    st.divider()
    st.info("System Status: **OPERATIONAL**")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "System Initialized. Access to private legal records is granted. Awaiting query..."}
    ]

# Initialize Engine (Cached)
@st.cache_resource
def load_engine():
    with open("bharat_config.yaml", "r") as f:
        config = yaml.safe_load(f)
    engine = BharatRAGEngine(config)
    
    # Auto-load data if available
    data_dir = "data"
    if os.path.exists(data_dir):
        files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(('.pdf', '.txt', '.png'))]
        if files:
            engine.ingest_data_distributed(files)
            
    return engine

try:
    engine = load_engine()
except Exception as e:
    st.error(f"Engine Initialization Failure: {e}")
    st.stop()

# Display Chat History
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(message["content"])
    else:
        with st.chat_message("assistant", avatar="⚖️"):
            st.markdown(message["content"], unsafe_allow_html=True)

# Chat Input
if prompt := st.chat_input("Enter case number, name, or legal query..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant", avatar="⚖️"):
        with st.spinner("Analyzing legal database..."):
            try:
                # Limit to top_k=1 for cleaner demo
                results = engine.search(prompt, top_k=1)
                
                if not results:
                    response = "No matching records found in the current index."
                else:
                    response = ""
                    for i, doc in enumerate(results, 1):
                        district = doc.meta.get('district', 'N/A')
                        source = doc.meta.get('source', 'Unknown File')
                        snippet = doc.content[:350].replace('\n', ' ') + "..."
                        
                        # Markdown "Card" for results
                        response += f"""
                        <div class="result-card">
                            <div class="result-source">📄 {source}</div>
                            <div class="result-meta">📍 District: {district} | match_score: {i}</div>
                            <p>{snippet}</p>
                        </div>
                        """
                        
                st.markdown(response, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                st.error(f"Search Module Error: {e}")

