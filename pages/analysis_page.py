import streamlit as st
from state_manager import StateManager

class AnalysisPage:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager

    def render(self):
        """Render the analysis page content."""
        st.header("Analysis Results")
        
        results = self.state_manager.get_results()
        if not results:
            # Show empty state with helpful information
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.info("No analysis results available yet.", icon="ℹ️")
                
                # Add a call to action
                if st.button("Upload Documents", type="primary", key="upload_cta"):
                    st.session_state.current_tab = "Upload"
                    st.rerun()
                
                # Show what to expect
                with st.expander("What will I see here?"):
                    st.write("""
                    Once you upload documents, you'll see:
                    - Detailed analysis of each document
                    - Key information extraction
                    - Important terms and conditions
                    - Contract specifications
                    - Processing time and confidence scores
                    """)
            
            with col2:
                # Show processing steps
                st.markdown("""
                ### Analysis Process
                1. Document Upload ⏳
                2. Text Extraction 📄
                3. Content Analysis 🔍
                4. Report Generation 📊
                """)
            return

        # Display results if available
        for file_name, result in results.items():
            with st.expander(f"📄 {file_name} - Details", expanded=False):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.info(f"Processing completed in {result['processing_time']:.2f} seconds")
                with col2:
                    if st.button("Export", key=f"export_{file_name}"):
                        self.export_results(file_name, result)
                
                for query, answer in zip(result.get('queries', []), result.get('results', [])):
                    st.markdown(f"**{query}**")
                    st.write(answer)
                    st.divider()

    def export_results(self, file_name: str, result: dict):
        """Export analysis results as markdown."""
        markdown_content = f"# Analysis Results for {file_name}\n\n"
        markdown_content += f"Processing Time: {result['processing_time']:.2f} seconds\n\n"
        
        for query, answer in zip(result['queries'], result['results']):
            markdown_content += f"## {query}\n{answer}\n\n"
            
        st.download_button(
            label="Download Analysis",
            data=markdown_content,
            file_name=f"{file_name}_analysis.md",
            mime="text/markdown"
        )