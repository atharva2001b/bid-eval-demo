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

    @staticmethod
    def _extract_section(report: str, section_name: str) -> str:
        """
        Extract a section from the evaluation report using robust pattern matching.
        
        Args:
            report (str): The full evaluation report
            section_name (str): The name of the section to extract
            
        Returns:
            str: The extracted section content
        """
        # Handle both bold markdown and plain text section headers
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
        """
        Extract a specific score value using precise pattern matching.
        
        Args:
            section (str): The section containing scores
            score_name (str): The name of the score to extract
            
        Returns:
            Optional[int]: The extracted score value
        """
        # Handle various score formats
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
        """
        Extract bullet points from a section using robust pattern matching.
        
        Args:
            section (str): The section containing bullet points
            
        Returns:
            List[str]: List of extracted bullet points
        """
        bullet_points = []
        
        # Match both markdown and plain bullet points
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
        """
        Extract structured analytics from evaluation report with improved accuracy.
        
        Args:
            evaluation_report (str): The full evaluation report text
            
        Returns:
            EvaluationAnalytics: Structured analytics data
        """
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

        # Extract bullet point lists
        analytics.key_strengths = self._extract_bullet_points(
            self._extract_section(evaluation_report, "Key Strengths")
        )
        analytics.key_weaknesses = self._extract_bullet_points(
            self._extract_section(evaluation_report, "Areas for Improvement")
        )
        analytics.risk_factors = self._extract_bullet_points(risk_section)

        # Extract commercial terms
        commercial_section = self._extract_section(evaluation_report, "Commercial Terms")
        
        # Extract pricing details with flexible pattern matching
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

        # Extract payment terms
        payment_match = re.search(r'Payment Terms:\s*([^.\n]+)', commercial_section)
        if payment_match:
            analytics.payment_terms = payment_match.group(1).strip()

        # Extract delivery timeline
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
        """
        Store processing results and extract evaluation analytics.
        
        Args:
            file_name (str): Name of the processed file
            result (Dict[str, Any]): Processing results including evaluation report
        """
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
        """
        Get formatted comparison data for all documents.
        
        Returns:
            Dict[str, Dict]: Comparison data formatted for display
        """
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
                'Pricing': analysis.pricing_details or 'N/A',
                'Payment Terms': analysis.payment_terms or 'N/A',
                'Delivery': analysis.delivery_timeline or 'N/A'
            }
        
        return comparison_data

    # File Processing Methods
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
    def get_results() -> Dict[str, Any]:
        """Get all stored results."""
        return st.session_state.get('results', {})

    @staticmethod
    def is_file_processed(file_name: str) -> bool:
        """Check if a file has already been processed."""
        return file_name in st.session_state.get('file_history', set())

    @staticmethod
    def clear_all_results():
        """Clear all stored results and reset the application state."""
        st.session_state.results = {}
        st.session_state.evaluation_analytics = {}
        st.session_state.file_history = set()
        st.session_state.processing_state = ProcessingState()
        st.session_state.processing_queue = []
        st.session_state.is_processing = False

    @staticmethod
    def get_processing_state() -> ProcessingState:
        """Get current processing state."""
        if not hasattr(st.session_state, 'processing_state'):
            st.session_state.processing_state = ProcessingState()
        return st.session_state.processing_state

    def generate_analytics_report(self, file_name: str) -> str:
        """
        Generate a formatted markdown report from evaluation analytics.
        
        Args:
            file_name (str): Name of the file to generate report for
            
        Returns:
            str: Formatted markdown report
        """
        analytics = st.session_state.evaluation_analytics.get(file_name)
        if not analytics:
            return "No analytics available for this document."

        report = []
        
        # Company Overview
        report.append("# Bid Evaluation Report\n")
        report.append("## Company Overview")
        report.append(f"- **Company Name:** {analytics.company_name or 'Not specified'}")
        report.append(f"- **Submission Date:** {analytics.submission_date or 'Not specified'}")
        report.append(f"- **Industry:** {analytics.industry or 'Not specified'}\n")

        # Scores
        report.append("## Evaluation Scores")
        scores = {
            'Technical': analytics.technical_score,
            'Commercial': analytics.commercial_score,
            'Compliance': analytics.compliance_score,
            'Risk': analytics.risk_score,
            'Overall': analytics.overall_score
        }
        for name, score in scores.items():
            report.append(f"- **{name} Score:** {score if score is not None else 'Not available'}")
        report.append("")

        # Risk Assessment
        report.append("## Risk Assessment")
        report.append(f"**Risk Level:** {analytics.risk_level or 'Not specified'}\n")
        
        if analytics.risk_factors:
            report.append("**Key Risk Factors:**")
            for factor in analytics.risk_factors:
                report.append(f"- {factor}")
        report.append("")

        # Strengths and Weaknesses
        report.append("## Strengths and Areas for Improvement")
        if analytics.key_strengths:
            report.append("\n**Key Strengths:**")
            for strength in analytics.key_strengths:
                report.append(f"- {strength}")
        
        if analytics.key_weaknesses:
            report.append("\n**Areas for Improvement:**")
            for weakness in analytics.key_weaknesses:
                report.append(f"- {weakness}")
        report.append("")

        # Commercial Terms
        report.append("## Commercial Terms")
        report.append(f"- **Pricing Details:** {analytics.pricing_details or 'Not specified'}")
        report.append(f"- **Payment Terms:** {analytics.payment_terms or 'Not specified'}")
        if analytics.delivery_timeline:
            report.append(f"- **Delivery Timeline:** {analytics.delivery_timeline}")
        report.append("")

        return "\n".join(report)

    def export_analytics_data(self) -> pd.DataFrame:
        """
        Export evaluation analytics as a pandas DataFrame.
        
        Returns:
            pd.DataFrame: Analytics data in tabular format
        """
        analytics = self.get_evaluation_analytics()
        data = []
        
        for file_name, analysis in analytics.items():
            row = {
                'File Name': file_name,
                'Company Name': analysis.company_name,
                'Industry': analysis.industry,
                'Technical Score': analysis.technical_score,
                'Commercial Score': analysis.commercial_score,
                'Compliance Score': analysis.compliance_score,
                'Risk Score': analysis.risk_score,
                'Overall Score': analysis.overall_score,
                'Risk Level': analysis.risk_level,
                'Number of Strengths': len(analysis.key_strengths),
                'Number of Weaknesses': len(analysis.key_weaknesses),
                'Number of Risk Factors': len(analysis.risk_factors),
                'Pricing Details': analysis.pricing_details,
                'Payment Terms': analysis.payment_terms,
                'Delivery Timeline': analysis.delivery_timeline
            }
            data.append(row)
        
        return pd.DataFrame(data)

    def get_aggregated_statistics(self) -> Dict[str, Any]:
        """
        Calculate aggregated statistics across all evaluated documents.
        
        Returns:
            Dict[str, Any]: Aggregated statistics
        """
        analytics = self.get_evaluation_analytics()
        if not analytics:
            return {}

        stats = {
            'total_documents': len(analytics),
            'average_scores': {
                'technical': 0,
                'commercial': 0,
                'compliance': 0,
                'risk': 0,
                'overall': 0
            },
            'risk_levels': {},
            'top_strengths': {},
            'top_weaknesses': {},
            'price_ranges': {'min': None, 'max': None, 'avg': None}
        }

        # Calculate averages and collect data
        for analysis in analytics.values():
            # Aggregate scores
            if analysis.technical_score:
                stats['average_scores']['technical'] += analysis.technical_score
            if analysis.commercial_score:
                stats['average_scores']['commercial'] += analysis.commercial_score
            if analysis.compliance_score:
                stats['average_scores']['compliance'] += analysis.compliance_score
            if analysis.risk_score:
                stats['average_scores']['risk'] += analysis.risk_score
            if analysis.overall_score:
                stats['average_scores']['overall'] += analysis.overall_score

            # Count risk levels
            if analysis.risk_level:
                stats['risk_levels'][analysis.risk_level] = \
                    stats['risk_levels'].get(analysis.risk_level, 0) + 1

            # Aggregate strengths and weaknesses
            for strength in analysis.key_strengths:
                stats['top_strengths'][strength] = \
                    stats['top_strengths'].get(strength, 0) + 1
            for weakness in analysis.key_weaknesses:
                stats['top_weaknesses'][weakness] = \
                    stats['top_weaknesses'].get(weakness, 0) + 1

        # Calculate averages
        for score_type in stats['average_scores']:
            stats['average_scores'][score_type] = \
                round(stats['average_scores'][score_type] / stats['total_documents'], 2)

        # Sort and limit top strengths and weaknesses
        stats['top_strengths'] = dict(sorted(
            stats['top_strengths'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5])
        stats['top_weaknesses'] = dict(sorted(
            stats['top_weaknesses'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5])

        return stats