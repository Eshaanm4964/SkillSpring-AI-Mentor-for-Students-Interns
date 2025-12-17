import streamlit as st
import subprocess
import sys
import re
import json
from openai import OpenAI
import os
import webbrowser
from dotenv import load_dotenv
from typing import Dict, List, Optional

# Learning resources by language
LEARNING_RESOURCES = {
    "Python": [
        {"name": "Python Official Docs", "url": "https://docs.python.org/3/", "icon": "📚"},
        {"name": "GeeksforGeeks", "url": "https://www.geeksforgeeks.org/python-programming-language/", "icon": "🔍"},
        {"name": "Real Python", "url": "https://realpython.com/", "icon": "🐍"},
        {"name": "LeetCode Problems", "url": "https://leetcode.com/tag/python/", "icon": "💻"}
    ],
    "JavaScript": [
        {"name": "MDN Web Docs", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript", "icon": "📚"},
        {"name": "JavaScript.info", "url": "https://javascript.info/", "icon": "ℹ️"},
        {"name": "GeeksforGeeks JS", "url": "https://www.geeksforgeeks.org/javascript/", "icon": "🔍"}
    ],
    "Java": [
        {"name": "Oracle Java Docs", "url": "https://docs.oracle.com/en/java/", "icon": "📚"},
        {"name": "GeeksforGeeks Java", "url": "https://www.geeksforgeeks.org/java/", "icon": "🔍"},
        {"name": "JavaTpoint", "url": "https://www.javatpoint.com/java-tutorial", "icon": "☕"}
    ],
    "C++": [
        {"name": "cplusplus.com", "url": "https://www.cplusplus.com/doc/tutorial/", "icon": "📚"},
        {"name": "GeeksforGeeks C++", "url": "https://www.geeksforgeeks.org/c-plus-plus/", "icon": "🔍"},
        {"name": "LearnCPP", "url": "https://www.learncpp.com/", "icon": "➕"}
    ]
}

# Code formatting styles
CODE_STYLES = {
    "Default": "default",
    "Monokai": "monokai",
    "Solarized": "solarized-light",
    "Dracula": "dracula",
    "GitHub": "github"
}

def apply_code_style(style: str) -> str:
    """Return CSS for the selected code style"""
    styles = {
        "default": "",
        "monokai": """
            .stCodeBlock pre { 
                background-color: #272822 !important;
                color: #f8f8f2 !important;
            }
            .stCodeBlock code {
                font-family: 'Fira Code', 'Consolas', monospace !important;
            }
        """,
        "solarized-light": """
            .stCodeBlock pre { 
                background-color: #fdf6e3 !important;
                color: #657b83 !important;
            }
        """,
        "dracula": """
            .stCodeBlock pre { 
                background-color: #282a36 !important;
                color: #f8f8f2 !important;
            }
        """,
        "github": """
            .stCodeBlock pre { 
                background-color: #f6f8fa !important;
                color: #24292e !important;
            }
        """
    }
    return f"""
    <style>
        {styles.get(style, '')}
        /* Common code block styling */
        .stCodeBlock {{
            border-radius: 8px;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stCodeBlock pre {{
            padding: 1rem !important;
            border-radius: 8px !important;
            font-size: 14px !important;
            line-height: 1.5 !important;
        }}
        /* Line numbers */
        pre {{ 
            counter-reset: line;
        }}
        pre .line {{
            counter-increment: line;
            position: relative;
            padding-left: 2.5em;
        }}
        pre .line:before {{
            content: counter(line);
            position: absolute;
            left: 0;
            color: #6c757d;
            user-select: none;
            width: 2em;
            text-align: right;
            padding-right: 0.5em;
        }}
    </style>
    """

# Load environment variables
load_dotenv()

class CodeExecutor:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.languages = {
            "Python": "python",
            "JavaScript": "node",
            "Java": "java",
            "C++": "g++"
        }
    
    def execute_code(self, code, language):
        """Execute code in a subprocess and return the output"""
        try:
            if language == "Python":
                result = subprocess.run(
                    [sys.executable, "-c", code],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            elif language == "JavaScript":
                result = subprocess.run(
                    ["node", "-e", code],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            # Add more languages as needed
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Execution timed out. Check for infinite loops."}
        except Exception as e:
            return {"error": str(e)}
    
    def get_code_feedback(self, code, language, problem_statement=None):
        """Get AI-powered feedback on the code"""
        try:
            prompt = f"""
            You are an expert code reviewer. Please provide feedback on this {language} code.
            {f'Problem Statement: {problem_statement}' if problem_statement else ''}
            
            Code:
            ```{language}
            {code}
            ```
            
            Please provide:
            1. A brief analysis of what the code does
            2. Any bugs or issues
            3. Suggestions for improvement
            4. Time and space complexity (if applicable)
            5. Best practices followed/violated
            """
            
            response =self.client.responses.create(
                model="gpt-4.1-mini",
                input=[
                    {"role": "system","content":"You are a helpful coding mentor providing clear, constructive feedback."},
                    {"role": "user", "content": prompt}
                ],
                temperature  = 0.4
            )
            
            return response.output_text
        except Exception as e:
            return f"Error getting feedback: {str(e)}"

def show_learning_resources(language: str):
    """Display learning resources for the selected language"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 Learning Resources")
    
    if language in LEARNING_RESOURCES:
        for resource in LEARNING_RESOURCES[language]:
            if st.sidebar.button(f"{resource['icon']} {resource['name']}", 
                              key=f"resource_{language}_{resource['name']}"):
                webbrowser.open_new_tab(resource['url'])
    else:
        st.sidebar.info("Select a language to see learning resources")

def show_coding_environment():
    st.set_page_config(layout="wide")
    
    # Add custom CSS for better layout
    st.markdown("""
    <style>
        .main .block-container {
            max-width: 95%;
            padding: 2rem 1rem;
        }
        .stCodeBlock {
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stButton>button {
            width: 100%;
            margin: 0.25rem 0;
        }
        .stTextArea textarea {
            font-family: 'Fira Code', 'Consolas', monospace !important;
            font-size: 14px !important;
            line-height: 1.5 !important;
        }
        .stMarkdown h3 {
            color: #2c3e50;
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'code' not in st.session_state:
        st.session_state.code = """# Welcome to SkillSpring Code Editor!\n# Write your code here and click 'Run Code' to execute it.\n\ndef hello_world():\n    print(\"Hello, World!\")\n\nif __name__ == \"__main__\":\n    hello_world()"""
    if 'output' not in st.session_state:
        st.session_state.output = ""
    if 'feedback' not in st.session_state:
        st.session_state.feedback = ""

    # Create code executor instance
    executor = CodeExecutor()
    
    # Main layout
    st.title("👨‍💻 Code Practice Environment")
    
    # Top controls
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        language = st.selectbox(
            "Programming Language",
            list(executor.languages.keys()),
            index=0,
            help="Select the programming language for your code"
        )
    with col2:
        code_style = st.selectbox(
            "Editor Theme",
            list(CODE_STYLES.keys()),
            index=0,
            help="Choose your preferred code editor theme"
        )
    with col3:
        st.markdown("<div style='height: 27px'></div>", unsafe_allow_html=True)
        show_line_numbers = st.checkbox("Show Line Numbers", value=True)
    
    # Apply selected code style
    st.markdown(apply_code_style(CODE_STYLES[code_style]), unsafe_allow_html=True)
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Problem statement
        with st.expander("📝 Problem Statement", expanded=True):
            problem = st.text_area(
                "Problem Statement",
                "Write a function to find the sum of two numbers.",
                height=100,
                label_visibility="collapsed"
            )
        
        # Code editor
        st.markdown("### ✏️ Code Editor")
        st.session_state.code = st.text_area(
            "Write your code here",
            st.session_state.code,
            height=400,
            label_visibility="collapsed",
            key="code_editor"
        )
        
        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("▶️ Run Code", use_container_width=True):
                with st.spinner("Running code..."):
                    result = executor.execute_code(st.session_state.code, language)
                    if "error" in result:
                        st.session_state.output = f"Error: {result['error']}"
                    else:
                        output = []
                        if result["stdout"]:
                            output.append(f"Output:\n{result['stdout']}")
                        if result["stderr"]:
                            output.append(f"Errors:\n{result['stderr']}")
                        st.session_state.output = "\n\n".join(output)
                        st.rerun()
        
        with col2:
            if st.button("💡 Get Feedback", use_container_width=True):
                with st.spinner("Analyzing code..."):
                    st.session_state.feedback = executor.get_code_feedback(
                        st.session_state.code, 
                        language,
                        problem
                    )
                    st.rerun()
        
        # Output
        if st.session_state.output:
            st.markdown("### 📤 Output")
            st.code(st.session_state.output, language="text")
    
    with col2:
        # Code tools
        st.markdown("### 🛠️ Code Tools")
        
        if st.button("📋 Copy Code", use_container_width=True):
            st.session_state.code = st.session_state.get('code', '')
            st.success("Code copied to clipboard!")
        
        if st.button("🧹 Clear Output", use_container_width=True):
            st.session_state.output = ""
            st.rerun()
        
        # Learning resources
        show_learning_resources(language)
        
        # Feedback section
        if st.session_state.feedback:
            st.markdown("### 📝 Feedback")
            st.markdown(st.session_state.feedback)
    
    # Add some spacing at the bottom
    st.markdown("<div style='height: 50px'></div>", unsafe_allow_html=True)
    
    # Copy code to clipboard
    js = f"""
    <script>
        function copyToClipboard() {{
            const el = document.createElement('textarea');
            el.value = `{st.session_state.code}`;
            document.body.appendChild(el);
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);
        }}
        copyToClipboard();
    </script>
    """
    st.components.v1.html(js, height=0)
    
    # Add clear button
    if st.button("🗑️ Clear Code"):
        st.session_state.code = ""
        st.session_state.output = ""
        st.session_state.feedback = ""
        st.rerun()
    
    st.markdown("---")
    # Interview Questions
    st.subheader("💼 Interview Questions")
    difficulty = st.select_slider(
        "Difficulty", 
        ["Easy", "Medium", "Hard"],
        value="Medium"
    )
    
    if st.button("🎯 Get Question"):
        with st.spinner("Generating question..."):
            try:
                response = executor.client.responses.create(
                    model="gpt-4.1-mini",
                    input=[
                        {"role": "system", "content": f"Generate a {difficulty.lower()} level {language} coding question."},
                        {"role": "user", "content": f"Generate a {difficulty.lower()} level {language} coding question with a clear problem statement and example inputs/outputs."}
                    ],
                    temperature=0.4
                )
                st.session_state.current_question = response.output_text
                st.session_state.show_answer = False
                st.rerun()
            except Exception as e:
                st.error(f"Error generating question: {str(e)}")
    
    if 'current_question' in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state.current_question)
        
        if st.button("👀 Show Answer"):
            st.session_state.show_answer = True
            st.rerun()
        
        if st.session_state.get('show_answer', False):
            with st.spinner("Generating solution..."):
                try:
                    response = executor.client.responses.create(
                        model="gpt-4.1-mini",
                        input=[
                            {"role": "system", "content": f"Provide a clear {language} solution with explanation for this coding question."},
                            {"role": "user", "content": f"Question:\n{st.session_state.current_question}\n\nPlease provide a {language} solution with explanation."}
                        ],
                        temperature=0.4
                    )
                    st.markdown("### Solution")
                    st.markdown(response.output_text)
                except Exception as e:
                    st.error(f"Error generating solution: {str(e)}")
        
        # Feedback section
        if st.session_state.feedback:
            st.markdown("---")
            st.subheader("📝 AI Feedback")
            st.markdown(st.session_state.feedback)
