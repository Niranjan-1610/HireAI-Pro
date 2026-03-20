"""
HireAI Pro - Smart Recruitment Management System
Enterprise Edition v2.0
Author: Professional Development Team
Date: 2026-03-17
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import base64
from datetime import datetime
from io import BytesIO
import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Clear any cached modules
modules_to_clear = ['modules.ai_engine', 'modules.database_manager']
for module in modules_to_clear:
    if module in sys.modules:
        del sys.modules[module]

# Import modules with comprehensive error handling
IMPORT_STATUS = {"ai_engine": False, "database_manager": False, "reportlab": False}
IMPORT_ERRORS = []

try:
    from modules.ai_engine import (
        extract_text_from_pdf, get_ai_evaluation, calculate_weighted_score,
        get_video_evaluation, cross_reference_analysis
    )
    IMPORT_STATUS["ai_engine"] = True
except ImportError as e:
    IMPORT_ERRORS.append(f"AI Engine: {str(e)}")

try:
    from modules.database_manager import (
        init_database, save_candidate_to_mongo, fetch_all_candidates,
        update_candidate_status, get_statistics, authenticate_hr, update_hr_profile,
        register_hr, log_unauthorized_access, get_org_key, update_org_key,
        create_session, get_session, delete_session, log_candidate_email,
        log_disqualified_candidate, fetch_disqualified_candidates
    )
    IMPORT_STATUS["database_manager"] = True
except ImportError as e:
    IMPORT_ERRORS.append(f"Database Manager/Email Service: {str(e)}")

# Check reportlab availability
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    IMPORT_STATUS["reportlab"] = True
except ImportError as e:
    IMPORT_ERRORS.append(f"ReportLab: {str(e)}")

# Safe logging function that handles encoding issues
def safe_log(message, level="INFO"):
    """Safely log messages without causing encoding errors."""
    try:
        # Avoid print() as it can cause I/O Operation on closed file errors in Streamlit/Windows
        if level == "ERROR":
            st.error(message)
        elif level == "WARNING":
            st.warning(message)
        elif level == "SUCCESS":
            st.success(message)
        elif level == "INFO":
            st.info(message)
    except Exception:
        pass  # Silently fail if even streamlit fails

# Log import status silently
if not all(IMPORT_STATUS.values()):
    for error in IMPORT_ERRORS:
        safe_log(f"Module Error: {error}", "ERROR")

# State Persistence logic (Refresh proofing)
if not st.session_state.get("logged_in", False):
    sid = st.query_params.get("sid")
    if sid and IMPORT_STATUS["database_manager"]:
        session = get_session(sid)
        if session:
            st.session_state.logged_in = True
            st.session_state.role = session["role"]
            st.session_state.hr_user = session["user"]
            st.session_state.candidate_session = session.get("candidate_data")
            # Clear target report if it was set
            if "target_report" in st.session_state: del st.session_state["target_report"]

# Page configuration
st.set_page_config(
    page_title="HireAI Pro - Multimodal Recruitment",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://hireai.pro/support',
        'Report a bug': 'https://hireai.pro/bugs',
        'About': 'HireAI Pro v2.0 - Intelligent Recruitment Platform'
    }
)

# Professional CSS styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * { 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; 
        font-size: 0.95rem;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.2);
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 4px solid #667eea;
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    }
    
    .status-badge {
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-shortlisted { 
        background: #d4edda; 
        color: #155724; 
        border: 2px solid #28a745; 
    }
    
    .status-evaluated { 
        background: #fff3cd; 
        color: #856404; 
        border: 2px solid #ffc107; 
    }
    
    .status-disqualified { 
        background: #f8d7da; 
        color: #721c24; 
        border: 2px solid #dc3545; 
    }
    
    .status-new { 
        background: #d1ecf1; 
        color: #0c5460; 
        border: 2px solid #17a2b8; 
    }
    
    .status-screened {
        background: #e0e7ff;
        color: #4338ca;
        border: 2px solid #6366f1;
    }
    
    .candidate-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        margin-bottom: 0.8rem;
        border: 1px solid #e9ecef;
        transition: all 0.2s ease;
    }
    
    .candidate-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-color: #667eea;
    }
    
    .section-header {
        background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 0.6rem 1.2rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 1.2rem 0 0.8rem 0;
    }
    
    .skill-bar-container {
        background: #e9ecef;
        border-radius: 8px;
        height: 10px;
        overflow: hidden;
        margin: 8px 0;
    }
    
    .skill-bar-fill {
        height: 100%;
        border-radius: 8px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        transition: width 0.6s ease;
    }
    
    .podium-card {
        text-align: center;
        padding: 2rem;
        border-radius: 16px;
        margin: 0 0.5rem;
    }
    
    .podium-1 { 
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); 
        border: 3px solid #FFD700; 
    }
    
    .podium-2 { 
        background: linear-gradient(135deg, #C0C0C0 0%, #A0A0A0 100%); 
        border: 3px solid #C0C0C0; 
    }
    
    .podium-3 { 
        background: linear-gradient(135deg, #CD7F32 0%, #B87333 100%); 
        border: 3px solid #CD7F32; 
    }
    
    .timeline-item {
        border-left: 3px solid #667eea;
        padding-left: 1.5rem;
        margin: 1rem 0;
        position: relative;
    }
    
    .timeline-item::before {
        content: '';
        position: absolute;
        left: -8px;
        top: 0;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background: #667eea;
    }
    
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    div[data-testid="stForm"] {
        background: #f8f9fa;
        padding: 1.2rem;
        border-radius: 10px;
        border: 1px solid #e9ecef;
    }
    
    .error-banner {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin-bottom: 1rem;
    }
    
    .success-banner {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state with defaults
DEFAULT_SESSION_STATE = {
    'logged_in': False,
    'role': None,
    'hr_user': None,
    'target_report': None,
    'weights': {"Technical": 50, "Experience": 30, "Soft_Skills": 20},
    'filter_status': "All",
    'db_initialized': False,
    'user_preferences': {}
}

for key, value in DEFAULT_SESSION_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Initialize database connection
if not st.session_state.db_initialized and IMPORT_STATUS["database_manager"]:
    try:
        st.session_state.db_initialized = init_database()
    except Exception as e:
        safe_log(f"Database initialization failed: {e}", "ERROR")
        st.session_state.db_initialized = False

# PDF Generation Function
def generate_pdf_report(candidate):
    """
    Generate professional PDF report for a candidate.
    Returns PDF bytes or None if generation fails.
    """
    if not IMPORT_STATUS["reportlab"]:
        st.error("PDF generation unavailable. Please install reportlab: pip install reportlab")
        return None
    
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=1,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#764ba2'),
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        
        # Title
        story.append(Paragraph(f"Candidate Evaluation Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Candidate Info
        story.append(Paragraph(f"<b>Candidate:</b> {candidate.get('full_name', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"<b>Role:</b> {candidate.get('ai_analysis', {}).get('best_role', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"<b>Email:</b> {candidate.get('email', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"<b>Status:</b> {candidate.get('status', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Scores Table
        story.append(Paragraph("Evaluation Scores", heading_style))
        
        metrics = candidate.get('metrics', {})
        ai_analysis = candidate.get('ai_analysis', {})
        efficiency = ai_analysis.get('efficiency', {})
        
        data = [
            ['Metric', 'Score (out of 10)'],
            ['Final Score', f"{metrics.get('final_score', 0):.2f}"],
            ['Technical Skills', f"{efficiency.get('Technical', 0):.1f}"],
            ['Experience', f"{efficiency.get('Experience', 0):.1f}"],
            ['Communication', f"{efficiency.get('Communication', 0):.1f}"],
            ['Logic', f"{efficiency.get('Logic', 0):.1f}"],
            ['Leadership', f"{efficiency.get('Leadership', 0):.1f}"]
        ]
        
        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        # Summary
        story.append(Paragraph("Executive Summary", heading_style))
        summary = ai_analysis.get('summary', 'No summary available.')
        story.append(Paragraph(summary, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Strengths and Areas for Improvement
        story.append(Paragraph("Key Strengths", heading_style))
        pros = ai_analysis.get('pros', [])
        if pros:
            for pro in pros[:3]:
                story.append(Paragraph(f"• {pro}", styles['Normal']))
        else:
            story.append(Paragraph("No specific strengths noted.", styles['Normal']))
        
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("Areas for Development", heading_style))
        cons = ai_analysis.get('cons', [])
        if cons:
            for con in cons[:3]:
                story.append(Paragraph(f"• {con}", styles['Normal']))
        else:
            story.append(Paragraph("No specific areas noted.", styles['Normal']))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            f"<i>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}</i>",
            styles['Normal']
        ))
        
        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
        
    except Exception as e:
        safe_log(f"PDF generation failed: {e}", "ERROR")
        return None

# Helper Functions
def get_status_badge(status):
    """Generate HTML status badge."""
    status_class = f"status-{status.lower()}"
    return f'<span class="status-badge {status_class}">{status}</span>'

def validate_email(email):
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Basic phone validation."""
    digits = ''.join(filter(str.isdigit, phone))
    return len(digits) >= 10

