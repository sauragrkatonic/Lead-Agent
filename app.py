# Handle SQLite for ChromaDB
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except (ImportError, KeyError):
    pass

import streamlit as st
import os
import re
import json
from datetime import datetime
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()

# Set API keys
#os.environ["GROQ_API_KEY"] = os.environ.get('GROQ_API_KEY', '')
llm = ChatGroq(
    model="groq/llama-3.1-8b-instant",  # or other Groq models
    temperature=0.3,
    groq_api_key=os.environ.get("GROQ_API_KEY")
)

from src.crew.lead_crew import run_email_qualification, run_form_qualification
from src.utils.validators import validate_email, validate_form_data
from src.utils.result_parser import parse_crew_result

#--------------------------------#
#         Streamlit App          #
#--------------------------------#

st.set_page_config(
    page_title="CrewAI Lead Qualification",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        font-weight: 700;
    }
    
    .main-header .gradient-text {
        background: linear-gradient(90deg, #4b2be3 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: #f8fafc;
        padding: 0.5rem;
        border-radius: 0.75rem;
        border: 1px solid #e2e8f0;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding: 0.5rem 1.5rem;
        border-radius: 0.5rem;
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        color: #64748b;
        font-weight: 600;
        font-size: 1rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4b2be3, #7c3aed);
        color: white;
        border-color: #4b2be3;
        box-shadow: 0 4px 12px rgba(75, 43, 227, 0.3);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #4b2be3, #7c3aed);
        color: white;
        border: none;
        border-radius: 0.75rem;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(75, 43, 227, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(75, 43, 227, 0.4);
    }
    
    .info-box {
        background: linear-gradient(135deg, #eff6ff, #dbeafe);
        padding: 1.5rem;
        border-radius: 0.75rem;
        border: 1px solid #93c5fd;
        margin: 1rem 0;
    }
    
    .score-card {
        background: #ffffff;
        border: 2px solid #4b2be3;
        padding: 1.5rem;
        border-radius: 1rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(75, 43, 227, 0.1);
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .agent-workflow {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4b2be3;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Configuration
def render_sidebar():
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        st.subheader("🤖 Model Selection")
        # model = st.selectbox(
        #     "Choose OpenAI Model",
        #     options=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        #     index=0,
        #     help="Select the OpenAI model for CrewAI agents"
        # )
        model = st.selectbox(
            "Choose Model",
            options=["groq/llama-3.1-70b-versatile","groq/llama-3.1-8b-instant","mixtral-8x7b-32768"],
            index=0
        )
        
        st.subheader("🎯 Lead Qualification Setup")
        
        st.markdown("**Target Industries**")
        target_industries = st.multiselect(
            "Select Industries",
            ["Technology", "Healthcare", "Finance", "Manufacturing", "Retail", "Education", "Consulting", "Real Estate"],
            default=["Technology", "Healthcare"],
            label_visibility="collapsed"
        )
        
        st.markdown("**Company Sizes**")
        target_company_sizes = st.multiselect(
            "Select Company Sizes",
            ["Startup (1-50)", "SMB (51-500)", "Enterprise (500+)"],
            default=["SMB (51-500)", "Enterprise (500+)"],
            label_visibility="collapsed"
        )
        
        st.markdown("**Target Regions**")
        target_regions = st.multiselect(
            "Select Regions",
            ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East & Africa"],
            default=["North America", "Europe"],
            label_visibility="collapsed"
        )
        
        with st.expander("📊 Scoring Guide"):
            st.markdown("""
            **Lead Scoring (100 points total):**
            
            **Email Domain (20 pts)**
            - Business email = 20
            - Generic with company = 10
            - Generic only = 0
            
            **Company Fit (40 pts)**
            - Industry match = 20
            - Size fit = 10
            - Location fit = 10
            
            **Contact Role (20 pts)**
            - Decision-maker = 20
            - Influencer = 10
            - Other = 0
            
            **Message Intent (20 pts)**
            - Specific interest = 20
            - General inquiry = 10
            - Vague = 0
            """)
        
        return {
            "model": model,
            "target_config": {
                "industries": target_industries,
                "company_sizes": target_company_sizes,
                "regions": target_regions
            }
        }

# Main header
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.markdown(
        '<h1 class="main-header">🎯 <span class="gradient-text">CrewAI Lead Qualification</span></h1>',
        unsafe_allow_html=True
    )

# Get configuration
config = render_sidebar()

# Check API key
if not os.environ.get("GROQ_API_KEY"):
    st.error("⚠️ Please set your OPENAI_API_KEY environment variable")
    st.info("Create a .env file with: OPENAI_API_KEY=your_key_here")
    st.stop()

# Main content
st.markdown("---")
st.markdown("### 📊 Lead Analysis with Multi-Agent AI")
st.markdown("""
<div class="info-box">
    <p style="color: #1e40af; font-weight: 600; margin: 0;">
        Choose your preferred method to analyze potential leads using CrewAI's multi-agent collaboration
    </p>
</div>
""", unsafe_allow_html=True)

# Input tabs
tab1, tab2 = st.tabs(["📧 Email Analysis", "📝 Form Submission"])

with tab1:
    st.markdown("**Analyze leads from email content using CrewAI agents**")
    
    with st.form("email_form"):
        st.markdown("**📧 Email Details**")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            sender_email = st.text_input(
                "Sender Email Address *",
                placeholder="john.doe@company.com",
                help="The email address of the sender"
            )
            
            email_subject = st.text_input(
                "Email Subject Line *",
                placeholder="Inquiry about your services",
                help="The subject line of the email"
            )
        
        with col2:
            email_content = st.text_area(
                "Email Content *",
                height=150,
                placeholder="Enter the full email content here...",
                help="Paste the complete email content"
            )
        
        st.markdown("---")
        email_submitted = st.form_submit_button("🚀 Analyze with CrewAI", type="primary", use_container_width=True)

with tab2:
    st.markdown("**Analyze leads from form submissions using CrewAI agents**")
    
    with st.form("form_form"):
        st.markdown("**📝 Contact Information**")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            form_name = st.text_input(
                "Contact Name *",
                placeholder="John Doe",
                help="Full name of the person"
            )
            
            form_company = st.text_input(
                "Company Name *",
                placeholder="ABC Corporation",
                help="Company name"
            )
            
            form_designation = st.text_input(
                "Job Title/Designation",
                placeholder="Marketing Manager (Optional)",
                help="Person's job title (optional)"
            )
        
        with col2:
            form_email = st.text_input(
                "Email Address *",
                placeholder="john.doe@company.com",
                help="Contact email address"
            )
            
            form_query = st.text_area(
                "Query/Message *",
                height=120,
                placeholder="I'm interested in learning more about your services...",
                help="The message or reason for contact"
            )
        
        st.markdown("---")
        form_submitted = st.form_submit_button("🚀 Analyze with CrewAI", type="primary", use_container_width=True)

# Process with CrewAI
if email_submitted or form_submitted:
    # Validation
    if email_submitted:
        if not all([sender_email, email_subject, email_content]):
            st.error("❌ Please fill in all required fields")
            st.stop()
        
        if not validate_email(sender_email):
            st.error("❌ Please enter a valid email address")
            st.stop()
        
        input_method = "email"
    
    elif form_submitted:
        is_valid, error_msg = validate_form_data(form_name, form_company, form_email, form_query)
        
        if not is_valid:
            st.error(f"❌ {error_msg}")
            st.stop()
        
        input_method = "form"
    
    # Run CrewAI analysis
    with st.status("🤖 CrewAI agents are analyzing...", expanded=True) as status:
        try:
            # Store output in session state
            if 'crew_output' not in st.session_state:
                st.session_state.crew_output = []
            
            if input_method == "email":
                status.update(label="📧 Email Parser Agent extracting information...")
                result = run_email_qualification(
                    sender_email,
                    email_subject,
                    email_content,
                    config['target_config'],
                    config['model']
                )
            else:
                status.update(label="📝 Form Parser Agent structuring data...")
                result = run_form_qualification(
                    form_name,
                    form_company,
                    form_designation,
                    form_email,
                    form_query,
                    config['target_config'],
                    config['model']
                )
            
            status.update(label="✅ Multi-agent analysis complete!", state="complete", expanded=False)
            
            # Parse the result
            parsed_result = parse_crew_result(result)
            
        except Exception as e:
            status.update(label="❌ Error occurred", state="error")
            st.error(f"An error occurred: {str(e)}")
            st.stop()
    
    # Display Results
    st.markdown("---")
    st.markdown("### 📊 CrewAI Analysis Results")
    
    # Agent workflow info
    st.markdown("""
    <div class="agent-workflow">
        <h4 style="color: #4b2be3; margin-top: 0;">🤖 Multi-Agent Workflow Completed</h4>
        <p style="margin: 0;">
            1️⃣ <strong>Email Parser Agent</strong> - Extracted contact information<br>
            2️⃣ <strong>Company Researcher Agent</strong> - Gathered company intelligence<br>
            3️⃣ <strong>Lead Scorer Agent</strong> - Calculated qualification score<br>
            4️⃣ <strong>Recommendation Agent</strong> - Generated strategic next steps
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display score if available
    if parsed_result['score']:
        score = parsed_result['score']
        qualification = parsed_result['qualification'] or "Unknown"
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if score >= 80:
                color = "#059669"
                icon = "🎯"
            elif score >= 50:
                color = "#d97706"
                icon = "⚠️"
            else:
                color = "#dc2626"
                icon = "❌"
            
            st.markdown(f"""
            <div style="background: #ffffff; border: 2px solid {color}; padding: 1.5rem; 
                        border-radius: 1rem; text-align: center; height: 120px; 
                        display: flex; flex-direction: column; justify-content: center;">
                <h3 style="margin: 0; color: {color}; font-size: 1.7rem;">{icon} {score}/100</h3>
                <p style="margin: 0; color: {color}; font-weight: 600;">{qualification}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="score-card">
                <h4 style="margin: 0; color: #4b2be3;">📧 Input Method</h4>
                <p style="margin: 0; color: #4b2be3; font-weight: 600;">{input_method.title()}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            priority = "High" if score >= 80 else "Medium" if score >= 50 else "Low"
            st.markdown(f"""
            <div class="score-card">
                <h4 style="margin: 0; color: #4b2be3;">🎯 Priority</h4>
                <p style="margin: 0; color: #4b2be3; font-weight: 600;">{priority}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            action = "Forward to Sales" if score >= 80 else "Manual Review" if score >= 50 else "Low Priority"
            st.markdown(f"""
            <div class="score-card">
                <h4 style="margin: 0; color: #4b2be3;">✅ Next Action</h4>
                <p style="margin: 0; color: #4b2be3; font-weight: 600;">{action}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Score breakdown
        if parsed_result.get('score_breakdown'):
            st.markdown("---")
            st.markdown("### 📈 Detailed Score Breakdown")
            
            breakdown = parsed_result['score_breakdown']
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'email_domain_score' in breakdown:
                    st.markdown("**📧 Email Domain Score**")
                    st.progress(breakdown['email_domain_score'] / 20)
                    st.caption(f"{breakdown['email_domain_score']}/20 - {breakdown.get('email_domain_justification', '')}")
                
                if 'company_fit_score' in breakdown:
                    st.markdown("**🏢 Company Fit Score**")
                    st.progress(breakdown['company_fit_score'] / 40)
                    st.caption(f"{breakdown['company_fit_score']}/40 - {breakdown.get('company_fit_justification', '')}")
            
            with col2:
                if 'role_score' in breakdown:
                    st.markdown("**👤 Contact Role Score**")
                    st.progress(breakdown['role_score'] / 20)
                    st.caption(f"{breakdown['role_score']}/20 - {breakdown.get('role_justification', '')}")
                
                if 'message_intent_score' in breakdown:
                    st.markdown("**💭 Message Intent Score**")
                    st.progress(breakdown['message_intent_score'] / 20)
                    st.caption(f"{breakdown['message_intent_score']}/20 - {breakdown.get('message_intent_justification', '')}")
    
    # Recommendations
    if parsed_result.get('recommendations'):
        st.markdown("---")
        st.markdown("### 💡 AI Recommendations")
        
        recs = parsed_result['recommendations']
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #eff6ff, #dbeafe); padding: 1.5rem; 
                    border-radius: 1rem; border-left: 4px solid #4b2be3;">
            <p><strong>Next Action:</strong> {recs.get('next_action', 'N/A')}</p>
            <p><strong>Priority:</strong> {recs.get('priority', 'N/A')}</p>
            <p><strong>Reasoning:</strong> {recs.get('reasoning', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Full output
    st.markdown("---")
    with st.expander("📄 View Full CrewAI Output"):
        st.code(parsed_result['raw_output'], language="text")
    
    # Download report
    st.markdown("---")
    report_content = f"""# CrewAI Lead Qualification Report

**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Input Method:** {input_method.title()}
**Model Used:** {config['model']}

## Score Summary
- **Total Score:** {parsed_result.get('score', 'N/A')}/100
- **Qualification:** {parsed_result.get('qualification', 'N/A')}

## Full Analysis
{parsed_result['raw_output']}

---
*Generated by CrewAI Lead Qualification System*
"""
    
    st.download_button(
        label="📥 Download Full Report",
        data=report_content,
        file_name=f"crewai_lead_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
        use_container_width=True
    )

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #f8fafc, #e2e8f0); 
            border-radius: 1rem; margin: 1rem 0;">
    <p style="color: #4b2be3; font-weight: 600; margin: 0;">
        Powered by <strong>CrewAI</strong> Multi-Agent Framework
    </p>
    <p style="color: #64748b; font-size: 0.9rem; margin-top: 0.5rem;">
        Intelligent lead qualification through agent collaboration
    </p>
</div>
""", unsafe_allow_html=True)
