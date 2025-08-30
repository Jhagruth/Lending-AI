# main.py
# The Streamlit front-end for the AI Risk Assessment Copilot, now with an integrated AI Assistant.

import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dotenv import load_dotenv
import streamlit.components.v1 as components

# --- Local Imports ---
from orchestrator import run_agentic_workflow

# This loads the environment variables from your .env file
load_dotenv()

# --- NEW: Chatbot Integration ---
def inject_chatbot():
    """
    Injects the complete HTML, CSS, and JavaScript for the AI Assistant chatbot
    into the Streamlit application.
    """
    chatbot_html = """
    <!-- This script is crucial for styling the chatbot correctly -->
    <script src="https://cdn.tailwindcss.com"></script>

    <style>
        /* Base styles from the original HTML file */
        #chat-widget {
            transition: transform 0.3s ease-out, opacity 0.3s ease-out;
            max-height: 70vh;
        }
        .chat-hidden {
            transform: translateY(20px);
            opacity: 0;
            pointer-events: none;
        }
    </style>

    <!-- Chatbot Widget Container -->
    <div id="chat-container" class="fixed bottom-5 right-5 z-[1000]">
        <!-- Chat Bubble -->
        <button id="chat-bubble" class="bg-blue-600 text-white w-16 h-16 rounded-full flex items-center justify-center shadow-lg hover:bg-blue-700 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        </button>

        <!-- Chat Widget Window -->
        <div id="chat-widget" class="chat-hidden absolute bottom-20 right-0 w-80 sm:w-96 bg-white rounded-lg shadow-2xl border border-slate-200 flex flex-col">
            <!-- Header -->
            <div class="bg-blue-600 text-white p-4 rounded-t-lg flex justify-between items-center">
                <div>
                    <h3 class="font-bold text-lg">AI Assistant</h3>
                    <p class="text-xs opacity-80">Powered by AWS Bedrock</p>
                </div>
                <button id="close-chat" class="text-white hover:opacity-75">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                </button>
            </div>
            <!-- Messages Area -->
            <div id="chat-messages" class="flex-1 p-4 overflow-y-auto h-96 space-y-4 text-black">
                <!-- Initial Bot Message -->
                <div class="flex items-start gap-3">
                    <div class="bg-blue-600 text-white p-2 rounded-full h-8 w-8 flex-shrink-0 flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 8-4 4 4 4"/><path d="M8 12h13"/></svg>
                    </div>
                    <div class="bg-slate-100 p-3 rounded-lg max-w-xs">
                        <p class="text-sm text-slate-800">Hello! I am an AI assistant. How can I help?</p>
                    </div>
                </div>
            </div>
            <!-- Input Area -->
            <div class="p-4 border-t border-slate-200 bg-white rounded-b-lg">
                <div class="flex items-center gap-2">
                    <input type="text" id="chat-input" placeholder="Type your message..." class="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-black">
                    <button id="send-btn" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50">Send</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // --- SCRIPT FOR CHATBOT WIDGET (Connected to AWS Bedrock Backend) ---
        const chatBubble = document.getElementById('chat-bubble');
        const chatWidget = document.getElementById('chat-widget');
        const closeChatBtn = document.getElementById('close-chat');
        const chatMessages = document.getElementById('chat-messages');
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        let conversationHistory = [];

        chatBubble.addEventListener('click', () => {
            chatWidget.classList.toggle('chat-hidden');
            if (!chatWidget.classList.contains('chat-hidden')) chatInput.focus();
        });
        closeChatBtn.addEventListener('click', () => chatWidget.classList.add('chat-hidden'));
        sendBtn.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });

        async function sendMessage() {
            const messageText = chatInput.value.trim();
            if (messageText === '') return;
            addMessage(messageText, 'user');
            conversationHistory.push({ role: 'user', content: messageText });
            chatInput.value = '';
            chatInput.disabled = true;
            sendBtn.disabled = true;
            showTypingIndicator();
            try {
                const botResponse = await getBedrockResponse(conversationHistory);
                removeTypingIndicator();
                addMessage(botResponse, 'bot');
                conversationHistory.push({ role: 'assistant', content: botResponse });
            } catch (error) {
                removeTypingIndicator();
                addMessage("Sorry, an error occurred. Ensure the backend chat server is running.", 'bot');
                console.error("Error fetching Bedrock response:", error);
            } finally {
                chatInput.disabled = false;
                sendBtn.disabled = false;
                chatInput.focus();
            }
        }
        
        async function getBedrockResponse(history) {
            const backendUrl = 'http://localhost:3000/api/chat'; 
            const response = await fetch(backendUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ conversation: history }),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            return data.reply;
        }

        function addMessage(text, sender) {
            const messageElement = document.createElement('div');
            if (sender === 'user') {
                messageElement.className = 'flex justify-end';
                messageElement.innerHTML = `<div class="bg-blue-600 text-white p-3 rounded-lg max-w-xs"><p class="text-sm">${text}</p></div>`;
            } else {
                messageElement.className = 'flex items-start gap-3';
                messageElement.innerHTML = `<div class="bg-blue-600 text-white p-2 rounded-full h-8 w-8 flex-shrink-0 flex items-center justify-center"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 8-4 4 4 4"/><path d="M8 12h13"/></svg></div><div class="bg-slate-100 p-3 rounded-lg max-w-xs"><p class="text-sm text-slate-800">${text}</p></div>`;
            }
            chatMessages.appendChild(messageElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function showTypingIndicator() {
            const typingElement = document.createElement('div');
            typingElement.id = 'typing-indicator';
            typingElement.className = 'flex items-start gap-3';
            typingElement.innerHTML = `<div class="bg-blue-600 text-white p-2 rounded-full h-8 w-8 flex-shrink-0 flex items-center justify-center"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 8-4 4 4 4"/><path d="M8 12h13"/></svg></div><div class="bg-slate-100 p-3 rounded-lg"><div class="flex items-center gap-1"><span class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0s;"></span><span class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.1s;"></span><span class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.2s;"></span></div></div>`;
            chatMessages.appendChild(typingElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function removeTypingIndicator() {
            const typingIndicator = document.getElementById('typing-indicator');
            if (typingIndicator) typingIndicator.remove();
        }
    </script>
    """
    components.html(chatbot_html, height=0, scrolling=False)


