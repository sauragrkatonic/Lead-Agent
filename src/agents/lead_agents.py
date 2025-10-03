"""
Define all CrewAI agents for lead qualification with Katonic LLM integration
"""

from crewai import Agent
from katonic.llm import generate_completion
from katonic.llm.log_requests import log_request_to_platform
import time


class KatonicLLMWrapper:
    """
    Custom LLM wrapper for Katonic to integrate with CrewAI agents
    """
    
    def __init__(self, model_id, user_email, project_name, model_name, temperature=0.3):
        self.model_id = model_id
        self.user_email = user_email
        self.project_name = project_name
        self.model_name = model_name
        self.temperature = temperature
    
    def generate_completion(self, prompt):
        """
        Generate completion using Katonic LLM with logging
        """
        start_time = time.time()
        try:
            response = generate_completion(
                model_id=self.model_id,
                data={"query": prompt}
            )
            
            latency = time.time() - start_time
            
            # Log the request
            try:
                log_request_to_platform(
                    input_query=prompt[:500],  # Limit query length for logging
                    response=response[:500],   # Limit response length for logging
                    user_name=self.user_email,
                    model_name=self.model_name,
                    product_type="Ace",
                    product_name="Lead Qualification System",
                    project_name=self.project_name,
                    latency=latency,
                    status="success"
                )
            except Exception as log_error:
                print(f"Logging warning: {log_error}")
            
            return response
            
        except Exception as e:
            latency = time.time() - start_time
            # Log error
            try:
                log_request_to_platform(
                    input_query=prompt[:500],
                    response=f"Error: {str(e)}",
                    user_name=self.user_email,
                    model_name=self.model_name,
                    product_type="Ace",
                    product_name="Lead Qualification System",
                    project_name=self.project_name,
                    latency=latency,
                    status="failed"
                )
            except:
                pass
            raise e
    
    def __call__(self, messages):
        """
        Convert CrewAI message format to Katonic completion call
        """
        # Convert messages to a single prompt
        prompt = self._format_messages(messages)
        return self.generate_completion(prompt)
    
    def _format_messages(self, messages):
        """
        Format CrewAI messages into a single prompt string
        """
        formatted_text = ""
        for message in messages:
            if hasattr(message, 'content'):
                content = message.content
            else:
                content = str(message)
            
            if hasattr(message, 'role'):
                role = message.role
                formatted_text += f"{role.upper()}: {content}\n\n"
            else:
                formatted_text += f"{content}\n\n"
        
        return formatted_text.strip()


def create_lead_qualification_agents(model_id, user_email, project_name, model_name, temperature=0.3):
    """
    Create all agents needed for lead qualification using Katonic LLM
    
    Args:
        model_id (str): Katonic model ID from My Model Library
        user_email (str): User email for logging
        project_name (str): Project name for logging
        model_name (str): Model name for logging
        temperature (float): Model temperature
    
    Returns:
        dict: Dictionary of agent instances and LLM wrapper
    """
    
    # Initialize Katonic LLM wrapper
    katonic_llm = KatonicLLMWrapper(
        model_id=model_id,
        user_email=user_email,
        project_name=project_name,
        model_name=model_name,
        temperature=temperature
    )
    
    email_parser = Agent(
        role='Email Information Extractor',
        goal='Extract all relevant contact and company information from email content',
        backstory='You are an expert at parsing emails and extracting structured data. '
                  'You can identify names, companies, job titles, and intent from email text. '
                  'You always return information in a clear, structured format.',
        llm=katonic_llm,
        verbose=True,
        allow_delegation=False
    )
    
    company_researcher = Agent(
        role='Company Research Specialist',
        goal='Research and gather detailed information about companies including industry, size, and location',
        backstory='You are a business intelligence expert who can infer company details from domains '
                  'and email information. You understand business classifications, market segments, '
                  'and can estimate company size from context clues.',
        llm=katonic_llm,
        verbose=True,
        allow_delegation=False
    )
    
    lead_scorer = Agent(
        role='Lead Qualification Specialist',
        goal='Score leads based on email quality, company fit, role seniority, and message intent',
        backstory='You are an experienced sales qualification expert who can assess lead quality. '
                  'You understand buyer personas, decision-making hierarchies, and sales readiness signals. '
                  'You follow strict scoring rubrics and provide detailed justifications.',
        llm=katonic_llm,
        verbose=True,
        allow_delegation=False
    )
    
    recommendation_agent = Agent(
        role='Sales Strategy Advisor',
        goal='Provide actionable recommendations for engaging with leads based on their qualification score',
        backstory='You are a senior sales strategist who advises on lead engagement tactics. '
                  'You know when to prioritize, nurture, or disqualify leads. '
                  'Your recommendations are specific, actionable, and tied to business outcomes.',
        llm=katonic_llm,
        verbose=True,
        allow_delegation=False
    )
    
    return {
        'email_parser': email_parser,
        'company_researcher': company_researcher,
        'lead_scorer': lead_scorer,
        'recommendation_agent': recommendation_agent,
        'llm': katonic_llm
    }
# """
# Define all CrewAI agents for lead qualification
# """

# from crewai import Agent
# from langchain_openai import ChatOpenAI
# #from langchain_groq import ChatGroq


# def create_lead_qualification_agents(model_name="gpt-4o"):
#     """
#     Create all agents needed for lead qualification
    
#     Returns:
#         dict: Dictionary of agent instances
#     """
    
#     llm = ChatOpenAI(model=model_name, temperature=0.3)
    
#     email_parser = Agent(
#         role='Email Information Extractor',
#         goal='Extract all relevant contact and company information from email content',
#         backstory='You are an expert at parsing emails and extracting structured data. '
#                   'You can identify names, companies, job titles, and intent from email text. '
#                   'You always return information in a clear, structured format.',
#         llm=llm,
#         verbose=True,
#         allow_delegation=False
#     )
    
#     company_researcher = Agent(
#         role='Company Research Specialist',
#         goal='Research and gather detailed information about companies including industry, size, and location',
#         backstory='You are a business intelligence expert who can infer company details from domains '
#                   'and email information. You understand business classifications, market segments, '
#                   'and can estimate company size from context clues.',
#         llm=llm,
#         verbose=True,
#         allow_delegation=False
#     )
    
#     lead_scorer = Agent(
#         role='Lead Qualification Specialist',
#         goal='Score leads based on email quality, company fit, role seniority, and message intent',
#         backstory='You are an experienced sales qualification expert who can assess lead quality. '
#                   'You understand buyer personas, decision-making hierarchies, and sales readiness signals. '
#                   'You follow strict scoring rubrics and provide detailed justifications.',
#         llm=llm,
#         verbose=True,
#         allow_delegation=False
#     )
    
#     recommendation_agent = Agent(
#         role='Sales Strategy Advisor',
#         goal='Provide actionable recommendations for engaging with leads based on their qualification score',
#         backstory='You are a senior sales strategist who advises on lead engagement tactics. '
#                   'You know when to prioritize, nurture, or disqualify leads. '
#                   'Your recommendations are specific, actionable, and tied to business outcomes.',
#         llm=llm,
#         verbose=True,
#         allow_delegation=False
#     )
    
#     return {
#         'email_parser': email_parser,
#         'company_researcher': company_researcher,
#         'lead_scorer': lead_scorer,
#         'recommendation_agent': recommendation_agent,
#         'llm': llm
#     }
