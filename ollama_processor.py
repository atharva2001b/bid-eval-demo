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
        """
        Generate a structured bid evaluation report using Ollama with RAG context 
        and tender requirements.
        
        Args:
            rag_context: Dict of query-answer pairs from bid document analysis
            tender_context: Optional dict containing tender document analysis
        
        Returns:
            str: Generated evaluation report
        """
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
1. Technical Alignment: How well does the bid meet each technical requirement?
2. Eligibility Compliance: Does the bidder meet all eligibility criteria?
3. Mandatory Requirements: Are all mandatory requirements satisfied?
4. Timeline Compatibility: Do the proposed timelines align with requirements?
5. Financial Terms: Are financial terms and pricing aligned with specifications?
6. Risk Assessment: What are the potential risks in terms of compliance?

For scoring, use the following criteria:
- Technical Score: Based on meeting technical specifications and requirements
- Commercial Score: Based on pricing, payment terms, and commercial viability
- Compliance Score: Based on meeting mandatory and regulatory requirements
- Risk Score: Based on identified risks and mitigation measures
- Overall Score: Weighted average considering all aspects
"""
        
        # Structured prompt template
        prompt = f"""{tender_prompt}
Based on the following bid document analysis:
{bid_context}

Generate a detailed bid evaluation report in the following structured markdown format.
Use '###' for main sections and include ALL the sections below:

### Company Overview
Company Name: [Extract or infer company name]
Submission Date: [Extract or infer date]
Industry: [Extract or infer industry]

### Scores
- Technical Score: [0-100] - Score based on meeting technical requirements
- Commercial Score: [0-100] - Score based on pricing and commercial terms
- Compliance Score: [0-100] - Score based on meeting mandatory requirements
- Risk Score: [0-100] - Score based on identified risks
- Overall Score: [0-100] - Weighted average of all scores

### Tender Compliance
- [List specific areas where bid meets tender requirements]
- [List any gaps or deviations from tender requirements]
- [Evaluate alignment with mandatory criteria]
- [Assess technical specification compliance]

### Key Strengths
- [List 3-5 key strengths with bullet points]
- [Focus on areas of strong alignment with tender]
- [Highlight unique value propositions]

### Areas for Improvement
- [List 3-5 weaknesses or areas needing improvement]
- [Identify gaps in tender requirement coverage]
- [Note any unclear or incomplete responses]

### Risk Analysis
Risk Level: [High/Medium/Low]
Key Risk Factors:
- [List specific risk factors related to tender compliance]
- [Identify technical and operational risks]
- [Note any commercial or financial risks]

### Commercial Terms
Pricing Details: [Specify pricing structure/amount]
Payment Terms: [Specify payment terms]
Delivery Timeline: [Specify delivery timeline]
- [Compare with tender requirements]
- [Note any deviations]

### Technical Compliance
Standards Met:
- [List technical standards/requirements met]
- [Compare with tender specifications]

Areas of Non-compliance:
- [List any technical gaps]
- [Identify missing requirements]

### Recommendations
- [Provide specific recommendations for improved compliance]
- [Suggest risk mitigation measures]
- [Note areas requiring clarification]

### Final Assessment
[Provide comprehensive evaluation of tender alignment]
[Summarize key decision factors]
[Make clear recommendation based on tender requirements]

Ensure all scores are numerical values between 0-100 and maintain consistent formatting throughout.
Score based on specific alignment with tender requirements where available.
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
        """
        Process RAG results and generate bid evaluation report.
        
        Args:
            rag_results: List of (query, answer) tuples from bid document analysis
            tender_context: Optional dict containing tender document analysis
        
        Returns:
            str: Generated evaluation report
        """
        rag_context = {query: answer for query, answer in rag_results}
        return self.generate_bid_evaluation(rag_context, tender_context)