import streamlit as st
from typing import Optional, List
from state_manager import StateManager
from pages.upload_page import UploadPage
from pages.analysis_page import AnalysisPage
from pages.evaluation_page import EvaluationPage

class BidAnalyzerUI:
    def __init__(self):
        self.state_manager = StateManager()
        self._initialize_pages()
        
    def _initialize_pages(self):
        """Initialize page components."""
        self.pages = {
            "Upload": UploadPage(self.state_manager),
            "Analysis": AnalysisPage(self.state_manager),
            "Evaluation": EvaluationPage(self.state_manager)
        }

    def setup_page(self):
        """Configure the page layout and title."""
        st.set_page_config(page_title="Bid Analyzer", layout="wide")
        
        # Setup sidebar
        with st.sidebar:
            st.title("Navigation")
            
            # Navigation buttons
            current_tab = st.session_state.get('current_tab', 'Upload')
            
            st.button("📤 Upload", key="sidebar_nav_upload", 
                     type="primary" if current_tab == "Upload" else "secondary",
                     use_container_width=True)
            
            st.button("📊 Analysis", key="sidebar_nav_analysis",
                     type="primary" if current_tab == "Analysis" else "secondary",
                     use_container_width=True)
            
            st.button("📋 Evaluation", key="sidebar_nav_evaluation",
                     type="primary" if current_tab == "Evaluation" else "secondary",
                     use_container_width=True)
            
            # Update current tab based on button clicks
            for tab in ["Upload", "Analysis", "Evaluation"]:
                if st.session_state.get(f"sidebar_nav_{tab.lower()}"):
                    st.session_state.current_tab = tab
                    st.rerun()
            
            # Add separator
            st.markdown("---")
            
            # Settings section
            st.markdown("### Settings")
            
            # Show current state
            st.write(f"Active Page: {current_tab}")
            st.write(f"Files Processed: {len(self.state_manager.get_results())}")
            
            # Clear results button
            if st.button("🗑️ Clear All Results", type="primary", use_container_width=True):
                self.state_manager.clear_all_results()
                st.rerun()
        
        # Main content area
        st.title("Bid Analyzer & Evaluator")

        # Initialize state
        self.state_manager.initialize_session_state()

    def show_processing_status(self):
        """Display current processing status."""
        state = self.state_manager.get_processing_state()
        if state.is_processing:
            progress_container = st.container()
            with progress_container:
                st.progress(state.progress)
                st.text(state.status_message)
                if state.error_message:
                    st.error(state.error_message)
            return progress_container
        return None

    def update_progress(self, progress: float, message: str):
        """Update progress bar and status message."""
        self.state_manager.update_processing_state(
            progress=progress,
            status=message
        )

    def display_error(self, error_message: str):
        """Display error message."""
        self.state_manager.update_processing_state(error=error_message)

    def create_processing_container(self):
        """Create and return a container for processing indicators."""
        return st.container()

    def render_current_tab(self) -> Optional[List]:
        """Render the content for the current tab."""
        current_tab = st.session_state.get('current_tab', 'Upload')
        
        if current_tab not in self.pages:
            st.error(f"Unknown tab: {current_tab}")
            return None
            
        return self.pages[current_tab].render()