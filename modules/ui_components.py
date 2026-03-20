import streamlit as st

def apply_custom_styles():
    """Applies professional HR portal styling that adapts to Light/Dark mode."""
    st.markdown("""
        <style>
        /* Responsive Banner: Uses semi-transparent colors to blend with any theme */
        .report-banner {
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            color: white;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 25px;
        }
        
        /* Rank Circle: Solid blue looks good in both themes */
        .rank-circle {
            background: #2563eb;
            color: white;
            width: 35px;
            height: 35px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }

        /* Metric Box Fix: Remove hardcoded white to support Dark Mode */
        div[data-testid="stMetric"] {
            border: 1px solid #4b5563; /* Subtle gray border */
            padding: 15px;
            border-radius: 10px;
        }
        
        /* Ensure progress bars stand out */
        .stProgress > div > div > div > div {
            background-image: linear-gradient(to right, #3b82f6 , #10b981);
        }
        </style>
    """, unsafe_allow_html=True)