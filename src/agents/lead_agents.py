"""
Define all CrewAI agents for lead qualification
"""

from crewai import Agent
from langchain_openai import ChatOpenAI


def create_lead_qualification_agents(model_name="gpt-4o"):
    """
    Create all agents needed for lead qualification
    
    Returns:
        dict: Dictionary of agent instances
    """
    
    llm = ChatOpenAI(model=model_name, temperature=0.3)
    
    email_parser = Agent(
        role='Email Information Extractor',
        goal='Extract all relevant contact and company information from email content',
        backstory='You are an expert at parsing emails and extracting structured data. '
                  'You can identify names, companies, job titles, and intent from email text. '
                  'You always return information in a clear, structured format.',
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
    
    company_researcher = Agent(
        role='Company Research Specialist',
        goal='Research and gather detailed information about companies including industry, size, and location',
        backstory='You are a business intelligence expert who can infer company details from domains '
                  'and email information. You understand business classifications, market segments, '
                  'and can estimate company size from context clues.',
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
    
    lead_scorer = Agent(
        role='Lead Qualification Specialist',
        goal='Score leads based on email quality, company fit, role seniority, and message intent',
        backstory='You are an experienced sales qualification expert who can assess lead quality. '
                  'You understand buyer personas, decision-making hierarchies, and sales readiness signals. '
                  'You follow strict scoring rubrics and provide detailed justifications.',
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
    
    recommendation_agent = Agent(
        role='Sales Strategy Advisor',
        goal='Provide actionable recommendations for engaging with leads based on their qualification score',
        backstory='You are a senior sales strategist who advises on lead engagement tactics. '
                  'You know when to prioritize, nurture, or disqualify leads. '
                  'Your recommendations are specific, actionable, and tied to business outcomes.',
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
    
    return {
        'email_parser': email_parser,
        'company_researcher': company_researcher,
        'lead_scorer': lead_scorer,
        'recommendation_agent': recommendation_agent,
        'llm': llm
    }
