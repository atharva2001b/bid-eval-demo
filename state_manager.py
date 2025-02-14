import streamlit as st
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import json
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
    """Represents the scores and justifications from a bid evaluation."""
    technical_score: Optional[int] = None
    commercial_score: Optional[int] = None
    compliance_score: Optional[int] = None
    risk_score: Optional[int] = None
    overall_score: Optional[int] = None
    technical_justification: Optional[str] = None
    commercial_justification: Optional[str] = None
    compliance_justification: Optional[str] = None
    risk_justification: Optional[str] = None
    overall_justification: Optional[str] = None
    company_name: Optional[str] = None
    pricing_details: Optional[str] = None
    delivery_timeline: Optional[str] = None

class StateManager:
    """Manages application state and provides interface for state updates."""
    
    def __init__(self):
        """
        Initialize the state manager.
        
        Args:
            ollama_processor: Instance of OllamaProcessor for score extraction
        """
        from ollama_processor import OllamaProcessor
        self.ollama_processor = OllamaProcessor()
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

    def _process_score_json(self, scores_json: str) -> BidScore:
        """
        Process the JSON scores from OllamaProcessor into BidScore object.
        
        Args:
            scores_json (str): JSON string containing the scores and justifications
            
        Returns:
            BidScore: Processed bid scores and justifications
        """
        try:
            scores_data = json.loads(scores_json)['scores']
            
            return BidScore(
                technical_score=scores_data['technical']['score'],
                commercial_score=scores_data['commercial']['score'],
                compliance_score=scores_data['compliance']['score'],
                risk_score=scores_data['risk']['score'],
                overall_score=scores_data['overall']['score'],
                technical_justification=scores_data['technical']['justification'],
                commercial_justification=scores_data['commercial']['justification'],
                compliance_justification=scores_data['compliance']['justification'],
                risk_justification=scores_data['risk']['justification'],
                overall_justification=scores_data['overall']['justification']
            )
        except (json.JSONDecodeError, KeyError) as e:
            st.error(f"Error processing score JSON: {str(e)}")
            return BidScore()

    def store_result(self, file_name: str, result: Dict[str, Any]):
        """
        Store processing results and extract scores using OllamaProcessor.
        
        Args:
            file_name (str): Name of the processed file
            result (Dict[str, Any]): Processing results including evaluation report
        """
        if not self.ollama_processor:
            st.error("OllamaProcessor not initialized")
            return
            
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
            # Get JSON scores from OllamaProcessor
            scores_json = self.ollama_processor.get_evaluation_scores(result['evaluation_report'])
            
            # Process JSON into BidScore object
            scores = self._process_score_json(scores_json)
            
            # Extract basic metadata that might be in the report
            company_match = re.search(r'Company Name:\s*([^,\n]+)', result['evaluation_report'])
            if company_match:
                scores.company_name = company_match.group(1).strip()
                
            pricing_match = re.search(r'Pricing Details:\s*([^.\n]+)', result['evaluation_report'])
            if pricing_match:
                scores.pricing_details = pricing_match.group(1).strip()
                
            delivery_match = re.search(r'Delivery Timeline:\s*([^.\n]+)', result['evaluation_report'])
            if delivery_match:
                scores.delivery_timeline = delivery_match.group(1).strip()
            
            st.session_state.evaluation_analytics[file_name] = scores

    def get_results(self) -> Dict[str, Any]:
        """Get all stored results."""
        return st.session_state.get('results', {})

    def get_evaluation_analytics(self) -> Dict[str, BidScore]:
        """Get evaluation analytics for all documents."""
        return st.session_state.get('evaluation_analytics', {})

    def get_comparison_data(self) -> Dict[str, Dict]:
        """
        Get formatted comparison data for evaluation.
        
        Returns:
            Dict[str, Dict]: Formatted comparison data for all documents
        """
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
                'Technical Justification': scores.technical_justification or 'N/A',
                'Commercial Justification': scores.commercial_justification or 'N/A',
                'Compliance Justification': scores.compliance_justification or 'N/A',
                'Risk Justification': scores.risk_justification or 'N/A',
                'Overall Justification': scores.overall_justification or 'N/A',
                'Pricing': scores.pricing_details or 'N/A',
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
        """
        Add files to processing queue.
        
        Args:
            files (List): List of files to process
        """
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
        """
        Check if a file has already been processed.
        
        Args:
            file_name (str): Name of the file to check
            
        Returns:
            bool: True if file has been processed
        """
        return file_name in st.session_state.get('file_history', set())

    @staticmethod
    def remove_from_queue(file_name: str):
        """
        Remove a file from the processing queue.
        
        Args:
            file_name (str): Name of the file to remove
        """
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
        """
        Update processing state parameters.
        
        Args:
            file_name (str, optional): Current file being processed
            progress (float, optional): Processing progress (0-1)
            status (str, optional): Status message
            is_processing (bool, optional): Processing state
            error (str, optional): Error message
            is_complete (bool, optional): Completion state
        """
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