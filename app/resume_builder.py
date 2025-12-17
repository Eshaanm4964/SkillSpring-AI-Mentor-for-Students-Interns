import streamlit as st
import PyPDF2
import docx2txt
import io
import json
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ResumeBuilder:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.templates = [
            "Professional",
            "Modern",
            "Creative",
            "Minimalist",
            "Executive"
        ]
    
    def extract_text(self, file):
        """Extract text from PDF or DOCX"""
        if file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return docx2txt.process(file)
        return None
    
    def analyze_resume(self, text):
        """Analyze resume using GPT-4.1-mini"""
        try:
            response = self.client.responses.create(
                model="gpt-4.1-mini",
                input=[
                    {"role": "system", "content": "You are an expert resume analyzer. Extract skills, experience, education, and projects from the resume. Also, provide an ATS score out of 100 and improvement suggestions."},
                    {"role": "user", "content": f"Analyze this resume:\n\n{text}"}
                ],
                temperature=0.4
            )
            return response.output_text
        except Exception as e:
            return f"Error analyzing resume: {str(e)}"
    
    def format_resume(self, text, template):
        """Format resume using the selected template"""
        try:
            response = self.client.responses.create(
                model="gpt-4.1-mini",
                input=[
                    {"role": "system", "content": f"Reformat this resume in a {template} style. Keep all the original information but improve the formatting, bullet points, and overall structure."},
                    {"role": "user", "content": text}
                ],
                temperature=0.4
            )
            return response.output_text
        except Exception as e:
            return f"Error formatting resume: {str(e)}"

def show_resume_builder():
    st.header("AI-Powered Resume Builder")
    
    # Initialize session state
    if 'resume_text' not in st.session_state:
        st.session_state.resume_text = ""
    if 'analysis' not in st.session_state:
        st.session_state.analysis = ""
    
    # Create resume builder instance
    builder = ResumeBuilder()
    
    # File upload
    st.subheader("1. Upload Your Resume")
    uploaded_file = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"])
    
    if uploaded_file is not None:
        # Extract text
        st.session_state.resume_text = builder.extract_text(uploaded_file)
        
        # Show extracted text
        with st.expander("View Extracted Text"):
            st.text_area("Extracted Text", st.session_state.resume_text, height=200)
        
        # Analyze button
        if st.button("🔍 Analyze Resume"):
            with st.spinner("Analyzing your resume..."):
                st.session_state.analysis = builder.analyze_resume(st.session_state.resume_text)
    
    # Show analysis
    if st.session_state.analysis:
        st.subheader("2. Resume Analysis")
        st.markdown(st.session_state.analysis)
        
        # ATS Optimization
        st.subheader("3. ATS Optimization")
        st.info("Our AI has analyzed your resume for ATS compatibility. Here are the key points:")
        
        # Formatting options
        st.subheader("4. Format Your Resume")
        template = st.selectbox("Choose a template", builder.templates)
        
        if st.button("🔄 Apply Formatting"):
            with st.spinner("Formatting your resume..."):
                formatted = builder.format_resume(st.session_state.resume_text, template)
                st.download_button(
                    label="📥 Download Formatted Resume",
                    data=formatted,
                    file_name=f"resume_{template.lower()}.txt",
                    mime="text/plain"
                )
                st.text_area("Preview", formatted, height=300)
    
    # Tips section
    with st.expander("💡 Resume Tips"):
        st.markdown("""
        ### Resume Writing Tips
        - Use action verbs (e.g., "Developed", "Led", "Optimized")
        - Quantify achievements (e.g., "Increased performance by 30%")
        - Include relevant keywords from the job description
        - Keep it concise (1-2 pages max)
        - Use a clean, professional format
        - Proofread for typos and grammar
        """)