# --- Visualization Class ---
class RiskVisualization:
    """Advanced visualization components for risk assessment"""
    
    def create_risk_dashboard(self, assessment):
        """Create comprehensive risk dashboard for single entity"""
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Credit Score', 'Financial Ratios', 'Compliance Score', 'Key Metrics'),
            specs=[[{"type": "indicator"}, {"type": "bar"}],
                   [{"type": "indicator"}, {"type": "table"}]]
        )
        
        # Credit Score Gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=assessment['credit_score'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Credit Score", 'font': {'size': 20}},
            gauge={
                'axis': {'range': [300, 850], 'tickwidth': 1, 'tickcolor': "lightgray"},
                'bar': {'color': assessment['risk_color']},
                'bgcolor': "#2c3e50",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [300, 550], 'color': '#5a2a27'},
                    {'range': [550, 650], 'color': '#625a33'},
                    {'range': [650, 850], 'color': '#335c42'}
                ],
            }
        ), row=1, col=1)
        
        # Financial Ratios Bar Chart
        ratios = assessment['financial_ratios']
        fig.add_trace(go.Bar(
            x=list(ratios.keys()),
            y=list(ratios.values()),
            name="Financial Ratios",
            marker_color=['#5DADE2', '#48C9B0', '#F4D03F', '#AF7AC5', '#EC7063', '#5D6D7E']
        ), row=1, col=2)
        
        # Compliance Score Gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=assessment['compliance_result']['compliance_score'],
            title={'text': "Compliance Score", 'font': {'size': 20}},
            gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#2E86C1"}, 'bgcolor': "#2c3e50"}
        ), row=2, col=1)

        # Key Metrics Table
        risk_data = {
            'Debt-to-Income': f"{assessment['financial_ratios'].get('debt_to_income', 0):.2%}",
            'Credit Utilization': f"{assessment['credit_data'].get('credit_utilization', 0):.2%}",
            'Current Ratio': f"{assessment['financial_ratios'].get('current_ratio', 0):.2f}"
        }
        fig.add_trace(go.Table(
            header=dict(values=['Metric', 'Value'],
                        fill_color='#1c2833',
                        align='left',
                        font=dict(color='white')),
            cells=dict(values=[list(risk_data.keys()), list(risk_data.values())],
                       fill_color='#2c3e50',
                       align='left',
                       font=dict(color='white'))
        ), row=2, col=2)
        
        fig.update_layout(
            height=700,
            showlegend=False,
            title_text=f"Risk Dashboard: {assessment['entity_name']}",
            title_font_size=24,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#f0f0f0'
        )
        
        return fig

