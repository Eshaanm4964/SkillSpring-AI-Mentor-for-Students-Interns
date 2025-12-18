import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import random

from assessments import (
    SkillAssessment, 
    CodeQualityMetrics, 
    PerformanceAnalytics,
    SkillLevel,
    SkillAssessor,
    assess_skills,
    get_code_quality_metrics,
    track_performance
)

def show_assessment_page(openai_client):
    """Display the assessment dashboard."""
    st.title("📊 Skill Assessment & Analytics")
    
    # Initialize session state for assessments if not exists
    if 'performance_analytics' not in st.session_state:
        st.session_state.performance_analytics = PerformanceAnalytics(
            user_id="demo_user"
        )
    
    # Create tabs for different assessment views
    tab1, tab2, tab3 = st.tabs(["Code Assessment", "Skill Progress", "Code Quality"])
    
    with tab1:
        show_code_assessment(openai_client)
    
    with tab2:
        show_skill_progress()
    
    with tab3:
        show_code_quality_metrics()

def show_code_assessment(openai_client):
    """Show the code assessment interface."""
    st.header("Code Assessment")
    
    # Code input
    code = st.text_area(
        "Paste your code here for assessment:",
        height=300,
        placeholder="# Your code here...\ndef example_function():\n    print('Hello, World!')"
    )
    
    language = st.selectbox(
        "Select programming language:",
        ["Python", "JavaScript", "Java", "C++"]
    )
    
    if st.button("Assess Code"):
        if not code.strip():
            st.warning("Please enter some code to assess.")
            return
            
        with st.spinner("Analyzing code and assessing skills..."):
            # Create assessor and get assessment
            assessor = SkillAssessor(openai_client)
            assessment = assessor.assess_skills(code, language.lower())
            
            # Track this assessment
            track_performance("demo_user", assessment)
            
            # Display results
            st.success("Assessment Complete!")
            
            # Show skill level with visual indicator
            col1, col2 = st.columns([1, 3])
            with col1:
                st.metric("Skill Level", assessment.level.value)
            with col2:
                progress = assessment.score  # Score is 0-1
                st.progress(progress)
                st.caption(f"Skill Score: {progress*100:.1f}/100")
            
            # Show feedback
            st.subheader("Feedback")
            for feedback in assessment.feedback:
                st.info(f"💡 {feedback}")
            
            # Show recommendations
            st.subheader("Recommendations")
            for rec in assessment.recommendations:
                st.success(f"✅ {rec}")

