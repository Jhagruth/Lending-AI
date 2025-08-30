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
    ```
2. **Set Up Environment Variables**
   
   Create a ```.env``` file in the project root:
    ```bash
    AWS_REGION=us-east-1
    ```
3. **Install Node.js Dependencies**
     ```bash
    npm install
     ```
4. **Install Python Dependencies**
     ```bash
    pip install -r requirements.txt
      ```
---
     
**▶️ Running the Application**

This project uses concurrently to run both the Node.js and Python servers with a single command:
```bash
npm run dev
```

This will start:
- Node.js server → http://localhost:3000
- Python FastAPI server → http://localhost:8000

Logs from both services will appear in your terminal.

![WhatsApp Image 2025-08-30 at 12 06 56](https://github.com/user-attachments/assets/64841348-cc64-47e8-9734-36a131d9d30d)

![WhatsApp Image 2025-08-30 at 11 22 59](https://github.com/user-attachments/assets/074cf143-1f6d-44dc-93d9-e474eda175ea)

![WhatsApp Image 2025-08-30 at 11 25 34](https://github.com/user-attachments/assets/f573eb4c-9e8a-45d9-bfd9-83c0ac1966c0)

![WhatsApp Image 2025-08-30 at 11 25 21](https://github.com/user-attachments/assets/e2113384-5760-41fd-8ce4-c67c1d4edd9b)

---

📌 Usage
1. Open the Frontend → Open index.html in your browser
2. Upload Data → Click Choose File and select entities.json (or similar JSON file)
3. Generate Report → Click Generate Report to start the assessment
4. View Dashboard → See interactive visualizations of risk and compliance metrics
5. Switch Entities → Use the dropdown to analyze different entities
6. Chat with AI → Click the chat bubble (bottom-right) to interact with the AI Assistant

---

📂 Project Structure
```bash
compliance-copilot/
│── index.html               # Frontend UI
│── server.js                # Node.js backend gateway
│── risk_agent_api.py        # FastAPI microservice
│── orchestrator.py          # Workflow manager for risk checks
│── requirements.txt         # Python dependencies
│── package.json             # Node.js dependencies
│── .env                     # AWS region config
│── /static                  # JS, CSS, assets
│── /data                    # Sample input JSON
```

---

**🤝 Contributing**

Contributions are welcome! Please fork the repo and submit a PR with improvements.
