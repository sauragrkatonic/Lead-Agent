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
import time
from datetime import datetime
from katonic.llm import generate_completion
from katonic.llm.log_requests import log_request_to_platform

st.set_page_config(
    page_title="CrewAI Lead Qualification",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar API Configuration
with st.sidebar:
    st.subheader("🔑 Katonic Configuration")
    
    # Katonic Model ID
    katonic_model_id = st.text_input(
        "Katonic Model ID *",
        type="password",
        placeholder="688b552061aa55897ae98fdc",
        help="Your Katonic model ID from My Model Library under LLM Management"
    )
    
    # Model Selection for Logging
    model_name = st.selectbox(
        "Model Name (for logging) *",
        options=[
            "Openai/gpt-4o",
            "Openai/gpt-4o-mini", 
            "Openai/gpt-4-turbo",
            "Openai/gpt-4",
            "anthropic/claude-3-5-sonnet-20241022",
            "anthropic/claude-3-opus-20240229",
            "google/gemini-1.5-pro",
            "google/gemini-1.5-flash"
        ],
        index=0,
        help="Select the model name for request logging (use lowercase provider names)"
    )
    
    # User Configuration for Logging
    st.subheader("👤 User Configuration")
    user_email = st.text_input(
        "User Email *",
        placeholder="user@company.com",
        help="Your email for request tracking"
    )
    
    project_name = st.text_input(
        "Project Name *",
        value="Lead Qualification",
        help="Project name for logging"
    )

# Wrapper function for Katonic LLM with logging
def katonic_llm_wrapper(query, model_id, user_email, project_name, model_name):
    """
    Wrapper function to use Katonic LLM with automatic request logging
    """
    start_time = time.time()
    status = "success"
    response = ""
    message_id = None
    
    try:
        # Generate completion using Katonic
        response = generate_completion(
            model_id=model_id,
            data={"query": query}
        )
        
        latency = time.time() - start_time
        status = "success"
        
    except Exception as e:
        latency = time.time() - start_time
        status = "failed"
        response = f"Error: {str(e)}"
        st.error(f"❌ Katonic LLM Error: {e}")
    
    finally:
        # Log the request to Katonic platform
        try:
            message_id = log_request_to_platform(
                input_query=query[:500],
                response=response[:500] if status == "success" else response,
                user_name=user_email,
                model_name=model_name,
                product_type="Ace",
                product_name="Lead Qualification System",
                project_name=project_name,
                latency=latency,
                status=status
            )
            
            if message_id and status == "success":
                st.sidebar.success(f"✅ Request logged: {message_id[:8]}...")
            elif message_id and status == "failed":
                st.sidebar.warning(f"⚠️ Failed request logged: {message_id[:8]}...")
        except Exception as log_error:
            st.sidebar.warning(f"⚠️ Logging failed: {log_error}")
    
    return response, latency, message_id

# Import CrewAI functions
try:
    from src.crew.lead_crew_simple import run_email_qualification_simple, run_form_qualification_simple
    crewai_available = True
except ImportError:
    st.warning("⚠️ CrewAI integration not available. Using direct Katonic LLM instead.")
    crewai_available = False

from src.utils.validators import validate_email, validate_form_data

#--------------------------------#
#         Streamlit App          #
#--------------------------------#

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        font-weight: 700;
    }
    
    .main-header .gradient-text {
        background: linear-gradient(90deg, #10a37f 0%, #1a7f64 100%);
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
        background: linear-gradient(135deg, #10a37f, #1a7f64);
        color: white;
        border-color: #10a37f;
        box-shadow: 0 4px 12px rgba(16, 163, 127, 0.3);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #10a37f, #1a7f64);
        color: white;
        border: none;
        border-radius: 0.75rem;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(16, 163, 127, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(16, 163, 127, 0.4);
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
        border: 2px solid #10a37f;
        padding: 1.5rem;
        border-radius: 1rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(16, 163, 127, 0.1);
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .agent-workflow {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #10a37f;
        margin: 1rem 0;
    }
    
    .katonic-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        display: inline-block;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fef3c7, #fde68a);
        padding: 1.5rem;
        border-radius: 0.75rem;
        border: 1px solid #f59e0b;
        margin: 1rem 0;
    }
    
    .success-box {
        background: linear-gradient(135deg, #d1fae5, #a7f3d0);
        padding: 1.5rem;
        border-radius: 0.75rem;
        border: 1px solid #10b981;
        margin: 1rem 0;
    }
    
    .cold-lead {
        background: linear-gradient(135deg, #fef2f2, #fecaca);
        border: 2px solid #dc2626;
    }
    
    .warm-lead {
        background: linear-gradient(135deg, #fffbeb, #fed7aa);
        border: 2px solid #d97706;
    }
    
    .hot-lead {
        background: linear-gradient(135deg, #f0fdf4, #bbf7d0);
        border: 2px solid #16a34a;
    }
    
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 1.5rem;
        border-radius: 1rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .analysis-section {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 4px solid #10a37f;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Configuration
def render_sidebar():
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        st.subheader("🤖 Model Settings")
        
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="Lower values make output more focused and deterministic"
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
        
        # Display configuration status
        st.markdown("---")
        st.subheader("📊 System Status")
        
        if katonic_model_id:
            st.success("✅ Katonic Model ID Set")
            st.caption(f"Model ID: {katonic_model_id[:8]}...")
        else:
            st.error("❌ Katonic Model ID Required")
        
        if user_email:
            st.success(f"✅ User: {user_email}")
        else:
            st.warning("⚠️ No user email set")
        
        if project_name:
            st.success(f"✅ Project: {project_name}")
        
        if not crewai_available:
            st.warning("⚠️ CrewAI integration disabled")
        
        return {
            "model": model_name,
            "temperature": temperature,
            "target_config": {
                "industries": target_industries,
                "company_sizes": target_company_sizes,
                "regions": target_regions
            }
        }

# Helper functions for result processing
def ensure_result_structure(parsed_result):
    """Ensure the result has all required fields with defaults"""
    defaults = {
        'score': 0,
        'qualification': 'Unknown',
        'score_breakdown': {},
        'recommendations': {},
        'analysis_summary': 'No analysis available',
        'contact_info': {},
        'company_analysis': {}
    }
    
    for key, default in defaults.items():
        if key not in parsed_result or parsed_result[key] is None:
            parsed_result[key] = default
    
    return parsed_result

def get_qualification_style(qualification, score):
    """Get CSS class and styling based on qualification level"""
    qualification_lower = str(qualification).lower()
    
    if 'hot' in qualification_lower or score >= 80:
        return "hot-lead", "#16a34a", "🎯"
    elif 'warm' in qualification_lower or score >= 50:
        return "warm-lead", "#d97706", "⚠️"
    elif 'cold' in qualification_lower or score < 50:
        return "cold-lead", "#dc2626", "❌"
    else:
        return "cold-lead", "#6b7280", "❓"

def parse_text_analysis(text_response):
    """Parse text response into structured format"""
    # Initialize default structure
    result = {
        'score': 0,
        'qualification': 'Unknown',
        'score_breakdown': {},
        'recommendations': {},
        'analysis_summary': text_response,
        'contact_info': {},
        'company_analysis': {}
    }
    
    # Try to extract score using regex
    score_match = re.search(r'score.*?(\d+)/100', text_response.lower())
    if score_match:
        result['score'] = int(score_match.group(1))
    
    # Try to extract qualification
    qual_match = re.search(r'(hot|warm|cold)', text_response.lower())
    if qual_match:
        result['qualification'] = qual_match.group(1).title()
    
    # Try to extract score breakdown
    breakdown_patterns = {
        'email_domain_score': r'email.*?(\d+)/20',
        'company_fit_score': r'company.*?fit.*?(\d+)/40',
        'role_score': r'role.*?(\d+)/20',
        'message_intent_score': r'message.*?intent.*?(\d+)/20'
    }
    
    for key, pattern in breakdown_patterns.items():
        match = re.search(pattern, text_response.lower())
        if match:
            result['score_breakdown'][key] = int(match.group(1))
    
    # Extract recommendations
    if 'recommend' in text_response.lower():
        result['recommendations'] = {
            'next_action': 'Review analysis for specific recommendations',
            'priority': 'Medium',
            'reasoning': 'See detailed analysis above'
        }
    
    return result

# Simple lead qualification function using direct Katonic LLM
def simple_lead_qualification(input_data, input_method, target_config):
    """Simple lead qualification using direct Katonic LLM calls"""
    
    prompt = f"""
    Analyze this {input_method} submission for lead qualification and provide a comprehensive text summary.
    
    INPUT DATA:
    {json.dumps(input_data, indent=2)}
    
    TARGET CRITERIA:
    - Target Industries: {', '.join(target_config['industries'])}
    - Target Company Sizes: {', '.join(target_config['company_sizes'])}
    - Target Regions: {', '.join(target_config['regions'])}
    
    Please provide a detailed analysis in the following format:
    
    LEAD QUALIFICATION ANALYSIS
    ===========================
    
    CONTACT INFORMATION:
    - Extracted contact details from the submission
    
    COMPANY ANALYSIS:
    - Company research and industry fit assessment
    - Size and location evaluation
    - Alignment with target criteria
    
    SCORING BREAKDOWN:
    - Overall Score: X/100
    - Email Domain Quality: X/20
    - Company Fit: X/40  
    - Contact Role: X/20
    - Message Intent: X/20
    
    QUALIFICATION LEVEL:
    - Hot/Warm/Cold with justification
    
    RECOMMENDATIONS:
    - Next action steps
    - Priority level (High/Medium/Low)
    - Detailed reasoning
    
    FINAL ASSESSMENT:
    - Summary of key findings and strategic recommendations
    """
    
    response, latency, message_id = katonic_llm_wrapper(
        query=prompt,
        model_id=katonic_model_id,
        user_email=user_email,
        project_name=project_name,
        model_name=config['model']
    )
    
    # Parse the text response into structured format
    parsed_result = parse_text_analysis(response)
    parsed_result['analysis_summary'] = response
    
    # Ensure all required fields are present
    parsed_result = ensure_result_structure(parsed_result)
    
    return parsed_result

# Main header
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.markdown(
        '<h1 class="main-header">🎯 <span class="gradient-text">CrewAI Lead Qualification</span></h1>',
        unsafe_allow_html=True
    )

# Get configuration
config = render_sidebar()

# Validate required configurations
if not katonic_model_id:
    st.error("""
    ⚠️ **Katonic Model ID Required**
    
    Please enter your Katonic Model ID in the sidebar to continue.
    
    **How to find your Model ID:**
    1. Go to **My Model Library** under **LLM Management** in Katonic UI
    2. Copy the Model ID from your preferred model
    3. Paste it in the sidebar under "Katonic Model ID"
    """)
    st.stop()

if not user_email:
    st.warning("⚠️ Please enter your email for request logging")
    st.stop()

if not project_name:
    st.warning("⚠️ Please enter a project name for logging")
    st.stop()

# Main content
st.markdown("---")
st.markdown("### 📊 Lead Analysis with Multi-Agent AI")

# Show Katonic configuration info
st.markdown(f"""
<div class="info-box">
    <p style="color: #1e40af; font-weight: 600; margin: 0;">
        Choose your preferred method to analyze potential leads using AI-powered qualification
    </p>
    <span class="katonic-badge">🔄 Powered by Katonic LLM Gateway</span>
    <p style="color: #64748b; font-size: 0.9rem; margin-top: 0.5rem;">
        Current Model: <strong>{config['model']}</strong> | Temperature: <strong>{config['temperature']}</strong> | Auto-logging enabled
    </p>
    {f'<p style="color: #dc2626; font-size: 0.9rem; margin-top: 0.5rem;"><strong>⚠️ CrewAI Integration: DISABLED - Using direct Katonic LLM</strong></p>' if not crewai_available else ''}
</div>
""", unsafe_allow_html=True)

# Input tabs
tab1, tab2 = st.tabs(["📧 Email Analysis", "📝 Form Submission"])

with tab1:
    st.markdown("**Analyze leads from email content using AI agents**")
    
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
        email_submitted = st.form_submit_button("🚀 Analyze with AI", type="primary", use_container_width=True)

with tab2:
    st.markdown("**Analyze leads from form submissions using AI agents**")
    
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
        form_submitted = st.form_submit_button("🚀 Analyze with AI", type="primary", use_container_width=True)

# Process with AI analysis
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
        input_data = {
            "sender_email": sender_email,
            "email_subject": email_subject,
            "email_content": email_content
        }
    
    elif form_submitted:
        is_valid, error_msg = validate_form_data(form_name, form_company, form_email, form_query)
        
        if not is_valid:
            st.error(f"❌ {error_msg}")
            st.stop()
        
        input_method = "form"
        input_data = {
            "form_name": form_name,
            "form_company": form_company,
            "form_designation": form_designation,
            "form_email": form_email,
            "form_query": form_query
        }
    
    # Initialize tracking variables
    request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    total_latency = 0
    message_ids = []
    
    # Run AI analysis
    with st.status("🤖 AI agents are analyzing...", expanded=True) as status:
        try:
            start_time = time.time()
            
            if crewai_available:
                # Use CrewAI if available
                if input_method == "email":
                    status.update(label="📧 Email Parser Agent extracting information...")
                    result = run_email_qualification_simple(
                        sender_email=sender_email,
                        email_subject=email_subject,
                        email_content=email_content,
                        target_config=config['target_config'],
                        model_id=katonic_model_id,
                        user_email=user_email,
                        project_name=project_name,
                        model_name=config['model']
                    )
                else:
                    status.update(label="📝 Form Parser Agent structuring data...")
                    result = run_form_qualification_simple(
                        name=form_name,
                        company=form_company,
                        designation=form_designation,
                        email=form_email,
                        query=form_query,
                        target_config=config['target_config'],
                        model_id=katonic_model_id,
                        user_email=user_email,
                        project_name=project_name,
                        model_name=config['model']
                    )
                
                # For CrewAI, we'll use the text result directly
                parsed_result = parse_text_analysis(str(result))
                parsed_result['analysis_summary'] = str(result)
            else:
                # Use simple Katonic LLM approach
                status.update(label="🔍 Analyzing lead information...")
                parsed_result = simple_lead_qualification(input_data, input_method, config['target_config'])
            
            end_time = time.time()
            processing_time = end_time - start_time
            total_latency = processing_time
            
            status.update(label="✅ AI analysis complete!", state="complete", expanded=False)
            
            # Additional logging for the complete analysis
            try:
                query_summary = f"Lead Qualification - {input_method.title()}"
                message_id = log_request_to_platform(
                    input_query=query_summary,
                    response=parsed_result.get('analysis_summary', '')[:500],
                    user_name=user_email,
                    model_name=config['model'],
                    product_type="Ace",
                    product_name="Lead Qualification System",
                    project_name=project_name,
                    latency=total_latency,
                    status="success"
                )
                
                if message_id:
                    message_ids.append(message_id)
            except Exception as log_err:
                st.warning(f"⚠️ Failed to log complete analysis: {log_err}")
            
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            
            status.update(label="❌ Error occurred", state="error")
            
            # Log error to Katonic
            try:
                error_query = f"Lead Qualification Error - {input_method.title()}"
                message_id = log_request_to_platform(
                    input_query=error_query,
                    response=f"Error: {str(e)}",
                    user_name=user_email,
                    model_name=config['model'],
                    product_type="Ace",
                    product_name="Lead Qualification System",
                    project_name=project_name,
                    latency=processing_time,
                    status="failed"
                )
                if message_id:
                    message_ids.append(message_id)
            except Exception as log_err:
                st.warning(f"⚠️ Failed to log error: {log_err}")
            
            st.error(f"An error occurred: {str(e)}")
            st.stop()
    
    # Ensure result structure
    parsed_result = ensure_result_structure(parsed_result)
    
    # Display Results
    st.markdown("---")
    st.markdown("### 📊 AI Analysis Results")
    
    # Get qualification styling
    score = parsed_result.get('score', 0)
    qualification = parsed_result.get('qualification', 'Unknown')
    css_class, color, icon = get_qualification_style(qualification, score)
    
    # Workflow info
    workflow_html = f"""
    <div class="agent-workflow">
        <h4 style="color: #10a37f; margin-top: 0;">🤖 {'Multi-Agent Workflow' if crewai_available else 'AI Analysis'} Completed</h4>
        <p style="margin: 0;">
            {'1️⃣ Email Parser Agent - Extracted contact information<br>2️⃣ Company Researcher Agent - Gathered company intelligence<br>3️⃣ Lead Scorer Agent - Calculated qualification score<br>4️⃣ Recommendation Agent - Generated strategic next steps' if crewai_available else '1️⃣ Contact Information Extraction<br>2️⃣ Company Fit Analysis<br>3️⃣ Lead Scoring & Qualification<br>4️⃣ Strategic Recommendations'}
            <br><br>
            <em>Powered by Katonic LLM Gateway | Model: {config['model']} | Processing time: {processing_time:.2f}s</em>
    """
    
    if message_ids:
        workflow_html += f"""<br><span class="katonic-badge">🔄 {len(message_ids)} requests logged to Katonic Platform</span>"""
    
    workflow_html += """
        </p>
    </div>
    """
    
    st.markdown(workflow_html, unsafe_allow_html=True)
    
    # Main Score Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="{css_class}" style="padding: 1.5rem; border-radius: 1rem; text-align: center; height: 120px; 
                    display: flex; flex-direction: column; justify-content: center;">
            <h3 style="margin: 0; color: {color}; font-size: 1.7rem;">{icon} {score}/100</h3>
            <p style="margin: 0; color: {color}; font-weight: 600;">{qualification.title()}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="score-card">
            <h4 style="margin: 0; color: #10a37f;">📧 Input Method</h4>
            <p style="margin: 0; color: #10a37f; font-weight: 600;">{input_method.title()}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        priority = "High" if score >= 80 else "Medium" if score >= 50 else "Low"
        st.markdown(f"""
        <div class="score-card">
            <h4 style="margin: 0; color: #10a37f;">🎯 Priority</h4>
            <p style="margin: 0; color: #10a37f; font-weight: 600;">{priority}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        action = "Forward to Sales" if score >= 80 else "Manual Review" if score >= 50 else "Low Priority"
        st.markdown(f"""
        <div class="score-card">
            <h4 style="margin: 0; color: #10a37f;">✅ Next Action</h4>
            <p style="margin: 0; color: #10a37f; font-weight: 600;">{action}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick Summary Metrics
    st.markdown("---")
    st.markdown("### 📋 Quick Summary")
    
    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    
    with summary_col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin: 0; color: #10a37f;">Overall Score</h4>
            <p style="margin: 0; color: #10a37f; font-weight: 600; font-size: 1.5rem;">{score}/100</p>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin: 0; color: #10a37f;">Qualification</h4>
            <p style="margin: 0; color: #10a37f; font-weight: 600; font-size: 1.2rem;">{qualification.title()}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_col3:
        industry_match = "✅ Yes" if score >= 50 else "❌ No"
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin: 0; color: #10a37f;">Industry Match</h4>
            <p style="margin: 0; color: #10a37f; font-weight: 600; font-size: 1.2rem;">{industry_match}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_col4:
        region_match = "✅ Yes" if score >= 50 else "❌ No"
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin: 0; color: #10a37f;">Region Match</h4>
            <p style="margin: 0; color: #10a37f; font-weight: 600; font-size: 1.2rem;">{region_match}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Score breakdown
    if parsed_result.get('score_breakdown'):
        st.markdown("---")
        st.markdown("### 📈 Detailed Score Breakdown")
        
        breakdown = parsed_result['score_breakdown']
        
        # Define score categories
        score_categories = {
            'email_domain_score': {'name': '📧 Email Domain', 'max': 20, 'description': 'Quality of email address and domain'},
            'company_fit_score': {'name': '🏢 Company Fit', 'max': 40, 'description': 'Industry, size, and location alignment'},
            'role_score': {'name': '👤 Contact Role', 'max': 20, 'description': 'Seniority and decision-making authority'},
            'message_intent_score': {'name': '💭 Message Intent', 'max': 20, 'description': 'Clarity and specificity of inquiry'}
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            for i, (key, category) in enumerate(list(score_categories.items())[:2]):
                if key in breakdown:
                    score_val = breakdown[key]
                    max_score = category['max']
                    percentage = (score_val / max_score) * 100
                    
                    st.markdown(f"**{category['name']}**")
                    st.progress(score_val / max_score)
                    st.caption(f"{score_val}/{max_score} ({percentage:.0f}%) - {category['description']}")
        
        with col2:
            for i, (key, category) in enumerate(list(score_categories.items())[2:]):
                if key in breakdown:
                    score_val = breakdown[key]
                    max_score = category['max']
                    percentage = (score_val / max_score) * 100
                    
                    st.markdown(f"**{category['name']}**")
                    st.progress(score_val / max_score)
                    st.caption(f"{score_val}/{max_score} ({percentage:.0f}%) - {category['description']}")
    
    # Display the text analysis summary
    st.markdown("---")
    st.markdown("### 📝 Detailed Analysis Summary")
    
    analysis_text = parsed_result.get('analysis_summary', 'No analysis available')
    
    # Display the analysis in a nicely formatted section
    st.markdown(f"""
    <div class="analysis-section">
        <div style="font-family: 'Monaco', 'Menlo', 'Consolas', monospace; white-space: pre-wrap; line-height: 1.5; font-size: 0.9rem;">
            {analysis_text}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Katonic Logging Summary
    if message_ids:
        st.markdown("---")
        st.markdown("### 📊 Katonic Logging Summary")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Requests Logged", len(message_ids))
        with col2:
            st.metric("Total Latency", f"{total_latency:.2f}s")
        with col3:
            st.metric("Status", "Success ✅")
        
        with st.expander("📋 View Message IDs"):
            for idx, msg_id in enumerate(message_ids, 1):
                st.code(f"Request {idx}: {msg_id}", language="text")
    
    # Download report
    st.markdown("---")
    
    # Build report content
    katonic_info = f"""
## Katonic Configuration
- **Model ID:** {katonic_model_id[:8]}...
- **Model Name:** {config['model']}
- **Requests Logged:** {len(message_ids)}
- **Total Latency:** {total_latency:.2f} seconds
- **User:** {user_email}
- **Project:** {project_name}
"""
    
    report_content = f"""# AI Lead Qualification Report

**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Request ID:** {request_id}
**Input Method:** {input_method.title()}
**Model Used:** {config['model']}
**Temperature:** {config['temperature']}
**Processing Time:** {processing_time:.2f} seconds

## Configuration
- **LLM Gateway:** Katonic
- **Analysis Engine:** {'CrewAI Multi-Agent' if crewai_available else 'Direct Katonic LLM'}
- **Target Industries:** {', '.join(config['target_config']['industries'])}
- **Company Sizes:** {', '.join(config['target_config']['company_sizes'])}
- **Target Regions:** {', '.join(config['target_config']['regions'])}

## Score Summary
- **Total Score:** {score}/100
- **Qualification:** {qualification.title()}
- **Priority:** {priority}
- **Recommended Action:** {action}

{katonic_info}

## Detailed Analysis
{analysis_text}

---
*Generated by {'CrewAI Lead Qualification System' if crewai_available else 'AI Lead Qualification System'}*
*Powered by Katonic LLM Gateway - {config['model']}*
"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📥 Download Full Report (Markdown)",
            data=report_content,
            file_name=f"lead_qualification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    
    with col2:
        # Create JSON export with structured data
        json_export = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "input_method": input_method,
            "input_data": input_data,
            "configuration": {
                "katonic_model_id": katonic_model_id[:8] + "...",
                "model_name": config['model'],
                "temperature": config['temperature'],
                "target_config": config['target_config'],
                "analysis_engine": "crewai" if crewai_available else "direct_katonic"
            },
            "results": {
                "score": score,
                "qualification": qualification,
                "priority": priority,
                "action": action,
                "score_breakdown": parsed_result.get('score_breakdown'),
                "analysis_summary": analysis_text
            },
            "performance": {
                "processing_time_seconds": processing_time,
                "total_latency_seconds": total_latency
            },
            "katonic_logging": {
                "message_ids": message_ids,
                "user": user_email,
                "project": project_name
            }
        }
        
        st.download_button(
            label="📥 Download Data (JSON)",
            data=json.dumps(json_export, indent=2),
            file_name=f"lead_qualification_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

# Footer
st.divider()

st.markdown(f"""
<div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #f8fafc, #e2e8f0); 
            border-radius: 1rem; margin: 1rem 0;">
    <p style="color: #10a37f; font-weight: 600; margin: 0;">
        Powered by {'<strong>CrewAI</strong> Multi-Agent Framework via ' if crewai_available else ''}<strong>Katonic LLM Gateway</strong>
    </p>
    <p style="color: #64748b; font-size: 0.9rem; margin-top: 0.5rem;">
        Intelligent lead qualification through AI collaboration | Automatic request logging & monitoring
    </p>
</div>
""", unsafe_allow_html=True)
# # Handle SQLite for ChromaDB
# try:
#     __import__('pysqlite3')
#     import sys
#     sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
# except (ImportError, KeyError):
#     pass

# import streamlit as st
# import os
# import re
# import json
# import time
# from datetime import datetime
# from katonic.llm import generate_completion
# from katonic.llm.log_requests import log_request_to_platform

# st.set_page_config(
#     page_title="CrewAI Lead Qualification",
#     page_icon="🎯",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # Sidebar API Configuration
# with st.sidebar:
#     st.subheader("🔑 Katonic Configuration")
    
#     # Katonic Model ID
#     katonic_model_id = st.text_input(
#         "Katonic Model ID *",
#         type="password",
#         placeholder="688b552061aa55897ae98fdc",
#         help="Your Katonic model ID from My Model Library under LLM Management"
#     )
    
#     # Model Selection for Logging - FIXED: lowercase provider names
#     model_name = st.selectbox(
#         "Model Name (for logging) *",
#         options=[
#             "openai/gpt-4o",
#             "openai/gpt-4o-mini", 
#             "openai/gpt-4-turbo",
#             "openai/gpt-4",
#             "anthropic/claude-3-5-sonnet-20241022",
#             "anthropic/claude-3-opus-20240229",
#             "google/gemini-1.5-pro",
#             "google/gemini-1.5-flash"
#         ],
#         index=0,
#         help="Select the model name for request logging (use lowercase provider names)"
#     )
    
#     # User Configuration for Logging
#     st.subheader("👤 User Configuration")
#     user_email = st.text_input(
#         "User Email *",
#         placeholder="user@company.com",
#         help="Your email for request tracking"
#     )
    
#     project_name = st.text_input(
#         "Project Name *",
#         value="Lead Qualification",
#         help="Project name for logging"
#     )

# # Wrapper function for Katonic LLM with logging
# def katonic_llm_wrapper(query, model_id, user_email, project_name, model_name):
#     """
#     Wrapper function to use Katonic LLM with automatic request logging
#     """
#     start_time = time.time()
#     status = "success"
#     response = ""
#     message_id = None
    
#     try:
#         # Generate completion using Katonic
#         response = generate_completion(
#             model_id=model_id,
#             data={"query": query}
#         )
        
#         latency = time.time() - start_time
#         status = "success"
        
#     except Exception as e:
#         latency = time.time() - start_time
#         status = "failed"
#         response = f"Error: {str(e)}"
#         st.error(f"❌ Katonic LLM Error: {e}")
    
#     finally:
#         # Log the request to Katonic platform
#         try:
#             message_id = log_request_to_platform(
#                 input_query=query[:500],  # Limit query length
#                 response=response[:500] if status == "success" else response,  # Limit response length
#                 user_name=user_email,
#                 model_name=model_name,
#                 product_type="Ace",
#                 product_name="Lead Qualification System",
#                 project_name=project_name,
#                 latency=latency,
#                 status=status
#             )
            
#             if message_id and status == "success":
#                 st.sidebar.success(f"✅ Request logged: {message_id[:8]}...")
#             elif message_id and status == "failed":
#                 st.sidebar.warning(f"⚠️ Failed request logged: {message_id[:8]}...")
#         except Exception as log_error:
#             st.sidebar.warning(f"⚠️ Logging failed: {log_error}")
    
#     return response, latency, message_id

# # Import CrewAI functions - using simplified versions
# try:
#     from src.crew.lead_crew_simple import run_email_qualification_simple, run_form_qualification_simple
#     crewai_available = True
# except ImportError:
#     st.warning("⚠️ CrewAI integration not available. Using direct Katonic LLM instead.")
#     crewai_available = False

# from src.utils.validators import validate_email, validate_form_data
# from src.utils.result_parser import parse_crew_result

# #--------------------------------#
# #         Streamlit App          #
# #--------------------------------#

# # Custom CSS (keep your existing CSS)
# st.markdown("""
# <style>
#     .main-header {
#         text-align: center;
#         padding: 2rem 0;
#         font-weight: 700;
#     }
    
#     .main-header .gradient-text {
#         background: linear-gradient(90deg, #10a37f 0%, #1a7f64 100%);
#         -webkit-background-clip: text;
#         -webkit-text-fill-color: transparent;
#         background-clip: text;
#     }
    
#     .stTabs [data-baseweb="tab-list"] {
#         gap: 2rem;
#         background: #f8fafc;
#         padding: 0.5rem;
#         border-radius: 0.75rem;
#         border: 1px solid #e2e8f0;
#     }
    
#     .stTabs [data-baseweb="tab"] {
#         height: 3rem;
#         padding: 0.5rem 1.5rem;
#         border-radius: 0.5rem;
#         background-color: #ffffff;
#         border: 2px solid #e2e8f0;
#         color: #64748b;
#         font-weight: 600;
#         font-size: 1rem;
#     }
    
#     .stTabs [aria-selected="true"] {
#         background: linear-gradient(135deg, #10a37f, #1a7f64);
#         color: white;
#         border-color: #10a37f;
#         box-shadow: 0 4px 12px rgba(16, 163, 127, 0.3);
#     }
    
#     .stButton > button {
#         background: linear-gradient(135deg, #10a37f, #1a7f64);
#         color: white;
#         border: none;
#         border-radius: 0.75rem;
#         padding: 0.75rem 2rem;
#         font-weight: 600;
#         transition: all 0.3s ease;
#         box-shadow: 0 4px 12px rgba(16, 163, 127, 0.3);
#     }
    
#     .stButton > button:hover {
#         transform: translateY(-2px);
#         box-shadow: 0 6px 20px rgba(16, 163, 127, 0.4);
#     }
    
#     .info-box {
#         background: linear-gradient(135deg, #eff6ff, #dbeafe);
#         padding: 1.5rem;
#         border-radius: 0.75rem;
#         border: 1px solid #93c5fd;
#         margin: 1rem 0;
#     }
    
#     .score-card {
#         background: #ffffff;
#         border: 2px solid #10a37f;
#         padding: 1.5rem;
#         border-radius: 1rem;
#         text-align: center;
#         box-shadow: 0 4px 12px rgba(16, 163, 127, 0.1);
#         height: 120px;
#         display: flex;
#         flex-direction: column;
#         justify-content: center;
#     }
    
#     .agent-workflow {
#         background: #f8fafc;
#         padding: 1rem;
#         border-radius: 0.5rem;
#         border-left: 4px solid #10a37f;
#         margin: 1rem 0;
#     }
    
#     .katonic-badge {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         color: white;
#         padding: 0.5rem 1rem;
#         border-radius: 0.5rem;
#         display: inline-block;
#         font-weight: 600;
#         margin-top: 0.5rem;
#     }
    
#     .warning-box {
#         background: linear-gradient(135deg, #fef3c7, #fde68a);
#         padding: 1.5rem;
#         border-radius: 0.75rem;
#         border: 1px solid #f59e0b;
#         margin: 1rem 0;
#     }
# </style>
# """, unsafe_allow_html=True)

# # Sidebar Configuration
# def render_sidebar():
#     with st.sidebar:
#         st.header("⚙️ Configuration")
        
#         st.subheader("🤖 Model Settings")
        
#         temperature = st.slider(
#             "Temperature",
#             min_value=0.0,
#             max_value=1.0,
#             value=0.3,
#             step=0.1,
#             help="Lower values make output more focused and deterministic"
#         )
        
#         st.subheader("🎯 Lead Qualification Setup")
        
#         st.markdown("**Target Industries**")
#         target_industries = st.multiselect(
#             "Select Industries",
#             ["Technology", "Healthcare", "Finance", "Manufacturing", "Retail", "Education", "Consulting", "Real Estate"],
#             default=["Technology", "Healthcare"],
#             label_visibility="collapsed"
#         )
        
#         st.markdown("**Company Sizes**")
#         target_company_sizes = st.multiselect(
#             "Select Company Sizes",
#             ["Startup (1-50)", "SMB (51-500)", "Enterprise (500+)"],
#             default=["SMB (51-500)", "Enterprise (500+)"],
#             label_visibility="collapsed"
#         )
        
#         st.markdown("**Target Regions**")
#         target_regions = st.multiselect(
#             "Select Regions",
#             ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East & Africa"],
#             default=["North America", "Europe"],
#             label_visibility="collapsed"
#         )
        
#         with st.expander("📊 Scoring Guide"):
#             st.markdown("""
#             **Lead Scoring (100 points total):**
            
#             **Email Domain (20 pts)**
#             - Business email = 20
#             - Generic with company = 10
#             - Generic only = 0
            
#             **Company Fit (40 pts)**
#             - Industry match = 20
#             - Size fit = 10
#             - Location fit = 10
            
#             **Contact Role (20 pts)**
#             - Decision-maker = 20
#             - Influencer = 10
#             - Other = 0
            
#             **Message Intent (20 pts)**
#             - Specific interest = 20
#             - General inquiry = 10
#             - Vague = 0
#             """)
        
#         # Display configuration status
#         st.markdown("---")
#         st.subheader("📊 System Status")
        
#         if katonic_model_id:
#             st.success("✅ Katonic Model ID Set")
#             st.caption(f"Model ID: {katonic_model_id[:8]}...")
#         else:
#             st.error("❌ Katonic Model ID Required")
        
#         if user_email:
#             st.success(f"✅ User: {user_email}")
#         else:
#             st.warning("⚠️ No user email set")
        
#         if project_name:
#             st.success(f"✅ Project: {project_name}")
        
#         if not crewai_available:
#             st.warning("⚠️ CrewAI integration disabled")
        
#         return {
#             "model": model_name,
#             "temperature": temperature,
#             "target_config": {
#                 "industries": target_industries,
#                 "company_sizes": target_company_sizes,
#                 "regions": target_regions
#             }
#         }

# # Main header
# col1, col2, col3 = st.columns([1, 3, 1])
# with col2:
#     st.markdown(
#         '<h1 class="main-header">🎯 <span class="gradient-text">CrewAI Lead Qualification</span></h1>',
#         unsafe_allow_html=True
#     )

# # Get configuration
# config = render_sidebar()

# # Validate required configurations
# if not katonic_model_id:
#     st.error("""
#     ⚠️ **Katonic Model ID Required**
    
#     Please enter your Katonic Model ID in the sidebar to continue.
    
#     **How to find your Model ID:**
#     1. Go to **My Model Library** under **LLM Management** in Katonic UI
#     2. Copy the Model ID from your preferred model
#     3. Paste it in the sidebar under "Katonic Model ID"
#     """)
#     st.stop()

# if not user_email:
#     st.warning("⚠️ Please enter your email for request logging")
#     st.stop()

# if not project_name:
#     st.warning("⚠️ Please enter a project name for logging")
#     st.stop()

# # Main content
# st.markdown("---")
# st.markdown("### 📊 Lead Analysis with Multi-Agent AI")

# # Show Katonic configuration info
# st.markdown(f"""
# <div class="info-box">
#     <p style="color: #1e40af; font-weight: 600; margin: 0;">
#         Choose your preferred method to analyze potential leads using CrewAI's multi-agent collaboration
#     </p>
#     <span class="katonic-badge">🔄 Powered by Katonic LLM Gateway</span>
#     <p style="color: #64748b; font-size: 0.9rem; margin-top: 0.5rem;">
#         Current Model: <strong>{config['model']}</strong> | Temperature: <strong>{config['temperature']}</strong> | Auto-logging enabled
#     </p>
#     {f'<p style="color: #dc2626; font-size: 0.9rem; margin-top: 0.5rem;"><strong>⚠️ CrewAI Integration: DISABLED - Using direct Katonic LLM</strong></p>' if not crewai_available else ''}
# </div>
# """, unsafe_allow_html=True)

# # Input tabs
# tab1, tab2 = st.tabs(["📧 Email Analysis", "📝 Form Submission"])

# with tab1:
#     st.markdown("**Analyze leads from email content using AI agents**")
    
#     with st.form("email_form"):
#         st.markdown("**📧 Email Details**")
        
#         col1, col2 = st.columns([1, 1])
        
#         with col1:
#             sender_email = st.text_input(
#                 "Sender Email Address *",
#                 placeholder="john.doe@company.com",
#                 help="The email address of the sender"
#             )
            
#             email_subject = st.text_input(
#                 "Email Subject Line *",
#                 placeholder="Inquiry about your services",
#                 help="The subject line of the email"
#             )
        
#         with col2:
#             email_content = st.text_area(
#                 "Email Content *",
#                 height=150,
#                 placeholder="Enter the full email content here...",
#                 help="Paste the complete email content"
#             )
        
#         st.markdown("---")
#         email_submitted = st.form_submit_button("🚀 Analyze with AI", type="primary", use_container_width=True)

# with tab2:
#     st.markdown("**Analyze leads from form submissions using AI agents**")
    
#     with st.form("form_form"):
#         st.markdown("**📝 Contact Information**")
        
#         col1, col2 = st.columns([1, 1])
        
#         with col1:
#             form_name = st.text_input(
#                 "Contact Name *",
#                 placeholder="John Doe",
#                 help="Full name of the person"
#             )
            
#             form_company = st.text_input(
#                 "Company Name *",
#                 placeholder="ABC Corporation",
#                 help="Company name"
#             )
            
#             form_designation = st.text_input(
#                 "Job Title/Designation",
#                 placeholder="Marketing Manager (Optional)",
#                 help="Person's job title (optional)"
#             )
        
#         with col2:
#             form_email = st.text_input(
#                 "Email Address *",
#                 placeholder="john.doe@company.com",
#                 help="Contact email address"
#             )
            
#             form_query = st.text_area(
#                 "Query/Message *",
#                 height=120,
#                 placeholder="I'm interested in learning more about your services...",
#                 help="The message or reason for contact"
#             )
        
#         st.markdown("---")
#         form_submitted = st.form_submit_button("🚀 Analyze with AI", type="primary", use_container_width=True)

# # Simple lead qualification function using direct Katonic LLM
# def simple_lead_qualification(input_data, input_method, target_config):
#     """Simple lead qualification using direct Katonic LLM calls"""
    
#     prompt = f"""
#     Analyze this {input_method} submission for lead qualification:
    
#     {json.dumps(input_data, indent=2)}
    
#     Target Criteria:
#     - Industries: {', '.join(target_config['industries'])}
#     - Company Sizes: {', '.join(target_config['company_sizes'])}
#     - Regions: {', '.join(target_config['regions'])}
    
#     Please provide a comprehensive analysis including:
#     1. Contact information extraction
#     2. Company research and fit assessment
#     3. Lead scoring (0-100) with breakdown
#     4. Qualification level (Hot, Warm, Cold)
#     5. Recommendations for next steps
    
#     Format your response as a structured JSON with the following fields:
#     - score (0-100)
#     - qualification (Hot/Warm/Cold)
#     - score_breakdown (object with email_domain_score, company_fit_score, role_score, message_intent_score)
#     - recommendations (object with next_action, priority, reasoning)
#     - raw_output (the full analysis text)
#     """
    
#     response, latency, message_id = katonic_llm_wrapper(
#         query=prompt,
#         model_id=katonic_model_id,
#         user_email=user_email,
#         project_name=project_name,
#         model_name=config['model']
#     )
    
#     # Try to parse as JSON, if fails return as raw output
#     try:
#         parsed_result = json.loads(response)
#         # Ensure all required fields are present
#         if 'score' not in parsed_result:
#             parsed_result['score'] = 0
#         if 'qualification' not in parsed_result:
#             parsed_result['qualification'] = 'Unknown'
#         if 'raw_output' not in parsed_result:
#             parsed_result['raw_output'] = response
#     except:
#         parsed_result = {
#             'score': 0,
#             'qualification': 'Unknown',
#             'raw_output': response,
#             'score_breakdown': {},
#             'recommendations': {}
#         }
    
#     return parsed_result

# # Process with AI analysis
# if email_submitted or form_submitted:
#     # Validation
#     if email_submitted:
#         if not all([sender_email, email_subject, email_content]):
#             st.error("❌ Please fill in all required fields")
#             st.stop()
        
#         if not validate_email(sender_email):
#             st.error("❌ Please enter a valid email address")
#             st.stop()
        
#         input_method = "email"
#         input_data = {
#             "sender_email": sender_email,
#             "email_subject": email_subject,
#             "email_content": email_content
#         }
    
#     elif form_submitted:
#         is_valid, error_msg = validate_form_data(form_name, form_company, form_email, form_query)
        
#         if not is_valid:
#             st.error(f"❌ {error_msg}")
#             st.stop()
        
#         input_method = "form"
#         input_data = {
#             "form_name": form_name,
#             "form_company": form_company,
#             "form_designation": form_designation,
#             "form_email": form_email,
#             "form_query": form_query
#         }
    
#     # Initialize tracking variables
#     request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
#     total_latency = 0
#     message_ids = []
    
#     # Run AI analysis
#     with st.status("🤖 AI agents are analyzing...", expanded=True) as status:
#         try:
#             start_time = time.time()
            
#             if crewai_available:
#                 # Use CrewAI if available
#                 if input_method == "email":
#                     status.update(label="📧 Email Parser Agent extracting information...")
#                     result = run_email_qualification_simple(
#                         sender_email=sender_email,
#                         email_subject=email_subject,
#                         email_content=email_content,
#                         target_config=config['target_config'],
#                         model_id=katonic_model_id,
#                         user_email=user_email,
#                         project_name=project_name,
#                         model_name=config['model']
#                     )
#                 else:
#                     status.update(label="📝 Form Parser Agent structuring data...")
#                     result = run_form_qualification_simple(
#                         name=form_name,
#                         company=form_company,
#                         designation=form_designation,
#                         email=form_email,
#                         query=form_query,
#                         target_config=config['target_config'],
#                         model_id=katonic_model_id,
#                         user_email=user_email,
#                         project_name=project_name,
#                         model_name=config['model']
#                     )
                
#                 # Parse CrewAI result
#                 parsed_result = parse_crew_result(result)
#             else:
#                 # Use simple Katonic LLM approach
#                 status.update(label="🔍 Analyzing lead information...")
#                 parsed_result = simple_lead_qualification(input_data, input_method, config['target_config'])
            
#             end_time = time.time()
#             processing_time = end_time - start_time
#             total_latency = processing_time
            
#             status.update(label="✅ AI analysis complete!", state="complete", expanded=False)
            
#             # Additional logging for the complete analysis
#             try:
#                 query_summary = f"Lead Qualification - {input_method.title()}"
#                 message_id = log_request_to_platform(
#                     input_query=query_summary,
#                     response=str(parsed_result.get('raw_output', '')[:500]),
#                     user_name=user_email,
#                     model_name=config['model'],
#                     product_type="Ace",
#                     product_name="Lead Qualification System",
#                     project_name=project_name,
#                     latency=total_latency,
#                     status="success"
#                 )
                
#                 if message_id:
#                     message_ids.append(message_id)
#             except Exception as log_err:
#                 st.warning(f"⚠️ Failed to log complete analysis: {log_err}")
            
#         except Exception as e:
#             end_time = time.time()
#             processing_time = end_time - start_time
            
#             status.update(label="❌ Error occurred", state="error")
            
#             # Log error to Katonic
#             try:
#                 error_query = f"Lead Qualification Error - {input_method.title()}"
#                 message_id = log_request_to_platform(
#                     input_query=error_query,
#                     response=f"Error: {str(e)}",
#                     user_name=user_email,
#                     model_name=config['model'],
#                     product_type="Ace",
#                     product_name="Lead Qualification System",
#                     project_name=project_name,
#                     latency=processing_time,
#                     status="failed"
#                 )
#                 if message_id:
#                     message_ids.append(message_id)
#             except Exception as log_err:
#                 st.warning(f"⚠️ Failed to log error: {log_err}")
            
#             st.error(f"An error occurred: {str(e)}")
#             st.stop()
    
#     # Display Results
#     st.markdown("---")
#     st.markdown("### 📊 AI Analysis Results")
    
#     # Workflow info
#     workflow_html = f"""
#     <div class="agent-workflow">
#         <h4 style="color: #10a37f; margin-top: 0;">🤖 {'Multi-Agent Workflow' if crewai_available else 'AI Analysis'} Completed</h4>
#         <p style="margin: 0;">
#             {'1️⃣ Email Parser Agent - Extracted contact information<br>2️⃣ Company Researcher Agent - Gathered company intelligence<br>3️⃣ Lead Scorer Agent - Calculated qualification score<br>4️⃣ Recommendation Agent - Generated strategic next steps' if crewai_available else '1️⃣ Contact Information Extraction<br>2️⃣ Company Fit Analysis<br>3️⃣ Lead Scoring & Qualification<br>4️⃣ Strategic Recommendations'}
#             <br><br>
#             <em>Powered by Katonic LLM Gateway | Model: {config['model']} | Processing time: {processing_time:.2f}s</em>
#     """
    
#     if message_ids:
#         workflow_html += f"""<br><span class="katonic-badge">🔄 {len(message_ids)} requests logged to Katonic Platform</span>"""
    
#     workflow_html += """
#         </p>
#     </div>
#     """
    
#     st.markdown(workflow_html, unsafe_allow_html=True)
    
#     # Display score if available
#     if parsed_result.get('score') is not None:
#         score = parsed_result['score']
#         qualification = parsed_result.get('qualification', 'Unknown')
        
#         col1, col2, col3, col4 = st.columns(4)
        
#         with col1:
#             if score >= 80:
#                 color = "#059669"
#                 icon = "🎯"
#             elif score >= 50:
#                 color = "#d97706"
#                 icon = "⚠️"
#             else:
#                 color = "#dc2626"
#                 icon = "❌"
            
#             st.markdown(f"""
#             <div style="background: #ffffff; border: 2px solid {color}; padding: 1.5rem; 
#                         border-radius: 1rem; text-align: center; height: 120px; 
#                         display: flex; flex-direction: column; justify-content: center;">
#                 <h3 style="margin: 0; color: {color}; font-size: 1.7rem;">{icon} {score}/100</h3>
#                 <p style="margin: 0; color: {color}; font-weight: 600;">{qualification}</p>
#             </div>
#             """, unsafe_allow_html=True)
        
#         with col2:
#             st.markdown(f"""
#             <div class="score-card">
#                 <h4 style="margin: 0; color: #10a37f;">📧 Input Method</h4>
#                 <p style="margin: 0; color: #10a37f; font-weight: 600;">{input_method.title()}</p>
#             </div>
#             """, unsafe_allow_html=True)
        
#         with col3:
#             priority = "High" if score >= 80 else "Medium" if score >= 50 else "Low"
#             st.markdown(f"""
#             <div class="score-card">
#                 <h4 style="margin: 0; color: #10a37f;">🎯 Priority</h4>
#                 <p style="margin: 0; color: #10a37f; font-weight: 600;">{priority}</p>
#             </div>
#             """, unsafe_allow_html=True)
        
#         with col4:
#             action = "Forward to Sales" if score >= 80 else "Manual Review" if score >= 50 else "Low Priority"
#             st.markdown(f"""
#             <div class="score-card">
#                 <h4 style="margin: 0; color: #10a37f;">✅ Next Action</h4>
#                 <p style="margin: 0; color: #10a37f; font-weight: 600;">{action}</p>
#             </div>
#             """, unsafe_allow_html=True)
        
#         # Score breakdown
#         if parsed_result.get('score_breakdown'):
#             st.markdown("---")
#             st.markdown("### 📈 Detailed Score Breakdown")
            
#             breakdown = parsed_result['score_breakdown']
            
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 if 'email_domain_score' in breakdown:
#                     st.markdown("**📧 Email Domain Score**")
#                     st.progress(breakdown['email_domain_score'] / 20)
#                     st.caption(f"{breakdown['email_domain_score']}/20 - {breakdown.get('email_domain_justification', '')}")
                
#                 if 'company_fit_score' in breakdown:
#                     st.markdown("**🏢 Company Fit Score**")
#                     st.progress(breakdown['company_fit_score'] / 40)
#                     st.caption(f"{breakdown['company_fit_score']}/40 - {breakdown.get('company_fit_justification', '')}")
            
#             with col2:
#                 if 'role_score' in breakdown:
#                     st.markdown("**👤 Contact Role Score**")
#                     st.progress(breakdown['role_score'] / 20)
#                     st.caption(f"{breakdown['role_score']}/20 - {breakdown.get('role_justification', '')}")
                
#                 if 'message_intent_score' in breakdown:
#                     st.markdown("**💭 Message Intent Score**")
#                     st.progress(breakdown['message_intent_score'] / 20)
#                     st.caption(f"{breakdown['message_intent_score']}/20 - {breakdown.get('message_intent_justification', '')}")
    
#     # Recommendations
#     if parsed_result.get('recommendations'):
#         st.markdown("---")
#         st.markdown("### 💡 AI Recommendations")
        
#         recs = parsed_result['recommendations']
#         st.markdown(f"""
#         <div style="background: linear-gradient(135deg, #eff6ff, #dbeafe); padding: 1.5rem; 
#                     border-radius: 1rem; border-left: 4px solid #10a37f;">
#             <p><strong>Next Action:</strong> {recs.get('next_action', 'N/A')}</p>
#             <p><strong>Priority:</strong> {recs.get('priority', 'N/A')}</p>
#             <p><strong>Reasoning:</strong> {recs.get('reasoning', 'N/A')}</p>
#         </div>
#         """, unsafe_allow_html=True)
    
#     # Katonic Logging Summary
#     if message_ids:
#         st.markdown("---")
#         st.markdown("### 📊 Katonic Logging Summary")
        
#         col1, col2, col3 = st.columns(3)
#         with col1:
#             st.metric("Total Requests Logged", len(message_ids))
#         with col2:
#             st.metric("Total Latency", f"{total_latency:.2f}s")
#         with col3:
#             st.metric("Status", "Success ✅")
        
#         with st.expander("📋 View Message IDs"):
#             for idx, msg_id in enumerate(message_ids, 1):
#                 st.code(f"Request {idx}: {msg_id}", language="text")
    
#     # Full output
#     st.markdown("---")
#     with st.expander("📄 View Full Analysis Output"):
#         st.code(parsed_result.get('raw_output', 'No output available'), language="text")
    
#     # Download report
#     st.markdown("---")
    
#     # Build report content
#     katonic_info = f"""
# ## Katonic Configuration
# - **Model ID:** {katonic_model_id[:8]}...
# - **Model Name:** {config['model']}
# - **Requests Logged:** {len(message_ids)}
# - **Message IDs:** {', '.join(message_ids)}
# - **Total Latency:** {total_latency:.2f} seconds
# - **User:** {user_email}
# - **Project:** {project_name}
# """
    
#     report_content = f"""# AI Lead Qualification Report

# **Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# **Request ID:** {request_id}
# **Input Method:** {input_method.title()}
# **Model Used:** {config['model']}
# **Temperature:** {config['temperature']}
# **Processing Time:** {processing_time:.2f} seconds

# ## Configuration
# - **LLM Gateway:** Katonic
# - **Analysis Engine:** {'CrewAI Multi-Agent' if crewai_available else 'Direct Katonic LLM'}
# - **Target Industries:** {', '.join(config['target_config']['industries'])}
# - **Company Sizes:** {', '.join(config['target_config']['company_sizes'])}
# - **Target Regions:** {', '.join(config['target_config']['regions'])}

# ## Score Summary
# - **Total Score:** {parsed_result.get('score', 'N/A')}/100
# - **Qualification:** {parsed_result.get('qualification', 'N/A')}
# - **Priority:** {priority}
# - **Recommended Action:** {action}

# {katonic_info}

# ## Full Analysis
# {parsed_result.get('raw_output', 'No analysis output available')}

# ---
# *Generated by {'CrewAI Lead Qualification System' if crewai_available else 'AI Lead Qualification System'}*
# *Powered by Katonic LLM Gateway - {config['model']}*
# """
    
#     col1, col2 = st.columns(2)
    
#     with col1:
#         st.download_button(
#             label="📥 Download Full Report (Markdown)",
#             data=report_content,
#             file_name=f"lead_qualification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
#             mime="text/markdown",
#             use_container_width=True
#         )
    
#     with col2:
#         # Create JSON export
#         json_export = {
#             "request_id": request_id,
#             "timestamp": datetime.now().isoformat(),
#             "input_method": input_method,
#             "input_data": input_data,
#             "configuration": {
#                 "katonic_model_id": katonic_model_id[:8] + "...",
#                 "model_name": config['model'],
#                 "temperature": config['temperature'],
#                 "target_config": config['target_config'],
#                 "analysis_engine": "crewai" if crewai_available else "direct_katonic"
#             },
#             "results": {
#                 "score": parsed_result.get('score'),
#                 "qualification": parsed_result.get('qualification'),
#                 "priority": priority,
#                 "action": action,
#                 "score_breakdown": parsed_result.get('score_breakdown'),
#                 "recommendations": parsed_result.get('recommendations')
#             },
#             "performance": {
#                 "processing_time_seconds": processing_time,
#                 "total_latency_seconds": total_latency
#             },
#             "katonic_logging": {
#                 "message_ids": message_ids,
#                 "user": user_email,
#                 "project": project_name
#             }
#         }
        
#         st.download_button(
#             label="📥 Download Data (JSON)",
#             data=json.dumps(json_export, indent=2),
#             file_name=f"lead_qualification_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
#             mime="application/json",
#             use_container_width=True
#         )

# # Footer
# st.divider()

# st.markdown(f"""
# <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #f8fafc, #e2e8f0); 
#             border-radius: 1rem; margin: 1rem 0;">
#     <p style="color: #10a37f; font-weight: 600; margin: 0;">
#         Powered by {'<strong>CrewAI</strong> Multi-Agent Framework via ' if crewai_available else ''}<strong>Katonic LLM Gateway</strong>
#     </p>
#     <p style="color: #64748b; font-size: 0.9rem; margin-top: 0.5rem;">
#         Intelligent lead qualification through AI collaboration | Automatic request logging & monitoring
#     </p>
# </div>
# """, unsafe_allow_html=True)
