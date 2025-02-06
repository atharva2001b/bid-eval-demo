import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from typing import List, Tuple
import nltk
from nltk.tokenize import sent_tokenize


class RAGProcessor:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the RAG processor with FAISS index and sentence transformer.
        
        Args:
            model_name (str): Name of the sentence transformer model to use
        """
        # Download necessary NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        # Initialize the sentence transformer model
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Store sentences for retrieval
        self.sentences = []
        
    def preprocess_text(self, text: str) -> List[str]:
        """
        Preprocess text by splitting it into sentences.
        
        Args:
            text (str): Input text
            
        Returns:
            List[str]: List of sentences
        """
        # Use NLTK for better sentence tokenization
        sentences = sent_tokenize(text)
        return [sent.strip() for sent in sentences if sent.strip()]
    
    def create_sentence_windows(self, sentences: List[str], window_size: int = 2) -> List[str]:
        """
        Create overlapping windows of sentences for better context.
        
        Args:
            sentences (List[str]): List of sentences
            window_size (int): Number of sentences before and after for context
            
        Returns:
            List[str]: List of sentence windows
        """
        windows = []
        for i in range(len(sentences)):
            start = max(0, i - window_size)
            end = min(len(sentences), i + window_size + 1)
            window = ' '.join(sentences[start:end])
            windows.append(window)
        return windows
    
    def index_text(self, text: str, window_size: int = 2):
        """
        Index the text using FAISS.
        
        Args:
            text (str): Input text to index
            window_size (int): Size of context window
        """
        # Reset index and sentences
        self.index = faiss.IndexFlatL2(self.dimension)
        self.sentences = []
        
        # Preprocess text and create windows
        sentences = self.preprocess_text(text)
        windows = self.create_sentence_windows(sentences, window_size)
        self.sentences = windows
        
        # Create embeddings and add to index
        embeddings = self.model.encode(windows, convert_to_tensor=True)
        embeddings_np = embeddings.cpu().numpy()
        self.index.add(embeddings_np)
    
    def retrieve_context(self, query: str, k: int = 3) -> List[Tuple[str, float]]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query (str): Query string
            k (int): Number of contexts to retrieve
            
        Returns:
            List[Tuple[str, float]]: List of (context, score) pairs
        """
        # Encode query
        query_embedding = self.model.encode([query], convert_to_tensor=True)
        query_embedding_np = query_embedding.cpu().numpy()
        
        # Search in FAISS index
        distances, indices = self.index.search(query_embedding_np, k)
        
        # Get relevant contexts with scores
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.sentences):
                score = 1 / (1 + dist)  # Convert distance to similarity score
                results.append((self.sentences[idx], float(score)))
        
        return sorted(results, key=lambda x: x[1], reverse=True)

def process_queries(text_file: str, queries: List[str]) -> List[str]:
    """
    Process a list of queries against the given text file and return answers.
    
    Args:
        text_file (str): Path to the text file
        queries (list): List of query strings
    
    Returns:
        list: List of answers corresponding to each query
    """
    try:
        # Read the text file
        with open(text_file, 'r') as f:
            text = f.read()
            
        # Initialize and index text
        processor = RAGProcessor()
        processor.index_text(text)
        
        # Process each query
        answers = []
        for query in queries:
            # Get relevant contexts with scores
            contexts = processor.retrieve_context(query, k=2)
            
            # Format answer with context and confidence
            if contexts:
                # Get the best context and its score
                best_context, score = contexts[0]
                answer = f"[Confidence: {score:.2f}] {best_context}"
                
                # Add supporting context if available
                if len(contexts) > 1:
                    support_context, support_score = contexts[1]
                    if support_score > 0.5:  # Only add if somewhat relevant
                        answer += f"\nSupporting context: {support_context}"
            else:
                answer = "No relevant context found for this query."
                
            answers.append(answer)
            
        return answers
        
    except FileNotFoundError:
        return ["Error: Text file not found."] * len(queries)
    except Exception as e:
        return [f"Error processing queries: {str(e)}"] * len(queries)