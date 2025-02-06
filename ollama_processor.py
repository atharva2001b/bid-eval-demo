import requests
import json
import time

class OllamaProcessor:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/api/generate"
        self.model = "llama3.2:3b"  # Specifically using llama2 3b model
        
    def generate_bid_evaluation(self, rag_context):
        """
        Generate a bid evaluation report using Ollama with RAG context.
        
        Args:
            rag_context (dict): Dictionary containing RAG query results
            
        Returns:
            str: Generated bid evaluation report in markdown format
        """
        # Combine all RAG results into a single context string
        context = "\n\n".join([
            f"Query: {query}\nAnswer: {answer}"
            for query, answer in rag_context.items()
        ])
        
        # Construct the prompt - keeping it simpler for the 3B model
        prompt = f"""
Context from document analysis:
{context}

Using the above context, create a bid evaluation report in markdown format. Include:
1. Company Overview
2. Technical Assessment
3. Commercial Terms
4. Risk Analysis
5. Final Score (0-100)

Keep the response clear and concise.
"""
        
        # Prepare the request payload
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
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Make the API call to Ollama
                response = requests.post(
                    self.api_endpoint, 
                    json=payload,
                    timeout=300  # Adding timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('response', '')
                else:
                    print(f"Attempt {attempt + 1}: Request failed with status {response.status_code}")
                    print(f"Response content: {response.text}")
                    
                    if attempt < max_retries - 1:
                        print(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    continue
                    
            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1}: Error communicating with Ollama: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                continue
        
        return "Error: Failed to generate bid evaluation after multiple attempts. Please check if Ollama is running correctly with the llama2:3b model."
        
    def evaluate_bid(self, rag_results):
        """
        Process RAG results and generate bid evaluation report.
        
        Args:
            rag_results (list): List of tuples containing (query, answer) pairs
            
        Returns:
            str: Generated bid evaluation report
        """
        # Convert RAG results to dictionary format
        rag_context = {
            query: answer for query, answer in rag_results
        }
        
        # Generate the evaluation report
        evaluation_report = self.generate_bid_evaluation(rag_context)
        
        return evaluation_report