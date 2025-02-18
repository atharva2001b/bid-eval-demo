from typing import List, Tuple
import nltk
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
import re

class RAGProcessor:
    def __init__(self, model_name: str = 'multi-qa-mpnet-base-dot-v1'):
        """Initialize the RAG processor with the specified embedding model."""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
            
        # Initialize LangChain components
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            separators=["\n\n", "\n", ".", " ", ""],
            keep_separator=True
        )
        
        # Storage for processed content
        self.vector_store = None
        self.sections = []
        self.section_map = {}
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text while preserving section markers."""
        text = re.sub(r'[^a-zA-Z0-9\s.:\-()§$%]', ' ', text)
        text = ' '.join(text.split())
        return text
    
    def identify_section_boundaries(self, text: str) -> List[Tuple[str, str]]:
        """Identify document sections using common patterns."""
        section_patterns = [
            r'(?i)^\s*(?:Section|SECTION)\s+\d+[.:]\s*(.+)$',
            r'(?i)^\s*\d+[.:]\s*(.+)$',
            r'(?i)^\s*[A-Z][A-Z\s]+[.:]\s*(.+)$',
            r'(?i)^\s*(?:Article|ARTICLE)\s+\d+[.:]\s*(.+)$',
            r'(?i)^\s*§\s*\d+[.:]\s*(.+)$'
        ]
        
        lines = text.split('\n')
        sections = []
        current_section = []
        current_title = "Introduction"
        
        for line in lines:
            is_header = False
            line_stripped = line.strip()
            
            if not line_stripped:
                continue
                
            for pattern in section_patterns:
                if re.match(pattern, line_stripped):
                    if current_section:
                        section_text = '\n'.join(current_section).strip()
                        if section_text:
                            sections.append((current_title, section_text))
                    current_section = []
                    current_title = line_stripped
                    is_header = True
                    break
            
            if not is_header:
                current_section.append(line)
        
        # Add the last section if it has content
        if current_section:
            section_text = '\n'.join(current_section).strip()
            if section_text:
                sections.append((current_title, section_text))
        
        # If no sections were found, treat the entire text as one section
        if not sections:
            sections = [("Main Content", text.strip())]
            
        return sections
    
    def preprocess_text(self, file_path: str) -> List[str]:
        """Extract and preprocess text from a file with section awareness."""
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        if not text.strip():
            return []
            
        # Identify sections
        sections = self.identify_section_boundaries(text)
        processed_sections = []
        section_map = {}
        
        # Split each section into chunks using LangChain's text splitter
        for i, (section_title, section_content) in enumerate(sections):
            if not section_content.strip():
                continue
                
            # Use LangChain's splitter
            chunks = self.text_splitter.split_text(section_content)
            
            for j, chunk in enumerate(chunks):
                section_map[len(processed_sections)] = {
                    'section_title': section_title,
                    'chunk_index': j
                }
                processed_sections.append(chunk)
        
        self.sections = processed_sections
        self.section_map = section_map
        
        return processed_sections
        
    def index_text(self, text: str, window_size: int = 3):
        """Index text for retrieval using LangChain's FAISS store."""
        # Reset state
        self.sections = []
        self.section_map = {}
        
        # Process and split text into sections
        sections = self.preprocess_text(text)
        if not sections:
            raise ValueError("No valid sections found in the text")
        
        # Create vector store
        self.vector_store = FAISS.from_texts(sections, self.embeddings)
    
    def retrieve_context(self, query: str, k: int = 3) -> List[Tuple[str, float]]:
        """Retrieve relevant context from the vector store."""
        if not query.strip() or not self.vector_store:
            return []
            
        # Get search results with scores
        docs_and_scores = self.vector_store.similarity_search_with_score(query, k=k*2)
        
        # Process and deduplicate results
        results = []
        seen_sections = set()
        
        for doc, score in docs_and_scores:
            content = doc.page_content
            doc_index = self.sections.index(content) if content in self.sections else -1
            
            if doc_index >= 0:
                section_info = self.section_map.get(doc_index, {'section_title': 'General'})
                section_title = section_info['section_title']
                
                # Convert score to similarity (FAISS returns distances)
                similarity_score = float(1.0 / (1.0 + score))
                
                if section_title not in seen_sections or len(results) < k:
                    results.append((content, similarity_score))
                    seen_sections.add(section_title)
                    
                    if len(results) >= k:
                        break
        
        return results

def process_queries(text: str, queries: List[str]) -> List[str]:
    """Process queries with section-aware context retrieval."""
    try:
        processor = RAGProcessor()
        processor.index_text(text)
        
        answers = []
        for query in queries:
            if not query.strip():
                answers.append("Empty query provided")
                continue
                
            contexts = processor.retrieve_context(query, k=3)
            
            if contexts:
                # Combine contexts with section info
                answer_parts = []
                for context, score in contexts:
                    doc_index = processor.sections.index(context) if context in processor.sections else -1
                    section_title = processor.section_map.get(doc_index, {}).get('section_title', 'General')
                    
                    answer_parts.append(f"[Section: {section_title}, Confidence: {score:.2f}]\n{context}")
                
                answer = "\n\n".join(answer_parts)
            else:
                answer = "No relevant context found for this query."
                
            answers.append(answer)
            
        return answers
        
    except Exception as e:
        print(f"Processing error: {str(e)}")  # Log error for debugging
        return [f"Error processing queries: {str(e)}"] * len(queries)