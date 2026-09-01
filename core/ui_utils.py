import streamlit as st

def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Outfit:wght@500;600;700&display=swap');

        /* Hide Streamlit Branding completely */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        [data-testid="stStatusWidget"] {visibility: hidden;}
        
        /* Global Typography */
        html, body, [class*="css"], .stMarkdown {
            font-family: 'Inter', sans-serif;
            color: #1E293B;
        }
        
        code, pre, .stCodeBlock {
            font-family: 'JetBrains Mono', monospace !important;
        }
        
        /* Soften the main app background */
        .stApp {
            background-color: #FAFAFA;
        }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #E2E8F0;
            box-shadow: 2px 0 12px rgba(0,0,0,0.03);
        }
        [data-testid="stSidebarNav"] span {
            font-weight: 500;
            font-size: 14px;
            color: #475569;
            text-transform: capitalize;
        }
        
        /* Headers with Display Font */
        h1 {
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            letter-spacing: -0.03em;
            color: #0F172A;
            font-size: 2.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        h2 {
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            color: #1E293B;
            letter-spacing: -0.02em;
            font-size: 1.75rem !important;
        }
        h3 {
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            color: #1E293B;
            letter-spacing: -0.01em;
            font-size: 1.25rem !important;
        }
        h4, h5 {
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            color: #334155;
        }
        
        /* Container/Form styling (Premium Elevaton) */
        [data-testid="stForm"], .stContainer, [data-testid="stExpander"] {
            background-color: #FFFFFF;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            border: 1px solid #F1F5F9;
            transition: box-shadow 0.2s ease;
        }
        [data-testid="stForm"]:hover, [data-testid="stExpander"]:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.05);
            border-color: #E2E8F0;
        }
        [data-testid="stForm"] {
            padding: 32px;
            margin-bottom: 24px;
        }
        
        /* Input field styling */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            border-radius: 8px;
            border: 1px solid #CBD5E1;
            transition: all 0.2s ease;
            padding: 12px 14px;
            font-size: 14px;
            font-family: 'Inter', sans-serif;
            color: #1E293B;
            background-color: #FFFFFF;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02) inset;
        }
        .stSelectbox>div>div>div {
            border-radius: 8px;
            border: 1px solid #CBD5E1;
            transition: all 0.2s ease;
            font-size: 14px;
            font-family: 'Inter', sans-serif;
            color: #1E293B;
            background-color: #FFFFFF;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02) inset;
        }
        .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus, .stSelectbox>div>div>div:focus {
            border-color: #4F46E5;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15);
        }
        
        /* Metrics Styling */
        [data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            padding: 20px 24px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        [data-testid="stMetricLabel"] {
            color: #64748B;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-family: 'Inter', sans-serif;
        }
        [data-testid="stMetricValue"] {
            color: #0F172A;
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            font-size: 32px;
            margin-top: 4px;
        }
        
        /* Tab Styling - Sleek horizontal pills */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
            padding-bottom: 12px;
            border-bottom: 1px solid #E2E8F0;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 8px 16px;
            background-color: transparent;
            border: none;
            color: #64748B;
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            font-size: 14px;
            transition: all 0.2s ease;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background-color: #F1F5F9;
            color: #334155;
        }
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid #E2E8F0 !important;
            color: #0F172A !important;
            font-weight: 600;
        }
        
        /* Buttons */
        .stButton>button {
            border-radius: 8px;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            padding: 8px 20px;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid #E2E8F0;
            background-color: #FFFFFF;
            color: #1E293B;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        .stButton>button:hover {
            background-color: #F8FAFC;
            border-color: #CBD5E1;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Primary Buttons */
        .stButton>button[kind="primary"] {
            background-color: #4F46E5;
            color: #FFFFFF;
            border-color: #4F46E5;
            box-shadow: 0 2px 4px rgba(79, 70, 229, 0.3);
        }
        .stButton>button[kind="primary"]:hover {
            background-color: #4338CA;
            border-color: #4338CA;
            box-shadow: 0 4px 6px rgba(79, 70, 229, 0.4);
        }
        
        /* Status Colors / Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 16px;
            font-family: 'Inter', sans-serif;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            line-height: 1;
        }
        .badge-pass { color: #047857; background: #D1FAE5; border: 1px solid #10B981; }
        .badge-warning { color: #B45309; background: #FEF3C7; border: 1px solid #F59E0B; }
        .badge-fail { color: #B91C1C; background: #FEE2E2; border: 1px solid #EF4444; }
        .badge-draft { color: #475569; background: #F1F5F9; border: 1px solid #CBD5E1; }
        .badge-review { color: #4338CA; background: #E0E7FF; border: 1px solid #818CF8; }
        
        /* DataFrame/Table styling enhancements */
        [data-testid="stDataFrame"] {
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            overflow: hidden;
        }
        
        /* Custom progress bar wrapper */
        .score-bar-container {
            width: 100%;
            background-color: #F1F5F9;
            border-radius: 8px;
            height: 12px;
            overflow: hidden;
            margin-top: 8px;
        }
        .score-bar-fill {
            height: 100%;
            border-radius: 8px;
            transition: width 0.5s ease-out;
        }
        .score-pass { background-color: #10B981; }
        .score-warn { background-color: #F59E0B; }
        .score-fail { background-color: #EF4444; }
        
    </style>
    """, unsafe_allow_html=True)
