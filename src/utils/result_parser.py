"""
Parse CrewAI results into structured format
"""

import json
import re


def parse_crew_result(result):
    """
    Parse CrewAI crew result into structured dictionary
    
    Args:
        result: CrewAI crew execution result
        
    Returns:
        dict: Parsed and structured result
    """
    
    result_text = str(result)
    
    # Try to extract JSON from the result
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    json_matches = re.findall(json_pattern, result_text, re.DOTALL)
    
    parsed_data = {
        'raw_output': result_text,
        'parsed_json': [],
        'score': None,
        'qualification': None,
        'recommendations': None
    }
    
    for match in json_matches:
        try:
            json_obj = json.loads(match)
            parsed_data['parsed_json'].append(json_obj)
            
            # Extract score if present
            if 'total_score' in json_obj:
                parsed_data['score'] = json_obj['total_score']
                parsed_data['score_breakdown'] = json_obj
            
            # Extract qualification
            if 'qualification_status' in json_obj:
                parsed_data['qualification'] = json_obj['qualification_status']
            
            # Extract recommendations
            if 'next_action' in json_obj:
                parsed_data['recommendations'] = json_obj
                
        except json.JSONDecodeError:
            continue
    
    return parsed_data