def show_skill_progress():
    """Show skill progress over time."""
    st.header("Skill Progress")
    
    # In a real app, this would come from the database
    # For demo, generate some sample data
    if not st.session_state.performance_analytics.skill_assessments:
        st.info("Complete code assessments to track your progress!")
        
        # Generate sample data for demo
        if st.button("Load Sample Data"):
            generate_sample_data()
            st.rerun()
    else:
        # Show progress chart
        skills_data = {}
        for assessment in st.session_state.performance_analytics.skill_assessments:
            skill = assessment.skill_name
            if skill not in skills_data:
                skills_data[skill] = []
            skills_data[skill].append((assessment.timestamp, assessment.score))
        
        # Create a DataFrame for plotting
        plot_data = []
        for skill, data in skills_data.items():
            for ts, score in data:
                plot_data.append({
                    "Date": ts,
                    "Skill": skill,
                    "Score": score * 100  # Convert to percentage
                })
        
        if plot_data:
            df = pd.DataFrame(plot_data)
            fig = px.line(
                df, 
                x="Date", 
                y="Score", 
                color="Skill",
                title="Skill Progress Over Time",
                labels={"Score": "Skill Score (%)"},
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Show latest assessments
        st.subheader("Recent Assessments")
        for assessment in sorted(
            st.session_state.performance_analytics.skill_assessments,
            key=lambda x: x.timestamp,
            reverse=True
        )[:5]:  # Show only last 5
            with st.expander(f"{assessment.skill_name} - {assessment.timestamp.strftime('%Y-%m-%d')}"):
                st.metric("Level", assessment.level.value)
                st.metric("Score", f"{assessment.score*100:.1f}/100")
                
                st.write("**Feedback:**")
                for fb in assessment.feedback[:3]:  # Show first 3 feedback points
                    st.info(f"💡 {fb}")

def show_code_quality_metrics():
    """Show code quality metrics and trends."""
    st.header("Code Quality Metrics")
    
    if not st.session_state.performance_analytics.code_quality_history:
        st.info("No code quality data available. Complete code assessments to see metrics.")
        return
    
    # Show current metrics
    st.subheader("Current Metrics")
    latest_metrics = st.session_state.performance_analytics.code_quality_history[-1]
    
    cols = st.columns(3)
    with cols[0]:
        st.metric("Maintainability", f"{latest_metrics.metrics.get('maintainability', 0):.1f}")
    with cols[1]:
        st.metric("Readability", f"{latest_metrics.metrics.get('readability', 0) * 100:.1f}%")
    with cols[2]:
        st.metric("Modularity", f"{latest_metrics.metrics.get('modularity', 0) * 100:.1f}%")
    
    # Show trends over time
    st.subheader("Trends Over Time")
    
    # Prepare data for plotting
    dates = []
    maintainability = []
    readability = []
    modularity = []
    
    for metrics in st.session_state.performance_analytics.code_quality_history:
        dates.append(metrics.timestamp)
        maintainability.append(metrics.metrics.get('maintainability', 0))
        readability.append(metrics.metrics.get('readability', 0) * 100)  # Convert to percentage
        modularity.append(metrics.metrics.get('modularity', 0) * 100)  # Convert to percentage
    
    # Create a DataFrame for plotting
    df = pd.DataFrame({
        'Date': dates,
        'Maintainability': maintainability,
        'Readability': readability,
        'Modularity': modularity
    })
    
    # Melt the DataFrame for plotting
    df_melted = df.melt(id_vars=['Date'], 
                        value_vars=['Maintainability', 'Readability', 'Modularity'],
                        var_name='Metric', 
                        value_name='Score')
    
    # Create the plot
    fig = px.line(
        df_melted, 
        x='Date', 
        y='Score', 
        color='Metric',
        title='Code Quality Trends',
        labels={'Score': 'Score (%)', 'Date': 'Date'},
        markers=True
    )
    
    # Update layout for better readability
    fig.update_layout(
        yaxis=dict(range=[0, 100]),  # Set y-axis from 0 to 100%
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Display the plot
    st.plotly_chart(fig, use_container_width=True)
    
    # Show recommendations based on metrics
    st.subheader("Recommendations")
    
    # Generate recommendations based on the latest metrics
    latest_maintainability = latest_metrics.metrics.get('maintainability', 0)
    latest_readability = latest_metrics.metrics.get('readability', 0)
    latest_modularity = latest_metrics.metrics.get('modularity', 0)
    
    if latest_maintainability < 60:
        st.warning("**Improve Maintainability:** Consider refactoring complex functions and adding documentation.")
    if latest_readability < 0.6:
        st.warning("**Improve Readability:** Add more comments and use more descriptive variable names.")
    if latest_modularity < 0.6:
        st.warning("**Improve Modularity:** Break down large functions into smaller, more focused ones.")

def generate_sample_data():
    """Generate sample assessment data for demo purposes."""
    # Generate sample skill assessments
    skills = ["Python Programming", "Data Analysis", "Web Development"]
    start_date = datetime.now() - timedelta(days=30)
    
    for i in range(10):  # 10 sample assessments
        skill = random.choice(skills)
        level = random.choice(list(SkillLevel))
        
        assessment = SkillAssessment(
            user_id="demo_user",
            skill_name=skill,
            level=level,
            score=random.uniform(0.3, 0.95),  # Random score
            timestamp=start_date + timedelta(days=i*3),  # Spread out over time
            feedback=[f"Sample feedback point {j+1} for {skill}" for j in range(3)],
            recommendations=[f"Sample recommendation {j+1} for {skill}" for j in range(2)]
        )
        
        # Add code quality metrics
        metrics = CodeQualityMetrics(
            file_path=f"sample_code_{i}.py",
            metrics={
                "maintainability": random.uniform(40, 90),
                "readability": random.uniform(0.4, 0.95),
                "modularity": random.uniform(0.3, 0.9)
            },
            issues=[],
            timestamp=start_date + timedelta(days=i*3)
        )
        
        # Add to performance analytics
        if 'performance_analytics' not in st.session_state:
            st.session_state.performance_analytics = PerformanceAnalytics(
                user_id="demo_user"
            )
            
        st.session_state.performance_analytics.skill_assessments.append(assessment)
        st.session_state.performance_analytics.code_quality_history.append(metrics)

# Using SkillAssessor from assessments module
