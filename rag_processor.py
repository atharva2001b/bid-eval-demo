import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from typing import List, Tuple
import nltk
from nltk.tokenize import sent_tokenize
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
import re
from functools import lru_cache

class RAGProcessor:
    def __init__(self, model_name: str = 'multi-qa-mpnet-base-dot-v1'):
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
        
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dimension)
        
        self.tokenizer = RegexpTokenizer(r'\w+')
        self.stopwords = set(stopwords.words('english'))
        self.sentences = []
        self.original_sentences = []
        self.embeddings_cache = {}
        
    def clean_text(self, text: str) -> str:
        text = re.sub(r'[^a-zA-Z0-9\s.:\-()]', ' ', text)
        text = ' '.join(text.split())
        return text
        
    @lru_cache(maxsize=1024)
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text with caching."""
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
            
        embedding = self.model.encode(text, convert_to_tensor=True)
        embedding_np = embedding.cpu().numpy()
        self.embeddings_cache[text] = embedding_np
        return embedding_np

    def normalize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """Normalize embeddings to unit length for cosine similarity."""
        faiss.normalize_L2(embeddings)
        return embeddings
        
    def preprocess_text(self, file_path: str) -> List[str]:
        # Read the content of the file
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        # Split the text into sections based on specific patterns
        sections = re.split(r'\n(?=\d+\.|\[|Section\s+\d+:|#)', text)
        
        processed_sentences = []
        original_sentences = []
        
        for section in sections:
            if not section.strip():
                continue
                
            section_sentences = sent_tokenize(section)
            
            for sent in section_sentences:
                cleaned = self.clean_text(sent)
                if len(cleaned) > 10:
                    words = self.tokenizer.tokenize(cleaned)
                    if len(words) > 3:
                        processed_sentences.append(cleaned)
                        original_sentences.append(sent.strip())
        
        self.original_sentences = original_sentences
        return processed_sentences
    
    def create_sentence_windows(self, sentences: List[str], window_size: int = 3) -> List[str]:
        windows = []
        original_windows = []
        
        for i in range(len(sentences)):
            current_section = re.match(r'^\d+\.|\[|Section\s+\d+:|#', sentences[i])
            
            start = max(0, i - window_size)
            end = min(len(sentences), i + window_size + 1)
            
            if current_section:
                start = i
            
            window_sentences = []
            for j in range(start, end):
                weight = 1.0 / (1 + abs(i - j))
                if re.match(r'^\d+\.|\[|Section\s+\d+:|#', sentences[j]):
                    weight *= 1.5
                window_sentences.append(sentences[j])
            
            window = ' '.join(window_sentences)
            windows.append(window)
            original_windows.append(' '.join([self.original_sentences[j] for j in range(start, end)]))
        
        self.sentences = original_windows
        return windows
    
    def index_text(self, text: str, window_size: int = 3):
        self.sentences = []
        self.embeddings_cache = {}
        
        sentences = self.preprocess_text(text)
        windows = self.create_sentence_windows(sentences, window_size)
        
        batch_size = 32
        all_embeddings = []
        
        for i in range(0, len(windows), batch_size):
            batch = windows[i:i + batch_size]
            embeddings = self.model.encode(batch, convert_to_tensor=True)
            normalized_embeddings = self.normalize_embeddings(embeddings.cpu().numpy())
            all_embeddings.append(normalized_embeddings)
        
        embeddings_np = np.vstack(all_embeddings)
        self.index.add(embeddings_np)
    
    def retrieve_context(self, query: str, k: int = 3) -> List[Tuple[str, float]]:
        clean_query = self.clean_text(query)
        query_embedding = self.get_embedding(clean_query)
        query_embedding = self.normalize_embeddings(query_embedding.reshape(1, -1))
        
        scores, indices = self.index.search(query_embedding, k * 2)
        
        results = []
        seen_content = set()
        
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.sentences):
                context = self.sentences[idx]
                content_hash = hash(context)
                
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    normalized_score = (score + 1) / 2
                    
                    if normalized_score > 0.5:
                        results.append((context, float(normalized_score)))
        
        return sorted(results, key=lambda x: x[1], reverse=True)[:k]

def process_queries(text: str, queries: List[str]) -> List[str]:
    """Process queries with text content directly instead of file."""
    try:
        processor = RAGProcessor()
        processor.index_text(text)
        
        answers = []
        for query in queries:
            contexts = processor.retrieve_context(query, k=2)
            
            if contexts:
                best_context, score = contexts[0]
                answer = f"[Confidence: {score:.2f}] {best_context}"
                
                if len(contexts) > 1:
                    support_context, support_score = contexts[1]
                    if support_score > 0.5:
                        answer += f"\nSupporting context [{support_score:.2f}]: {support_context}"
            else:
                answer = "No relevant context found for this query."
                
            answers.append(answer)
            
        return answers
        
    except Exception as e:
        return [f"Error processing queries: {str(e)}"] * len(queries)