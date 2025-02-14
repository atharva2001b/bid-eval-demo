import requests
import json
import time
from typing import Dict, List, Optional, Union, Tuple

class OllamaProcessor:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/api/generate"
        self.model = "llama3.2:3b"

    def generate_bid_evaluation(
        self,
        rag_context: Dict[str, str],
        tender_context: Optional[Dict[str, Union[str, List[str]]]] = None
    ) -> str:
        """Generate a structured bid evaluation report."""
        # Combine RAG results into context
        bid_context = "\n\n".join([
            f"Query: {query}\nAnswer: {answer}"
            for query, answer in rag_context.items()
        ])
        
        # Add tender context if available
        tender_prompt = ""
        if tender_context:
            tender_requirements = "\n\n".join([
                f"Requirement {i+1}: {query}\nSpecification: {answer}"
                for i, (query, answer) in enumerate(zip(
                    tender_context['queries'],
                    tender_context['results']
                ))
            ])
            
            tender_prompt = f"""
Given the following tender requirements:
{tender_requirements}

Evaluate this bid proposal against these specific tender requirements. 
Consider the following in your evaluation:
1. How well does the bid meet each technical requirement?
2. Does the bidder meet all eligibility criteria?
3. Are there any compliance gaps?
4. Do the proposed timelines match requirements?
5. Are financial terms aligned with tender specifications?
"""

        # Main evaluation prompt
        prompt = f"""{tender_prompt}
Based on the following bid document analysis:
{bid_context}

Generate a structured evaluation report in the following format, ensuring scores reflect alignment with tender requirements:

### Company Overview
Company Name: [Extract from document]
Submission Date: [Extract from document]
Industry: [Extract from document]

### Evaluation Scores
Each score should be a numeric value between 0-100, with clear justification:
* Technical Score: [0-100] - Based on technical requirements alignment
* Commercial Score: [0-100] - Based on commercial terms alignment
* Compliance Score: [0-100] - Based on mandatory requirements met
* Risk Score: [0-100] - Based on risk assessment
* Overall Score: [0-100] - Weighted average considering all factors

[... Rest of standard sections ...]

### Bid Evaluation Score Table
| Category    | Score | Justification |
|------------|-------|---------------|
| Technical  | [0-100] | Brief reason |
| Commercial | [0-100] | Brief reason |
| Compliance | [0-100] | Brief reason |
| Risk       | [0-100] | Brief reason |
| Overall    | [0-100] | Overall assessment |

Note: Ensure all scores are numeric values and include brief justification based on tender requirements.
"""
        
        # Prepare request payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2048
            }
        }
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_endpoint,
                    json=payload,
                    timeout=300
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('response', '')
                else:
                    print(f"Attempt {attempt + 1}: Request failed with status {response.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    continue
                    
            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1}: Error communicating with Ollama: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                continue
        
        return "Error: Failed to generate bid evaluation after multiple attempts."

    def evaluate_bid(
        self,
        rag_results: List[Tuple[str, str]],
        tender_context: Optional[Dict[str, Union[str, List[str]]]] = None
    ) -> str:
        """Process RAG results and generate evaluation report."""
        rag_context = {query: answer for query, answer in rag_results}
        return self.generate_bid_evaluation(rag_context, tender_context)