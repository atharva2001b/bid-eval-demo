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
class EvaluationAnalytics:
    """Structured representation of evaluation report analytics."""
    company_name: Optional[str] = None
    submission_date: Optional[str] = None
    industry: Optional[str] = None
    technical_score: Optional[int] = None
    commercial_score: Optional[int] = None
    compliance_score: Optional[int] = None
    risk_score: Optional[int] = None
    overall_score: Optional[int] = None
    risk_level: Optional[str] = None
    key_strengths: List[str] = None
    key_weaknesses: List[str] = None
    risk_factors: List[str] = None
    pricing_details: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_timeline: Optional[str] = None
    tender_compliance: List[str] = None
    
    def __post_init__(self):
        """Initialize empty lists for collections if None."""
        if self.key_strengths is None:
            self.key_strengths = []
        if self.key_weaknesses is None:
            self.key_weaknesses = []
        if self.risk_factors is None:
            self.risk_factors = []
        if self.tender_compliance is None:
            self.tender_compliance = []

class StateManager:
    """Manages application state and provides interface for state updates."""
    
    def __init__(self):
        """Initialize the state manager and ensure all required state variables exist."""
        self.initialize_session_state()

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

    @staticmethod
    def _extract_section(report: str, section_name: str) -> str:
        """Extract a section from the evaluation report using robust pattern matching."""
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

    @staticmethod
    def _extract_score(section: str, score_name: str) -> Optional[int]:
        """Extract a specific score value using precise pattern matching."""
        patterns = [
            f"{score_name} Score:\\s*\\*\\*([0-9]+)\\*\\*",  # Bold markdown
            f"{score_name} Score:\\s*([0-9]+)",              # Plain number
            f"{score_name}:\\s*\\*\\*([0-9]+)\\*\\*",       # Alternate bold format
            f"{score_name}:\\s*([0-9]+)"                     # Alternate plain format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, section, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None

    @staticmethod
    def _extract_bullet_points(section: str) -> List[str]:
        """Extract bullet points from a section using robust pattern matching."""
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

    def _extract_evaluation_analytics(self, evaluation_report: str) -> EvaluationAnalytics:
        """Extract structured analytics from evaluation report with improved accuracy."""
        analytics = EvaluationAnalytics()
        
        # Extract company overview information
        overview_section = self._extract_section(evaluation_report, "Company Overview")
        
        # Extract company details with flexible pattern matching
        company_patterns = [
            r'Company Name:\s*([^,\n]+)',
            r'Company:\s*([^,\n]+)',
            r'Vendor:\s*([^,\n]+)'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, overview_section)
            if match:
                analytics.company_name = match.group(1).strip()
                break
        
        # Extract submission date and industry
        submission_match = re.search(r'Submission Date:\s*([^,\n]+)', overview_section)
        if submission_match:
            analytics.submission_date = submission_match.group(1).strip()
        
        industry_match = re.search(r'Industry:\s*([^,\n]+)', overview_section)
        if industry_match:
            analytics.industry = industry_match.group(1).strip()

        # Extract scores
        scores_section = self._extract_section(evaluation_report, "Scores")
        analytics.technical_score = self._extract_score(scores_section, "Technical")
        analytics.commercial_score = self._extract_score(scores_section, "Commercial")
        analytics.compliance_score = self._extract_score(scores_section, "Compliance")
        analytics.risk_score = self._extract_score(scores_section, "Risk")
        analytics.overall_score = self._extract_score(scores_section, "Overall")

        # Extract tender compliance
        tender_section = self._extract_section(evaluation_report, "Tender Compliance")
        analytics.tender_compliance = self._extract_bullet_points(tender_section)

        # Extract risk analysis
        risk_section = self._extract_section(evaluation_report, "Risk Analysis")
        risk_level_patterns = [
            r'Risk Level:\s*\*\*([^*]+)\*\*',
            r'Risk Level:\s*([^,\n]+)',
            r'Level:\s*\*\*([^*]+)\*\*'
        ]
        
        for pattern in risk_level_patterns:
            match = re.search(pattern, risk_section)
            if match:
                analytics.risk_level = match.group(1).strip()
                break

        # Extract lists
        analytics.key_strengths = self._extract_bullet_points(
            self._extract_section(evaluation_report, "Key Strengths")
        )
        analytics.key_weaknesses = self._extract_bullet_points(
            self._extract_section(evaluation_report, "Areas for Improvement")
        )
        analytics.risk_factors = self._extract_bullet_points(risk_section)

        # Extract commercial terms
        commercial_section = self._extract_section(evaluation_report, "Commercial Terms")
        
        pricing_patterns = [
            r'Pricing Details:\s*([^.\n]+)',
            r'Price:\s*([^.\n]+)',
            r'Cost:\s*([^.\n]+)'
        ]
        
        for pattern in pricing_patterns:
            match = re.search(pattern, commercial_section)
            if match:
                analytics.pricing_details = match.group(1).strip()
                break

        payment_match = re.search(r'Payment Terms:\s*([^.\n]+)', commercial_section)
        if payment_match:
            analytics.payment_terms = payment_match.group(1).strip()

        delivery_patterns = [
            r'Delivery Timeline:\s*([^#]+?)(?=\*\*|$)',
            r'Timeline:\s*([^#]+?)(?=\*\*|$)',
            r'Delivery:\s*([^#]+?)(?=\*\*|$)'
        ]
        
        for pattern in delivery_patterns:
            match = re.search(pattern, commercial_section, re.DOTALL)
            if match:
                analytics.delivery_timeline = match.group(1).strip()
                break

        return analytics

    def store_result(self, file_name: str, result: Dict[str, Any]):
        """Store processing results and extract evaluation analytics."""
        if 'results' not in st.session_state:
            st.session_state.results = {}
        if 'evaluation_analytics' not in st.session_state:
            st.session_state.evaluation_analytics = {}
        if 'file_history' not in st.session_state:
            st.session_state.file_history = set()
            
        # Store the result data
        st.session_state.results[file_name] = result
        st.session_state.file_history.add(file_name)
        
        # Extract and store evaluation analytics
        if 'evaluation_report' in result:
            analytics = self._extract_evaluation_analytics(result['evaluation_report'])
            st.session_state.evaluation_analytics[file_name] = analytics

    def get_evaluation_analytics(self) -> Dict[str, EvaluationAnalytics]:
        """Get evaluation analytics for all documents."""
        return st.session_state.get('evaluation_analytics', {})

    def get_comparison_data(self) -> Dict[str, Dict]:
        """Get formatted comparison data for all documents."""
        analytics = self.get_evaluation_analytics()
        comparison_data = {}
        
        for file_name, analysis in analytics.items():
            comparison_data[file_name] = {
                'Company': analysis.company_name or 'N/A',
                'Technical Score': analysis.technical_score or 0,
                'Commercial Score': analysis.commercial_score or 0,
                'Compliance Score': analysis.compliance_score or 0,
                'Risk Score': analysis.risk_score or 0,
                'Overall Score': analysis.overall_score or 0,
                'Risk Level': analysis.risk_level or 'N/A',
                'Key Strengths': len(analysis.key_strengths),
                'Key Weaknesses': len(analysis.key_weaknesses),
                'Risk Factors': len(analysis.risk_factors),
                'Tender Compliance': len(analysis.tender_compliance),
                'Pricing': analysis.pricing_details or 'N/A',
                'Payment Terms': analysis.payment_terms or 'N/A',
                'Delivery': analysis.delivery_timeline or 'N/A'
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
    def remove_from_queue(file_name: str):
        """Remove a file from the processing queue."""
        st.session_state.processing_queue = [
            f for f in st.session_state.processing_queue 
            if f.name != file_name
        ]
        if not st.session_state.processing_queue:
            st.session_state.is_processing = False

    @staticmethod
    def get_results() -> Dict[str, Any]:
        """Get all stored results."""
        return st.session_state.get('results', {})

    @staticmethod
    def is_file_processed(file_name: str) -> bool:
        """Check if a file has already been processed."""
        return file_name in st.session_state.get('file_history', set())

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