# --- Streamlit App Main Function ---
def main():
    st.set_page_config(page_title="AI Risk Copilot", layout="wide")
    
    # --- Custom CSS for Styling ---
    st.markdown("""
        <style>
            .stApp {
                background: linear-gradient(to bottom right, #2c3e50, #1c2833);
                color: #f0f0f0;
            }
            [data-testid="stSidebar"] {
                background-color: #1c2833;
                border-right: 1px solid #4a4a4a;
            }
            .stButton>button {
                border-radius: 8px;
                border: none;
                padding: 10px 20px;
                background-color: #007bff;
                color: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: all 0.2s ease-in-out;
            }
            .stButton>button:hover {
                background-color: #0056b3;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }
            .card {
                background-color: #2c3e50;
                border-radius: 10px;
                padding: 25px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                margin-bottom: 20px;
                border: 1px solid #4a4a4a;
            }
            [data-testid="stMetric"] {
                background-color: #2c3e50;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                border: 1px solid #4a4a4a;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- App Header ---
    st.title("🏦 AI-Powered Risk & Compliance Copilot")
    st.markdown("An intelligent agentic system for comprehensive loan application analysis.")
    
    # --- Session State Initialization ---
    if 'risk_system_initialized' not in st.session_state:
        st.session_state.risk_system_initialized = True
        st.session_state.visualizer = RiskVisualization()
        st.session_state.assessments = []

    # --- Sidebar for User Input ---
    with st.sidebar:
        st.header("⚙️ Controls")
        uploaded_file = st.file_uploader("Upload JSON File", type="json")
        
        if st.button("🚀 Run Assessment"):
            if uploaded_file is not None:
                try:
                    entities_data = json.load(uploaded_file)
                    if not isinstance(entities_data, list):
                        entities_data = [entities_data]

                    progress_bar = st.progress(0)
                    st.session_state.assessments = [] 
                    
                    for i, entity in enumerate(entities_data):
                        with st.spinner(f"Processing {entity.get('entity_name', 'entity')}..."):
                            try:
                                assessment = run_agentic_workflow(entity)
                                st.session_state.assessments.append(assessment)
                            except Exception as e:
                                st.error(f"❌ Workflow failed for {entity.get('entity_name', 'unknown entity')}: {e}")
                        progress_bar.progress((i + 1) / len(entities_data))
                    
                    st.success("✅ Assessment complete!")

                except Exception as e:
                    st.error(f"❌ Failed to parse JSON: {e}")
            else:
                st.warning("Please upload a JSON file.")

        if st.button("🗑️ Clear History"):
            st.session_state.assessments = []
            st.success("History cleared!")
            st.rerun()

    # --- Main Dashboard Display ---
    if st.session_state.assessments:
        entity_names = [a['entity_name'] for a in st.session_state.assessments]
        selected_entity_name = st.selectbox("Select an entity to view its dashboard:", entity_names)
        
        selected_assessment = next((a for a in st.session_state.assessments if a['entity_name'] == selected_entity_name), None)

        if selected_assessment:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Credit Score", selected_assessment['credit_score'])
            col2.metric("Risk Level", selected_assessment['risk_level'])
            col3.metric("Compliance Score", f"{selected_assessment['compliance_result']['compliance_score']}%")
            col4.metric("AI Confidence", f"{selected_assessment['explanation'].get('confidence_score', 'N/A')}%")
            
            st.markdown('<hr style="margin-top: 2rem; margin-bottom: 2rem;">', unsafe_allow_html=True)
            st.plotly_chart(st.session_state.visualizer.create_risk_dashboard(selected_assessment), use_container_width=True)
            
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("🤖 AI Decision Analysis")
            decision = selected_assessment['explanation'].get('decision', 'N/A')
            st.markdown(f"#### Final Recommendation: **{decision}**")
            st.info(f"**Primary Explanation:** {selected_assessment['explanation'].get('primary_explanation', 'N/A')}")
            
            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                st.markdown("**Detailed Factors:**")
                for factor in selected_assessment['explanation'].get('detailed_factors', []):
                    st.markdown(f"- {factor}")
            with exp_col2:
                st.markdown("**Suggestions for Improvement:**")
                for suggestion in selected_assessment['explanation'].get('suggestions_for_improvement', []):
                    st.markdown(f"- {suggestion}")
            st.markdown('</div>', unsafe_allow_html=True)
            
    else:
        st.info("👆 Upload a file and click 'Run Assessment' in the sidebar to begin.")

    # --- Inject the chatbot at the end of the app ---
    inject_chatbot()

if __name__ == "__main__":
    main()