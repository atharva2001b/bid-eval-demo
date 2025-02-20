import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from state_manager import StateManager

class EvaluationPage:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager

    def _create_radar_chart(self, df: pd.DataFrame):
        """Create an enhanced radar chart for score comparison."""
        score_cols = ['Technical Score', 'Commercial Score', 'Compliance Score', 'Risk Score']
        
        fig = go.Figure()
        for company in df['Company'].unique():
            company_data = df[df['Company'] == company]
            fig.add_trace(go.Scatterpolar(
                r=company_data[score_cols].values[0],
                theta=score_cols,
                fill='toself',
                name=company
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(size=10),
                    gridcolor="rgba(0,0,0,0.1)"
                )
            ),
            showlegend=True,
            title="Score Distribution Analysis",
            height=400
        )
        return fig

    def _create_score_breakdown(self, df: pd.DataFrame):
        """Create a detailed score breakdown chart."""
        fig = go.Figure()
        
        companies = df['Company'].tolist()
        score_cols = ['Technical Score', 'Commercial Score', 'Compliance Score', 'Risk Score']
        
        for score in score_cols:
            fig.add_trace(go.Bar(
                name=score,
                x=companies,
                y=df[score],
                text=df[score].apply(lambda x: f"{x}%"),
                textposition='auto',
            ))

        fig.update_layout(
            barmode='group',
            title="Detailed Score Breakdown",
            yaxis_title="Score (%)",
            yaxis_range=[0, 100],
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        return fig

    def _create_risk_assessment(self, df: pd.DataFrame):
        """Create a risk assessment visualization."""
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df['Risk Score'],
            y=df['Overall Score'],
            mode='markers+text',
            text=df['Company'],
            textposition='top center',
            marker=dict(
                size=df['Risk Score'].apply(lambda x: max(20, 50 - x/2)),
                color=df['Risk Score'],
                colorscale='RdYlGn_r',
                showscale=True,
                colorbar=dict(title="Risk Score")
            )
        ))

        fig.update_layout(
            title="Risk vs Overall Performance",
            xaxis_title="Risk Score (Lower is Better)",
            yaxis_title="Overall Score",
            height=400,
            xaxis_range=[0, 100],
            yaxis_range=[0, 100]
        )
        return fig

    def render(self):
        """Render the enhanced evaluation dashboard."""
        st.header("Bid Evaluation Dashboard")
        
        results = self.state_manager.get_results()
        if not results:
            self._render_empty_state()
            return

        # Get comparison data
        comparison_data = self.state_manager.get_comparison_data()
        if comparison_data:
            df = pd.DataFrame(comparison_data).T.reset_index()
            df.columns = ['Document'] + list(df.columns[1:])

            # Top Summary Metrics
            self._render_summary_metrics(df)

            # Main Dashboard Tabs
            tabs = st.tabs(["📊 Performance Analysis", "🎯 Detailed Scores", "📋 Reports", "📈 Data Table"])
            
            with tabs[0]:
                self._render_performance_analysis(df)
            
            with tabs[1]:
                self._render_detailed_scores(df)
            
            with tabs[2]:
                self._render_individual_reports(results)
            
            with tabs[3]:
                self._render_comparison_table(comparison_data)

    def _render_empty_state(self):
        """Render empty state message."""
        st.info("No evaluation data available. Please upload and process documents first.")
        if st.button("Upload Documents", type="primary"):
            st.session_state.current_tab = "Upload"
            st.rerun()

    def _render_summary_metrics(self, df: pd.DataFrame):
        """Render top summary metrics."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            top_performer = df.loc[df['Overall Score'].idxmax()]
            st.metric(
                "Top Performer",
                top_performer['Company'],
                f"{top_performer['Overall Score']}%"
            )
        
        with col2:
            avg_score = df['Overall Score'].mean()
            st.metric(
                "Average Score",
                f"{avg_score:.1f}%",
                f"{avg_score - 70:.1f}% vs Target"
            )
        
        with col3:
            qualified_bids = len(df[df['Overall Score'] >= 70])
            st.metric(
                "Qualified Bids",
                qualified_bids,
                f"{(qualified_bids/len(df))*100:.0f}% of total"
            )
        
        with col4:
            avg_risk = df['Risk Score'].mean()
            st.metric(
                "Average Risk Score",
                f"{avg_risk:.1f}%",
                f"{50 - avg_risk:.1f}% margin",
                delta_color="inverse"
            )

    def _render_performance_analysis(self, df: pd.DataFrame):
        """Render performance analysis section."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(self._create_radar_chart(df), use_container_width=True)
            
        with col2:
            st.plotly_chart(self._create_risk_assessment(df), use_container_width=True)
        
        # Score Breakdown
        st.plotly_chart(self._create_score_breakdown(df), use_container_width=True)
        
        # Key Insights
        with st.expander("📈 Key Insights"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("### Strengths")
                top_performer = df.loc[df['Overall Score'].idxmax()]
                st.write(f"• {top_performer['Company']} leads with {top_performer['Overall Score']:.0f}% overall score")
                st.write(f"• Average technical score: {df['Technical Score'].mean():.1f}%")
                st.write(f"• {len(df[df['Compliance Score'] >= 80])} bidders exceed 80% compliance")
                
            with col2:
                st.write("### Areas of Concern")
                high_risk = df[df['Risk Score'] > 60]['Company'].tolist()
                if high_risk:
                    st.write(f"• High risk profiles: {', '.join(high_risk)}")
                low_commercial = df[df['Commercial Score'] < 60]['Company'].tolist()
                if low_commercial:
                    st.write(f"• Low commercial scores: {', '.join(low_commercial)}")

    def _render_detailed_scores(self, df: pd.DataFrame):
        """Render detailed scores analysis."""
        # Score Distribution
        score_cols = ['Technical Score', 'Commercial Score', 'Compliance Score', 'Risk Score']
        for score_type in score_cols:
            expander_label = f"{score_type} Analysis"
            with st.expander(expander_label):
                col1, col2 = st.columns([2, 1])
                with col1:
                    fig = px.bar(
                        df,
                        x='Company',
                        y=score_type,
                        color=score_type,
                        title=f"{score_type} Distribution",
                        color_continuous_scale='viridis'
                    )
                    fig.update_layout(yaxis_range=[0, 100])
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.write(f"### {score_type} Insights")
                    avg_score = df[score_type].mean()
                    top_scorer = df.loc[df[score_type].idxmax()]
                    st.write(f"• Average: {avg_score:.1f}%")
                    st.write(f"• Top performer: {top_scorer['Company']}")
                    st.write(f"• Score range: {df[score_type].min():.0f}% - {df[score_type].max():.0f}%")
                    
                    if score_type == 'Risk Score':
                        risky_bids = df[df[score_type] > 60]['Company'].tolist()
                        if risky_bids:
                            st.write("### High Risk Bids")
                            for bid in risky_bids:
                                st.write(f"• {bid}")

    def _render_individual_reports(self, results):
        """Render individual evaluation reports."""
        for file_name, result in results.items():
            with st.expander(f"📊 {file_name} - Detailed Report", expanded=False):
                if 'evaluation_report' in result:
                    st.markdown(result['evaluation_report'])
                    st.download_button(
                        "📥 Export Report",
                        result['evaluation_report'],
                        file_name=f"{file_name}_evaluation.md",
                        mime="text/markdown"
                    )
                else:
                    st.warning("No evaluation report available for this document.")

    def _render_comparison_table(self, comparison_data):
        """Render interactive comparison table."""
        if not comparison_data:
            st.info("No comparison data available.")
            return

        df = pd.DataFrame(comparison_data).T.reset_index()
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            min_score = st.slider("Minimum Overall Score", 0, 100, 0, 5)
        with col2:
            selected_companies = st.multiselect(
                "Filter by Company",
                options=df['Company'].unique(),
                default=df['Company'].unique()
            )
        
        # Filter data
        filtered_df = df[
            (df['Overall Score'] >= min_score) &
            (df['Company'].isin(selected_companies))
        ]

        # Display interactive table
        st.dataframe(
            filtered_df,
            column_config={
                "Company": st.column_config.TextColumn("Company", width="medium"),
                "Technical Score": st.column_config.ProgressColumn(
                    "Technical Score",
                    help="Technical evaluation score",
                    format="%d%%",
                    min_value=0,
                    max_value=100
                ),
                "Commercial Score": st.column_config.ProgressColumn(
                    "Commercial Score",
                    help="Commercial evaluation score",
                    format="%d%%",
                    min_value=0,
                    max_value=100
                ),
                "Overall Score": st.column_config.ProgressColumn(
                    "Overall Score",
                    help="Overall evaluation score",
                    format="%d%%",
                    min_value=0,
                    max_value=100
                ),
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Export option
        if st.button("📥 Export Comparison Data"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                file_name="bid_comparison.csv",
                mime="text/csv"
            )