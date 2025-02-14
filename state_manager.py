import streamlit as st
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import re
import pandas as pd

@dataclass
class ProcessingState:
    """Represents the current state of document processing."""
    is_processing: bool = False
    current_file: Optional[str] = None
    progress: float = 0.0
    status_message: str = ""
    error_message: Optional[str] = None
    is_processing_complete: bool = False

@dataclass
class BidScore:
    """Represents the scores from a bid evaluation."""
    technical_score: Optional[int] = None
    commercial_score: Optional[int] = None
    compliance_score: Optional[int] = None
    risk_score: Optional[int] = None
    overall_score: Optional[int] = None
    company_name: Optional[str] = None
    risk_level: Optional[str] = None
    key_strengths: List[str] = None
    key_weaknesses: List[str] = None
    risk_factors: List[str] = None
    pricing_details: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_timeline: Optional[str] = None
    
    def __post_init__(self):
        """Initialize empty lists for collections if None."""
        if self.key_strengths is None:
            self.key_strengths = []
        if self.key_weaknesses is None:
            self.key_weaknesses = []
        if self.risk_factors is None:
            self.risk_factors = []

class StateManager:
    """Manages application state and provides interface for state updates."""
    
    def __init__(self):
        """Initialize the state manager."""
        self.initialize_session_state()
    
    @staticmethod
    def initialize_session_state():
        """Initialize all required session state variables."""
        if 'processing_state' not in st.session_state:
            st.session_state.processing_state = ProcessingState()
        if 'results' not in st.session_state:
            st.session_state.results = {}
        if 'evaluation_analytics' not in st.session_state:
            st.session_state.evaluation_analytics = {}
        if 'file_history' not in st.session_state:
            st.session_state.file_history = set()
        if 'current_tab' not in st.session_state:
            st.session_state.current_tab = "Upload"
        if 'processing_queue' not in st.session_state:
            st.session_state.processing_queue = []
        if 'is_processing' not in st.session_state:
            st.session_state.is_processing = False
        if 'tender_context' not in st.session_state:
            st.session_state.tender_context = None

    def _extract_bullet_points(self, section: str) -> List[str]:
        """Extract bullet points from a section using regex."""
        bullet_points = []
        
        patterns = [
            r"(?:^|\n)[*-]\s*(?:\*\*)?([^*\n]+?)(?:\*\*)?(?=\n|$)",  # Markdown bullets
            r"(?:^|\n)(?:\d+\.|\u2022|\u25E6|\u25AA)\s*([^\n]+)",     # Numbered and unicode bullets
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, section, re.MULTILINE)
            bullet_points.extend([
                match.group(1).strip()
                for match in matches
                if match.group(1).strip()
            ])
        
        return bullet_points

    def _extract_section(self, report: str, section_name: str) -> str:
        """Extract a section from the evaluation report."""
        patterns = [
            f"\\*\\*{section_name}\\*\\*\\s*([^*]+?)(?=\\*\\*|$)",  # Bold markdown
            f"{section_name}:\\s*([^*]+?)(?=\\*\\*|$)",             # Plain text with colon
            f"{section_name}\\s*([^*]+?)(?=\\*\\*|$)"               # Plain text without colon
        ]
        
        for pattern in patterns:
            match = re.search(pattern, report, re.DOTALL | re.MULTILINE)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_score_table(self, evaluation_report: str) -> BidScore:
        """Extract scores and other data from the evaluation report."""
        scores = BidScore()
        
        # Extract company name
        company_match = re.search(r'Company Name:\s*([^,\n]+)', evaluation_report)
        if company_match:
            scores.company_name = company_match.group(1).strip()
        
        # Extract scores using multiple patterns
        score_patterns = {
            'technical_score': [
                r'Technical Score:?\s*\*?(\d+)\*?',
                r'\|\s*Technical\s*\|\s*(\d+)\s*\|'
            ],
            'commercial_score': [
                r'Commercial Score:?\s*\*?(\d+)\*?',
                r'\|\s*Commercial\s*\|\s*(\d+)\s*\|'
            ],
            'compliance_score': [
                r'Compliance Score:?\s*\*?(\d+)\*?',
                r'\|\s*Compliance\s*\|\s*(\d+)\s*\|'
            ],
            'risk_score': [
                r'Risk Score:?\s*\*?(\d+)\*?',
                r'\|\s*Risk\s*\|\s*(\d+)\s*\|'
            ],
            'overall_score': [
                r'Overall Score:?\s*\*?(\d+)\*?',
                r'\|\s*Overall\s*\|\s*(\d+)\s*\|'
            ]
        }
        
        # Extract scores
        for score_name, patterns in score_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, evaluation_report)
                if match:
                    try:
                        setattr(scores, score_name, int(match.group(1)))
                        break
                    except (ValueError, IndexError):
                        continue

        # Extract risk level
        risk_section = self._extract_section(evaluation_report, "Risk Analysis")
        risk_level_match = re.search(r'Risk Level:\s*\*?([^*\n]+?)\*?(?=\n|$)', risk_section)
        if risk_level_match:
            scores.risk_level = risk_level_match.group(1).strip()

        # Extract lists
        scores.key_strengths = self._extract_bullet_points(
            self._extract_section(evaluation_report, "Key Strengths")
        )
        scores.key_weaknesses = self._extract_bullet_points(
            self._extract_section(evaluation_report, "Areas for Improvement")
        )
        scores.risk_factors = self._extract_bullet_points(risk_section)

        # Extract commercial terms
        commercial_section = self._extract_section(evaluation_report, "Commercial Terms")
        
        pricing_match = re.search(r'Pricing Details:\s*([^.\n]+)', commercial_section)
        if pricing_match:
            scores.pricing_details = pricing_match.group(1).strip()

        payment_match = re.search(r'Payment Terms:\s*([^.\n]+)', commercial_section)
        if payment_match:
            scores.payment_terms = payment_match.group(1).strip()

        delivery_match = re.search(r'Delivery Timeline:\s*([^.\n]+)', commercial_section)
        if delivery_match:
            scores.delivery_timeline = delivery_match.group(1).strip()
        
        return scores

    def store_result(self, file_name: str, result: Dict[str, Any]):
        """Store processing results."""
        if 'results' not in st.session_state:
            st.session_state.results = {}
        if 'evaluation_analytics' not in st.session_state:
            st.session_state.evaluation_analytics = {}
        if 'file_history' not in st.session_state:
            st.session_state.file_history = set()
            
        # Store the result data
        st.session_state.results[file_name] = result
        st.session_state.file_history.add(file_name)
        
        # Extract and store scores if evaluation report exists
        if 'evaluation_report' in result:
            scores = self._extract_score_table(result['evaluation_report'])
            st.session_state.evaluation_analytics[file_name] = scores

    def get_results(self) -> Dict[str, Any]:
        """Get all stored results."""
        return st.session_state.get('results', {})

    def get_evaluation_analytics(self) -> Dict[str, BidScore]:
        """Get evaluation analytics for all documents."""
        return st.session_state.get('evaluation_analytics', {})

    def get_comparison_data(self) -> Dict[str, Dict]:
        """Get formatted comparison data for evaluation."""
        analytics = self.get_evaluation_analytics()
        comparison_data = {}
        
        for file_name, scores in analytics.items():
            comparison_data[file_name] = {
                'Company': scores.company_name or 'N/A',
                'Technical Score': scores.technical_score or 0,
                'Commercial Score': scores.commercial_score or 0,
                'Compliance Score': scores.compliance_score or 0,
                'Risk Score': scores.risk_score or 0,
                'Overall Score': scores.overall_score or 0,
                'Risk Level': scores.risk_level or 'N/A',
                'Key Strengths': len(scores.key_strengths),
                'Key Weaknesses': len(scores.key_weaknesses),
                'Risk Factors': len(scores.risk_factors),
                'Pricing': scores.pricing_details or 'N/A',
                'Payment Terms': scores.payment_terms or 'N/A',
                'Delivery': scores.delivery_timeline or 'N/A'
            }
        
        return comparison_data

    @staticmethod
    def store_tender_context(tender_context: dict):
        """Store tender context in session state."""
        st.session_state.tender_context = tender_context

    @staticmethod
    def get_tender_context() -> Optional[dict]:
        """Get stored tender context."""
        return st.session_state.get('tender_context')

    @staticmethod
    def start_processing(files: List):
        """Add files to processing queue."""
        st.session_state.processing_queue = [
            f for f in files 
            if f.name not in st.session_state.file_history
        ]
        st.session_state.is_processing = True

    @staticmethod
    def is_processing() -> bool:
        """Check if processing is ongoing."""
        return st.session_state.get('is_processing', False)

    @staticmethod
    def get_processing_queue() -> List:
        """Get current processing queue."""
        return st.session_state.get('processing_queue', [])

    @staticmethod
    def is_file_processed(file_name: str) -> bool:
        """Check if a file has already been processed."""
        return file_name in st.session_state.get('file_history', set())

    @staticmethod
    def remove_from_queue(file_name: str):
        """Remove a file from the processing queue."""
        st.session_state.processing_queue = [
            f for f in st.session_state.processing_queue 
            if f.name != file_name
        ]
        if not st.session_state.processing_queue:
            st.session_state.is_processing = False

    @staticmethod
    def update_processing_state(
        file_name: Optional[str] = None,
        progress: Optional[float] = None,
        status: Optional[str] = None,
        is_processing: Optional[bool] = None,
        error: Optional[str] = None,
        is_complete: Optional[bool] = None
    ):
        """Update processing state parameters."""
        if not hasattr(st.session_state, 'processing_state'):
            st.session_state.processing_state = ProcessingState()
            
        if file_name is not None:
            st.session_state.processing_state.current_file = file_name
        if progress is not None:
            st.session_state.processing_state.progress = progress
        if status is not None:
            st.session_state.processing_state.status_message = status
        if is_processing is not None:
            st.session_state.processing_state.is_processing = is_processing
        if error is not None:
            st.session_state.processing_state.error_message = error
        if is_complete is not None:
            st.session_state.processing_state.is_processing_complete = is_complete

    @staticmethod
    def get_processing_state() -> ProcessingState:
        """Get current processing state."""
        if not hasattr(st.session_state, 'processing_state'):
            st.session_state.processing_state = ProcessingState()
        return st.session_state.processing_state

    @staticmethod
    def clear_all_results():
        """Clear all stored results and reset the application state."""
        st.session_state.results = {}
        st.session_state.evaluation_analytics = {}
        st.session_state.file_history = set()
        st.session_state.processing_state = ProcessingState()
        st.session_state.processing_queue = []
        st.session_state.is_processing = False
        st.session_state.tender_context = None