import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from state_manager import StateManager

class EvaluationPage:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager

    def _plot_score_comparison(self, df: pd.DataFrame):
        """Create a score comparison chart using plotly."""
        # Melt the dataframe to get scores in long format
        score_cols = ['Technical Score', 'Commercial Score', 'Compliance Score', 'Risk Score']
        df_melted = df.melt(
            id_vars=['Company'],
            value_vars=score_cols,
            var_name='Category',
            value_name='Score'
        )

        # Create radar chart
        fig = px.line_polar(
            df_melted,
            r='Score',
            theta='Category',
            color='Company',
            line_close=True,
            range_r=[0, 100]
        )
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)

    def _plot_overall_rankings(self, df: pd.DataFrame):
        """Create an overall rankings bar chart."""
        fig = px.bar(
            df,
            x='Company',
            y='Overall Score',
            title='Overall Bid Rankings',
            color='Overall Score',
            color_continuous_scale='viridis'
        )
        fig.update_layout(yaxis_range=[0, 100])
        st.plotly_chart(fig, use_container_width=True)

    def render(self):
        """Render the evaluation page content."""
        st.header("Evaluation Reports")
        
        results = self.state_manager.get_results()
        if not results:
            st.info("No evaluation reports available yet. Please upload and process documents first.")
            if st.button("Upload Documents", type="primary"):
                st.session_state.current_tab = "Upload"
                st.rerun()
            return

        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📊 Score Analysis", "📋 Reports", "📈 Comparison Table"])
        
        with tab1:
            # Get comparison data
            comparison_data = self.state_manager.get_comparison_data()
            if comparison_data:
                df = pd.DataFrame(comparison_data).T.reset_index()
                df.columns = ['Document'] + list(df.columns[1:])
                
                # Score comparison visualization
                st.subheader("Score Comparison")
                col1, col2 = st.columns(2)
                
                with col1:
                    self._plot_score_comparison(df)
                
                with col2:
                    self._plot_overall_rankings(df)
                
                # Show tender context if available
                tender_context = self.state_manager.get_tender_context()
                if tender_context:
                    with st.expander("View Tender Requirements"):
                        st.write("### Key Requirements from Tender Document")
                        for query, result in zip(tender_context['queries'], tender_context['results']):
                            st.markdown(f"**{query}**")
                            st.write(result)
                            st.markdown("---")
            
        with tab2:
            self._render_individual_reports(results)
            
        with tab3:
            self._render_comparison_table(comparison_data)

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

    def _render_comparison_table(self, comparison_data):
        """Render detailed comparison table."""
        if not comparison_data:
            st.info("No comparison data available yet.")
            return

        df = pd.DataFrame(comparison_data).T
        
        # Apply filters
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
        
        # Filter data
        mask = (df['Overall Score'] >= min_score) & (df['Company'].isin(selected_companies))
        filtered_df = df[mask]
        
        # Display table
        st.dataframe(
            filtered_df,
            column_config={
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
                "Compliance Score": st.column_config.NumberColumn(
                    "Compliance Score",
                    help="Compliance evaluation score",
                    format="%d%%"
                ),
                "Risk Score": st.column_config.NumberColumn(
                    "Risk Score",
                    help="Risk evaluation score",
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
        
        if st.button("Export Comparison"):
            self._export_comparison_table(filtered_df)

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
            label="Download Comparison",
            data=csv,
            file_name="bid_comparison.csv",
            mime="text/csv"
        )