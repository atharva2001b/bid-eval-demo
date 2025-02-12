import streamlit as st
import pandas as pd
from state_manager import StateManager

class EvaluationPage:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager

    def render(self):
        """Render the evaluation page content."""
        st.header("Evaluation Reports")
        
        results = self.state_manager.get_results()
        if not results:
            self._render_empty_state()
            return

        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📋 Reports", "📊 Comparison Table", "📈 Visual Analysis"])
        
        with tab1:
            self._render_individual_reports(results)
            
        with tab2:
            self._render_comparison_table()
            
        with tab3:
            self._render_visual_analysis()

    def _render_empty_state(self):
        """Render empty state message."""
        st.info("No evaluation reports available yet. Please upload documents to begin analysis.", icon="ℹ️")
        if st.button("Upload Documents", type="primary"):
            st.session_state.current_tab = "Upload"
            st.rerun()

    def _render_individual_reports(self, results):
        """Render individual evaluation reports."""
        for file_name, result in results.items():
            with st.expander(f"📊 {file_name}", expanded=False):
                if 'evaluation_report' in result:
                    st.markdown(result['evaluation_report'])
                    
                    if st.button("Export Report", key=f"export_{file_name}"):
                        self._export_evaluation(file_name, result['evaluation_report'])
                else:
                    st.warning("No evaluation report available for this document.")

    def _render_comparison_table(self):
        """Render detailed comparison table."""
        analytics = self.state_manager.get_evaluation_analytics()
        if not analytics:
            st.info("No comparison data available yet.")
            return

        # Create comparison DataFrame
        comparison_data = []
        for file_name, analysis in analytics.items():
            data = {
                'Document': file_name,
                'Company': analysis.company_name or 'N/A',
                'Technical Score': f"{analysis.technical_score}%" if analysis.technical_score is not None else 'N/A',
                'Commercial Score': f"{analysis.commercial_score}%" if analysis.commercial_score is not None else 'N/A',
                'Compliance Score': f"{analysis.compliance_score}%" if analysis.compliance_score is not None else 'N/A',
                'Risk Score': f"{analysis.risk_score}%" if analysis.risk_score is not None else 'N/A',
                'Overall Score': f"{analysis.overall_score}%" if analysis.overall_score is not None else 'N/A',
                'Key Strengths': ', '.join(analysis.key_strengths[:3]) if analysis.key_strengths else 'N/A',
                'Key Weaknesses': ', '.join(analysis.key_weaknesses[:3]) if analysis.key_weaknesses else 'N/A',
                'Risk Factors': ', '.join(analysis.risk_factors[:3]) if analysis.risk_factors else 'N/A',
                'Pricing Details': analysis.pricing_details or 'N/A',
                'Delivery Timeline': analysis.delivery_timeline or 'N/A'
            }
            comparison_data.append(data)

        df = pd.DataFrame(comparison_data)
        
        # Display filters
        st.subheader("Comparison Filters")
        cols = st.columns(3)
        with cols[0]:
            min_score = st.slider("Minimum Overall Score", 0, 100, 0, 5)
        with cols[1]:
            selected_companies = st.multiselect(
                "Filter by Company",
                options=df['Company'].unique(),
                default=df['Company'].unique()
            )
        
        # Apply filters
        filtered_df = df.copy()
        
        # Convert percentage strings to floats, handling 'N/A' values
        filtered_df['Score_Numeric'] = filtered_df['Overall Score'].apply(
            lambda x: float(x.rstrip('%')) if x != 'N/A' else 0
        )
        
        # Apply filters
        filtered_df = filtered_df[
            (filtered_df['Score_Numeric'] >= min_score) &
            (filtered_df['Company'].isin(selected_companies))
        ]
        
        # Remove the temporary numeric column
        filtered_df = filtered_df.drop('Score_Numeric', axis=1)
        
        # Main comparison table
        st.subheader("Detailed Comparison")
        st.dataframe(
            filtered_df,
            column_config={
                "Document": st.column_config.TextColumn("Document", width="medium"),
                "Company": st.column_config.TextColumn("Company", width="medium"),
                "Technical Score": st.column_config.NumberColumn(
                    "Technical Score",
                    help="Technical evaluation score",
                    format="%d%%"
                ),
                "Commercial Score": st.column_config.NumberColumn(
                    "Commercial Score",
                    help="Commercial evaluation score",
                    format="%d%%"
                ),
                "Overall Score": st.column_config.NumberColumn(
                    "Overall Score",
                    help="Overall evaluation score",
                    format="%d%%"
                ),
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Export functionality
        if st.button("Export Comparison Table"):
            self._export_comparison_table(filtered_df)

    def _render_visual_analysis(self):
        """Render visual analysis of comparison data."""
        analytics = self.state_manager.get_evaluation_analytics()
        if not analytics:
            st.info("No data available for visual analysis.")
            return

        st.subheader("Score Distribution")
        
        # Prepare data for visualization
        score_data = []
        for file_name, analysis in analytics.items():
            if analysis.overall_score:  # Only include if we have scores
                score_data.append({
                    'Company': analysis.company_name or file_name,
                    'Technical': analysis.technical_score or 0,
                    'Commercial': analysis.commercial_score or 0,
                    'Compliance': analysis.compliance_score or 0,
                    'Risk': analysis.risk_score or 0,
                    'Overall': analysis.overall_score or 0
                })

        if score_data:
            df = pd.DataFrame(score_data)
            st.bar_chart(df.set_index('Company'))

    def _export_evaluation(self, file_name: str, evaluation_report: str):
        """Export individual evaluation report."""
        st.download_button(
            label="Download Report",
            data=evaluation_report,
            file_name=f"{file_name}_evaluation.md",
            mime="text/markdown"
        )

    def _export_comparison_table(self, df: pd.DataFrame):
        """Export comparison table as CSV."""
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Comparison Table",
            data=csv,
            file_name="bid_comparison.csv",
            mime="text/csv"
        )