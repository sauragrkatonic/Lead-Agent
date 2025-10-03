"""
CrewAI Crew orchestration for lead qualification with Katonic integration
"""

from crewai import Crew, Process
from src.agents.lead_agents import create_lead_qualification_agents
from src.tasks.lead_tasks import create_email_tasks, create_form_tasks


def run_email_qualification(sender_email, email_subject, email_content, target_config, 
                          model_id, user_email, project_name, model_name, temperature=0.3):
    """
    Run email-based lead qualification with CrewAI using Katonic LLM
    
    Args:
        sender_email: Email address
        email_subject: Email subject
        email_content: Email content
        target_config: Target criteria
        model_id: Katonic model ID from My Model Library
        user_email: User email for logging
        project_name: Project name for logging
        model_name: Model name for logging
        temperature: Model temperature
        
    Returns:
        CrewAI result object
    """
    
    # Create agents with Katonic integration
    agents = create_lead_qualification_agents(
        model_id=model_id,
        user_email=user_email,
        project_name=project_name,
        model_name=model_name,
        temperature=temperature
    )
    
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
        agents=[agents['email_parser'], agents['company_researcher'], agents['lead_scorer'], agents['recommendation_agent']],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    
    result = crew.kickoff()
    return result


def run_form_qualification(name, company, designation, email, query, target_config,
                         model_id, user_email, project_name, model_name, temperature=0.3):
    """
    Run form-based lead qualification with CrewAI using Katonic LLM
    
    Args:
        name: Contact name
        company: Company name
        designation: Job title
        email: Email address
        query: Message/query
        target_config: Target criteria
        model_id: Katonic model ID from My Model Library
        user_email: User email for logging
        project_name: Project name for logging
        model_name: Model name for logging
        temperature: Model temperature
        
    Returns:
        CrewAI result object
    """
    
    # Create agents with Katonic integration
    agents = create_lead_qualification_agents(
        model_id=model_id,
        user_email=user_email,
        project_name=project_name,
        model_name=model_name,
        temperature=temperature
    )
    
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
        agents=[agents['email_parser'], agents['company_researcher'], agents['lead_scorer'], agents['recommendation_agent']],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    
    result = crew.kickoff()
    return result


# Simple wrapper for the Streamlit app
def run_email_qualification_simple(sender_email, email_subject, email_content, target_config, 
                                 model_id, user_email, project_name, model_name):
    """
    Simplified version for Streamlit app
    """
    try:
        return run_email_qualification(
            sender_email=sender_email,
            email_subject=email_subject,
            email_content=email_content,
            target_config=target_config,
            model_id=model_id,
            user_email=user_email,
            project_name=project_name,
            model_name=model_name,
            temperature=0.3
        )
    except Exception as e:
        raise e


def run_form_qualification_simple(name, company, designation, email, query, target_config,
                                model_id, user_email, project_name, model_name):
    """
    Simplified version for Streamlit app
    """
    try:
        return run_form_qualification(
            name=name,
            company=company,
            designation=designation,
            email=email,
            query=query,
            target_config=target_config,
            model_id=model_id,
            user_email=user_email,
            project_name=project_name,
            model_name=model_name,
            temperature=0.3
        )
    except Exception as e:
        raise e
# """
# CrewAI Crew orchestration for lead qualification
# """

# from crewai import Crew, Process
# from src.agents.lead_agents import create_lead_qualification_agents
# from src.tasks.lead_tasks import create_email_tasks, create_form_tasks


# def run_email_qualification(sender_email, email_subject, email_content, target_config, model_name="gpt-4o"):
#     """
#     Run email-based lead qualification with CrewAI
    
#     Args:
#         sender_email: Email address
#         email_subject: Email subject
#         email_content: Email content
#         target_config: Target criteria
#         model_name: OpenAI model to use
        
#     Returns:
#         CrewAI result object
#     """
    
#     # Create agents
#     agents = create_lead_qualification_agents(model_name)
    
#     # Create tasks
#     tasks = create_email_tasks(
#         agents,
#         sender_email,
#         email_subject,
#         email_content,
#         target_config
#     )
    
#     # Create and run crew
#     crew = Crew(
#         agents=list(agents.values())[:-1],  # Exclude 'llm' from agents list
#         tasks=tasks,
#         process=Process.sequential,
#         verbose=True
#     )
    
#     result = crew.kickoff()
#     return result

# #llama
# def run_form_qualification(name, company, designation, email, query, target_config, model_name="gpt-4o"):
#     """
#     Run form-based lead qualification with CrewAI
    
#     Args:
#         name: Contact name
#         company: Company name
#         designation: Job title
#         email: Email address
#         query: Message/query
#         target_config: Target criteria
#         model_name: OpenAI model to use
        
#     Returns:
#         CrewAI result object
#     """
    
#     # Create agents
#     agents = create_lead_qualification_agents(model_name)
    
#     # Create tasks
#     tasks = create_form_tasks(
#         agents,
#         name,
#         company,
#         designation,
#         email,
#         query,
#         target_config
#     )
    
#     # Create and run crew
#     crew = Crew(
#         agents=list(agents.values())[:-1],  # Exclude 'llm' from agents list
#         tasks=tasks,
#         process=Process.sequential,
#         verbose=True
#     )
    
#     result = crew.kickoff()
#     return result