# Authentication Section
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style="text-align: center; padding: 1.5rem 0;">
                <h1 style="font-size: 2.2rem; background: linear-gradient(135deg, #667eea, #764ba2); 
                          -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.2rem;">
                    HireAI Pro
                </h1>
                <p style="font-size: 1rem; color: #666; margin-bottom: 1.5rem;">
                    Intelligent Recruitment Management System
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Show import errors if any
        if IMPORT_ERRORS:
            with st.expander("System Status", expanded=True):
                for error in IMPORT_ERRORS:
                    st.error(f"Module Error: {error}")
                st.info("Some features may be limited. Please check your installation.")
        
        tab1, tab2 = st.tabs(["Candidate Portal", "HR Administration"])
        
        with tab1:
            st.subheader("Submit Your Application")
            st.write("Upload your resume for AI-powered evaluation and career matching.")
            
            if st.button("Enter Candidate Portal", use_container_width=True, type="primary"):
                st.session_state.logged_in = True
                st.session_state.role = "Student"
                st.rerun()
        
        with tab2:
            st.subheader("HR Management")
            
            auth_mode = st.radio("Access Mode", ["Login", "Register"], horizontal=True, label_visibility="collapsed")
            
            if auth_mode == "Login":
                with st.form("hr_login"):
                    username = st.text_input("Username", placeholder="admin")
                    password = st.text_input("Password", type="password", placeholder="Enter password")
                    submit_login = st.form_submit_button("Login as HR", use_container_width=True, type="primary")
                    
                    if submit_login:
                        if IMPORT_STATUS["database_manager"]:
                            user = authenticate_hr(username, password)
                            if user:
                                st.session_state.logged_in = True
                                st.session_state.role = "HR"
                                st.session_state.hr_user = user
                                
                                # Create persistent session
                                sid = create_session(user, "HR")
                                if sid: st.query_params["sid"] = sid
                                
                                st.success(f"Welcome back, {user.get('full_name')}!")
                                st.rerun()
                            else:
                                log_unauthorized_access(username, "Failed Login", {"reason": "Invalid credentials"})
                                st.error("Invalid credentials. Please try again.")
                        else:
                            # Fallback for troubleshooting if DB is down
                            if username == "admin" and password == "mumbai2026":
                                st.session_state.logged_in = True
                                st.session_state.role = "HR"
                                st.session_state.hr_user = {"full_name": "Admin Fallback", "username": "admin"}
                                st.success("Login successful (Mock Mode)!")
                                st.rerun()
                            else:
                                st.error("Database connection unavailable and invalid fallback credentials.")
            
            else: # Register Mode
                with st.form("hr_register"):
                    st.info("Authorized Personnel Only: Registration requires Organization Secret Key.")
                    reg_name = st.text_input("Full Name", placeholder="Enter your full name")
                    reg_email = st.text_input("Work Email", placeholder="email@company.com")
                    reg_mobile = st.text_input("Mobile Number", placeholder="+91 99999 99999")
                    reg_username = st.text_input("Choose Username", placeholder="e.g., johndoe")
                    reg_password = st.text_input("Choose Password", type="password")
                    reg_role = st.selectbox("Assign Role", ["Screener", "Technical Lead"], help="Screeners filter candidates; Technical Leads handle final rankings.")
                    reg_secret = st.text_input("Organization Secret Key", type="password", help="Contact administrator for this key")
                    
                    submit_reg = st.form_submit_button("Create HR Account", use_container_width=True, type="primary")
                    
                    if submit_reg:
                        if not all([reg_name, reg_email, reg_username, reg_password, reg_secret]):
                            st.error("All fields are required for registration.")
                        else:
                            hr_data = {
                                "full_name": reg_name,
                                "email": reg_email,
                                "mobile": reg_mobile,
                                "username": reg_username,
                                "password": reg_password,
                                "role": reg_role
                            }
                            success, msg = register_hr(hr_data, reg_secret)
                            if success:
                                st.success(msg)
                                st.info("You can now switch to 'Login' mode to access the dashboard.")
                            else:
                                st.error(msg)

