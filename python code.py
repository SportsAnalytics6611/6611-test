import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Soccer Analytics Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .stMetric {
        background-color: #f0f2f6;
        border: 1px solid #e1e5e9;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .alert-high {
        background-color: #fee2e2;
        border: 1px solid #fecaca;
        color: #dc2626;
    }
    .alert-medium {
        background-color: #fef3c7;
        border: 1px solid #fde68a;
        color: #d97706;
    }
    .alert-low {
        background-color: #dcfce7;
        border: 1px solid #bbf7d0;
        color: #16a34a;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and process CSV data files from GitHub"""
    try:
        # GitHub raw URLs for your CSV files
        sub_optimizer_url = "https://raw.githubusercontent.com/Dion-Chettiar/Streamlit_Dashboard/refs/heads/main/sub_optimizer%202.csv"
        performance_url = "https://raw.githubusercontent.com/Dion-Chettiar/Streamlit_Dashboard/refs/heads/main/Performance_Dropoff_Per_Player.csv"
        
        # Load CSV files
        sub_data = pd.read_csv(sub_optimizer_url)
        perf_data = pd.read_csv(performance_url)
        
        # Clean column names
        sub_data.columns = sub_data.columns.str.strip()
        perf_data.columns = perf_data.columns.str.strip()
        
        # Merge datasets on Player column
        merged_data = pd.merge(
            sub_data, 
            perf_data[['Player', 'Actual Impact']].rename(columns={'Actual Impact': 'Actual_Impact_Perf'}), 
            on='Player', 
            how='left'
        )
        
        # Calculate overperformance using existing Impact column from sub_data (which matches Actual Impact)
        merged_data['Overperformance'] = merged_data['Impact'] - merged_data['Predicted Impact']
        
        # Clean and format data
        merged_data = merged_data.dropna()
        merged_data['Player'] = merged_data['Player'].str.strip()
        merged_data['Position'] = merged_data['Position'].str.strip()
        
        # Rename columns for better display
        merged_data = merged_data.rename(columns={
            'Impact': 'Actual Impact',
            'Fatigue_Score': 'Fatigue Score',
            'Sub_Recommendation': 'Sub Recommendation',
            'Sub Early Probability': 'Sub Early Probability'
        })
        
        return merged_data
        
    except Exception as e:
        st.error(f"Error loading data from GitHub: {e}")
        return pd.DataFrame()

def get_fatigue_color(score):
    """Return color emoji based on fatigue score"""
    if score > 2:
        return "🔴"
    elif score > 1:
        return "🟡"
    else:
        return "🟢"

def get_recommendation_color(recommendation):
    """Return color styling for recommendations"""
    colors = {
        'Sub Early': '#ef4444',
        'Monitor': '#f59e0b', 
        'Keep in Game': '#22c55e'
    }
    return colors.get(recommendation, '#6b7280')

# Load data
data = load_data()

if not data.empty:
    # Dashboard header
    st.title("⚽ Soccer Analytics Dashboard")
    st.markdown("*Real-time analysis from GitHub CSV data*")
    
    # Quick stats row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Players", len(data))
    with col2:
        avg_fatigue = data['Fatigue Score'].mean()
        st.metric("Avg Fatigue Score", f"{avg_fatigue:.2f}")
    with col3:
        high_fatigue = len(data[data['Fatigue Score'] > 2])
        st.metric("High Fatigue Players", high_fatigue)
    with col4:
        sub_early_count = len(data[data['Sub Recommendation'] == 'Sub Early'])
        st.metric("Sub Early Recommendations", sub_early_count)
    
    # Sidebar controls
    st.sidebar.header("📊 Dashboard Controls")
    
    # Filtering options
    unique_recommendations = ['All'] + sorted(data['Sub Recommendation'].unique().tolist())
    unique_positions = ['All'] + sorted([pos.strip() for pos in ','.join(data['Position'].unique()).split(',') if pos.strip()])
    
    # Filters
    top_n = st.sidebar.slider("Show Top N Players", 5, 50, 15)
    selected_recommendation = st.sidebar.selectbox(
        "Filter by Recommendation", 
        unique_recommendations
    )
    selected_position = st.sidebar.selectbox(
        "Filter by Position", 
        unique_positions
    )
    
    # Fatigue score filter
    fatigue_range = st.sidebar.slider(
        "Fatigue Score Range",
        float(data['Fatigue Score'].min()),
        float(data['Fatigue Score'].max()),
        (float(data['Fatigue Score'].min()), float(data['Fatigue Score'].max()))
    )
    
    # Apply filters
    filtered_data = data.copy()
    
    if selected_recommendation != 'All':
        filtered_data = filtered_data[filtered_data['Sub Recommendation'] == selected_recommendation]
    
    if selected_position != 'All':
        filtered_data = filtered_data[filtered_data['Position'].str.contains(selected_position, na=False)]
    
    # Apply fatigue filter
    filtered_data = filtered_data[
        (filtered_data['Fatigue Score'] >= fatigue_range[0]) & 
        (filtered_data['Fatigue Score'] <= fatigue_range[1])
    ]
    
    # Get top performers based on overperformance
    top_performers = filtered_data.nlargest(top_n, 'Overperformance')
    
    # Main dashboard layout
    col_left, col_right = st.columns([3, 1])
    
    with col_left:
        st.subheader(f"🎯 Top {top_n} Overperforming Players")
        
        if not top_performers.empty:
            # Interactive bar chart
            fig = px.bar(
                top_performers,
                x='Overperformance',
                y='Player',
                orientation='h',
                color='Fatigue Score',
                color_continuous_scale='RdYlGn_r',
                title=f"Player Overperformance Analysis ({len(top_performers)} players)",
                labels={'Overperformance': 'Overperformance Value', 'Player': 'Player Name'},
                hover_data=['Position', 'Minutes', 'Actual Impact', 'Sub Recommendation']
            )
            
            fig.update_layout(
                height=max(400, len(top_performers) * 25),
                showlegend=True,
                xaxis_title="Overperformance Value",
                yaxis_title="Player",
                font=dict(size=12)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No players found matching the current filters.")
    
    with col_right:
        st.subheader("🚨 Featured Player")
        
        # Highest fatigue player in filtered data
        if not filtered_data.empty:
            highest_fatigue_player = filtered_data.loc[filtered_data['Fatigue Score'].idxmax()]
            
            fatigue_emoji = get_fatigue_color(highest_fatigue_player['Fatigue Score'])
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>{highest_fatigue_player['Player']}</h3>
                <h1>{fatigue_emoji} {highest_fatigue_player['Fatigue Score']:.2f}</h1>
                <p><strong>Fatigue Score</strong></p>
                <hr style="border-color: rgba(255,255,255,0.3);">
                <p><strong>Position:</strong> {highest_fatigue_player['Position']}</p>
                <p><strong>Minutes:</strong> {highest_fatigue_player['Minutes']:,.0f}</p>
                <p><strong>Overperformance:</strong> {highest_fatigue_player['Overperformance']:.4f}</p>
                <p><strong>Recommendation:</strong> {highest_fatigue_player['Sub Recommendation']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("No players match current filters.")
    
    # Data table section
    st.subheader("📋 Player Performance Analysis")
    
    if not filtered_data.empty:
        # Sorting options
        sort_col1, sort_col2 = st.columns(2)
        with sort_col1:
            sort_column = st.selectbox(
                "Sort by:", 
                ['Overperformance', 'Fatigue Score', 'Minutes', 'Actual Impact', 'Sub Early Probability']
            )
        with sort_col2:
            sort_order = st.radio("Order:", ['Descending', 'Ascending'], horizontal=True)
        
        # Sort data
        ascending = sort_order == 'Ascending'
        display_data = filtered_data.sort_values(sort_column, ascending=ascending)
        
        # Format data for display
        display_columns = [
            'Player', 'Position', 'Minutes', 'Actual Impact', 
            'Predicted Impact', 'Overperformance', 'Fatigue Score', 
            'Sub Recommendation', 'Sub Early Probability'
        ]
        
        formatted_data = display_data[display_columns].copy()
        
        # Format numeric columns
        numeric_columns = ['Actual Impact', 'Predicted Impact', 'Overperformance']
        for col in numeric_columns:
            formatted_data[col] = formatted_data[col].apply(lambda x: f"{x:.4f}")
        
        formatted_data['Fatigue Score'] = formatted_data['Fatigue Score'].apply(lambda x: f"{x:.2f}")
        formatted_data['Minutes'] = formatted_data['Minutes'].apply(lambda x: f"{x:,.0f}")
        formatted_data['Sub Early Probability'] = formatted_data['Sub Early Probability'].apply(lambda x: f"{x:.3f}")
        
        # Display interactive table
        st.dataframe(
            formatted_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Player": st.column_config.TextColumn("Player", width="medium"),
                "Position": st.column_config.TextColumn("Position", width="small"),
                "Minutes": st.column_config.TextColumn("Minutes", width="small"),
                "Fatigue Score": st.column_config.TextColumn("Fatigue Score", width="small"),
                "Sub Recommendation": st.column_config.TextColumn("Recommendation", width="medium"),
                "Sub Early Probability": st.column_config.TextColumn("Sub Probability", width="small")
            }
        )
        
        # Download functionality
        st.subheader("📥 Export Data")
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = formatted_data.to_csv(index=False)
            st.download_button(
                label="📁 Download Filtered Data as CSV",
                data=csv_data,
                file_name=f"soccer_analytics_filtered_{len(formatted_data)}_players.csv",
                mime="text/csv"
            )
        
        with col2:
            full_csv = data.to_csv(index=False)
            st.download_button(
                label="📁 Download Full Dataset as CSV", 
                data=full_csv,
                file_name="soccer_analytics_full_dataset.csv",
                mime="text/csv"
            )
    
    else:
        st.warning("No data available with current filters. Please adjust your selection.")
    
    # Summary statistics
    if not filtered_data.empty:
        st.subheader("📊 Dataset Summary")
        
        summary_col1, summary_col2 = st.columns(2)
        
        with summary_col1:
            st.write("**Recommendation Distribution:**")
            recommendation_counts = filtered_data['Sub Recommendation'].value_counts()
            
            fig_pie = px.pie(
                values=recommendation_counts.values,
                names=recommendation_counts.index,
                title="Recommendation Distribution",
                color_discrete_map={
                    'Sub Early': '#ef4444',
                    'Monitor': '#f59e0b',
                    'Keep in Game': '#22c55e'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with summary_col2:
            st.write("**Fatigue Score Distribution:**")
            
            fig_hist = px.histogram(
                filtered_data,
                x='Fatigue Score',
                nbins=20,
                title="Fatigue Score Distribution",
                color_discrete_sequence=['#3b82f6']
            )
            fig_hist.add_vline(x=1, line_dash="dash", line_color="orange", 
                              annotation_text="Moderate Fatigue")
            fig_hist.add_vline(x=2, line_dash="dash", line_color="red", 
                              annotation_text="High Fatigue")
            
            st.plotly_chart(fig_hist, use_container_width=True)
    
    # Footer with key insights
    st.markdown("---")
    st.subheader("🔍 Key Insights")
    
    if not data.empty:
        # Calculate insights
        high_fatigue_players = data[data['Fatigue Score'] > 2]
        top_overperformers = data.nlargest(5, 'Overperformance')
        sub_early_players = data[data['Sub Recommendation'] == 'Sub Early']
        
        insight_col1, insight_col2, insight_col3 = st.columns(3)
        
        with insight_col1:
            st.markdown(f"""
            **🚨 High Risk Players:**
            - {len(high_fatigue_players)} players with fatigue score > 2
            - Average overperformance: {high_fatigue_players['Overperformance'].mean():.4f}
            - Recommendation: Monitor closely for substitution
            """)
        
        with insight_col2:
            st.markdown(f"""
            **⭐ Top Performers:**
            - Best overperformance: {top_overperformers['Overperformance'].iloc[0]:.4f}
            - By: {top_overperformers['Player'].iloc[0]}
            - Average minutes: {top_overperformers['Minutes'].mean():.0f}
            """)
        
        with insight_col3:
            st.markdown(f"""
            **🔄 Substitution Strategy:**
            - {len(sub_early_players)} players recommended for early sub
            - Average fatigue of sub candidates: {sub_early_players['Fatigue Score'].mean():.2f}
            - Potential impact preservation: {sub_early_players['Overperformance'].sum():.4f}
            """)

else:
    st.error("❌ No data available. Please check your GitHub CSV files.")
    st.info("Expected files: sub_optimizer 2.csv and Performance_Dropoff_Per_Player.csv")
    st.markdown("""
    **Troubleshooting:**
    - Verify that the CSV files exist at the specified GitHub URLs
    - Check if the repository is public
    - Ensure the file names match exactly (including spaces and special characters)
    """)