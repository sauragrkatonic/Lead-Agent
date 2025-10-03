"""
CrewAI Crew orchestration for lead qualification
"""

from crewai import Crew, Process
from src.agents.lead_agents import create_lead_qualification_agents
from src.tasks.lead_tasks import create_email_tasks, create_form_tasks


def run_email_qualification(sender_email, email_subject, email_content, target_config, model_name="gpt-4o"):
    """
    Run email-based lead qualification with CrewAI
    
    Args:
        sender_email: Email address
        email_subject: Email subject
        email_content: Email content
        target_config: Target criteria
        model_name: OpenAI model to use
        
    Returns:
        CrewAI result object
    """
    
    # Create agents
    agents = create_lead_qualification_agents(model_name)
    
    # Create tasks
    tasks = create_email_tasks(
        agents,
        sender_email,
        email_subject,
        email_content,
        target_config
    )
    
    # Create and run crew
    crew = Crew(
        agents=list(agents.values())[:-1],  # Exclude 'llm' from agents list
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    
    result = crew.kickoff()
    return result


def run_form_qualification(name, company, designation, email, query, target_config, model_name="gpt-4o"):
    """
    Run form-based lead qualification with CrewAI
    
    Args:
        name: Contact name
        company: Company name
        designation: Job title
        email: Email address
        query: Message/query
        target_config: Target criteria
        model_name: OpenAI model to use
        
    Returns:
        CrewAI result object
    """
    
    # Create agents
    agents = create_lead_qualification_agents(model_name)
    
    # Create tasks
    tasks = create_form_tasks(
        agents,
        name,
        company,
        designation,
        email,
        query,
        target_config
    )
    
    # Create and run crew
    crew = Crew(
        agents=list(agents.values())[:-1],  # Exclude 'llm' from agents list
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    
    result = crew.kickoff()
    return result
