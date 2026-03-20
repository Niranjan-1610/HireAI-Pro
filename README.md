# 🎯 HireAI Pro - Smart Recruitment Management System

HireAI Pro is an intelligent, multimodal recruitment platform designed to streamline the hiring process using advanced AI evaluation. It leverages Google Gemini 1.5 Flash to analyze resumes, evaluate video introductions, and provide deep cross-referenced insights for HR professionals.

## 🚀 Features

- **📄 Smart Resume Parsing**: Automatic text extraction from PDFs and structured evaluation of skills, experience, and leadership.
- **🎥 Multimodal Video Analysis**: Evaluates candidate confidence, clarity, and sentiment from video introductions.
- **🧠 Cross-Verification Logic**: Aligning resume data with video persona to generate consistency scores and hiring recommendations.
- **📊 HR Dashboard**: Real-time statistics, candidate rankings based on weighted scores, and status management.
- **📋 Professional PDF Reports**: Automatically generate and download detailed candidate evaluation reports.
- **🔐 Secure HR Portal**: Role-based access control (Screener vs. Technical Lead) with bcrypt password hashing and environment-based credentials.
- **🧠 Cross-Verification Logic**: Aligning resume data with video persona to generate consistency scores.
- **💼 Role Inference**: Keyword-based logic to suggest the best fit (e.g., DevOps, Backend, Lead).

## 🛠️ Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **AI Engine**: [Google Gemini 1.5 Flash](https://ai.google.dev/)
- **Database**: [MongoDB](https://www.mongodb.com/)
- **Parsing**: [PyMuPDF](https://pymupdf.readthedocs.io/) / [PyPDF2](https://pypdf2.readthedocs.io/)
- **Reporting**: [ReportLab](https://www.reportlab.com/)
- **Visuals**: [Plotly](https://plotly.com/) / [Pandas](https://pandas.pydata.org/)

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-repo/HireAI-Pro.git
   cd HireAI-Pro
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   MONGO_URI=mongodb://localhost:27017/
   ORG_KEY=your_organization_secret_key
   ADMIN_PASSWORD=your_initial_admin_password
   ```

4. **Run the Application**:
   ```bash
   streamlit run main.py
   ```

## 🏗️ Project Structure

```text
HireAI-Pro/
├── main.py                # Main Streamlit Application
├── modules/               # Core Logic Modules
│   ├── ai_engine.py       # AI Evaluation & Multimodal Logic
│   ├── database_manager.py# MongoDB Interactions
│   └── ui_components.py   # Reusable UI Elements
├── tests/                 # System Verification Tests
│   └── system_test_flow.py# Integration Test Script
├── requirements.txt       # Project Dependencies
└── .env                   # Configuration
```

## 🧪 Verification

To verify the core system logic, run the included test suite:
```bash
python tests/system_test_flow.py
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---
*Built with ❤️ for Modern Recruitment Teams.*