# Main Application Logic
else:
    # Sidebar Navigation
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 1rem 0; border-bottom: 2px solid #e0e0e0; margin-bottom: 1rem;">
                <h2 style="margin: 0; color: #667eea; font-size: 1.4rem;">HireAI Pro</h2>
                <small style="color: #888;">Enterprise v2.0</small>
            </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.role == "HR":
            hr_role = st.session_state.hr_user.get('role', 'Screener')
            
            # Specialized menu based on role
            if hr_role == "Technical Lead":
                nav_options = ["Dashboard", "Rankings", "Compare", "Analytics", "Reports", "Disqualified", "Profile", "Settings"]
                default_status = "Screened"
            else: # Screener
                nav_options = ["Dashboard", "Candidates", "Reports", "Disqualified", "Profile", "Settings"]
                default_status = "New"
                
            menu = st.radio(
                "Navigation",
                nav_options,
                label_visibility="collapsed"
            )
            
            st.divider()
            st.session_state.filter_status = st.selectbox(
                "Filter by Status",
                ["All", "New", "Screened", "Evaluated", "Shortlisted", "Disqualified"],
                index=["All", "New", "Screened", "Evaluated", "Shortlisted", "Disqualified"].index(default_status) if 'filter_status' not in st.session_state else None
            )
            
            st.info(f"Role: **{hr_role}**")
        else:
            menu = "Candidate Portal"
        
        st.divider()
        
        # User info
        st.caption(f"Logged in as: {st.session_state.role}")
        st.caption(f"Session: {datetime.now().strftime('%H:%M')}")
        
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            # Clean up database session
            sid = st.query_params.get("sid")
            if sid and IMPORT_STATUS["database_manager"]:
                delete_session(sid)
            
            st.session_state.logged_in = False
            st.session_state.role = None
            st.session_state.hr_user = None
            st.query_params.clear()
            st.rerun()

    # =====================
    # CANDIDATE PORTAL
    # =====================
    if st.session_state.role == "Student":
        st.markdown("""
            <div class="main-header">
                <h1 style="margin: 0; font-size: 2.5rem;">Candidate Application Portal</h1>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                    Submit your resume for comprehensive AI evaluation and career matching
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        if not IMPORT_STATUS["ai_engine"]:
            st.error("AI Engine not available. Please contact support.")
        else:
            col_form, col_info = st.columns([2, 1])
            
            with col_form:
                with st.form("application_form", clear_on_submit=True):
                    st.subheader("Application Details")
                    
                    full_name = st.text_input(
                        "Full Name *", 
                        placeholder="Enter your full name",
                        help="As it appears on your official documents"
                    )
                    
                    email = st.text_input(
                        "Email Address *", 
                        placeholder="your.email@example.com",
                        help="We'll use this to contact you about your application"
                    )
                    
                    phone = st.text_input(
                        "Mobile Number", 
                        placeholder="+91 98765 43210",
                        help="Include country code for international numbers"
                    )
                    
                    applied_role = st.selectbox(
                        "Applying For *",
                        ["Software Engineer", "Frontend Developer", "Backend Developer", "Data Scientist", "DevOps Engineer", "Project Manager", "UI/UX Designer"],
                        index=0,
                        help="Select the role you are applying for"
                    )
                    
                    st.divider()
                    
                    uploaded_file = st.file_uploader(
                        "Upload Resume (PDF) *", 
                        type="pdf",
                        help="Maximum file size: 10MB. Text-searchable PDFs work best."
                    )
                    
                    uploaded_video = st.file_uploader(
                        "Video Introduction (Optional)", 
                        type=["mp4", "mov", "avi"],
                        help="Brief 30-60 second intro. Shows your communication and persona."
                    )
                    
                    # Privacy notice
                    st.caption("""
                        By submitting, you agree to our privacy policy. 
                        Your data will be processed by our AI system for evaluation purposes.
                    """)
                    
                    submitted = st.form_submit_button(
                        "Submit Application", 
                        use_container_width=True, 
                        type="primary"
                    )
                    
                    if submitted:
                        errors = []
                        
                        if not full_name or len(full_name.strip()) < 2:
                            errors.append("Please enter a valid full name")
                        
                        if not email or not validate_email(email):
                            errors.append("Please enter a valid email address")
                        
                        if phone and not validate_phone(phone):
                            errors.append("Please enter a valid phone number")
                        
                        if not uploaded_file:
                            errors.append("Please upload your resume (PDF format)")
                        
                        if errors:
                            for error in errors:
                                st.error(error)
                        else:
                            with st.spinner("AI is analyzing your resume... This may take a moment."):
                                try:
                                    # Extract text from PDF
                                    text = extract_text_from_pdf(uploaded_file)
                                    
                                    if not text or len(text.strip()) < 50:
                                        st.error("Could not extract sufficient text from PDF. Please ensure it's text-searchable.")
                                    else:
                                        # Get AI evaluation (Resume)
                                        ai_result = get_ai_evaluation(text)
                                        
                                        video_result = None
                                        cross_ref_result = None
                                        
                                        # Process Video if uploaded
                                        if uploaded_video:
                                            with st.status("Analyzing video persona...", expanded=True) as status:
                                                st.write("Uploading video to AI Engine...")
                                                # Save temp video file for processing
                                                import tempfile
                                                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_video.name.split('.')[-1]}") as tmp:
                                                    tmp.write(uploaded_video.read())
                                                    tmp_path = tmp.name
                                                
                                                st.write("Processing Multimodal Insights...")
                                                video_result = get_video_evaluation(tmp_path)
                                                
                                                st.write("Cross-referencing Resume & Persona...")
                                                cross_ref_result = cross_reference_analysis(ai_result, video_result)
                                                
                                                # Clean up temp file
                                                os.unlink(tmp_path)
                                                status.update(label="Multimodal Analysis Complete!", state="complete", expanded=False)
                                        
                                        # Save to database
                                        if IMPORT_STATUS["database_manager"]:
                                            success, message, candidate_id = save_candidate_to_mongo(
                                                full_name.strip(),
                                                email.strip().lower(),
                                                phone.strip() if phone else "",
                                                ai_result,
                                                st.session_state.weights,
                                                applied_role,
                                                video_result,
                                                cross_ref_result
                                            )
                                            
                                            if success:
                                                st.success(f"Application submitted successfully! Candidate ID: {candidate_id}")
                                                st.info(f"Your AI Score: {ai_result.get('score', 0)}/10")
                                                if cross_ref_result:
                                                    st.success(f"Persona Alignment: {cross_ref_result.get('consistency_score', 0)}/10")
                                                
                                                st.balloons()
                                                
                                                # Show next steps
                                                st.subheader("What happens next?")
                                                st.write(f"""
                                                    1. **Multimodal Analysis** (Complete) - Your {'resume and video have' if uploaded_video else 'resume has'} been evaluated
                                                    2. **HR Review** (24-48 hours) - Our team will review your profile
                                                    3. **Interview** - Shortlisted candidates will be contacted via email
                                                """)
                                            else:
                                                st.error(f"Database error: {message}")
                                        else:
                                            st.warning("Database not available. Showing preview only.")
                                            st.json(ai_result)
                                            
                                except Exception as e:
                                    st.error(f"Processing error: {str(e)}")
                                    safe_log(f"Application processing failed: {e}", "ERROR")
            
            with col_info:
                st.info("""
                    **Application Process**
                    
                    1. **Submit Resume** (Instant)
                       - PDF format required
                       - AI extracts skills and experience
                    
                    2. **AI Evaluation** (2-3 minutes)
                       - Technical skills assessment
                       - Experience analysis
                       - Soft skills evaluation
                    
                    3. **HR Review** (24-48 hours)
                       - Profile verification
                       - Interview shortlisting
                       - Direct email contact
                    
                    **Tips for Best Results:**
                    - Use standard PDF format (not scanned images)
                    - Include clear section headers
                    - List specific technologies and tools
                    - Quantify achievements where possible
                """)
                
                st.divider()
                
                st.caption("Supported File Types: PDF (Max 10MB)")
                st.caption("Questions? Contact: support@hireai.pro")

    # =====================
    # HR DASHBOARD
    # =====================
    elif st.session_state.role == "HR":
        # Fetch data from database
        data = []
        stats = {}
        
        if IMPORT_STATUS["database_manager"] and st.session_state.db_initialized:
            try:
                data = fetch_all_candidates(st.session_state.filter_status)
                stats = get_statistics()
            except Exception as e:
                st.error(f"Database connection error: {e}")
                safe_log(f"Data fetch failed: {e}", "ERROR")
        else:
            st.warning("Database not connected. Showing demo data.")
            # Demo data for testing UI
            data = []
            stats = {"total": 0, "shortlisted": 0, "evaluated": 0, "disqualified": 0, "new": 0, "average_score": 0}
        
        # Show database status
        if not st.session_state.db_initialized:
            st.warning("Database connection failed. Some features are unavailable.")
        
        # ------------------
        # DASHBOARD
        # ------------------
        if menu == "Dashboard":
            st.markdown("""
                <div class="main-header">
                    <h1 style="margin: 0; font-size: 2.5rem;">Recruitment Dashboard</h1>
                    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                        Real-time pipeline overview and key performance metrics
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            # Key Metrics
            total = stats.get('total', 0)
            shortlisted = stats.get('shortlisted', 0)
            evaluated = stats.get('evaluated', 0)
            disqualified = stats.get('disqualified', 0)
            new_apps = stats.get('new', 0)
            avg_score = stats.get('average_score', 0)
            
            m1, m2, m3, m4, m5 = st.columns(5)
            metrics_data = [
                ("Total Applications", total, "#667eea"),
                ("Shortlisted", shortlisted, "#28a745"),
                ("Evaluated", evaluated, "#ffc107"),
                ("Disqualified", disqualified, "#dc3545"),
                ("New", new_apps, "#17a2b8")
            ]
            
            for col, (label, value, color) in zip([m1, m2, m3, m4, m5], metrics_data):
                with col:
                    st.markdown(f"""
                        <div class="metric-card" style="border-left-color: {color};">
                            <h2 style="margin: 0; color: {color}; font-size: 2.2rem;">{value}</h2>
                            <p style="margin: 0; color: #666; font-size: 0.9rem;">{label}</p>
                        </div>
                    """, unsafe_allow_html=True)
            
            st.divider()
            
            # Charts Section
            col_left, col_right = st.columns([2, 1])
            
            with col_left:
                st.subheader("Recruitment Funnel")
                
                funnel_values = [
                    total,
                    evaluated + shortlisted + disqualified,
                    evaluated + shortlisted,
                    shortlisted
                ]
                
                fig_funnel = go.Figure(go.Funnel(
                    y=['Applications', 'AI Evaluated', 'HR Reviewed', 'Shortlisted'],
                    x=funnel_values,
                    textposition="inside",
                    textinfo="value+percent initial",
                    marker=dict(color=["#667eea", "#764ba2", "#f093fb", "#4facfe"]),
                    connector=dict(line=dict(color="white", width=2))
                ))
                
                fig_funnel.update_layout(
                    height=400,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Inter, sans-serif")
                )
                
                st.plotly_chart(fig_funnel, use_container_width=True)
            
            with col_right:
                st.subheader("Status Distribution")
                
                if total > 0:
                    status_df = pd.DataFrame([
                        {'Status': 'Shortlisted', 'Count': shortlisted},
                        {'Status': 'Evaluated', 'Count': evaluated},
                        {'Status': 'Disqualified', 'Count': disqualified},
                        {'Status': 'New', 'Count': new_apps}
                    ])
                    
                    fig_pie = px.pie(
                        status_df,
                        values='Count',
                        names='Status',
                        hole=0.4,
                        color='Status',
                        color_discrete_map={
                            'Shortlisted': '#28a745',
                            'Evaluated': '#ffc107',
                            'Disqualified': '#dc3545',
                            'New': '#17a2b8'
                        }
                    )
                    
                    fig_pie.update_layout(
                        height=350,
                        paper_bgcolor='rgba(0,0,0,0)',
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=-0.1)
                    )
                    
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("No data available")
                
                st.metric("Average Score", f"{avg_score:.1f}/10")
            
            # Recent Activity
            st.divider()
            st.subheader("Recent Applications")
            
            if data:
                recent = sorted(data, key=lambda x: x.get('submitted_at', ''), reverse=True)[:5]
                cols = st.columns(min(5, len(recent)))
                
                for col, candidate in zip(cols, recent):
                    score = candidate.get('metrics', {}).get('final_score', 0)
                    score_color = "#28a745" if score >= 8 else "#ffc107" if score >= 6 else "#dc3545"
                    
                    with col:
                        st.markdown(f"""
                            <div style="background: white; padding: 1rem; border-radius: 12px; 
                                        box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center;">
                                <h4 style="margin: 0; font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                    {candidate.get('full_name', 'Unknown')[:15]}...
                                </h4>
                                <p style="margin: 8px 0; font-size: 1.8rem; color: {score_color}; font-weight: bold;">
                                    {score:.1f}
                                </p>
                                <span class="status-badge status-{candidate.get('status', 'new').lower()}">
                                    {candidate.get('status', 'New')}
                                </span>
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No applications yet. Waiting for candidate submissions.")

        # ------------------
        # CANDIDATE MANAGEMENT
        # ------------------
        elif menu == "Candidates":
            st.markdown("""
                <div class="main-header">
                    <h1 style="margin: 0; font-size: 2.5rem;">Candidate Management</h1>
                    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                        Review, evaluate, and manage candidate applications
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if not data:
                st.info("No candidates found. Candidates will appear here once they submit applications.")
            else:
                # Search and filter
                search = st.text_input("Search by name, email, or role...", placeholder="Type to search...")
                
                if search:
                    search_lower = search.lower()
                    data = [
                        x for x in data 
                        if search_lower in x.get('full_name', '').lower() 
                        or search_lower in x.get('email', '').lower()
                        or search_lower in x.get('ai_analysis', {}).get('best_role', '').lower()
                    ]
                
                st.caption(f"Showing {len(data)} candidate(s)")
                
                # Table Header
                header_cols = st.columns([2, 1.2, 1.2, 0.8, 0.8, 1, 1.2, 1.8])
                headers = ["Candidate", "Applied For", "AI Role", "Tech", "Overall", "Status", "Score", "Actions"]
                
                for col, header in zip(header_cols, headers):
                    col.markdown(f"**{header}**")
                
                st.divider()
                
                # Candidate Rows
                for candidate in data:
                    ai = candidate.get('ai_analysis', {})
                    metrics = candidate.get('metrics', {})
                    candidate_id = candidate.get('_id', 'unknown')
                    
                    with st.container():
                        cols = st.columns([2, 1.2, 1.2, 0.8, 0.8, 1, 1.2, 1.8])
                        
                        with cols[0]:
                            st.markdown(f"**{candidate.get('full_name', 'Unknown')}**")
                            st.caption(f"{candidate.get('email', 'No email')}")
                        
                        with cols[1]:
                            st.markdown(f"`{candidate.get('applied_role', 'Not Spec.')}`")
                            
                        with cols[2]:
                            role = ai.get('best_role', 'Analyzing...')
                            st.code(role, language="text")
                        
                        with cols[3]:
                            tech_score = ai.get('efficiency', {}).get('Technical', 0)
                            st.markdown(f"**{tech_score:.1f}**")
                        
                        with cols[4]:
                            final_score = metrics.get('final_score', 0)
                            st.markdown(f"**{final_score:.1f}**")
                        
                        with cols[5]:
                            status = candidate.get('status', 'New')
                            st.markdown(get_status_badge(status), unsafe_allow_html=True)
                        
                        with cols[6]:
                            resume_score = metrics.get('resume_score', 0)
                            st.metric("Resume", f"{resume_score:.1f}", label_visibility="collapsed")
                        
                        with cols[7]:
                            action_cols = st.columns(3)
                            
                            with action_cols[0]:
                                if st.button("View", key=f"view_{candidate_id}", help="View full report"):
                                    st.session_state.target_report = candidate.get('full_name')
                                    st.rerun()
                            
                            with action_cols[1]:
                                current_status = candidate.get('status', 'New')
                                options = ["New", "Evaluated", "Shortlisted", "Disqualified"]
                                
                                try:
                                    current_index = options.index(current_status)
                                except ValueError:
                                    current_index = 0
                                
                                new_status = st.selectbox(
                                    "Update Status",
                                    options,
                                    index=current_index,
                                    key=f"status_{candidate_id}",
                                    label_visibility="collapsed"
                                )
                                
                                if new_status != current_status and IMPORT_STATUS["database_manager"]:
                                    try:
                                        success, msg = update_candidate_status(candidate_id, new_status)
                                        if success:
                                            st.success(f"Updated to {new_status}")
                                            st.rerun()
                                        else:
                                            st.error(msg)
                                    except Exception as e:
                                        st.error(f"Update failed: {e}")
                            
                            with action_cols[2]:
                                if st.button("PDF", key=f"pdf_{candidate_id}", help="Download report"):
                                    pdf_bytes = generate_pdf_report(candidate)
                                    if pdf_bytes:
                                        b64 = base64.b64encode(pdf_bytes).decode()
                                        filename = f"{candidate.get('full_name', 'Candidate').replace(' ', '_')}_Report.pdf"
                                        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="text-decoration: none;">📥</a>'
                                        st.markdown(href, unsafe_allow_html=True)

        # ------------------
        # REPORTS
        # ------------------
        elif menu == "Reports":
            st.markdown("""
                <div class="main-header">
                    <h1 style="margin: 0; font-size: 2.5rem;">Candidate Evaluation Report</h1>
                    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                        Comprehensive AI analysis and HR assessment
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if not data:
                st.info("No candidate data available.")
            else:
                names = [x.get('full_name', 'Unknown') for x in data]
                target = st.session_state.get('target_report')
                
                try:
                    default_idx = names.index(target) if target in names else 0
                except ValueError:
                    default_idx = 0
                
                selected_name = st.selectbox("Select Candidate", names, index=default_idx)
                candidate = next((x for x in data if x.get('full_name') == selected_name), None)
                
                if candidate:
                    ai = candidate.get('ai_analysis', {})
                    metrics = candidate.get('metrics', {})
                    
                    # Header Section
                    col_head1, col_head2 = st.columns([3, 1])
                    
                    with col_head1:
                        st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                        padding: 2.5rem; border-radius: 16px; color: white; margin-bottom: 2rem;">
                                <h1 style="margin: 0; font-size: 2.8rem;">{candidate.get('full_name', 'Unknown')}</h1>
                                <p style="font-size: 1.2rem; opacity: 0.95; margin: 0.5rem 0;">
                                    Applied For: <b>{candidate.get('applied_role', 'Not Specified')}</b> |
                                    AI Suggested: {ai.get('best_role', 'Not specified')}
                                </p>
                                <p style="font-size: 1rem; opacity: 0.8;">
                                    {candidate.get('email', 'No email')} | {candidate.get('mobile', 'No phone')}
                                </p>
                                <div style="margin-top: 1rem;">
                                    {get_status_badge(candidate.get('status', 'New'))}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col_head2:
                        final_score = metrics.get('final_score', 0)
                        
                        fig_gauge = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=final_score,
                            domain={'x': [0, 1], 'y': [0, 1]},
                            title={'text': "Final Score", 'font': {'size': 20, 'color': 'white'}},
                            number={'font': {'size': 40, 'color': 'white'}, 'suffix': "/10"},
                            gauge={
                                'axis': {'range': [None, 10]},
                                'bar': {'color': "#28a745" if final_score >= 8 else "#ffc107" if final_score >= 6 else "#dc3545"},
                                'bgcolor': "rgba(255,255,255,0.2)",
                                'steps': [
                                    {'range': [0, 6], 'color': "rgba(255,255,255,0.1)"},
                                    {'range': [6, 8], 'color': "rgba(255,255,255,0.1)"},
                                    {'range': [8, 10], 'color': "rgba(255,255,255,0.1)"}
                                ],
                                'threshold': {
                                    'line': {'color': "white", 'width': 4},
                                    'thickness': 0.75,
                                    'value': final_score
                                }
                            }
                        ))
                        
                        fig_gauge.update_layout(height=280, paper_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_gauge, use_container_width=True)
                    
                    # Main Content
                    col_main1, col_main2 = st.columns([2, 1])
                    
                    with col_main1:
                        st.markdown('<div class="section-header"><h3>Executive Summary</h3></div>', unsafe_allow_html=True)
                        st.info(ai.get('summary', 'No summary available for this candidate.'))
                        
                        st.markdown('<div class="section-header"><h3>Skills Proficiency</h3></div>', unsafe_allow_html=True)
                        skills = ai.get('skills', {})
                        
                        if skills:
                            skills_df = pd.DataFrame([
                                {'Skill': k, 'Level': float(v)} 
                                for k, v in sorted(skills.items(), key=lambda x: x[1], reverse=True)
                            ])
                            
                            fig_skills = px.bar(
                                skills_df, 
                                x='Level', 
                                y='Skill', 
                                orientation='h',
                                color='Level',
                                color_continuous_scale='Viridis',
                                range_x=[0, 10]
                            )
                            
                            fig_skills.update_layout(
                                height=350,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                showlegend=False,
                                yaxis=dict(autorange="reversed")
                            )
                            
                            st.plotly_chart(fig_skills, use_container_width=True)
                        else:
                            st.write("No skills data available")
                        
                        st.markdown('<div class="section-header"><h3>Experience Timeline</h3></div>', unsafe_allow_html=True)
                        experiences = ai.get('experience', [])
                        
                        if experiences:
                            for exp in experiences:
                                st.markdown(f"""
                                    <div class="timeline-item">
                                        <h4 style="margin: 0;">{exp.get('title', 'Position')}</h4>
                                        <p style="color: #667eea; font-weight: 600;">
                                            {exp.get('company', 'Company')} | {exp.get('duration', 'Duration not specified')}
                                        </p>
                                        <p style="color: #666; font-size: 0.9rem;">
                                            {exp.get('description', '')}
                                        </p>
                                    </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.write("No detailed experience data available")
                    
                    with col_main2:
                        st.markdown('<div class="section-header"><h3>Competency Matrix</h3></div>', unsafe_allow_html=True)
                        
                        eff = ai.get('efficiency', {})
                        categories = ['Technical', 'Logic', 'Experience', 'Communication', 'Leadership']
                        values = [float(eff.get(cat, 5)) for cat in categories]
                        values += values[:1]
                        categories_plot = categories + [categories[0]]
                        
                        fig_radar = go.Figure(go.Scatterpolar(
                            r=values,
                            theta=categories_plot,
                            fill='toself',
                            fillcolor='rgba(102, 126, 234, 0.25)',
                            line=dict(color='#667eea', width=3),
                            marker=dict(size=6)
                        ))
                        
                        fig_radar.update_layout(
                            polar=dict(
                                radialaxis=dict(visible=True, range=[0, 10], gridcolor='rgba(0,0,0,0.1)'),
                                angularaxis=dict(gridcolor='rgba(0,0,0,0.1)')
                            ),
                            height=380,
                            paper_bgcolor='rgba(0,0,0,0)',
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig_radar, use_container_width=True)
                        
                        st.markdown('<div class="section-header"><h3>Analysis</h3></div>', unsafe_allow_html=True)
                        
                        st.write("**Strengths**")
                        pros = ai.get('pros', [])
                        if pros:
                            for pro in pros[:3]:
                                st.success(f"• {pro}")
                        else:
                            st.write("No specific strengths noted")
                        
                        st.write("**Development Areas**")
                        cons = ai.get('cons', [])
                        if cons:
                            for con in cons[:3]:
                                st.warning(f"• {con}")
                        else:
                            st.write("No specific areas noted")
                    
                    # Multimodal & Video Insights Section
                    video = candidate.get('video_analysis')
                    multi_insight = candidate.get('multimodal_insights')
                    
                    if video or multi_insight:
                        st.divider()
                        st.markdown('<div class="section-header"><h3>Multimodal Persona & Alignment</h3></div>', unsafe_allow_html=True)
                        
                        m_col1, m_col2, m_col3 = st.columns([1, 1, 1])
                        
                        with m_col1:
                            st.markdown("##### Video Persona")
                            if video:
                                st.metric("Confidence", f"{video.get('confidence', 0)}/10")
                                st.metric("Clarity", f"{video.get('clarity', 0)}/10")
                                st.markdown(f"**Sentiment:** `{video.get('sentiment', 'N/A')}`")
                                st.markdown(f"**Social Alignment:** {video.get('social_alignment', 'N/A')}")
                            else:
                                st.info("No video data available")
                                
                        with m_col2:
                            st.markdown("##### Personality Traits")
                            if video and video.get('traits'):
                                for trait in video['traits']:
                                    st.markdown(f'<span style="background: #e1e7ff; color: #444; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; margin: 2px; display: inline-block;">{trait}</span>', unsafe_allow_html=True)
                                
                                st.markdown("##### Speech Keywords")
                                if video.get('keywords'):
                                    st.caption(", ".join(video['keywords']))
                            else:
                                st.write("Video traits not analyzed")
                                
                        with m_col3:
                            st.markdown("##### Resume vs Persona")
                            if multi_insight:
                                alignment_score = multi_insight.get('consistency_score', 0)
                                st.progress(alignment_score / 10, text=f"Consistency: {alignment_score}/10")
                                
                                rec_strength = multi_insight.get('recommendation_strength', 0)
                                st.metric("Rec. Strength", f"{rec_strength}/10")
                                
                                st.markdown(f"**Key Insight:** *{multi_insight.get('multimodal_insight', 'N/A')}*")
                            else:
                                st.info("Multimodal cross-reference not available")
                        
                        if multi_insight and multi_insight.get('alignment_details'):
                            with st.expander("View Alignment Details"):
                                st.write(multi_insight['alignment_details'])
                    
                    # HR Actions
                    st.divider()
                    st.subheader("HR Actions")
                    
                    act_col1, act_col2, act_col3, act_col4, act_col5 = st.columns(5)
                    
                    with act_col1:
                        # Screener Action: Hand-off to tech lead
                        if hr_role in ["Screener", "Technical Lead"]:
                            if candidate.get('status') == "New":
                                if st.button("Approve ✅", use_container_width=True, type="primary", help="Approve and send to Technical Lead"):
                                    if IMPORT_STATUS["database_manager"]:
                                        try:
                                            update_candidate_status(candidate.get('_id'), "Screened")
                                            st.success("Sent to Tech Lead!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Action failed: {e}")
                            elif candidate.get('status') == "Screened":
                                st.info("Screened")

                    with act_col2:
                        # Tech Lead Action: Final Shortlist
                        if hr_role == "Technical Lead":
                            if candidate.get('status') == "Screened":
                                if st.button("Shortlist 🏆", use_container_width=True, type="primary"):
                                    if IMPORT_STATUS["database_manager"]:
                                        try:
                                            update_candidate_status(candidate.get('_id'), "Shortlisted")
                                            st.success("Shortlisted!")
                                            st.balloons()
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Action failed: {e}")
                            elif candidate.get('status') == "Shortlisted":
                                st.success("Shortlisted")
                            else:
                                st.caption("Await Screen")
                        else:
                            st.caption("Admin Only")

                    with act_col3:
                        if candidate.get('status') != "Disqualified":
                            if st.button("Disqualify ❌", use_container_width=True):
                                if IMPORT_STATUS["database_manager"]:
                                    try:
                                        hr_user = st.session_state.hr_user
                                        hr_name = hr_user.get('full_name', 'HR Team')
                                        rejection_sub = "Update regarding your application at HireAI Pro"
                                        rejection_body = f"Dear {candidate.get('full_name', 'Candidate')},\n\nThank you for your interest in the position. We have carefully reviewed your application, and while your profile is impressive, we have decided to move forward with other candidates at this time.\n\nWe wish you the best in your career pursuits.\n\nRegards,\n{hr_name}\nHireAI Pro"
                                        
                                        # 1. Log to Disqualified Candidate Table
                                        current_status = candidate.get('status', 'New')
                                        round_label = "Screening" if current_status == "New" else "Technical Review"
                                        log_disqualified_candidate(candidate, hr_user, round_name=round_label)
                                        
                                        # 2. Update Primary Status
                                        update_candidate_status(candidate.get('_id'), "Disqualified")
                                        
                                        # 3. Show Manual Link
                                        import urllib.parse
                                        encoded_msg = urllib.parse.quote(rejection_body)
                                        encoded_sub = urllib.parse.quote(rejection_sub)
                                        mailto_link = f"mailto:{candidate.get('email')}?subject={encoded_sub}&body={encoded_msg}"
                                        
                                        st.error(f"Candidate Disqualified from {round_label} & Record Logged!")
                                        st.info("Now send the rejection email via your local mail client:")
                                        st.markdown(f'<a href="{mailto_link}" target="_blank" style="text-decoration: none;"><button style="width: 100%; padding: 0.8rem; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; margin-top: 10px;">Send Rejection via Gmail/Outlook ✉️</button></a>', unsafe_allow_html=True)
                                    except Exception as e:
                                        st.error(f"Action failed: {e}")
                        else:
                            st.error("Rejected")
                    
                    with act_col4:
                        if st.button("Report 📄", use_container_width=True):
                            pdf_bytes = generate_pdf_report(candidate)
                            if pdf_bytes:
                                b64 = base64.b64encode(pdf_bytes).decode()
                                filename = f"{candidate.get('full_name', 'Candidate').replace(' ', '_')}_Report.pdf"
                                href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="text-decoration: none;"><button style="width: 100%; padding: 0.5rem; background: #28a745; color: white; border: none; border-radius: 8px; cursor: pointer;">Download</button></a>'
                                st.markdown(href, unsafe_allow_html=True)
                    
                    with act_col5:
                        if st.button("Email ✉️", use_container_width=True):
                            st.session_state.show_email_panel = True
                            
                        if st.session_state.get('show_email_panel', False):
                            with st.container():
                                st.markdown("---")
                                st.subheader("✉️ Compose Email")
                                with st.form("email_form", clear_on_submit=True):
                                    hr_email = st.session_state.hr_user.get('email', 'admin@hireaipro.com')
                                    st.write(f"**From:** `{hr_email}`")
                                    st.write(f"**To:** `{candidate.get('email', 'Candidate')}`")
                                    
                                    m_subject = st.text_input("Subject", value=f"Interview Invitation - {candidate.get('full_name', 'Candidate')}")
                                    m_body = st.text_area("Message", value=f"Dear {candidate.get('full_name', 'Candidate')},\n\nWe are impressed with your profile. Your assessment score: {metrics.get('final_score', 0)}/10.\n\nWould you be available for an interview?\n\nBest regards,\n{st.session_state.hr_user.get('full_name', 'HR Team')}", height=150)
                                    
                                    f_cols = st.columns([1, 1])
                                    with f_cols[0]:
                                        if st.form_submit_button("Prepare Manual Email", type="primary", use_container_width=True):
                                            if IMPORT_STATUS["database_manager"]:
                                                import urllib.parse
                                                encoded_msg = urllib.parse.quote(m_body)
                                                encoded_sub = urllib.parse.quote(m_subject)
                                                mailto_link = f"mailto:{candidate.get('email')}?subject={encoded_sub}&body={encoded_msg}"
                                                
                                                # Log the intent
                                                log_candidate_email(st.session_state.hr_user, candidate.get('email'), m_subject, "(Manual Send Path)")
                                                
                                                st.info("Click the button below to send using your local mail client:")
                                                st.markdown(f'<a href="{mailto_link}" target="_blank" style="text-decoration: none;"><button style="width: 100%; padding: 0.8rem; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">Send via Gmail/Outlook ✉️</button></a>', unsafe_allow_html=True)
                                    with f_cols[1]:
                                        if st.form_submit_button("Cancel", use_container_width=True):
                                            st.session_state.show_email_panel = False
                                            st.rerun()

        # ------------------
        # RANKINGS
        # ------------------
        elif menu == "Rankings":
            st.markdown("""
                <div class="main-header">
                    <h1 style="margin: 0; font-size: 1.8rem;">Candidate Rankings</h1>
                    <p style="margin: 0.3rem 0 0 0; opacity: 0.9; font-size: 0.9rem;">
                        Top performers based on AI evaluation scores
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if not data:
                st.info("No candidates available for ranking.")
            else:
                sorted_data = sorted(
                    data, 
                    key=lambda x: x.get('metrics', {}).get('final_score', 0), 
                    reverse=True
                )
                
                # Podium for top 3
                top_3 = sorted_data[:3]
                
                if top_3:
                    st.subheader("Top Performers")
                    cols = st.columns(min(3, len(top_3)))
                    
                    for idx, (col, candidate) in enumerate(zip(cols, top_3)):
                        medal = ["1st", "2nd", "3rd"][idx]
                        podium_class = ["podium-1", "podium-2", "podium-3"][idx]
                        score = candidate.get('metrics', {}).get('final_score', 0)
                        
                        with col:
                            st.markdown(f"""
                                <div class="podium-card {podium_class}">
                                    <div style="font-size: 2rem; font-weight: bold;">{medal}</div>
                                    <h3 style="margin: 0.5rem 0; font-size: 1.2rem;">
                                        {candidate.get('full_name', 'Unknown')}
                                    </h3>
                                    <p style="font-size: 2rem; font-weight: bold; margin: 0;">
                                        {score:.1f}
                                    </p>
                                    <p style="font-size: 0.9rem; opacity: 0.8;">
                                        {candidate.get('ai_analysis', {}).get('best_role', 'Role TBD')}
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)
                
                st.divider()
                st.subheader("Complete Rankings")
                
                rank_df = pd.DataFrame([
                    {
                        'Rank': i + 1,
                        'Name': x.get('full_name', 'Unknown'),
                        'Role': x.get('ai_analysis', {}).get('best_role', 'N/A'),
                        'Score': x.get('metrics', {}).get('final_score', 0),
                        'Status': x.get('status', 'New'),
                        'Email': x.get('email', 'N/A')
                    }
                    for i, x in enumerate(sorted_data)
                ])
                
                st.dataframe(
                    rank_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Rank': st.column_config.NumberColumn('Rank', width='small'),
                        'Score': st.column_config.NumberColumn('Score', format='%.1f'),
                        'Name': st.column_config.TextColumn('Candidate Name', width='medium'),
                        'Status': st.column_config.TextColumn('Status', width='small')
                    }
                )

        # ------------------
        # COMPARE
        # ------------------
        elif menu == "Compare":
            st.markdown("""
                <div class="main-header">
                    <h1 style="margin: 0; font-size: 2.5rem;">Candidate Comparison</h1>
                    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                        Side-by-side competency analysis
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if len(data) < 2:
                st.info("Need at least 2 candidates to perform comparison.")
            else:
                available_names = [x.get('full_name', 'Unknown') for x in data]
                
                selected = st.multiselect(
                    "Select candidates to compare (2-4):",
                    available_names,
                    max_selections=4,
                    default=available_names[:2] if len(available_names) >= 2 else []
                )
                
                if len(selected) >= 2:
                    selected_data = [
                        next((x for x in data if x.get('full_name') == name), None) 
                        for name in selected
                    ]
                    
                    selected_data = [x for x in selected_data if x is not None]
                    
                    fig_compare = go.Figure()
                    colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe']
                    categories = ['Technical', 'Logic', 'Experience', 'Communication', 'Leadership']
                    
                    for idx, cand in enumerate(selected_data):
                        ai = cand.get('ai_analysis', {})
                        eff = ai.get('efficiency', {})
                        values = [eff.get(k, 5) for k in categories]
                        values += values[:1]
                        
                        fig_compare.add_trace(go.Scatterpolar(
                            r=values,
                            theta=categories + [categories[0]],
                            fill='toself',
                            name=cand.get('full_name', f'Candidate {idx+1}'),
                            line=dict(color=colors[idx % len(colors)], width=2),
                            fillcolor=f'rgba{tuple(list(int(colors[idx % len(colors)].lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + [0.2])}'
                        ))
                    
                    fig_compare.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
                        height=500,
                        paper_bgcolor='rgba(0,0,0,0)',
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2)
                    )
                    
                    st.plotly_chart(fig_compare, use_container_width=True)
                    
                    # Comparison table
                    st.subheader("Detailed Comparison")
                    compare_df = pd.DataFrame([
                        {
                            'Candidate': cand.get('full_name'),
                            'Final Score': cand.get('metrics', {}).get('final_score', 0),
                            'Technical': cand.get('ai_analysis', {}).get('efficiency', {}).get('Technical', 0),
                            'Experience': cand.get('ai_analysis', {}).get('efficiency', {}).get('Experience', 0),
                            'Communication': cand.get('ai_analysis', {}).get('efficiency', {}).get('Communication', 0),
                            'Status': cand.get('status', 'New')
                        }
                        for cand in selected_data
                    ])
                    
                    st.dataframe(compare_df, use_container_width=True, hide_index=True)

        # ------------------
        # ANALYTICS
        # ------------------
        elif menu == "Analytics":
            st.markdown("""
                <div class="main-header">
                    <h1 style="margin: 0; font-size: 2.5rem;">Advanced Analytics</h1>
                    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                        Recruitment insights and trend analysis
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if not data:
                st.info("No data available for analytics.")
            else:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Role Distribution")
                    roles = [
                        x.get('ai_analysis', {}).get('best_role', 'Unknown') 
                        for x in data
                    ]
                    role_counts = pd.Series(roles).value_counts()
                    
                    if not role_counts.empty:
                        fig_roles = px.pie(
                            values=role_counts.values,
                            names=role_counts.index,
                            hole=0.3,
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        fig_roles.update_layout(
                            height=400,
                            paper_bgcolor='rgba(0,0,0,0)',
                            showlegend=True
                        )
                        st.plotly_chart(fig_roles, use_container_width=True)
                    else:
                        st.write("No role data available")
                
                with col2:
                    st.subheader("Score Distribution")
                    scores_data = [
                        {
                            'Score': x.get('metrics', {}).get('final_score', 0),
                            'Status': x.get('status', 'New')
                        }
                        for x in data
                    ]
                    scores_df = pd.DataFrame(scores_data)
                    
                    if not scores_df.empty:
                        fig_hist = px.histogram(
                            scores_df,
                            x='Score',
                            color='Status',
                            nbins=15,
                            color_discrete_map={
                                'Shortlisted': '#28a745',
                                'Evaluated': '#ffc107',
                                'Disqualified': '#dc3545',
                                'New': '#17a2b8'
                            },
                            barmode='group'
                        )
                        fig_hist.update_layout(
                            height=400,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            bargap=0.1
                        )
                        st.plotly_chart(fig_hist, use_container_width=True)
                    else:
                        st.write("No score data available")
                
                # Additional metrics
                st.divider()
                st.subheader("Key Insights")
                
                insight_cols = st.columns(3)
                
                with insight_cols[0]:
                    avg_score = sum(x.get('metrics', {}).get('final_score', 0) for x in data) / len(data) if data else 0
                    st.metric("Average Score", f"{avg_score:.2f}")
                
                with insight_cols[1]:
                    top_role = role_counts.index[0] if not role_counts.empty else "N/A"
                    st.metric("Most Common Role", top_role)
                
                with insight_cols[2]:
                    shortlisted_pct = (stats.get('shortlisted', 0) / len(data) * 100) if data else 0
                    st.metric("Shortlist Rate", f"{shortlisted_pct:.1f}%")

        # ------------------
        # DISQUALIFIED
        # ------------------
        elif menu == "Disqualified":
            st.markdown("""
                <div class="main-header">
                    <h1 style="margin: 0; font-size: 2.5rem;">Disqualified Candidates</h1>
                    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                        Audit logs for candidates removed from the recruitment process
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if IMPORT_STATUS["database_manager"]:
                disq_list = fetch_disqualified_candidates()
                
                if not disq_list:
                    st.info("No disqualified records found in the database.")
                else:
                    # Convert to DataFrame for better viewing
                    import pandas as pd
                    df_disq = pd.DataFrame(disq_list)
                    
                    # Clean up for display
                    df_display = pd.DataFrame({
                        "Name": df_disq["full_name"],
                        "Email": df_disq["email"],
                        "ROUND": df_disq.get("round", "N/A"),
                        "REASON": df_disq["reason"],
                        "DISQUALIFIED AT": df_disq["rejected_at"].apply(lambda x: x[:16].replace('T', ' ')),
                        "HR USER": df_disq["hr_username"],
                        "SCORE": df_disq["candidate_metadata"].apply(lambda x: x.get('score', 0))
                    })
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                    
                    st.caption(f"Total Disqualified Records: {len(df_disq)}")
            else:
                st.error("Database connection required to view logs.")

        # ------------------
        # PROFILE
        # ------------------
        elif menu == "Profile":
            st.markdown("""
                <div class="main-header">
                    <h1 style="margin: 0; font-size: 2.5rem;">HR Profile Management</h1>
                    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                        Update your credentials and account information
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            hr_user = st.session_state.get('hr_user', {})
            
            with st.container():
                col_p1, col_p2 = st.columns([1, 1])
                
                with col_p1:
                    st.subheader("Account Information")
                    with st.form("profile_form"):
                        new_name = st.text_input("Full Name", value=hr_user.get('full_name', ''))
                        new_username = st.text_input("Username", value=hr_user.get('username', ''))
                        new_email = st.text_input("Email", value=hr_user.get('email', ''))
                        new_mobile = st.text_input("Mobile Number", value=hr_user.get('mobile', ''))
                        
                        st.divider()
                        st.caption("Change Password (Leave blank to keep current)")
                        new_password = st.text_input("New Password", type="password")
                        confirm_password = st.text_input("Confirm Password", type="password")
                        
                        save_profile = st.form_submit_button("Update Profile", type="primary", use_container_width=True)
                        
                        if save_profile:
                            if new_password and new_password != confirm_password:
                                st.error("Passwords do not match!")
                            elif not new_name or not new_username:
                                st.error("Name and Username are required!")
                            else:
                                update_data = {
                                    "full_name": new_name,
                                    "username": new_username,
                                    "email": new_email,
                                    "mobile": new_mobile
                                }
                                if new_password:
                                    update_data["password"] = new_password
                                
                                success, msg = update_hr_profile(hr_user.get('_id'), update_data)
                                if success:
                                    st.success(msg)
                                    # Update session state with new data
                                    updated_user = authenticate_hr(new_username, new_password if new_password else hr_user.get('password'))
                                    if updated_user:
                                        st.session_state.hr_user = updated_user
                                    st.rerun()
                                else:
                                    st.error(msg)
                
                with col_p2:
                    st.subheader("Current Details")
                    st.markdown(f"""
                        <div style="background: #f8f9fa; padding: 2rem; border-radius: 12px; border: 1px solid #e9ecef;">
                            <p><strong>Full Name:</strong> {hr_user.get('full_name')}</p>
                            <p><strong>Username:</strong> {hr_user.get('username')}</p>
                            <p><strong>Email:</strong> {hr_user.get('email')}</p>
                            <p><strong>Mobile:</strong> {hr_user.get('mobile')}</p>
                            <p><strong>Account ID:</strong> <code>{hr_user.get('_id')}</code></p>
                            <p><strong>Member Since:</strong> {hr_user.get('created_at', 'N/A')[:10]}</p>
                        </div>
                    """, unsafe_allow_html=True)

        # ------------------
        # SETTINGS
        # ------------------
        elif menu == "Settings":
            st.markdown("""
                <div class="main-header">
                    <h1 style="margin: 0; font-size: 2.5rem;">System Configuration</h1>
                    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                        Customize AI scoring weights and system preferences
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            st.subheader("AI Scoring Weights")
            st.write("Adjust the importance of each factor in the final score calculation.")
            
            weight_cols = st.columns(3)
            
            with weight_cols[0]:
                tech_w = st.slider(
                    "Technical Skills %",
                    0, 100,
                    st.session_state.weights['Technical'],
                    help="Weight given to technical competencies"
                )
            
            with weight_cols[1]:
                exp_w = st.slider(
                    "Experience %",
                    0, 100,
                    st.session_state.weights['Experience'],
                    help="Weight given to years and quality of experience"
                )
            
            with weight_cols[2]:
                soft_w = st.slider(
                    "Soft Skills %",
                    0, 100,
                    st.session_state.weights['Soft_Skills'],
                    help="Weight given to communication and leadership"
                )
            
            total_weight = tech_w + exp_w + soft_w
            
            if total_weight != 100:
                st.error(f"Weights must sum to 100%. Current total: {total_weight}%")
            else:
                st.success(f"Total: {total_weight}% - Configuration valid")
                
                if st.button("Save Configuration", type="primary", use_container_width=True):
                    st.session_state.weights = {
                        "Technical": tech_w,
                        "Experience": exp_w,
                        "Soft_Skills": soft_w
                    }
                    st.success("Settings saved successfully!")
                    safe_log(f"Weights updated: {st.session_state.weights}", "INFO")
            
            st.divider()
            
            st.subheader("🛡️ Organization Security")
            st.write("Manage the secret key required for new HR staff registration.")
            
            current_key = get_org_key()
            
            sec_col1, sec_col2 = st.columns([2, 1])
            
            with sec_col1:
                show_key = st.checkbox("Show Current Secret Key")
                key_display = current_key if show_key else "••••••••••••"
                st.info(f"Current Registration Key: **{key_display}**")
            
            with sec_col2:
                new_org_key = st.text_input("New Secret Key", type="password", help="Enter a new key for HR registration")
                if st.button("Update Organization Key", use_container_width=True):
                    if not new_org_key:
                        st.error("Key cannot be empty!")
                    else:
                        success, msg = update_org_key(new_org_key)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            
            st.divider()
            
            st.subheader("Calculation Formula")
            st.code(f"""
Final Score = (Technical × {tech_w/100:.2f}) + 
              (Experience × {exp_w/100:.2f}) + 
              (Soft Skills × {soft_w/100:.2f})

Example Calculation:
  Technical: 9.0 × {tech_w/100:.2f} = {9.0 * tech_w/100:.2f}
  Experience: 7.0 × {exp_w/100:.2f} = {7.0 * exp_w/100:.2f}
  Soft Skills: 8.0 × {soft_w/100:.2f} = {8.0 * soft_w/100:.2f}
  ─────────────────────────────────────────
  Final Score: {9.0 * tech_w/100 + 7.0 * exp_w/100 + 8.0 * soft_w/100:.2f}
            """)

# Footer
st.divider()
st.caption("HireAI Pro v2.0 | Enterprise Recruitment Platform | © 2026")