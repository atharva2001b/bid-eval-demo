import streamlit as st
from typing import List
from state_manager import StateManager

class UploadPage:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager

    def render(self) -> List:
        """Render the upload page content."""
        st.header("Upload Documents")
        
        # Create columns for layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("Upload one or more PDF files to analyze contracts and generate evaluation reports.")
            
            # File uploader
            uploaded_files = st.file_uploader(
                "Choose PDF files",
                type="pdf",
                accept_multiple_files=True,
                key="pdf_uploader"
            )

            # Show placeholder when no files are uploaded
            if not uploaded_files:
                st.info("👆 Upload your bid documents here to get started!", icon="ℹ️")
                
                # Example information
                with st.expander("ℹ️ What documents can I analyze?"):
                    st.write("""
                    You can upload any PDF documents related to:
                    - Bid proposals
                    - Tender documents
                    - RFP responses
                    - Contract documents
                    - Technical specifications
                    """)
            else:
                # Show uploaded files status
                st.write(f"Selected {len(uploaded_files)} file(s):")
                for file in uploaded_files:
                    status_col1, status_col2 = st.columns([3, 1])
                    with status_col1:
                        st.write(f"📄 {file.name}")
                    with status_col2:
                        if self.state_manager.is_file_processed(file.name):
                            st.success("Processed", icon="✅")
                        else:
                            st.info("Pending", icon="⏳")
        
        with col2:
            # Show quick stats if there are processed files
            processed_files = len(self.state_manager.get_results())
            if processed_files > 0:
                st.metric("Files Processed", processed_files)
            else:
                # Show helper card
                st.markdown("""
                🔍 **Quick Guide**
                1. Upload PDF files
                2. Wait for processing
                3. View analysis results
                4. Check evaluation reports
                """)

        return uploaded_files