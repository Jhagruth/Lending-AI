# Lending AI

An advanced financial analysis tool that leverages **AI** to transform complex financial data into clear, actionable intelligence reports.  
This system provides **institutional-grade risk assessment, compliance checks, and an interactive AI assistant** to streamline decision-making.

---

## ✨ Core Features

- **AI-Powered Risk Assessment**  
  Utilizes **AWS Bedrock** to perform deep analysis of credit and financial data.

- **Interactive Dashboard**  
  A rich, user-friendly interface to visualize credit scores, risk levels, and compliance metrics using **Plotly.js**.

- **Automated Compliance Checks**  
  The AI agent automatically flags potential policy violations based on financial ratios.

- **Natural Language Explanations**  
  Generates clear, human-readable explanations for every assessment, detailing key factors and suggestions for improvement.

- **Integrated AI Assistant**  
  A real-time chatbot, powered by **AWS Bedrock**, to answer questions and provide assistance.

---

## 🏗️ System Architecture

The Compliance Copilot is built on a **microservice-based architecture**, ensuring separation of concerns and scalability.

- **Frontend (`index.html`)**  
  - Single-page app built with **HTML, Tailwind CSS, and vanilla JavaScript**  
  - Handles file uploads, data visualization, and AI assistant interaction  

- **Node.js Backend (`server.js`)**  
  - Built with **Express.js**  
  - Acts as a central gateway  
  - **Chatbot API (`/api/chat`)** → Communicates with **AWS Bedrock**  
  - **Proxy Server (`/api/assess`)** → Forwards assessment requests to Python backend  

- **Python Risk Agent (`risk_agent_api.py`, `orchestrator.py`)**  
  - **FastAPI microservice** forming the core analysis engine  
  - Workflow orchestrator runs:  
    - Validation  
    - Financial ratio calculations  
    - Compliance checks  
    - Explanation generation (via AWS Bedrock)  
  - Returns a **comprehensive JSON object** with the full assessment  

---

## 🛠️ Tech Stack

| Category    | Technology / Library |
|-------------|----------------------|
| **Frontend** | HTML, Tailwind CSS, JavaScript, Plotly.js |
| **Backend**  | Node.js, Express.js, Axios, AWS SDK (Bedrock) |
| **AI Agent** | Python, FastAPI, Boto3, Pandas, Scikit-learn |
| **AI Service** | AWS Bedrock (Amazon Titan) |
| **Database** | SQLite |
| **Tooling**  | concurrently |

---

## 🚀 Getting Started

Follow these instructions to set up and run the project locally.

### ✅ Prerequisites

- **Node.js & npm** → [Download Node.js](https://nodejs.org/)  
- **Python 3.8+** → [Download Python](https://www.python.org/downloads/)  
- **AWS Account & CLI**  
  - Active AWS account with access to **Amazon Bedrock**  
  - AWS CLI installed & configured (`aws configure`)  

---

### ⚙️ Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/compliance-copilot.git
   cd compliance-copilot
