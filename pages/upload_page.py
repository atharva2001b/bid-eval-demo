import streamlit as st
from typing import List, Optional, Tuple
from state_manager import StateManager
import tempfile
import os
from rag_processor import process_queries
from pdf_processor import convert_pdf_to_text

class UploadPage:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager

    def _process_tender_document(self, tender_file) -> dict:
        """Process tender document and extract requirements."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(tender_file.getvalue())
            tmp_path = tmp_file.name

        try:
            # Convert PDF to text
            text_content = convert_pdf_to_text(tmp_path)
            
            # Define tender-specific queries
            tender_queries = [
                "what are the technical requirements or specifications?",
                "what are the eligibility criteria for bidders?",
                "what are the mandatory compliance requirements?",
                "what are the delivery and timeline requirements?",
                "what are the payment terms and financial requirements?",
                "what are the evaluation criteria and scoring system?",
                "list all the mandatory requirements that must be met",
                "what are the technical specifications and standards?"
            ]
            
            # Process queries using RAG
            results = process_queries(text_content, tender_queries)
            
            # Format tender context
            tender_context = {
                'file_name': tender_file.name,
                'queries': tender_queries,
                'results': results,
                'text_content': text_content
            }
            
            return tender_context

        except Exception as e:
            st.error(f"Error processing tender document: {str(e)}")
            return None
        finally:
            try:
                os.unlink(tmp_path)
            except Exception as e:
                print(f"Error removing temporary file: {str(e)}")

    def _render_tender_upload(self) -> Optional[dict]:
        """Render tender document upload section and return processed tender data."""
        st.subheader("Upload Tender Document")
        
        # Create columns for tender upload
        col1, col2 = st.columns([2, 1])
        
        with col1:
            tender_file = st.file_uploader(
                "Upload tender document (PDF)",
                type="pdf",
                key="tender_uploader",
                help="Upload the main tender document that contains requirements and specifications"
            )
            
            if tender_file is None:
                st.info("👆 First, upload the tender document to establish evaluation criteria")
                return None

        with col2:
            if tender_file:
                st.write("Selected tender document:")
                st.write(f"📄 {tender_file.name}")
                
                # Check if already processed
                tender_context = self.state_manager.get_tender_context()
                if tender_context and tender_context['file_name'] == tender_file.name:
                    st.success("Tender document processed", icon="✅")
                else:
                    # Process button
                    if st.button("Process Tender", key="process_tender", type="primary"):
                        with st.spinner("Processing tender document..."):
                            tender_context = self._process_tender_document(tender_file)
                            if tender_context:
                                # Store tender context
                                self.state_manager.store_tender_context(tender_context)
                                st.success("Tender document processed successfully!")
                                return tender_context
        
        # Return existing tender context if available
        return self.state_manager.get_tender_context()

    def _render_bid_upload(self, tender_context: Optional[dict]) -> List:
        """Render bid document upload section."""
        st.subheader("Upload Bid Documents")
        
        if tender_context is None:
            st.warning("Please upload and process a tender document first")
            return []
        
        # Create columns for bid upload
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_files = st.file_uploader(
                "Upload bid documents (PDF)",
                type="pdf",
                accept_multiple_files=True,
                key="bid_uploader",
                help="Upload one or more bid documents to evaluate against tender requirements"
            )

            if not uploaded_files:
                st.info("👆 Upload bid documents for evaluation against the tender requirements")
            else:
                st.write(f"Selected {len(uploaded_files)} bid document(s):")
                for file in uploaded_files:
                    status_col1, status_col2 = st.columns([3, 1])
                    with status_col1:
                        st.write(f"📄 {file.name}")
                    with status_col2:
                        if self.state_manager.is_file_processed(file.name):
                            st.success("Processed", icon="✅")
                        else:
                            st.info("Pending", icon="⏳")

        # Show tender summary if files are uploaded
        if uploaded_files:
            with st.expander("View Tender Requirements"):
                st.write("### Key Requirements from Tender Document")
                for query, result in zip(tender_context['queries'], tender_context['results']):
                    st.markdown(f"**{query}**")
                    st.write(result)
                    st.markdown("---")

        return uploaded_files

    def render(self) -> List:
        """Render the upload page with both tender and bid document sections."""
        st.header("Document Upload")
        
        # Render tender upload first
        tender_context = self._render_tender_upload()
        
        st.markdown("---")
        
        # Then render bid upload
        uploaded_files = self._render_bid_upload(tender_context)
        
        return uploaded_files  # Return uploaded bid files for processing