"""
Define all CrewAI tasks for lead qualification workflows
"""

from crewai import Task


def create_email_tasks(agents, sender_email, email_subject, email_content, target_config):
    """
    Create tasks for email-based lead qualification
    
    Args:
        agents: Dictionary of agent instances
        sender_email: Email address
        email_subject: Email subject line
        email_content: Full email content
        target_config: Target criteria configuration
        
    Returns:
        list: List of Task instances
    """
    
    parse_task = Task(
        description=f"""
        Extract the following information from this email:
        - Sender Email: {sender_email}
        - Subject: {email_subject}
        - Content: {email_content}
        
        Extract and return in JSON format:
        {{
            "sender_name": "Full name if found",
            "company_name": "Company name if mentioned or inferred",
            "designation": "Job title if mentioned",
            "domain": "Email domain",
            "intent": "Main purpose of the email"
        }}
        """,
        agent=agents['email_parser'],
        expected_output='JSON object with sender_name, company_name, designation, domain, and intent'
    )
    
    research_task = Task(
        description=f"""
        Based on the parsed email information, research and infer company details.
        
        Return in JSON format:
        {{
            "industry": "One of: Technology, Healthcare, Finance, Manufacturing, Retail, Education, Consulting, Real Estate, Other",
            "company_size": "One of: Startup (1-50), SMB (51-500), Enterprise (500+)",
            "location": "Geographic region",
            "domain_type": "business or personal"
        }}
        
        If the email domain is generic (gmail, yahoo, hotmail, outlook), set domain_type to "personal"
        and note that company information may be limited.
        """,
        agent=agents['company_researcher'],
        expected_output='JSON with industry, company_size, location, and domain_type',
        context=[parse_task]
    )
    
    score_task = Task(
        description=f"""
        Score this lead using the following rubric (100 points total):
        
        Target Criteria:
        - Target Industries: {', '.join(target_config['industries'])}
        - Target Company Sizes: {', '.join(target_config['company_sizes'])}
        - Target Regions: {', '.join(target_config['regions'])}
        
        Scoring Rubric:
        
        1. Email Domain Score (20 points):
           - Business email domain: 20 points
           - Generic email but company mentioned: 10 points
           - Generic email only: 0 points
        
        2. Company Fit Score (40 points):
           - Industry matches target: 20 points
           - Company size matches target: 10 points
           - Location matches target region: 10 points
        
        3. Contact Role Score (20 points):
           - C-level, VP, Director: 20 points
           - Manager, Lead, Specialist: 10 points
           - No clear role or junior: 0 points
        
        4. Message Intent Score (20 points):
           - Specific interest with clear need: 20 points
           - General inquiry: 10 points
           - Vague or spam-like: 0 points
        
        Return in JSON format:
        {{
            "total_score": 0-100,
            "email_domain_score": 0-20,
            "email_domain_justification": "explanation",
            "company_fit_score": 0-40,
            "company_fit_justification": "explanation",
            "role_score": 0-20,
            "role_justification": "explanation",
            "message_intent_score": 0-20,
            "message_intent_justification": "explanation",
            "qualification_status": "Qualified/Needs Review/Unqualified"
        }}
        """,
        agent=agents['lead_scorer'],
        expected_output='JSON with total_score, breakdown, and qualification_status',
        context=[parse_task, research_task]
    )
    
    recommendation_task = Task(
        description=f"""
        Based on the lead score and analysis, provide recommendations.
        
        Return in JSON format:
        {{
            "next_action": "Forward to Sales / Manual Review / Disqualify",
            "priority": "High / Medium / Low",
            "reasoning": "Detailed explanation",
            "talking_points": ["point 1", "point 2"],
            "concerns": ["concern 1", "concern 2"]
        }}
        """,
        agent=agents['recommendation_agent'],
        expected_output='JSON with next_action, priority, reasoning, talking_points, and concerns',
        context=[parse_task, research_task, score_task]
    )
    
    return [parse_task, research_task, score_task, recommendation_task]


def create_form_tasks(agents, name, company, designation, email, query, target_config):
    """
    Create tasks for form-based lead qualification
    
    Args:
        agents: Dictionary of agent instances
        name: Contact name
        company: Company name
        designation: Job title
        email: Email address
        query: Message/query
        target_config: Target criteria configuration
        
    Returns:
        list: List of Task instances
    """
    
    structure_task = Task(
        description=f"""
        Structure the following form submission data:
        - Name: {name}
        - Company: {company}
        - Designation: {designation or 'Not provided'}
        - Email: {email}
        - Query: {query}
        
        Extract and return in JSON format:
        {{
            "sender_name": "{name}",
            "company_name": "{company}",
            "designation": "{designation or 'Not provided'}",
            "email": "{email}",
            "domain": "extracted domain",
            "domain_type": "business or personal",
            "intent": "classified intent from query"
        }}
        """,
        agent=agents['email_parser'],
        expected_output='JSON with structured form data and analysis'
    )
    
    research_task = Task(
        description=f"""
        Based on company name "{company}" and email domain, infer company details.
        
        Return in JSON format with industry, company_size, location, and any additional insights.
        """,
        agent=agents['company_researcher'],
        expected_output='JSON with company intelligence',
        context=[structure_task]
    )
    
    score_task = Task(
        description=f"""
        Score this lead using the 100-point rubric.
        
        Target Criteria:
        - Target Industries: {', '.join(target_config['industries'])}
        - Target Company Sizes: {', '.join(target_config['company_sizes'])}
        - Target Regions: {', '.join(target_config['regions'])}
        
        Return complete scoring breakdown in JSON format.
        """,
        agent=agents['lead_scorer'],
        expected_output='JSON with complete scoring breakdown',
        context=[structure_task, research_task]
    )
    
    recommendation_task = Task(
        description=f"""
        Provide actionable recommendations based on the qualification score.
        
        Return in JSON format with next_action, priority, reasoning, and specific recommendations.
        """,
        agent=agents['recommendation_agent'],
        expected_output='JSON with recommendations',
        context=[structure_task, research_task, score_task]
    )
    
    return [structure_task, research_task, score_task, recommendation_task]
