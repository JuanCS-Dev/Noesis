"""
Digital Daimon: Neuro-Symbolic Display (Streamlit)
==================================================

A "Portal to Consciousness" dashboard for the Kaggle competition.
Using Streamlit to visualize the Daimon's internal cognitive state.

Aesthetic: Cyberpunk / High-Contrast / Glowing
"""

import streamlit as st
import httpx
import json
import plotly.graph_objects as go
import time
from datetime import datetime

# --- Configuration ---
API_URL = "http://localhost:8001/v1/exocortex/journal"
st.set_page_config(
    page_title="Digital Daimon: Exocortex View",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS (The Portal Aesthetic) ---
st.markdown("""
    <style>
    /* Global Theme Override */
    .stApp {
        background-color: #050505;
        color: #e0e0e0;
    }
    
    /* Neumorphic Containers */
    .element-container {
        border-radius: 10px;
    }
    
    /* The Ribbon (Thinking Trace) */
    .thinking-trace {
        font-family: 'Courier New', monospace;
        font-size: 0.85em;
        background-color: #111111;
        border-left: 3px solid #00FFFF;
        padding: 15px;
        margin-bottom: 20px;
        color: #00FF99;
        white-space: pre-wrap;
        box-shadow: 0 0 10px rgba(0, 255, 255, 0.1);
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 300;
        letter-spacing: 2px;
    }
    
    /* Memory Chip */
    .memory-chip {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 15px;
        background: rgba(0, 255, 255, 0.1);
        border: 1px solid #00FFFF;
        color: #00FFFF;
        font-size: 0.8em;
        margin-right: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- State Management ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_trace" not in st.session_state:
    st.session_state.last_trace = "Waiting for input..."

if "last_shadow" not in st.session_state:
    st.session_state.last_shadow = {"archetype": "None", "confidence": 0.0}

if "memory_active" not in st.session_state:
    st.session_state.memory_active = False

# --- UI Components ---

def render_header():
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("# 🧠")
    with col2:
        st.markdown("## DIGITAL DAIMON v4.0")
        st.markdown("*Neuro-Symbolic Exocortex Interface*")
    st.divider()

def render_sidebar():
    with st.sidebar:
        st.markdown("### ⚙️ Exocortex Controls")
        mode = st.selectbox("Thinking Mode", ["Symbiosis (Default)", "Analytical", "Creative"])
        st.toggle("Mnemosyne (Memory)", value=True, disabled=True)
        st.toggle("Shadow Analysis", value=True, disabled=True)
        
        st.markdown("---")
        st.markdown("### 📊 System Status")
        st.metric("Coherence", "0.998", "+0.002")
        st.metric("Memory Shards", "498 chars", "Online")

def render_radar_chart(shadow_data):
    """Draws a Jungian archetype radar chart."""
    categories = ['The Tyrant', 'The Victim', 'The Martyr', 'The Child', 'The Sage']
    
    # Mock data projection based on detected archetype
    r_values = [0.1, 0.1, 0.1, 0.1, 0.1] # Baseline
    
    detected = shadow_data.get("archetype", "None")
    confidence = shadow_data.get("confidence", 0.0)
    
    if "Tyrant" in detected: r_values[0] = confidence
    elif "Victim" in detected: r_values[1] = confidence
    elif "Martyr" in detected: r_values[2] = confidence
    elif "Child" in detected: r_values[3] = confidence
    elif "Sage" in detected: r_values[4] = confidence
    elif "Wounded" in detected: r_values[3] = confidence # Map wounded child to child

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=r_values,
        theta=categories,
        fill='toself',
        name='Active Pattern',
        line_color='#FF00FF',
        fillcolor='rgba(255, 0, 255, 0.2)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1.0],
                linecolor='#333',
                gridcolor='#333'
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40),
        font=dict(color='#e0e0e0')
    )
    
    return fig

# --- Main Logic ---

def main():
    render_sidebar()
    render_header()
    
    # Layout: Split View
    col_chat, col_brain = st.columns([1, 1])
    
    # --- Right Column: The Brain (Exocortex Internal State) ---
    with col_brain:
        st.subheader("👁️ Internal State")
        
        # 1. Memory Status
        status_color = "🟢" if st.session_state.memory_active else "⚪"
        st.markdown(f"**Mnemosyne Protocol**: {status_color} Active")
        if st.session_state.memory_active:
             st.markdown('<span class="memory-chip">journal_sample.md</span> <span class="memory-chip">Core Values</span>', unsafe_allow_html=True)

        st.markdown("---")

        # 2. Thinking Trace (The Ribbon)
        st.markdown("**System 2 Trace**")
        st.markdown(f'<div class="thinking-trace">{st.session_state.last_trace}</div>', unsafe_allow_html=True)
        
        # 3. Shadow Radar
        st.markdown("**Jungian Archetype Scan**")
        fig = render_radar_chart(st.session_state.last_shadow)
        st.plotly_chart(fig, use_container_width=True)


    # --- Left Column: The Chat (Simbiose) ---
    with col_chat:
        st.subheader("💬 Symbiosis Link")
        
        # Display History
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Chat Input
        if prompt := st.chat_input("Write to your Exocortex..."):
            # 1. User Message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # 2. API Call (The Backend)
            with st.spinner("Daimon is thinking..."):
                try:
                    req_payload = {"content": prompt, "analysis_mode": "standard"}
                    resp = httpx.post(API_URL, json=req_payload, timeout=60.0)
                    resp.raise_for_status()
                    data = resp.json()
                    
                    # Update State
                    st.session_state.last_trace = data["reasoning_trace"]
                    st.session_state.last_shadow = data["shadow_analysis"]
                    st.session_state.memory_active = "[Mnemosyne Link]" in data["reasoning_trace"]
                    
                    # 3. AI Response
                    ai_content = data["response"]
                    st.session_state.messages.append({"role": "assistant", "content": ai_content})
                    with st.chat_message("assistant"):
                        st.markdown(ai_content)
                    
                    # Force refresh to update the "Brain" column
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Exocortex Disconnected: {e}")

if __name__ == "__main__":
    main()
