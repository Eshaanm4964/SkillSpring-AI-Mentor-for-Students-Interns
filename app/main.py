import streamlit as st
import os
import json
import requests
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
from auth import show_login_form, is_authenticated, get_current_user, logout
import tempfile
from pathlib import Path
from openai import OpenAI
from streamlit.components.v1 import html
from streamlit_extras.stylable_container import stylable_container
import base64

# Import new features
from resume_builder import show_resume_builder
from coding_environment import show_coding_environment

# Load environment variables first
load_dotenv()

# Initialize OpenAI client with error handling
client = None
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    st.warning("⚠️ OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
else:
    try:
        client = OpenAI(api_key=openai_api_key)
        # Test the connection
        client.models.list()
    except Exception as e:
        st.error(f"❌ Error initializing OpenAI client: {str(e)}")
        st.info("Please check your OPENAI_API_KEY in the .env file and restart the app.")

# Page configuration
def main():
    st.set_page_config(
        page_title="SkillSpring - Your AI Mentor",
        page_icon="🎓",
        layout="wide"
    )
    
    # Initialize session state for navigation and authentication
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Home"
    if 'current_community_page' not in st.session_state:
        st.session_state.current_community_page = None

# Add logo and title to sidebar
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2729/2729007.png", width=80)
st.sidebar.markdown("# SkillSpring")
st.sidebar.markdown("### Your AI-Powered Career Mentor")
st.sidebar.markdown("---")

# Custom CSS for professional UI
st.markdown("""
    <style>
    /* Main theme colors */
    :root {
        --primary: #2563eb;
        --primary-dark: #1d4ed8;
        --secondary: #64748b;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --light: #f8fafc;
        --dark: #0f172a;
        --gray-100: #f1f5f9;
        --gray-200: #e2e8f0;
        --gray-300: #cbd5e1;
    }
    
    /* Global styles */
    body {
        color: var(--dark);
        background-color: #ffffff;
    }
    
    /* Sidebar */
    .css-1d391kg, .css-1y4p8pa {
        background-color: #f8fafc !important;
        border-right: 1px solid var(--gray-200);
    }
    
    /* Headers */
    .main-header { 
        color: var(--primary) !important;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    .sub-header {
        color: var(--primary-dark) !important;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--gray-200);
    }
    
    /* Cards */
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.05);
        margin: 1rem 0;
        border: 1px solid var(--gray-200);
        transition: all 0.2s ease;
    }
    
    .card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        transform: translateY(-2px);
    }
    
    /* Buttons */
    .stButton>button {
        background-color: var(--primary) !important;
        color: white !important;
        border: none;
        padding: 0.5rem 1.5rem;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton>button:hover {
        background-color: var(--primary-dark) !important;
        transform: translateY(-1px);
    }
    
    /* Input fields */
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea {
        border: 1px solid var(--gray-300) !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
    }
    
    /* Chat messages */
    .stChatMessage {
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
    }
    
    .stChatMessage:has(> .stChatMessageContent) {
        background-color: var(--gray-100);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        color: var(--secondary) !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        color: var(--primary) !important;
        border-bottom: 3px solid var(--primary) !important;
    }
    
    /* Success and error messages */
    .stAlert {
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Custom utility classes */
    .text-muted {
        color: var(--secondary) !important;
    }
    
    .bg-light {
        background-color: var(--gray-100) !important;
    }
    
    .rounded-lg {
        border-radius: 12px !important;
    }
    
    .shadow-sm {
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    }
    </style>
""", unsafe_allow_html=True)

def chat_with_mentor():
    """Chat interface with AI mentor"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💬 AI Mentor")
    st.sidebar.markdown("Ask me anything about your learning journey!")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi! I'm your AI mentor. How can I help you with your learning journey today?"}
        ]
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.sidebar.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)
    
    # Show warning if OpenAI client is not initialized
    if client is None:
        st.sidebar.warning("⚠️ OpenAI client not initialized. Please check your API key in the .env file.")
        return
    
    # Chat input
    if prompt := st.sidebar.chat_input("Ask me anything..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.sidebar.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.sidebar.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # Get context from user's profile if available
                context = {}
                if 'github_username' in st.session_state:
                    context['github_username'] = st.session_state.github_username
                
                # Create a system message with context
                system_message = {
                    "role": "system",
                    "content": f"""You are an AI mentor helping students and interns with their learning journey. 
                    The user's GitHub username is {context.get('github_username', 'not provided')}.
                    Be encouraging, specific, and provide actionable advice."""
                }
                
                # Prepare messages for the API
                messages_for_api = [system_message] + [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]
                
                # Get response from OpenAI
                response = client.responses.create(
                    model="gpt-4.1-mini",
                    input=[
                        {
                            "role": "system",
                            "content": "You are an AI mentor helping students and interns."
                        },
                        *messages_for_api
                    ],
                    temperature=0.7
                )

                full_response = response.output_text
                message_placeholder.markdown(full_response)

                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response
                })
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

def main():
    st.title("🎓 SkillSpring - Your AI Mentor")
    st.markdown("### Personalized learning roadmap and career guidance for students and interns")
    
    # Navigation with icons in the main sidebar
    with st.sidebar:
        # Show user info if logged in
        if is_authenticated():
            st.markdown(f"### 👤 {get_current_user()}")
            if st.button("🚪 Logout"):
                logout()
            st.markdown("---")
        
        st.markdown("## Navigation")
        
        # Navigation options
        nav_options = [
            "🏠 Home",
            "👤 Profile",
            "📝 Resume Builder",
            "💻 Code Practice",
            "📊 Assessment",
            "📚 Learning Path",
            "💼 Mock Interview",
            "📈 Progress"
        ]
        
        # Add community option if logged in
        if is_authenticated():
            nav_options.append("👥 Community")
        
        # Create vertical radio button navigation
        page = st.radio(
            "",
            nav_options,
            label_visibility="collapsed"
        )
        
        # Set the current page in session state
        st.session_state.current_page = page.split(" ", 1)[1]  # Remove emoji for session state
        
        # Add some space
        st.markdown("---")
        
        # Show chat interface in the main content area
        chat_with_mentor()
        
        # Add version info at the bottom
        st.markdown("---")
        st.markdown("<div style='text-align: center; color: #64748b; font-size: 0.8rem;'>v1.0.0</div>", unsafe_allow_html=True)
    
    # Main content area - full width
    if not is_authenticated():
        show_login_form()
    else:
        # Page routing using session state
        if "Home" in st.session_state.current_page:
            show_home()
        elif "Profile" in st.session_state.current_page:
            show_profile()
        elif "Resume Builder" in st.session_state.current_page:
            show_resume_builder()
        elif "Code Practice" in st.session_state.current_page:
            show_coding_environment()
        elif "Learning Path" in st.session_state.current_page:
            show_learning_path()
        elif "Mock Interview" in st.session_state.current_page:
            show_mock_interview()
        elif "Progress" in st.session_state.current_page:
            show_progress()
        elif "Assessment" in st.session_state.current_page:
            from assessments_page import show_assessment_page
            show_assessment_page(client)
        elif "Community" in st.session_state.current_page:
            if hasattr(st.session_state, 'current_community_page'):
                show_community_page(st.session_state.current_community_page)
            else:
                show_community_hub()

def show_community_page(page_name):
    """Show individual community feature pages"""
    st.title(f"Community - {page_name}")
    
    if page_name == "Activity Feed":
        st.markdown("## 🔥 Live Activity Feed")
        st.write("See what others in the community are learning and achieving in real-time.")
        
        # Sample activity data
        activities = [
            {"user": "Alex Johnson", "action": "completed", "item": "Python Basics", "time": "2 min ago"},
            {"user": "Sarah Kim", "action": "started", "item": "Data Structures", "time": "5 min ago"},
            {"user": "Michael Chen", "action": "earned", "item": "Python Expert Badge", "time": "15 min ago"},
            {"user": "Priya Patel", "action": "shared", "item": "a new project", "time": "25 min ago"},
            {"user": "David Wilson", "action": "commented on", "item": "your post", "time": "1 hour ago"}
        ]
        
        for activity in activities:
            with st.container():
                st.markdown(f"""
                <div style='padding: 1rem; border-radius: 10px; background: #f8fafc; margin: 0.5rem 0;'>
                    <strong>{activity['user']}</strong> {activity['action']} <strong>{activity['item']}</strong>
                    <div style='color: #64748b; font-size: 0.9rem;'>{activity['time']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    elif page_name == "Study Groups":
        st.markdown("## 👥 Study Groups")
        st.write("Join or create study groups with peers at your level.")
        
        # Sample study groups
        groups = [
            {"name": "Python Beginners", "members": 42, "level": "Beginner", "focus": "Python, Algorithms"},
            {"name": "Web Dev Masters", "members": 28, "level": "Intermediate", "focus": "React, Node.js"},
            {"name": "Data Science Pros", "members": 35, "level": "Advanced", "focus": "ML, Data Analysis"},
            {"name": "System Design", "members": 19, "level": "Advanced", "focus": "System Architecture"}
        ]
        
        for group in groups:
            with st.expander(f"{group['name']} - {group['members']} members"):
                st.write(f"👥 **Level:** {group['level']}")
                st.write(f"🎯 **Focus:** {group['focus']}")
                if st.button("Join Group", key=f"join_{group['name']}"):
                    st.success(f"You've joined {group['name']}!")
    
    elif page_name == "Discussion Forums":
        st.markdown("## 💬 Discussion Forums")
        st.write("Ask questions and share knowledge with the community.")
        
        # Sample discussions
        discussions = [
            {"title": "How to optimize Python code?", "replies": 12, "user": "Alex J.", "time": "2h ago"},
            {"title": "Best resources for learning React", "replies": 8, "user": "Sarah K.", "time": "5h ago"},
            {"title": "System design interview tips", "replies": 15, "user": "Mike C.", "time": "1d ago"},
            {"title": "Python vs JavaScript for beginners", "replies": 24, "user": "Priya P.", "time": "2d ago"}
        ]
        
        for discussion in discussions:
            with st.container():
                st.markdown(f"""
                <div style='padding: 1rem; border-radius: 10px; border: 1px solid #e2e8f0; margin: 0.5rem 0;'>
                    <div style='font-weight: 600;'>{discussion['title']}</div>
                    <div style='color: #64748b; font-size: 0.9rem;'>{discussion['replies']} replies • {discussion['user']} • {discussion['time']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Add new discussion button
        if st.button("Start New Discussion"):
            st.text_area("Your question or topic")
            if st.button("Post"):
                st.success("Your discussion has been posted!")
    
    elif page_name == "Leaderboard":
        st.markdown("## 🏆 Leaderboard")
        st.write("See how you rank against other learners.")
        
        # Sample leaderboard data
        leaderboard = [
            {"rank": 1, "name": "Alex Johnson", "points": 12450, "badges": 12},
            {"rank": 2, "name": "Sarah Kim", "points": 11870, "badges": 10},
            {"rank": 3, "name": "Michael Chen", "points": 10230, "badges": 9},
            {"rank": 4, "name": "You", "points": 9750, "badges": 8},
            {"rank": 5, "name": "Priya Patel", "points": 8450, "badges": 7}
        ]
        
        # Display leaderboard
        for user in leaderboard:
            if user["name"] == "You":
                st.markdown(f"""
                <div style='padding: 1rem; border-radius: 10px; background: #e0f2fe; margin: 0.5rem 0;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div style='font-weight: 600;'>
                            #{user['rank']} {user['name']} (You)
                        </div>
                        <div>
                            🏅 {user['points']} pts • {user['badges']} badges
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='padding: 1rem; border-radius: 10px; background: #f8fafc; margin: 0.5rem 0;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            #{user['rank']} {user['name']}
                        </div>
                        <div>
                            🏅 {user['points']} pts • {user['badges']} badges
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

def show_community_hub():
    """Main community hub page that links to all community features"""
    st.title("👥 Community Hub")
    st.markdown("Connect with other learners, join study groups, and participate in discussions.")
    
    # Community features grid
    community_features = [
        {
            "icon": "🔥", 
            "title": "Activity Feed", 
            "desc": "See what others are learning and achieving in real-time.",
            "color": "#ef4444"
        },
        {
            "icon": "👥", 
            "title": "Study Groups", 
            "desc": "Join or create study groups with peers at your level.",
            "color": "#3b82f6"
        },
        {
            "icon": "💬", 
            "title": "Discussion Forums", 
            "desc": "Ask questions and share knowledge with the community.",
            "color": "#10b981"
        },
        {
            "icon": "🏆", 
            "title": "Leaderboard", 
            "desc": "Compete with others and track your ranking.",
            "color": "#f59e0b"
        }
    ]
    
    # Create two rows of two features each
    for i in range(0, len(community_features), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(community_features):
                feature = community_features[i + j]
                with cols[j]:
                    if st.button(
                        f"""
                        <div style='text-align: left; padding: 1.5rem; border-radius: 12px; 
                                  border-left: 4px solid {feature['color']}; height: 100%;'>
                            <div style='font-size: 2rem; margin-bottom: 1rem;'>{feature['icon']}</div>
                            <h3 style='margin-top: 0;'>{feature['title']}</h3>
                            <p style='color: #64748b;'>{feature['desc']}</p>
                            <div style='color: {feature['color']}; font-weight: 600;'>Explore →</div>
                        </div>
                        """,
                        key=f"community_{feature['title']}",
                        use_container_width=True
                    ):
                        st.session_state.current_community_page = feature['title']
                        st.rerun()
    
    # Show the selected community page if any
    if hasattr(st.session_state, 'current_community_page'):
        show_community_page(st.session_state.current_community_page)

def show_home():
    # Add custom CSS for animations and styling
    st.markdown("""
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .fade-in {
            animation: fadeIn 0.6s ease-out forwards;
        }
        .stat-card {
            background: linear-gradient(145deg, #ffffff, #f8fafc);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
            height: 100%;
            border: 1px solid rgba(0,0,0,0.05);
        }
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            color: #2563eb;
            margin: 0.5rem 0;
        }
        .feature-card {
            transition: all 0.3s ease;
            height: 100%;
            cursor: pointer;
        }
        .feature-card:hover {
            transform: translateY(-5px);
        }
        .testimonial-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
            border-left: 4px solid #2563eb;
            transition: all 0.3s ease;
        }
        .testimonial-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(37, 99, 235, 0.1);
        }
        .progress-bar {
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            margin: 1rem 0;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: #2563eb;
            border-radius: 4px;
            transition: width 1s ease-in-out;
        }
    </style>
    """, unsafe_allow_html=True)

    # Hero Section
    st.markdown("""
    <div class='fade-in'>
        <h1 class='main-header'>Welcome to SkillSpring</h1>
        <p class='text-muted' style='font-size: 1.2rem;'>Your AI-powered career mentor and learning companion.</p>
    </div>
    """, unsafe_allow_html=True)

    # Hero section with animation
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        <div class='card fade-in' style='animation-delay: 0.2s;'>
            <h2 style='color: #2563eb;'>🚀 Accelerate Your Career Growth</h2>
            <p style='font-size: 1.1rem;'>Get personalized guidance, learning paths, and interview preparation 
            powered by AI to help you succeed in your tech career.</p>
            <a href='#' onclick='window.parent.postMessage({"action": "set_page", "page": "Profile"}, "*"); return false;' 
               style='display: inline-block; background: #2563eb; color: white; padding: 0.5rem 1.5rem; border-radius: 8px; text-decoration: none; font-weight: 600; margin-top: 1rem;'>
                Get Started →
            </a>
        </div>
        """, unsafe_allow_html=True)

    # Statistics Section
    st.markdown("<div class='fade-in' style='margin: 2rem 0;'><h2>Why Choose SkillSpring?</h2></div>", unsafe_allow_html=True)

    stats = [
        {"number": "95%", "label": "Success Rate"},
        {"number": "10K+", "label": "Active Learners"},
        {"number": "50+", "label": "Learning Paths"},
        {"number": "24/7", "label": "AI Support"}
    ]

    cols = st.columns(4)
    for i, stat in enumerate(stats):
        with cols[i]:
            st.markdown(f"""
            <div class='stat-card fade-in' style='animation-delay: {0.3 + i*0.1}s;'>
                <div class='stat-number'>{stat['number']}</div>
                <div style='color: #64748b;'>{stat['label']}</div>
            </div>
            """, unsafe_allow_html=True)

    # Features grid with hover effects
    st.markdown("<div class='fade-in' style='margin: 3rem 0 1rem 0;'><h2>Key Features</h2></div>", unsafe_allow_html=True)

    features = [
        {"icon": "📊", "title": "Personalized Roadmap", "desc": "Get a customized learning path based on your skills and career goals."},
        {"icon": "💼", "title": "Mock Interviews", "desc": "Practice with AI-powered mock interviews and get detailed feedback."},
        {"icon": "📈", "title": "Progress Tracking", "desc": "Monitor your learning journey and see your improvement over time."},
        {"icon": "🤖", "title": "AI Mentor", "desc": "Get 24/7 guidance from our AI mentor for any career-related questions."},
        {"icon": "🎯", "title": "Skill Assessment", "desc": "Test your skills and identify areas for improvement."},
        {"icon": "📱", "title": "Mobile Friendly", "desc": "Access your learning materials anytime, anywhere on any device."}
    ]

    for i in range(0, len(features), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(features):
                with cols[j]:
                    feature = features[i + j]
                    st.markdown(f"""
                    <div class='card feature-card fade-in' style='animation-delay: {0.5 + i*0.1 + j*0.1}s;'>
                        <div style='font-size: 2rem; margin-bottom: 1rem;'>{feature['icon']}</div>
                        <h4>{feature['title']}</h4>
                        <p class='text-muted'>{feature['desc']}</p>
                    </div>
                    """, unsafe_allow_html=True)

    # Testimonials Section
    st.markdown("<div class='fade-in' style='margin: 3rem 0 1rem 0;'><h2>What Our Users Say</h2></div>", unsafe_allow_html=True)

    testimonials = [
        {"name": "Alex Johnson", "role": "Software Engineer", "text": "SkillSpring helped me land my dream job at Google! The mock interviews were incredibly helpful."},
        {"name": "Sarah Kim", "role": "Data Scientist", "text": "The personalized learning path made it easy to upskill and transition into data science."},
        {"name": "Michael Chen", "role": "Product Manager", "text": "Best platform for interview preparation. The AI feedback was spot on!"}
    ]

    # Create a carousel effect using columns
    test_cols = st.columns(3)
    for i, test in enumerate(testimonials):
        with test_cols[i]:
            st.markdown(f"""
            <div class='testimonial-card fade-in' style='animation-delay: {0.8 + i*0.2}s;'>
                <p style='font-style: italic;'>&quot;{test['text']}&quot;</p>
                <div style='margin-top: 1rem; font-weight: 600;'>{test['name']}</div>
                <div style='color: #64748b; font-size: 0.9rem;'>{test['role']}</div>
            </div>
            """, unsafe_allow_html=True)

    # Community & Social Features Section
    st.markdown("<div class='fade-in' style='margin: 4rem 0 1rem 0;'><h2>Join Our Thriving Community</h2></div>", unsafe_allow_html=True)
    
    # Community Stats
    community_stats = [
        {"count": "15,000+", "label": "Active Members"},
        {"count": "500+", "label": "Study Groups"},
        {"count": "10,000+", "label": "Discussions"},
        {"count": "95%", "label": "Engagement Rate"}
    ]
    
    # Community stats cards
    cols = st.columns(4)
    for i, stat in enumerate(community_stats):
        with cols[i]:
            st.markdown(f"""
            <div class='stat-card fade-in' style='animation-delay: {0.3 + i*0.1}s; background: linear-gradient(145deg, #f8fafc, #f1f5f9);'>
                <div class='stat-number' style='color: #3b82f6;'>{stat['count']}</div>
                <div style='color: #64748b;'>{stat['label']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Community Features Grid
    st.markdown("<div class='fade-in' style='margin: 3rem 0 1rem 0;'><h3>Connect & Collaborate</h3></div>", unsafe_allow_html=True)
    
    community_features = [
        {
            "icon": "🔥", 
            "title": "Live Activity Feed", 
            "desc": "See what others are learning and achieving in real-time.",
            "link": "#activity",
            "color": "#ef4444"
        },
        {
            "icon": "👥", 
            "title": "Study Groups", 
            "desc": "Join or create study groups with peers at your level.",
            "link": "#groups",
            "color": "#3b82f6"
        },
        {
            "icon": "💬", 
            "title": "Discussion Forums", 
            "desc": "Ask questions and share knowledge with the community.",
            "link": "#discuss",
            "color": "#10b981"
        },
        {
            "icon": "🏆", 
            "title": "Leaderboard", 
            "desc": "Compete with others and track your ranking.",
            "link": "#leaderboard",
            "color": "#f59e0b"
        }
    ]
    
    # Create two rows of two features each
    for i in range(0, len(community_features), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(community_features):
                feature = community_features[i + j]
                with cols[j]:
                    # Create a container for the feature card
                    with st.container():
                        # Add custom styling
                        st.markdown(
                            f"""
                            <style>
                                .feature-card-{i}-{j} {{
                                    padding: 1.5rem;
                                    border-radius: 12px;
                                    border-left: 4px solid {feature['color']};
                                    background: white;
                                    margin-bottom: 1rem;
                                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                                    transition: all 0.3s ease;
                                }}
                                .feature-card-{i}-{j}:hover {{
                                    transform: translateY(-5px);
                                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                                }}
                            </style>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        # Create the card content
                        with st.container():
                            st.markdown(f"<div class='feature-card-{i}-{j}'>", unsafe_allow_html=True)
                            
                            # Icon and title
                            col1, col2 = st.columns([1, 5])
                            with col1:
                                st.markdown(f"<div style='font-size: 2rem;'>{feature['icon']}</div>", unsafe_allow_html=True)
                            with col2:
                                st.markdown(f"<h3 style='margin: 0;'>{feature['title']}</h3>", unsafe_allow_html=True)
                            
                            # Description
                            st.markdown(f"<p style='color: #64748b; margin: 1rem 0;'>{feature['desc']}</p>", unsafe_allow_html=True)
                            
                            # Explore button
                            if st.button(
                                "Explore →",
                                key=f"community_btn_{i}_{j}",
                                type="primary" if feature['title'] == 'Activity Feed' else "secondary"
                            ):
                                st.session_state.current_community_page = feature['title']
                                st.session_state.current_page = "Community"
                                st.rerun()
                            
                            st.markdown("</div>", unsafe_allow_html=True)
    
    # Call to Action Section
    st.markdown("""
    <div class='fade-in' style='margin: 4rem 0;'>
        <div class='card' style='background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; padding: 2rem; border-radius: 12px;'>
            <div style='max-width: 800px; margin: 0 auto; text-align: center;'>
                <h2 style='color: white;'>Ready to transform your career?</h2>
                <p style='font-size: 1.1rem; margin: 1rem 0 2rem 0;'>Join thousands of professionals who have accelerated their career growth with SkillSpring</p>
                <button class='css-1x8cf1d edgvbvh10' style='background: white; color: #2563eb; border: none; padding: 0.75rem 2rem; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 1.1rem;'>Start Your Journey Now</button>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Progress tracking preview
    st.markdown("<div class='fade-in' style='margin: 3rem 0 1rem 0;'><h2>Track Your Progress</h2></div>", unsafe_allow_html=True)

    progress_data = [
        {"skill": "Python Programming", "progress": 75},
        {"skill": "Data Structures", "progress": 60},
        {"skill": "System Design", "progress": 45},
        {"skill": "Interview Prep", "progress": 30}
    ]

    for item in progress_data:
        st.markdown(f"""
        <div class='fade-in' style='margin-bottom: 1rem;'>
            <div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
                <span>{item['skill']}</span>
                <span>{item['progress']}%</span>
            </div>
            <div class='progress-bar'>
                <div class='progress-fill' style='width: {item['progress']}%'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_profile():
    st.header("Your Profile")

    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Personal Information")
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            education = st.text_area("Education")
            
        with col2:
            st.subheader("Career Information")
            role = st.selectbox("Target Role", ["Software Developer", "Data Scientist", "ML Engineer", "Other"])
            experience = st.slider("Years of Experience", 0, 10, 0)
            skills = st.text_area("Current Skills (comma separated)")
        
        st.subheader("Resume & GitHub (Optional)")
        resume = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])
        
        with st.expander("🔗 GitHub Integration (Optional)"):
            st.markdown("""
            ### Connect Your GitHub Profile
            Connect your GitHub to unlock these features:
            - 📊 Code analysis of your repositories
            - 🎯 Personalized project recommendations
            - 📈 Contribution tracking
            - 🏆 Badges for your achievements
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                github_username = st.text_input("GitHub Username")
            with col2:
                github_token = st.text_input(
                    "Personal Access Token",
                    type="password",
                    placeholder="ghp_xxxxxxxxxxxxxxxxxxxx",
                    help="Required for private repositories. Create one at GitHub Settings > Developer Settings > Personal Access Tokens"
                )
            
            if github_username:
                if st.button("🔍 Analyze My GitHub Profile"):
                    if not github_token:
                        st.warning("A token is required to analyze private repositories. You can still analyze public repositories.")
                    analyze_github_profile(github_username, github_token)
        
        if st.form_submit_button("💾 Save Profile"):
            if resume is not None:
                save_uploaded_file(resume)
                st.success("✅ Profile and resume saved successfully!")
                
            if github_username:
                if github_token:
                    os.environ["GITHUB_TOKEN"] = github_token
                    st.session_state.github_connected = True
                    st.session_state.github_username = github_username
                    st.success("✅ GitHub connected successfully!")
                    
                    # Store GitHub data in session
                    if 'github_data' not in st.session_state:
                        st.session_state.github_data = analyze_github_profile(github_username, github_token)
                else:
                    st.session_state.github_connected = False
                    st.warning("⚠️ GitHub username saved but no token provided. Some features will be limited.")

def analyze_github_profile(username, token=None):
    """Analyze GitHub profile and return insights"""
    try:
        # Initialize GitHub API client
        headers = {"Authorization": f"token {token}"} if token else {}
        
        # Get user data
        user_url = f"https://api.github.com/users/{username}"
        repos_url = f"https://api.github.com/users/{username}/repos"
        
        with st.spinner(f"🔍 Analyzing {username}'s GitHub profile..."):
            # Get user info
            user_data = requests.get(user_url, headers=headers).json()
            
            # Get repositories
            repos = []
            page = 1
            while True:
                response = requests.get(f"{repos_url}?per_page=100&page={page}", headers=headers)
                if response.status_code != 200:
                    break
                page_repos = response.json()
                if not page_repos:
                    break
                repos.extend(page_repos)
                page += 1
            
            # Basic analysis
            total_stars = sum(repo['stargazers_count'] for repo in repos)
            total_forks = sum(repo['forks_count'] for repo in repos)
            languages = {}
            
            for repo in repos:
                if repo['language']:
                    languages[repo['language']] = languages.get(repo['language'], 0) + 1
            
            # Store results
            analysis = {
                'username': username,
                'public_repos': len(repos),
                'total_stars': total_stars,
                'total_forks': total_forks,
                'languages': sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5],
                'recent_repos': sorted(repos, key=lambda x: x['updated_at'], reverse=True)[:5]
            }
            
            # Display results
            st.success(f"✅ Successfully analyzed {username}'s profile!")
            
            # Show summary cards
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Public Repositories", analysis['public_repos'])
            with col2:
                st.metric("Total Stars", analysis['total_stars'])
            with col3:
                st.metric("Total Forks", analysis['total_forks'])
            
            # Show top languages
            st.subheader("Top Programming Languages")
            for lang, count in analysis['languages']:
                st.progress(count/len(repos), f"{lang}: {count} repos")
            
            # Show recent repositories
            st.subheader("Recent Repositories")
            for repo in analysis['recent_repos']:
                st.markdown(f"""
                ### {repo['name']}
                {repo['description'] or 'No description'}
                🌟 {repo['stargazers_count']} | 🍴 {repo['forks_count']} | 📝 {repo['language'] or 'N/A'}
                [View on GitHub]({repo['html_url']})
                ---
                """)
            
            return analysis
            
    except Exception as e:
        st.error(f"❌ Error analyzing GitHub profile: {str(e)}")
        return None

def generate_progress_chart(completed, total):
    """Generate a progress chart"""
    progress = (completed / total) * 100 if total > 0 else 0
    chart_html = f"""
    <div style="width: 100%; background: #f0f2f6; border-radius: 10px; margin: 10px 0 20px 0;">
        <div style="width: {progress}%; background: #4CAF50; color: white; text-align: center; 
                    border-radius: 10px; padding: 5px 0; font-size: 14px;">
            {int(progress)}% Complete
        </div>
    </div>
    <div style="text-align: center; margin-bottom: 20px; color: #666; font-size: 14px;">
        {completed} of {total} topics completed
    </div>
    """
    return chart_html

def show_learning_path():
    # Custom CSS
    st.markdown("""
    <style>
        /* Track cards */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            background: #ffffff;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"]:hover {
            transform: translateY(-5px);
        }
        .progress-bar {
            height: 10px;
            border-radius: 5px;
            background: #e0e0e0;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            border-radius: 5px;
            background: linear-gradient(90deg, #6366f1, #8b5cf6);
        }
        /* Resource cards */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
            padding: 0.75rem;
            margin: 0.5rem 0;
            border-left: 4px solid #8b5cf6;
            background: #f8fafc;
        }
        /* Module cards */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar - User Profile
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/artificial-intelligence.png", width=80)
        st.title("Your Learning Dashboard")
        st.progress(0.15)
        st.caption("15% of annual goal completed")
        
        st.subheader("Quick Stats")
        col1, col2 = st.columns(2)
        col1.metric("Active Tracks", "3")
        col2.metric("Completed", "2/15")
        
        st.subheader("Upcoming Deadlines")
        st.caption("Neural Networks - Due in 3 days")
        st.caption("Python Basics - Due tomorrow")
        
        if st.button("🔄 Update Progress"):
            st.success("Progress updated!")

    # Main Content
    st.title("🚀 AI/ML Engineering Learning Path")
    st.caption("Master AI/ML Engineering through this comprehensive, project-based learning path")

    # Progress Overview
    st.subheader("🎯 Your Progress")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Completion", "15%", "5% this month")
    with col2:
        st.metric("Active Days Streak", "12", "+2 days")
    with col3:
        st.metric("Hours This Week", "3.5h", "-1.2h from last week")

    # Learning Tracks
    st.subheader("📚 Learning Tracks")

    # Track 1: Deep Learning
    with st.expander("🧠 Deep Learning (10 weeks)", expanded=True):
        with stylable_container(key="track1"):
            st.markdown("### 🧠 Deep Learning Fundamentals")
            st.caption("Master the core concepts of neural networks and deep learning")
            
            # Progress
            st.markdown("**Progress** 25%")
            st.markdown('<div class="progress-bar"><div class="progress-fill" style="width: 25%"></div></div>', 
                      unsafe_allow_html=True)
            
            # Modules
            with st.expander("View Modules"):
                tab1, tab2, tab3 = st.tabs(["Neural Networks", "Deep Learning Frameworks", "Computer Vision"])
                
                with tab1:
                    st.markdown("### Neural Networks (3 weeks)")
                    st.markdown("""
                    - **Week 1-2**: Perceptrons & Activation Functions
                    - **Week 2-3**: Backpropagation & Optimization
                    - **Week 3-4**: CNNs & RNNs Architecture
                    """)
                    
                    # Resources
                    st.markdown("#### 📚 Resources")
                    with stylable_container(key="resource1"):
                        st.markdown("🎥 [Neural Networks - 3Blue1Brown](https://youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi)")
                        st.markdown("📖 [Neural Networks and Deep Learning](http://neuralnetworksanddeeplearning.com/)")
                        st.markdown("💻 [Interactive NN Playground](https://playground.tensorflow.org/)")
                    
                    # Action Buttons
                    col1, col2 = st.columns(2)
                    col1.button("Start Learning", key="nn_start", use_container_width=True)
                    col2.button("Take Quiz", key="nn_quiz", use_container_width=True)
                
                with tab2:
                    st.markdown("### Deep Learning Frameworks (4 weeks)")
                    st.markdown("""
                    - **Week 1-2**: TensorFlow/Keras Fundamentals
                    - **Week 2-3**: PyTorch Basics
                    - **Week 3-4**: Advanced Model Architectures
                    """)
                    
                    st.markdown("#### 📚 Resources")
                    with stylable_container(key="resource2"):
                        st.markdown("📖 [TensorFlow Documentation](https://www.tensorflow.org/guide)")
                        st.markdown("🎥 [PyTorch Tutorials](https://pytorch.org/tutorials/)")
                    
                    col1, col2 = st.columns(2)
                    col1.button("Start Learning", key="dl_start", use_container_width=True)
                    col2.button("Take Quiz", key="dl_quiz", use_container_width=True)
                
                with tab3:
                    st.markdown("### Computer Vision (3 weeks)")
                    st.markdown("""
                    - **Week 1**: Image Processing Basics
                    - **Week 2**: Object Detection
                    - **Week 3**: Image Segmentation
                    """)
                    
                    st.markdown("#### 📚 Resources")
                    with stylable_container(key="resource3"):
                        st.markdown("📖 [CS231n: Convolutional Neural Networks](http://cs231n.stanford.edu/)")
                        st.markdown("💻 [OpenCV Tutorials](https://docs.opencv.org/master/d9/df8/tutorial_root.html)")
                    
                    col1, col2 = st.columns(2)
                    col1.button("Start Learning", key="cv_start", use_container_width=True)
                    col2.button("Take Quiz", key="cv_quiz", use_container_width=True)

    # Track 2: Natural Language Processing
    with st.expander("📝 Natural Language Processing (7 weeks)"):
        with stylable_container(key="track2"):
            st.markdown("### 📝 Natural Language Processing")
            st.caption("From text processing to advanced language models")
            st.progress(0.1)
            
            st.markdown("""
            - **Text Processing (2 weeks)**: Tokenization, stemming, lemmatization
            - **Transformers & LLMs (3 weeks)**: BERT, GPT architectures
            - **NLP Applications (2 weeks)**: Sentiment analysis, text generation
            """)
            
            st.markdown("#### 🎯 Learning Outcomes")
            st.markdown("""
            - Build and train NLP models
            - Work with transformer architectures
            - Deploy NLP applications
            """)

    # Roadmap Visualization
    st.subheader("🗺️ Learning Roadmap")
    fig = go.Figure(go.Gantt(
        y = ["Deep Learning", "NLP", "MLOps"],
        x = [0, 10, 17],  # Start weeks
        xend = [10, 17, 22],  # End weeks
        text = ["10 weeks", "7 weeks", "5 weeks"],
        textposition = "auto",
        marker = dict(color = ["#6366f1", "#8b5cf6", "#a78bfa"]),
        hoverinfo = "text",
        hovertext = ["Deep Learning Track", "NLP Track", "MLOps Track"]
    ))

    fig.update_layout(
        title="Learning Timeline",
        xaxis_title="Weeks",
        yaxis_title="Track",
        height=200,
        showlegend=False,
        margin=dict(l=0, r=0, t=30, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Recommended Next Steps
    st.subheader("👉 Recommended Next")
    with stylable_container(key="next_steps"):
        st.markdown("### 🧠 Neural Networks Fundamentals")
        st.markdown("Start with the basics of how neural networks work")
        st.progress(0.2)
        st.button("Continue Learning", type="primary", use_container_width=True, key="continue_learning_btn")

    # Achievement Badges
    st.subheader("🏆 Your Achievements")
    
    badge_style = """
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 16px;
        background: linear-gradient(135deg, #ffffff, #f9fafb);
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    """
    
    col1, col2, col3 = st.columns(3)

    with col1:
        with stylable_container(css_styles=badge_style, key="badge1"):
            st.markdown("🎓 **Python Pro**")
            st.caption("Completed Python Fundamentals")

    with col2:
        with stylable_container(css_styles=badge_style, key="badge2"):
            st.markdown("📊 **Data Wrangler**")
            st.caption("Mastered Pandas & NumPy")

    with col3:
        with stylable_container(css_styles=badge_style, key="badge3"):
            st.markdown("🤖 **ML Enthusiast**")
            st.caption("Completed first ML project")

    # Define learning paths
    LEARNING_PATHS = {
        'Frontend Development': {
            'Core Technologies': [
                'HTML5 & CSS3 Fundamentals (2 weeks)',
                'JavaScript/TypeScript (4 weeks)',
                'Responsive Design (2 weeks)'
            ],
            'Frameworks': [
                'React.js (4 weeks)',
                'State Management (Redux/Context) (2 weeks)',
                'Modern CSS (Tailwind/SASS) (2 weeks)'
            ],
            'Advanced Topics': [
                'Progressive Web Apps (2 weeks)',
                'Web Performance (2 weeks)',
                'Testing (Jest/React Testing Library) (2 weeks)'
            ]
        },
        'Backend Development': {
            'Foundations': [
                'Node.js & Express (3 weeks)',
                'RESTful API Design (2 weeks)',
                'Database Design (2 weeks)'
            ],
            'Advanced Backend': [
                'Authentication & Authorization (2 weeks)',
                'Caching & Performance (2 weeks)',
                'Microservices Architecture (3 weeks)'
            ],
            'DevOps': [
                'Docker & Containerization (2 weeks)',
                'CI/CD Pipelines (2 weeks)',
                'Cloud Deployment (AWS/GCP/Azure) (3 weeks)'
            ]
        },
        'Mobile Development': {
            'Cross-Platform': [
                'Flutter & Dart (4 weeks)',
                'React Native (4 weeks)',
                'State Management (2 weeks)'
            ],
            'Native Development': [
                'Swift for iOS (4 weeks)',
                'Kotlin for Android (4 weeks)',
                'Platform-Specific Features (2 weeks)'
            ],
            'Publishing': [
                'App Store Guidelines (1 week)',
                'Testing & Debugging (2 weeks)',
                'App Deployment (1 week)'
            ]
        },
        # Data Science & AI/ML
        'Data Science': {
            'Foundations': [
                'Python for Data Science (3 weeks)',
                'Pandas & NumPy (3 weeks)',
                'Data Visualization (Matplotlib/Seaborn) (2 weeks)'
            ],
            'Machine Learning': [
                'Supervised Learning (4 weeks)',
                'Unsupervised Learning (3 weeks)',
                'Model Evaluation & Tuning (2 weeks)'
            ],
            'Big Data': [
                'SQL & NoSQL Databases (3 weeks)',
                'Apache Spark (3 weeks)',
                'Data Pipelines (2 weeks)'
            ]
        },
        'AI/ML Engineering': {
            'Deep Learning': [
                'Neural Networks (3 weeks)',
                'TensorFlow/PyTorch (4 weeks)',
                'Computer Vision (3 weeks)'
            ],
            'NLP': [
                'Text Processing (2 weeks)',
                'Transformers & LLMs (3 weeks)',
                'NLP Applications (2 weeks)'
            ],
            'MLOps': [
                'Model Deployment (2 weeks)',
                'ML Pipeline Automation (2 weeks)',
                'Monitoring & Maintenance (1 week)'
            ]
        },
        # Cloud & DevOps
        'Cloud Computing': {
            'Cloud Fundamentals': [
                'Cloud Concepts (1 week)',
                'AWS/Azure/GCP Core Services (3 weeks)',
                'Serverless Computing (2 weeks)'
            ],
            'Infrastructure as Code': [
                'Terraform (2 weeks)',
                'CloudFormation/CDK (2 weeks)',
                'Configuration Management (1 week)'
            ],
            'Containerization': [
                'Docker (2 weeks)',
                'Kubernetes (3 weeks)',
                'Service Mesh (1 week)'
            ]
        },
        'Cybersecurity': {
            'Fundamentals': [
                'Network Security (2 weeks)',
                'Cryptography (2 weeks)',
                'Security Protocols (1 week)'
            ],
            'Offensive Security': [
                'Ethical Hacking (3 weeks)',
                'Penetration Testing (3 weeks)',
                'Vulnerability Assessment (2 weeks)'
            ],
            'Defensive Security': [
                'SIEM Tools (2 weeks)',
                'Incident Response (2 weeks)',
                'Threat Intelligence (1 week)'
            ]
        },
        # Emerging Technologies
        'Blockchain Development': {
            'Fundamentals': [
                'Blockchain Basics (2 weeks)',
                'Smart Contracts (3 weeks)',
                'Ethereum/Solidity (3 weeks)'
            ],
            'dApps': [
                'Web3.js/ethers.js (2 weeks)',
                'Decentralized Storage (1 week)',
                'IPFS (1 week)'
            ],
            'Advanced': [
                'DeFi Protocols (2 weeks)',
                'NFT Development (2 weeks)',
                'Layer 2 Solutions (1 week)'
            ]
        },
        'Game Development': {
            'Game Design': [
                'Game Mechanics (2 weeks)',
                'Level Design (2 weeks)',
                'Game Physics (2 weeks)'
            ],
            'Development': [
                'Unity/Unreal Engine (4 weeks)',
                '3D Modeling Basics (3 weeks)',
                'Game AI (2 weeks)'
            ],
            'Publishing': [
                'Game Testing (1 week)',
                'Monetization (1 week)',
                'App Store Deployment (1 week)'
            ]
        },
        'UI/UX Design': {
            'Fundamentals': [
                'Design Principles (2 weeks)',
                'User Research (2 weeks)',
                'Wireframing (1 week)'
            ],
            'Tools': [
                'Figma/Sketch (2 weeks)',
                'Prototyping (2 weeks)',
                'Design Systems (2 weeks)'
            ],
            'Advanced': [
                'Interaction Design (2 weeks)',
                'UX Writing (1 week)',
                'Accessibility (1 week)'
            ]
        }
    }
    
    # Enhanced learning resources for each topic
    LEARNING_RESOURCES = {
        # Web Development Resources
        'HTML5 & CSS3 Fundamentals': {
            'documentation': [
                '🌐 MDN Web Docs - https://developer.mozilla.org/en-US/docs/Learn/HTML',
                '📜 W3Schools HTML - https://www.w3schools.com/html/'
            ],
            'courses': [
                '� FreeCodeCamp Responsive Web Design - https://www.freecodecamp.org/learn/responsive-web-design/',
                '🎓 CSS Grid by Wes Bos - https://cssgrid.io/'
            ],
            'practice': [
                '💻 Frontend Mentor - https://www.frontendmentor.io/',
                '🎮 CSS Battle - https://cssbattle.dev/'
            ]
        },
        'JavaScript/TypeScript': {
            'documentation': [
                '� JavaScript.info - https://javascript.info/',
                '� TypeScript Handbook - https://www.typescriptlang.org/docs/'
            ],
            'courses': [
                '🎓 JavaScript30 - https://javascript30.com/',
                '🎓 TypeScript Course for Beginners - https://www.udemy.com/course/typescript/'
            ],
            'practice': [
                '💻 Codewars - https://www.codewars.com/',
                '🎯 LeetCode - https://leetcode.com/'
            ]
        },
        'React.js': {
            'documentation': [
                '⚛️ React Official Docs - https://reactjs.org/docs/getting-started.html',
                '📖 React Patterns - https://reactpatterns.com/'
            ],
            'courses': [
                '🎓 Scrimba Learn React - https://scrimba.com/learn/learnreact',
                '� Full Modern React - https://www.udemy.com/course/modern-react-bootcamp/'
            ],
            'practice': [
                '💡 Frontend Practice - https://www.frontendpractice.com/',
                '🛠️ React Challenges - https://github.com/Asabeneh/React-Exercise/'
            ]
        },
        # Data Science Resources
        'Python for Data Science': {
            'documentation': [
                '🐍 Python Data Science Handbook - https://jakevdp.github.io/PythonDataScienceHandbook/',
                '📊 Pandas Documentation - https://pandas.pydata.org/docs/'
            ],
            'courses': [
                '🎓 Data Science with Python - https://www.coursera.org/learn/python-for-data-science',
                '🎓 Python for Data Science - https://www.udacity.com/course/intro-to-python-for-data-science--ud110'
            ],
            'practice': [
                '📈 Kaggle Learn - https://www.kaggle.com/learn',
                '🔍 DataCamp Projects - https://www.datacamp.com/projects'
            ]
        },
        'Scikit-learn': {
            'documentation': [
                '📚 Scikit-learn User Guide - https://scikit-learn.org/stable/user_guide.html',
                '📖 Introduction to ML with Python - https://www.oreilly.com/library/view/introduction-to-machine/9781449369880/'
            ],
            'courses': [
                '🎓 Machine Learning with Python - https://www.coursera.org/learn/machine-learning-with-python',
                '🎓 Hands-On ML with Scikit-Learn - https://www.udemy.com/course/hands-on-machine-learning-with-scikit-learn/'
            ],
            'practice': [
                '🏆 Kaggle Competitions - https://www.kaggle.com/competitions',
                '🧠 Machine Learning Exercises - https://github.com/ageron/handson-ml2'
            ]
        },
        # Add more topics as needed
    }

    # User input form
    with st.expander("🎯 Set Your Learning Goals", expanded=not st.session_state.learning_goals):
        with st.form("learning_goals_form"):
            st.subheader("Customize Your Learning Path")
            
            # Basic information
            col1, col2 = st.columns(2)
            with col1:
                current_level = st.selectbox(
                    "Your Current Skill Level",
                    ["Beginner", "Intermediate", "Advanced"]
                )
            with col2:
                time_commitment = st.selectbox(
                    "Weekly Study Time",
                    ["1-5 hours", "5-10 hours", "10-15 hours", "15+ hours"]
                )
            
            # Learning track selection
            learning_track = st.selectbox(
                "Choose Your Learning Track",
                list(LEARNING_PATHS.keys())
            )
            
            # Specific goals
            goals = st.multiselect(
                "What are your main goals? (Select up to 3)",
                ["Get a job", "Build a portfolio", "Freelance", "Start a startup", "Learn for fun"],
                max_selections=3
            )
            
            # Submit button
            if st.form_submit_button("Generate Learning Path"):
                st.session_state.learning_goals = {
                    'current_level': current_level,
                    'time_commitment': time_commitment,
                    'learning_track': learning_track,
                    'goals': goals
                }
                st.success("✅ Learning path generated successfully!")
                st.rerun()
    
    # Display learning path if goals are set
    if st.session_state.learning_goals:
        track = st.session_state.learning_goals['learning_track']
        categories = LEARNING_PATHS[track]
        
        # Calculate progress
        total_topics = sum(len(topics) for topics in categories.values())
        completed_topics = sum(1 for key in st.session_state.learning_path 
                             if key.startswith(track) and st.session_state.learning_path[key])
        
        # Header with progress
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### 🎯 {track} Track")
            st.caption(f"Level: {st.session_state.learning_goals['current_level']} | "
                     f"Time Commitment: {st.session_state.learning_goals['time_commitment']} per week")
        with col2:
            st.markdown(generate_progress_chart(completed_topics, total_topics), unsafe_allow_html=True)
        
        # Detailed view with checkboxes and resources
        st.markdown("### 📚 Detailed Learning Path")
        for category, topics in categories.items():
            with st.expander(f"### 🗂️ {category}", expanded=True):
                for i, topic in enumerate(topics, 1):
                    # Create a unique key for each topic's checkbox
                    topic_key = f"{track}_{category}_{i}"
                    if topic_key not in st.session_state.learning_path:
                        st.session_state.learning_path[topic_key] = False
                    
                    # Display topic with checkbox and resources
                    col1, col2 = st.columns([1, 15])
                    with col1:
                        completed = st.checkbox(
                            "",
                            value=st.session_state.learning_path[topic_key],
                            key=f"check_{topic_key}",
                            on_change=lambda k=topic_key: st.session_state.learning_path.update({
                                k: not st.session_state.learning_path.get(k, False)
                            })
                        )
                    with col2:
                        topic_name = topic.split('(')[0].strip()
                        topic_weeks = topic[topic.find("("):] if "(" in topic else ""
                        st.markdown(f"**{topic_name}** {topic_weeks}")
                        
                        # Show resources if available
                        for t in LEARNING_RESOURCES.keys():
                            if t.lower() in topic.lower():
                                with st.expander("📚 Learning Resources", expanded=False):
                                    st.markdown("### 📚 Learning Resources")
                                    
                                    # Documentation
                                    if 'documentation' in LEARNING_RESOURCES[t]:
                                        st.markdown("#### 📚 Documentation")
                                        for resource in LEARNING_RESOURCES[t]['documentation']:
                                            st.markdown(f"- {resource}")
                                        st.write("")
                                    
                                    # Courses
                                    if 'courses' in LEARNING_RESOURCES[t]:
                                        st.markdown("#### 🎓 Courses")
                                        for resource in LEARNING_RESOURCES[t]['courses']:
                                            st.markdown(f"- {resource}")
                                        st.write("")
                                    
                                    # Practice Platforms
                                    if 'practice' in LEARNING_RESOURCES[t]:
                                        st.markdown("#### 🏋️ Practice")
                                        for resource in LEARNING_RESOURCES[t]['practice']:
                                            st.markdown(f"- {resource}")
                                        st.write("")
                                    
                                    # Add a note about more resources
                                    st.info("💡 Pro Tip: Bookmark your favorite resources and track your progress!")
                                break
    else:
        st.info("🎯 Set your learning goals above to generate a personalized learning path.")
        
        # Show example learning paths
        st.subheader("Example Learning Paths")
        for track, categories in list(LEARNING_PATHS.items())[:2]:  # Show first 2 tracks as examples
            with st.expander(f"{track} Track"):
                for category, topics in categories.items():
                    st.markdown(f"**{category}**")
                    for topic in topics:
                        st.markdown(f"- {topic}")
                    st.write("")

def rate_answer(question, answer, interview_type, job_role):
    """Rate the answer on a scale of 1-5 based on relevance, depth, and role requirements"""
    # Simple rating logic - in a real app, this could use NLP or more sophisticated analysis
    word_count = len(answer.split())
    
    # Base score on answer length (just as an example)
    if word_count < 10:
        base_score = 1
    elif word_count < 30:
        base_score = 2
    elif word_count < 60:
        base_score = 3
    elif word_count < 100:
        base_score = 4
    else:
        base_score = 5
    
    # Adjust based on question type
    if "technical" in interview_type.lower():
        tech_keywords = ["I used", "I implemented", "code", "algorithm", "optimized", "debugged", "framework"]
        if any(keyword in answer.lower() for keyword in tech_keywords):
            base_score = min(5, base_score + 1)
    
    return base_score

def get_feedback(score, question_type):
    """Provide feedback based on the score"""
    if score >= 4:
        return "Great job! Your answer was detailed and relevant to the question."
    elif score >= 3:
        return "Good effort! Consider adding more specific examples or details."
    else:
        return "Try to provide more detailed and structured responses. Consider using the STAR method for behavioral questions."

def show_mock_interview():
    st.header("🎤 Mock Interview")
    st.markdown("Practice your interview skills with our AI interviewer and get instant feedback on your answers.")
    
    # Initialize session state
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
        st.session_state.answers = {}
        st.session_state.interview_started = False
        st.session_state.show_code_editor = False
    
    # Company selection
    companies = {
        "General (All Companies)": None,
        "Google": "google",
        "Amazon": "amazon",
        "Microsoft": "microsoft",
        "Meta (Facebook)": "meta",
        "Apple": "apple",
        "Netflix": "netflix",
        "Uber": "uber",
        "Airbnb": "airbnb"
    }
    selected_company = st.selectbox("Select Company", list(companies.keys()))
    
    # Job role selection
    job_roles = ["Software Engineer", "Data Scientist", "Product Manager", "UX Designer", "DevOps Engineer"]
    job_role = st.selectbox("Select Target Job Role", job_roles)
    
    # Interview type selection
    interview_type = st.selectbox(
        "Select Interview Type",
        ["Technical Interview", "Behavioral Interview", "System Design"]
    )
    
    # Question bank with company-specific questions
    questions = {
        "Technical Interview": {
            "general": [
                "Explain a challenging technical problem you solved recently.",
                "How would you optimize a slow database query?",
                "Describe your experience with version control systems.",
                "How do you handle debugging complex issues?"
            ],
            "google": [
                "How would you design a system to count the frequency of words in a large document?",
                "Find the k most frequent elements in an array.",
                "Design an LRU (Least Recently Used) cache.",
                "How would you implement a spell checker?"
            ],
            "amazon": [
                "Design a parking lot system.",
                "How would you design a recommendation system for Amazon products?",
                "Find the first non-repeating character in a string.",
                "Design an elevator system."
            ],
            "microsoft": [
                "Design a URL shortening service like bit.ly.",
                "How would you implement a text editor's undo/redo functionality?",
                "Design a file system.",
                "How would you implement a thread-safe queue?"
            ]
        },
        "Behavioral Interview": {
            "general": [
                "Tell me about a time you had to work under pressure.",
                "Describe a situation where you had to work with a difficult team member.",
                "How do you prioritize tasks when everything is a priority?",
                "Tell me about a time you failed and what you learned."
            ],
            "google": [
                "Tell me about a time you had to make a decision without all the information.",
                "Describe a time when you had to learn something new quickly.",
                "How do you handle ambiguity in projects?",
                "Tell me about a time you had to persuade someone to adopt your idea."
            ],
            "amazon": [
                "Tell me about a time you had to deal with a difficult customer.",
                "Describe a time when you had to make a decision based on incomplete data.",
                "How do you handle competing priorities?",
                "Tell me about a time you took a calculated risk."
            ]
        },
        "System Design": {
            "general": [
                "How would you design a URL shortening service like bit.ly?",
                "Design a chat application like WhatsApp.",
                "How would you scale a web application to handle millions of users?",
                "Design a recommendation system for an e-commerce platform."
            ],
            "netflix": [
                "Design a system that can handle millions of concurrent video streams.",
                "How would you design a recommendation system for Netflix?",
                "Design a system to handle video uploads and processing.",
                "How would you implement a feature to allow users to download videos for offline viewing?"
            ],
            "uber": [
                "Design a ride-sharing service like Uber.",
                "How would you implement surge pricing?",
                "Design a system to match riders with drivers efficiently.",
                "How would you handle real-time location tracking for millions of users?"
            ],
            "airbnb": [
                "Design a booking system for Airbnb.",
                "How would you implement a review and rating system?",
                "Design a search system that can handle complex filters.",
                "How would you prevent fraud in the booking system?"
            ]
        }
    }
    
    # Start interview
    if st.button("Start Mock Interview") or st.session_state.interview_started:
        st.session_state.interview_started = True
        
        # Get questions based on company selection
        company_key = companies[selected_company] or "general"
        available_questions = questions[interview_type].get(company_key, questions[interview_type]["general"])
        
        # Display current question
        current_q = available_questions[st.session_state.current_question % len(available_questions)]
        st.subheader(f"Question {st.session_state.current_question + 1}")
        st.write(current_q)
        
        # Toggle code editor for technical questions
        if interview_type in ["Technical Interview", "System Design"]:
            if st.checkbox("Use Code Editor"):
                st.session_state.show_code_editor = True
            else:
                st.session_state.show_code_editor = False
        
        # Answer input - text area or code editor
        if hasattr(st.session_state, 'show_code_editor') and st.session_state.show_code_editor:
            # Initialize code editor
            if f'code_{st.session_state.current_question}' not in st.session_state:
                st.session_state[f'code_{st.session_state.current_question}'] = "# Write your code here\n# You can run the code to test it"
            
            # Code editor with syntax highlighting
            code = st.text_area(
                "Write your code:", 
                value=st.session_state[f'code_{st.session_state.current_question}'],
                height=300,
                key=f"code_editor_{st.session_state.current_question}"
            )
            
            # Save code to session state
            st.session_state[f'code_{st.session_state.current_question}'] = code
            
            # Add run button
            if st.button("Run Code"):
                try:
                    # Create a local namespace for the code execution
                    local_namespace = {}
                    # Execute the code
                    exec(code, globals(), local_namespace)
                    st.success("Code executed successfully!")
                    # Show output if any
                    if 'output' in local_namespace:
                        st.write("Output:", local_namespace['output'])
                except Exception as e:
                    st.error(f"Error executing code: {str(e)}")
            
            # Add text area for additional explanation
            answer = st.text_area(
                "Explain your approach:", 
                key=f"explanation_{st.session_state.current_question}",
                height=150
            )
        else:
            # Regular text answer
            answer = st.text_area(
                "Your answer:", 
                key=f"answer_{st.session_state.current_question}", 
                height=150
            )
        
        if st.button("Submit Answer"):
            # Prepare answer data
            answer_data = {
                'question': current_q,
                'score': 0,  # Will be set after rating
                'feedback': ''
            }
            
            # Handle code and explanation if in code editor mode
            if hasattr(st.session_state, 'show_code_editor') and st.session_state.show_code_editor:
                answer_data['code'] = st.session_state.get(f'code_{st.session_state.current_question}', '')
                answer_data['explanation'] = answer
                answer_data['answer'] = f"Code solution with explanation: {answer}"
                
                # Execute code to get output (for display purposes)
                if answer_data['code']:
                    try:
                        local_namespace = {}
                        exec(answer_data['code'], globals(), local_namespace)
                        if 'output' in local_namespace:
                            answer_data['output'] = str(local_namespace['output'])
                    except Exception as e:
                        answer_data['output'] = f"Error executing code: {str(e)}"
            else:
                answer_data['answer'] = answer
            
            # Rate the answer
            answer_data['score'] = rate_answer(current_q, answer_data['answer'], interview_type, job_role)
            answer_data['feedback'] = get_feedback(answer_data['score'], interview_type)
            
            # Store the answer data
            st.session_state.answers[st.session_state.current_question] = answer_data
            
            # Show rating and feedback
            st.subheader("Your Score")
            st.write(f"⭐" * score + f" ({score}/5)")
            st.info(f"Feedback: {feedback}")
            
            # Move to next question or end interview
            if st.session_state.current_question < len(questions[interview_type]) - 1:
                if st.button("Next Question"):
                    st.session_state.current_question += 1
                    st.rerun()
            else:
                st.success("🎉 Interview completed! Review your answers below.")
                
                # Show summary
                st.subheader("Interview Summary")
                
                # Calculate average score
                total_score = sum(data['score'] for data in st.session_state.answers.values())
                avg_score = total_score / len(st.session_state.answers) if st.session_state.answers else 0
                
                # Display overall performance
                st.metric("Overall Performance", f"{avg_score:.1f}/5.0")
                st.progress(avg_score / 5.0)
                
                # Display detailed feedback
                for i, (q, data) in enumerate(st.session_state.answers.items()):
                    with st.expander(f"Question {q+1}: {data['question']} ({'⭐' * int(round(data['score']))} {data['score']}/5)"):
                        if 'code' in data:
                            st.subheader("Your Code:")
                            st.code(data['code'], language='python')
                            if 'output' in data:
                                st.subheader("Output:")
                                st.code(data['output'], language='')
                            if data.get('explanation'):
                                st.subheader("Your Explanation:")
                                st.write(data['explanation'])
                        else:
                            st.write(f"**Your answer:** {data['answer']}")
                        
                        st.subheader("Feedback:")
                        st.info(data['feedback'])
                        
                        # Add improvement tips
                        if data['score'] < 3:
                            st.warning("💡 **Areas for Improvement:**")
                            if interview_type == "Technical Interview":
                                st.write("- Consider providing more specific examples from your experience")
                                st.write("- Explain your thought process in more detail")
                                if 'code' in data:
                                    st.write("- Add comments to explain complex parts of your code")
                            elif interview_type == "Behavioral Interview":
                                st.write("- Use the STAR method (Situation, Task, Action, Result)")
                                st.write("- Be more specific about your role and contributions")
                            elif interview_type == "System Design":
                                st.write("- Start with clarifying questions to understand requirements")
                                st.write("- Consider edge cases and scalability from the beginning")
                
                # Add download button for interview report
                interview_report = {
                    "company": selected_company,
                    "job_role": job_role,
                    "interview_type": interview_type,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "score": avg_score,
                    "questions_answered": len(st.session_state.answers),
                    "details": [
                        {
                            "question": data['question'],
                            "answer": data.get('answer', ''),
                            "code": data.get('code', ''),
                            "explanation": data.get('explanation', ''),
                            "score": data['score'],
                            "feedback": data['feedback']
                        }
                        for q, data in st.session_state.answers.items()
                    ]
                }
                
                # Convert to JSON for download
                import json
                json_report = json.dumps(interview_report, indent=2)
                st.download_button(
                    label="📥 Download Interview Report",
                    data=json_report,
                    file_name=f"interview_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                
                if st.button("🔄 Restart Interview"):
                    st.session_state.current_question = 0
                    st.session_state.answers = {}
                    st.session_state.interview_started = False
                    st.session_state.show_code_editor = False
                    st.rerun()

def show_progress():
    st.header("Your Progress")
    st.markdown("### Weekly Progress Tracker")
    
    # Placeholder progress data
    progress_data = {
        "Week": ["Week 1", "Week 2", "Week 3", "Week 4"],
        "Completed Topics": [3, 5, 7, 4],
        "Hours Spent": [5, 8, 10, 6],
        "Projects Completed": [0, 1, 2, 1]
    }
    
    st.bar_chart(progress_data, x="Week", y=["Completed Topics", "Hours Spent", "Projects Completed"])

def save_uploaded_file(uploaded_file):
    try:
        # Create temp directory if it doesn't exist
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        # Save the uploaded file
        file_path = temp_dir / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return str(file_path)
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None

if __name__ == "__main__":
    main()
