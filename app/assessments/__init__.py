"""
Assessment module for SkillSpring AI Mentor.
Handles skill assessments, code quality metrics, and performance analytics.
"""

from .models import SkillAssessment, CodeQualityMetrics, PerformanceAnalytics, SkillLevel, CodeQualityMetric
from .assess import SkillAssessor, get_code_quality_metrics, track_performance

# Create a default instance for easier imports
assessor = SkillAssessor(None)  # None for the OpenAI client, which should be provided when used

def assess_skills(code: str, language: str = "python", client=None):
    """Assess skills using a default or provided client."""
    assessor = SkillAssessor(client) if client is not None else assessor
    return assessor.assess_skills(code, language)

__all__ = [
    'SkillAssessment',
    'CodeQualityMetrics',
    'PerformanceAnalytics',
    'SkillAssessor',
    'SkillLevel',
    'CodeQualityMetric',
    'assess_skills',
    'get_code_quality_metrics',
    'track_performance',
    'assessor'
]
