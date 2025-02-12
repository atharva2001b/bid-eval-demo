import streamlit as st
from state_manager import StateManager

class NavBar:
    def __init__(self):
        self.state_manager = StateManager()
        if 'current_tab' not in st.session_state:
            st.session_state.current_tab = "Upload"

    def render(self):
        """Render the navigation bar."""
        st.markdown("---")
        cols = st.columns(3)
        
        with cols[0]:
            if st.button("📤 Upload hii", 
                        key="nav_upload",
                        help="Upload new bid documents",
                        use_container_width=True,
                        type="primary" if st.session_state.current_tab == "Upload" else "secondary"):
                st.session_state.current_tab = "Upload"
                st.rerun()

        with cols[1]:
            if st.button("📊 Analysis", 
                        key="nav_analysis",
                        help="View detailed analysis",
                        use_container_width=True,
                        type="primary" if st.session_state.current_tab == "Analysis" else "secondary"):
                st.session_state.current_tab = "Analysis"
                st.rerun()

        with cols[2]:
            if st.button("📋 Evaluation", 
                        key="nav_evaluation",
                        help="View evaluation reports",
                        use_container_width=True,
                        type="primary" if st.session_state.current_tab == "Evaluation" else "secondary"):
                st.session_state.current_tab = "Evaluation"
                st.rerun()
                
        st.markdown("---")

    def get_current_tab(self):
        """Get the currently selected tab."""
        return st.session_state.current_tab