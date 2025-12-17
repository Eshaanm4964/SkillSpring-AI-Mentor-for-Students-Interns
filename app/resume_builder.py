import streamlit as st
import PyPDF2
import docx2txt
import io
import json
import base64
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
import os
from dotenv import load_dotenv
from fpdf import FPDF
from docx import Document
import plotly.express as px
import pandas as pd

# Load environment variables
load_dotenv()

# Constants
SUPPORTED_FILE_TYPES = ["pdf", "docx", "txt"]
TEMPLATE_STYLES = {
    "Professional": "Clean, traditional layout with clear section headers",
    "Modern": "Sleek design with subtle colors and modern typography",
    "Creative": "Innovative layout with visual elements and creative sections",
    "Minimalist": "Plenty of white space with focus on content",
    "Executive": "Elegant design with conservative styling for leadership roles"
}

# Initialize session state
if 'resume_versions' not in st.session_state:
    st.session_state.resume_versions = {}
if 'current_version' not in st.session_state:
    st.session_state.current_version = None
if 'job_descriptions' not in st.session_state:
    st.session_state.job_descriptions = {}
if 'cover_letters' not in st.session_state:
    st.session_state.cover_letters = {}

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """Generates a link to download the given file"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href

class ResumeBuilder:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.templates = list(TEMPLATE_STYLES.keys())
        self.ats_keywords = {
            'technical': ['Python', 'Machine Learning', 'AWS', 'SQL', 'Docker', 'Kubernetes', 'CI/CD'],
            'soft': ['Leadership', 'Communication', 'Teamwork', 'Problem Solving', 'Time Management'],
            'tools': ['Git', 'Jira', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP']
        }
    
    def extract_text(self, file) -> Tuple[Optional[str], str]:
        """Extract text from PDF, DOCX, or TXT"""
        try:
            if file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip(), ""
            elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                return docx2txt.process(file), ""
            elif file.type == "text/plain":
                return file.read().decode("utf-8"), ""
            return None, "Unsupported file type"
        except Exception as e:
            return None, f"Error extracting text: {str(e)}"
    
    def analyze_resume(self, text: str, job_description: str = "") -> Dict:
        """Analyze resume and return structured data"""
        try:
            # First, try to extract basic information without AI
            analysis = {
                "summary": "Professional summary will be generated here",
                "skills": {
                    "technical": [],
                    "soft": []
                },
                "experience": [],
                "education": [],
                "projects": [],
                "ats_score": 0,
                "improvement_suggestions": [],
                "missing_keywords": []
            }
            
            # If we have an OpenAI API key, use AI for more detailed analysis
            if os.getenv('OPENAI_API_KEY'):
                prompt = f"""Analyze this resume and extract the following information in JSON format:
                {{
                    "summary": "Brief professional summary",
                    "skills": {{
                        "technical": ["list", "of", "technical", "skills"],
                        "soft": ["list", "of", "soft", "skills"]
                    }},
                    "experience": [
                        {{
                            "title": "Job Title",
                            "company": "Company Name",
                            "duration": "Employment Duration",
                            "achievements": ["achievement 1", "achievement 2"]
                        }}
                    ],
                    "education": [
                        {{
                            "degree": "Degree Name",
                            "institution": "Institution Name",
                            "year": "Graduation Year"
                        }}
                    ],
                    "projects": [
                        {{
                            "name": "Project Name",
                            "description": "Brief description",
                            "technologies": ["tech1", "tech2"],
                            "achievements": ["achievement 1", "achievement 2"]
                        }}
                    ],
                    "improvement_suggestions": ["suggestion 1", "suggestion 2"],
                    "missing_keywords": ["keyword1", "keyword2"]
                }}
                
                Resume Text:
                {text}
                
                {"Analyze against this job description:" + job_description if job_description else ""}"""
                
                try:
                    # First try with gpt-4
                    response = self.client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are an expert resume analyzer. Provide detailed, structured analysis in valid JSON format."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3
                    )
                except Exception as e:
                    if "model_not_found" in str(e) or "gpt-4" in str(e):
                        # Fall back to gpt-3.5-turbo if gpt-4 is not available
                        st.warning("GPT-4 not available, falling back to GPT-3.5-turbo")
                        response = self.client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are an expert resume analyzer. Provide detailed, structured analysis in valid JSON format. Be concise but thorough."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.3
                        )
                    else:
                        # Re-raise other errors
                        raise e
                
                try:
                    ai_analysis = json.loads(response.choices[0].message.content)
                    # Update our analysis with AI results
                    for key in ai_analysis:
                        if key in analysis and ai_analysis[key]:
                            analysis[key] = ai_analysis[key]
                except json.JSONDecodeError:
                    st.warning("Could not parse AI analysis. Using basic analysis.")
            
            # Calculate ATS score
            analysis['ats_score'] = self._calculate_ats_score(analysis, job_description)
            
            # Add missing keywords if we have a job description
            if job_description:
                job_keywords = self._extract_keywords(job_description)
                resume_text = json.dumps(analysis).lower()
                analysis['missing_keywords'] = [
                    kw for kw in job_keywords 
                    if kw.lower() not in resume_text
                ][:10]  # Limit to top 10 missing keywords
                
            return analysis
            
        except Exception as e:
            st.error(f"Error analyzing resume: {str(e)}")
            return {
                "error": str(e),
                "summary": "Error analyzing resume. Please try again."
            }
    
    def _calculate_ats_score(self, analysis: Dict, job_description: str) -> int:
        """Calculate ATS compatibility score (0-100)"""
        score = 70  # Base score
        
        # Check for required sections
        required_sections = ['experience', 'education', 'skills']
        for section in required_sections:
            if section not in analysis or not analysis[section]:
                score -= 10
        
        # Check for keywords in job description
        if job_description:
            # Extract keywords from job description
            job_keywords = self._extract_keywords(job_description)
            resume_text = json.dumps(analysis).lower()
            
            # Count matching keywords
            matched_keywords = [kw for kw in job_keywords if kw.lower() in resume_text]
            match_ratio = len(matched_keywords) / max(len(job_keywords), 1)
            
            # Add points based on keyword matches (up to 30 points)
            score += min(30, int(30 * match_ratio))
        
        # Add points for having quantifiable achievements
        if 'experience' in analysis:
            has_achievements = any('achievements' in exp and exp['achievements'] 
                                 for exp in analysis['experience'])
            if has_achievements:
                score += 10
        
        # Ensure score is within 0-100 range
        return max(0, min(100, score))
        
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Simple keyword extraction - can be enhanced with NLP
        words = text.lower().split()
        # Remove common words and get unique words
        stop_words = set(['the', 'and', 'or', 'in', 'on', 'at', 'for', 'to', 'with'])
        return list(set(word for word in words if len(word) > 3 and word not in stop_words))
    
    def format_resume(self, analysis: Dict, template: str, format_type: str = 'txt') -> str:
        """Format resume using the selected template and format"""
        try:
            # Convert analysis to formatted text based on template
            if format_type == 'txt':
                return self._format_as_text(analysis, template)
            elif format_type == 'pdf':
                return self._generate_pdf(analysis, template)
            elif format_type == 'docx':
                return self._generate_docx(analysis, template)
            else:
                return "Unsupported format type"
        except Exception as e:
            return f"Error formatting resume: {str(e)}"
            
    def _format_as_text(self, analysis: Dict, template: str) -> str:
        """Format resume as plain text"""
        sections = []
        
        # Header
        if 'name' in analysis:
            sections.append(f"{analysis['name'].upper()}\n{'-'*40}")
        if 'contact' in analysis:
            sections.append("\n".join(f"{k}: {v}" for k, v in analysis['contact'].items()))
            
        # Summary
        if 'summary' in analysis:
            sections.append(f"\nSUMMARY\n{'-'*40}\n{analysis['summary']}")
            
        # Skills
        if 'skills' in analysis:
            skills_section = "\nSKILLS\n" + "-"*40
            for skill_type, skills in analysis['skills'].items():
                if skills:
                    skills_section += f"\n{skill_type.title()}: {', '.join(skills)}"
            sections.append(skills_section)
            
        # Experience
        if 'experience' in analysis:
            exp_section = "\nEXPERIENCE\n" + "-"*40
            for exp in analysis['experience']:
                exp_section += f"\n{exp.get('title', '')} at {exp.get('company', '')}"
                exp_section += f"\n{exp.get('duration', '')}\n"
                for achievement in exp.get('achievements', []):
                    exp_section += f"- {achievement}\n"
            sections.append(exp_section)
            
        return "\n\n".join(sections)
        
    def _generate_pdf(self, analysis: Dict, template: str) -> str:
        """Generate PDF version of the resume"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add content based on template
        if 'name' in analysis:
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt=analysis['name'], ln=True, align='C')
            pdf.ln(10)
            
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf.output(temp_file.name)
        return temp_file.name
        
    def _generate_docx(self, analysis: Dict, template: str) -> str:
        """Generate DOCX version of the resume"""
        doc = Document()
        
        # Add content based on template
        if 'name' in analysis:
            doc.add_heading(analysis['name'], 0)
            
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        doc.save(temp_file.name)
        return temp_file.name
        
    def generate_cover_letter(self, resume_analysis: Dict, job_description: str, company: str = "") -> str:
        """Generate a personalized cover letter"""
        try:
            prompt = f"""Write a professional cover letter based on the following resume and job description.
            
            Resume Summary:
            {json.dumps(resume_analysis, indent=2)}
            
            Job Description:
            {job_description}
            
            Company: {company}
            
            The cover letter should be concise (3-4 paragraphs) and highlight relevant experience and skills.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional career advisor. Write a compelling cover letter."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error generating cover letter: {str(e)}"

def generate_skill_improvement_plan(missing_keywords: List[str], existing_skills: Dict) -> Dict:
    """Generate a skill improvement plan based on missing keywords"""
    # This is a simplified version - in a real app, this would call an AI model
    return {
        "missing_skills": missing_keywords[:5],
        "learning_resources": {
            "courses": [
                f"{skill} for Beginners" for skill in missing_keywords[:3]
            ],
            "projects": [
                f"Build a project using {skill}" for skill in missing_keywords[:3]
            ],
            "practice": [
                "Practice on LeetCode/HackerRank",
                "Contribute to open source projects",
                "Build a portfolio project"
            ]
        }
    }

def show_resume_editor(builder):
    st.header("✏️ Resume Editor")
    st.write("Edit and enhance your resume content")
    
    if 'current_version' in st.session_state and st.session_state.current_version:
        version = st.session_state.resume_versions[st.session_state.current_version]
        resume_text = st.text_area("Edit your resume", value=version['text'], height=400)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Changes"):
                version['text'] = resume_text
                version['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                st.success("Resume updated successfully!")
        
        with col2:
            export_format = st.selectbox("Export as", ["PDF", "DOCX", "TXT"])
            if st.button(f"⬇️ Export as {export_format}"):
                formatted = builder.format_resume(
                    version['analysis'], 
                    "Professional",  # Default template for export
                    export_format.lower()
                )
                st.download_button(
                    label=f"Download {export_format}",
                    data=formatted,
                    file_name=f"resume_{st.session_state.current_version}.{export_format.lower()}",
                    mime="application/octet-stream"
                )
    else:
        st.info("Please analyze a resume first from the Resume Analysis page")

def show_cover_letters(builder):
    st.header("✉️ Cover Letter Generator")
    
    if 'current_version' not in st.session_state or not st.session_state.current_version:
        st.warning("Please analyze a resume first to generate a cover letter")
        return
    
    version = st.session_state.resume_versions[st.session_state.current_version]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Job Details")
        company = st.text_input("Company Name")
        job_title = st.text_input("Job Title")
        job_description = st.text_area("Job Description", height=200)
        
        if st.button("✨ Generate Cover Letter"):
            with st.spinner("Generating your cover letter..."):
                cover_letter = builder.generate_cover_letter(
                    version['analysis'],
                    job_description,
                    company
                )
                st.session_state.current_cover_letter = cover_letter
    
    with col2:
        st.subheader("Your Cover Letter")
        if 'current_cover_letter' in st.session_state:
            st.text_area("Generated Cover Letter", 
                        st.session_state.current_cover_letter, 
                        height=400)
            
            if st.button("📄 Save Cover Letter"):
                cover_letter_id = f"cover_{len(st.session_state.cover_letters) + 1}"
                st.session_state.cover_letters[cover_letter_id] = {
                    'content': st.session_state.current_cover_letter,
                    'company': company,
                    'job_title': job_title,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                st.success("Cover letter saved!")

def show_job_search(builder):
    st.header("🔍 Job Search Assistant")
    st.write("Coming soon: Job search and application tracking features")
    
    # Placeholder for job search functionality
    st.info("This feature is under development. Check back soon for updates!")

def show_resume_analysis(builder):
    st.header("📊 Resume Analysis & Optimization")
    
    # Two-column layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # File upload section
        st.subheader("1. Upload Your Resume")
        uploaded_file = st.file_uploader("Choose a file", type=SUPPORTED_FILE_TYPES, 
                                      help="Supported formats: PDF, DOCX, TXT")
        
        # Job description analysis
        st.subheader("2. Add Job Description (Optional)")
        job_description = st.text_area("Paste job description here to compare against your resume", 
                                     height=150, help="Get tailored recommendations based on specific job requirements")
        
        # Analyze button
        if st.button("🔍 Analyze Resume", use_container_width=True):
            if uploaded_file:
                with st.spinner("Analyzing your resume..."):
                    # Extract text
                    text, error = builder.extract_text(uploaded_file)
                    if error:
                        st.error(error)
                    else:
                        st.session_state.resume_text = text
                        st.session_state.analysis = builder.analyze_resume(text, job_description)
                        st.session_state.current_version = f"version_{len(st.session_state.resume_versions) + 1}"
                        st.session_state.resume_versions[st.session_state.current_version] = {
                            'text': text,
                            'analysis': st.session_state.analysis,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        st.success("Analysis complete!")
                        st.rerun()
            else:
                st.warning("Please upload a resume first")
    
    with col2:
        # Template preview
        st.subheader("Templates")
        selected_template = st.selectbox("Choose a template", builder.templates, 
                                       format_func=lambda x: f"{x} - {TEMPLATE_STYLES[x]}")
        
        # Show template preview (placeholder)
        with st.expander("📝 Template Preview"):
            st.caption(TEMPLATE_STYLES[selected_template])
            st.image("https://via.placeholder.com/300x400.png?text=Template+Preview", 
                   width=300)
    
    # Show analysis results if available
    if 'analysis' in st.session_state and st.session_state.analysis:
        analysis = st.session_state.analysis
        
        # Show error if analysis failed
        if 'error' in analysis:
            st.error(f"Analysis error: {analysis['error']}")
            return
            
        # ATS Score Card
        st.subheader("📈 ATS Score & Recommendations")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # ATS Score Gauge
            ats_score = analysis.get('ats_score', 0)
            score_color = "#4CAF50" if ats_score > 70 else "#FFC107" if ats_score > 40 else "#F44336"
            
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="width: 150px; height: 150px; border-radius: 50%; 
                            background: conic-gradient({score_color} {ats_score}%, #E0E0E0 {100-ats_score}%);
                            display: flex; align-items: center; justify-content: center; margin: 0 auto 10px;">
                    <div style="background: white; width: 130px; height: 130px; 
                                border-radius: 50%; display: flex; align-items: center; 
                                justify-content: center;">
                        <span style="font-size: 24px; font-weight: bold; color: {score_color};">
                            {ats_score}/100
                        </span>
                    </div>
                </div>
                <h3>ATS Score</h3>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Strengths
            st.markdown("### ✅ Strengths")
            strengths = []
            
            # Add strengths based on analysis
            if analysis.get('skills', {}).get('technical'):
                strengths.append(f"✅ Strong in {', '.join(analysis['skills']['technical'][:3])}")
            if analysis.get('experience'):
                strengths.append("✅ Well-structured work history")
            if any('achievements' in exp for exp in analysis.get('experience', [])):
                strengths.append("✅ Includes quantifiable achievements")
            if not strengths:
                strengths = ["✅ Well-formatted document", "✅ Good use of sections"]
                
            for strength in strengths[:3]:  # Show max 3 strengths
                st.markdown(f"- {strength}")
        
        with col3:
            # Areas for Improvement
            st.markdown("### 📝 Recommendations")
            
            # Default suggestions
            default_suggestions = [
                "Add more quantifiable achievements",
                "Include relevant keywords from the job description",
                "Ensure consistent formatting throughout"
            ]
            
            # Use AI suggestions if available, otherwise use defaults
            suggestions = analysis.get('improvement_suggestions', [])[:3] or default_suggestions[:3]
            
            for i, suggestion in enumerate(suggestions, 1):
                st.markdown(f"{i}. {suggestion}")
        
        # Skills Gap Analysis
        if job_description and 'missing_keywords' in analysis and analysis['missing_keywords']:
            st.subheader("🔍 Skills Gap Analysis")
            
            # Show missing keywords as tags
            st.write("The following keywords from the job description are missing from your resume:")
            st.write(" ".join([f"`{kw}`" for kw in analysis['missing_keywords'][:10]]))
            
            # Generate skill improvement plan
            if st.button("🛠️ Generate Skill Improvement Plan"):
                with st.spinner("Creating a personalized learning path..."):
                    st.session_state.skill_plan = generate_skill_improvement_plan(
                        analysis['missing_keywords'], 
                        analysis.get('skills', {})
                    )
        
        # Resume Versions
        if st.session_state.resume_versions:
            st.subheader("📚 Resume Versions")
            version_cols = st.columns(3)
            for i, (version_id, version) in enumerate(st.session_state.resume_versions.items()):
                with version_cols[i % 3]:
                    with st.container(border=True):
                        st.markdown(f"**Version {i+1}**")
                        st.caption(f"Last updated: {version['timestamp']}")
                        ats_score = version.get('analysis', {}).get('ats_score', 'N/A')
                        st.caption(f"ATS Score: {ats_score if ats_score != 'N/A' else 'Not available'}")
                        
                        # Action buttons
                        btn1, btn2 = st.columns(2)
                        with btn1:
                            if st.button(f"View {i+1}", key=f"view_{version_id}"):
                                st.session_state.current_version = version_id
                                st.session_state.analysis = version['analysis']
                                st.rerun()
                        with btn2:
                            # Export options
                            export_format = st.selectbox(
                                "Export as", 
                                ["PDF", "DOCX", "TXT"], 
                                key=f"export_{version_id}",
                                label_visibility="collapsed"
                            )
                            if st.button(f"Export {i+1}", key=f"export_btn_{version_id}"):
                                # Generate and offer download
                                formatted = builder.format_resume(
                                    version['analysis'], 
                                    "Professional",  # Default template for export
                                    export_format.lower()
                                )
                                st.download_button(
                                    label=f"⬇️ {export_format}",
                                    data=formatted,
                                    file_name=f"resume_{version_id}.{export_format.lower()}",
                                    mime="application/octet-stream"
                                )

def show_resume_builder():
    st.set_page_config(layout="wide")
    st.title("📝 AI-Powered Resume Builder & Career Assistant")
    
    # Initialize resume builder
    builder = ResumeBuilder()
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Resume Analysis", "Resume Builder", "Cover Letters", "Job Search"])
    
    # Main content area
    if page == "Resume Analysis":
        show_resume_analysis(builder)
    elif page == "Resume Builder":
        show_resume_editor(builder)
    elif page == "Cover Letters":
        show_cover_letters(builder)
    elif page == "Job Search":
        show_job_search(builder)
