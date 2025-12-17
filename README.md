# SkillSpring - AI Mentor for Students & Interns

SkillSpring is an AI-powered mentorship platform that helps students and interns navigate their learning journey, prepare for interviews, and track their progress.

## Features

- **Personalized Learning Path**: Get a customized learning roadmap based on your resume, GitHub, and career goals
- **Resume Analysis**: Upload your resume for AI-powered analysis and improvement suggestions
- **Mock Interviews**: Practice technical and behavioral interviews with AI
- **Progress Tracking**: Monitor your learning journey with detailed analytics
- **Skill Assessment**: Identify skill gaps and get recommendations

## Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/skillspring.git
   cd skillspring
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   GITHUB_TOKEN=your_github_token
   ```

### Running the Application

1. Start the Streamlit app:
   ```bash
   streamlit run app/main.py
   ```

2. Open your browser and navigate to `http://localhost:8501`

## Project Structure

```
skillspring/
├── app/                    # Main application code
│   ├── main.py             # Streamlit app entry point
│   ├── resume_parser.py    # Resume parsing functionality
│   ├── roadmap_generator.py # Learning path generation
│   └── interview_simulator.py # Mock interview logic
├── data/                   # Data storage
│   └── user_profiles/      # User profile data
├── models/                 # ML models
├── tests/                  # Test files
├── utils/                  # Utility functions
├── .env.example           # Example environment variables
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with ❤️ for students and interns
- Powered by OpenAI and Streamlit
