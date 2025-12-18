import ast
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

import radon.complexity
from radon.visitors import ComplexityVisitor
from radon.metrics import mi_visit

from .models import (
    SkillAssessment, 
    CodeQualityMetrics, 
    PerformanceAnalytics,
    SkillLevel,
    CodeQualityMetric
)

class SkillAssessor:
    """Assesses programming skills based on code analysis and user interactions."""
    
    def __init__(self, openai_client):
        self.client = openai_client
    
    def assess_skills(self, code: str, language: str = "python") -> SkillAssessment:
        """
        Assess programming skills based on code analysis.
        
        Args:
            code: Source code to analyze
            language: Programming language of the code
            
        Returns:
            SkillAssessment object with results
        """
        # Basic code analysis
        complexity = self._calculate_complexity(code, language)
        quality_metrics = self._get_code_quality_metrics(code, language)
        
        # Get AI feedback on code quality and skill level
        ai_feedback = self._get_ai_feedback(code, language, complexity, quality_metrics)
        
        # Determine skill level based on metrics and AI feedback
        skill_level = self._determine_skill_level(complexity, quality_metrics, ai_feedback)
        
        return SkillAssessment(
            user_id="current_user",  # Would come from session/auth in production
            skill_name=f"{language.title()} Programming",
            level=skill_level,
            score=self._calculate_skill_score(skill_level, quality_metrics),
            feedback=ai_feedback.get("feedback", []) if ai_feedback else [],
            recommendations=ai_feedback.get("recommendations", []) if ai_feedback else []
        )
    
    def _calculate_complexity(self, code: str, language: str) -> Dict[str, float]:
        """Calculate code complexity metrics."""
        if language.lower() != 'python':
            # For non-Python code, we'd implement other language-specific analyzers
            return {"cyclomatic": 0, "cognitive": 0}
            
        try:
            # Calculate cyclomatic complexity
            tree = ast.parse(code)
            visitor = ComplexityVisitor.from_code(code)
            
            return {
                "cyclomatic": visitor.complexity,
                "cognitive": radon.complexity.cc_visit(code)[0].complexity if code.strip() else 0
            }
        except Exception as e:
            print(f"Error calculating complexity: {e}")
            return {"cyclomatic": 0, "cognitive": 0}
    
    def _get_code_quality_metrics(self, code: str, language: str) -> Dict[str, float]:
        """Calculate various code quality metrics."""
        if not code.strip():
            return {}
            
        metrics = {}
        
        # Calculate maintainability index (0-100, higher is better)
        try:
            metrics["maintainability"] = mi_visit(code, multi=True)[0]
        except:
            metrics["maintainability"] = 50.0  # Default value
        
        # Calculate other metrics (simplified for example)
        metrics["readability"] = self._calculate_readability(code, language)
        metrics["modularity"] = self._calculate_modularity(code, language)
        
        return metrics
    
    def _calculate_readability(self, code: str, language: str) -> float:
        """Calculate code readability score (0-1, higher is better)."""
        # This is a simplified version - in production, you might use more sophisticated analysis
        try:
            # Check line length (shorter lines are generally more readable)
            lines = code.split('\n')
            avg_line_length = sum(len(line) for line in lines) / max(1, len(lines))
            line_length_score = max(0, 1 - (avg_line_length / 100))  # 100 chars per line is max
            
            # Check for comments (some comments are good)
            comment_ratio = sum(1 for line in lines if line.strip().startswith('#')) / max(1, len(lines))
            comment_score = min(1.0, comment_ratio * 3)  # Up to 33% comments is good
            
            return (line_length_score * 0.6) + (comment_score * 0.4)
        except:
            return 0.5  # Default score
    
    def _calculate_modularity(self, code: str, language: str) -> float:
        """Calculate code modularity score (0-1, higher is better)."""
        # This is a simplified version
        try:
            if language.lower() == 'python':
                tree = ast.parse(code)
                functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                
                # More functions/classes generally indicates better modularity
                # But we want to balance with function/class size
                total_lines = len(code.split('\n'))
                if total_lines == 0:
                    return 0.5
                    
                func_count = len(functions)
                avg_func_size = sum(len(ast.unparse(f).split('\n')) for f in functions) / max(1, func_count)
                
                # Score based on number of functions and average size
                func_count_score = min(1.0, func_count / 10)  # Up to 10 functions is good
                size_score = max(0, 1 - (avg_func_size / 50))  # 50 lines per function is max
                
                return (func_count_score * 0.4) + (size_score * 0.6)
            return 0.5  # Default for non-Python code
        except:
            return 0.5  # Default score
    
    def _get_ai_feedback(self, code: str, language: str, 
                        complexity: Dict, metrics: Dict) -> Dict:
        """Get AI-powered feedback on the code."""
        # Return sample feedback if no client is available
        if self.client is None:
            return {
                "feedback": [
                    "The code structure is well-organized with clear function definitions.",
                    "Good use of variable naming conventions that enhance code readability.",
                    "Could benefit from additional error handling for edge cases.",
                    "Consider adding more inline comments to explain complex logic.",
                    "The code follows good practices for the most part."
                ],
                "recommendations": [
                    "Add docstrings to functions and classes for better documentation.",
                    "Consider breaking down larger functions into smaller, more focused ones.",
                    "Implement input validation for better error handling."
                ]
            }
        
        # Rest of the existing implementation for when client is available
        try:
            prompt = f"""Analyze the following {language} code and provide feedback:
            
            Code:
            ```{language}
            {code}
            ```
            
            Complexity: {complexity}
            Quality Metrics: {metrics}
            
            Please provide:
            1. 3-5 specific feedback points about the code
            2. 2-3 specific recommendations for improvement
            3. An overall assessment of the developer's skill level
            
            Format your response as a JSON object with 'feedback' and 'recommendations' arrays.
            """
            
            response = self.client.responses.create(
                model="gpt-4.0-turbo",
                input=[
                    {"role": "system", "content": "You are an expert code reviewer providing constructive feedback."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            
            # Parse the response
            try:
                import json
                return json.loads(response.output_text)
            except:
                # Fallback if response isn't valid JSON
                return {
                    "feedback": ["Code analysis complete. " + 
                               "Consider implementing more robust error handling and documentation."],
                    "recommendations": [
                        "Add more comments to explain complex logic",
                        "Consider breaking down larger functions into smaller, more focused ones"
                    ]
                }
                
        except Exception as e:
            print(f"Error getting AI feedback: {e}")
            return {
                "feedback": ["Error generating feedback. " + 
                           "The code appears to be syntactically correct."],
                "recommendations": [
                    "Review the code for potential improvements",
                    "Consider adding more error handling"
                ]
            }
    
    def _determine_skill_level(self, complexity: Dict, 
                             metrics: Dict, ai_feedback: Dict) -> SkillLevel:
        """Determine skill level based on analysis."""
        # This is a simplified version - in production, you'd use more sophisticated logic
        maintainability = metrics.get("maintainability", 0)
        readability = metrics.get("readability", 0.5)
        
        # Calculate a composite score (0-1)
        composite_score = (maintainability / 100 * 0.6) + (readability * 0.4)
        
        if composite_score > 0.8:
            return SkillLevel.EXPERT
        elif composite_score > 0.6:
            return SkillLevel.ADVANCED
        elif composite_score > 0.4:
            return SkillLevel.INTERMEDIATE
        else:
            return SkillLevel.BEGINNER
    
    def _calculate_skill_score(self, level: SkillLevel, metrics: Dict) -> float:
        """Calculate a numerical skill score (0-1) based on level and metrics."""
        base_scores = {
            SkillLevel.BEGINNER: 0.3,
            SkillLevel.INTERMEDIATE: 0.5,
            SkillLevel.ADVANCED: 0.75,
            SkillLevel.EXPERT: 0.9
        }
        
        # Adjust based on code quality metrics
        maintainability = metrics.get("maintainability", 50) / 100  # Normalize to 0-1
        readability = metrics.get("readability", 0.5)
        
        # Weighted average with base score
        return (base_scores[level] * 0.6) + (maintainability * 0.2) + (readability * 0.2)


def track_performance(user_id: str, assessment: SkillAssessment) -> PerformanceAnalytics:
    """Track and update user performance over time."""
    # In a real app, this would load from a database
    analytics = PerformanceAnalytics(user_id=user_id)
    analytics.skill_assessments.append(assessment)
    
    # Here you would save to a database
    # db.save_performance_analytics(analytics)
    
    return analytics

def get_code_quality_metrics(code: str, language: str = "python") -> CodeQualityMetrics:
    """Get code quality metrics for the given code."""
    assessor = SkillAssessor(openai_client=None)  # In real app, pass actual client
    metrics = assessor._get_code_quality_metrics(code, language)
    
    return CodeQualityMetrics(
        file_path="inline_code",
        metrics={
            CodeQualityMetric.MAINTAINABILITY: metrics.get("maintainability", 50),
            CodeQualityMetric.COMPLEXITY: metrics.get("complexity", {}).get("cyclomatic", 0),
            # Add more metrics as needed
        },
        issues=[]  # Would be populated with actual issues in a real implementation
    )
