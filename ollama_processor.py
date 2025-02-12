import requests
import json
import time

class OllamaProcessor:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/api/generate"
        self.model = "llama3.2:3b"

    def generate_bid_evaluation(self, rag_context):
        """Generate a structured bid evaluation report using Ollama with RAG context."""
        # Combine RAG results into context
        context = "\n\n".join([
            f"Query: {query}\nAnswer: {answer}"
            for query, answer in rag_context.items()
        ])
        
        # Structured prompt template
        prompt = f"""
Based on the following context from document analysis:
{context}

Generate a detailed bid evaluation report in the following structured markdown format. 
Use '###' for main sections and include ALL the sections below:

### Company Overview
Company Name: [Extract or infer company name]
Submission Date: [Extract or infer date]
Industry: [Extract or infer industry]

### Scores
- Technical Score: [0-100]
- Commercial Score: [0-100]
- Compliance Score: [0-100]
- Risk Score: [0-100]
- Overall Score: [0-100]

### Key Strengths
- [List 3-5 key strengths with bullet points]

### Areas for Improvement
- [List 3-5 weaknesses or areas needing improvement with bullet points]

### Risk Analysis
Risk Level: [High/Medium/Low]
Key Risk Factors:
- [List 3-5 specific risk factors with bullet points]

### Commercial Terms
Pricing Details: [Specify pricing structure/amount]
Payment Terms: [Specify payment terms]
Delivery Timeline: [Specify delivery timeline]

### Technical Compliance
Standards Met:
- [List key technical standards/requirements met]

Areas of Non-compliance:
- [List any technical gaps or non-compliance]

### Recommendations
- [List 2-3 specific recommendations]

### Final Assessment
[2-3 sentences summarizing the overall evaluation and recommendation]

Ensure all scores are numerical values between 0-100 and maintain consistent formatting throughout.
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

    def evaluate_bid(self, rag_results):
        """Process RAG results and generate bid evaluation report."""
        rag_context = {query: answer for query, answer in rag_results}
        return self.generate_bid_evaluation(rag_context)