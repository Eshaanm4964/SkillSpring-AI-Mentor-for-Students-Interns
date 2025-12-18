from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum

class SkillLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"

class CodeQualityMetric(str, Enum):
    COMPLEXITY = "complexity"
    DUPLICATION = "duplication"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"
    TEST_COVERAGE = "test_coverage"

@dataclass
class SkillAssessment:
    """Represents a user's skill assessment result."""
    user_id: str
    skill_name: str
    level: SkillLevel
    score: float  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    feedback: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

@dataclass
class CodeQualityMetrics:
    """Represents code quality metrics for a codebase or file."""
    file_path: str
    metrics: Dict[CodeQualityMetric, float]  # Metric to score mapping
    issues: List[Dict] = field(default_factory=list)  # List of code issues
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def get_overall_score(self) -> float:
        """Calculate an overall code quality score."""
        if not self.metrics:
            return 0.0
        return sum(self.metrics.values()) / len(self.metrics)

@dataclass
class PerformanceAnalytics:
    """Tracks and analyzes user performance over time."""
    user_id: str
    skill_assessments: List[SkillAssessment] = field(default_factory=list)
    code_quality_history: List[CodeQualityMetrics] = field(default_factory=list)
    
    def get_skill_progress(self, skill_name: str) -> List[Tuple[datetime, float]]:
        """Get historical progress for a specific skill."""
        return [
            (assess.timestamp, assess.score)
            for assess in sorted(
                [a for a in self.skill_assessments if a.skill_name == skill_name],
                key=lambda x: x.timestamp
            )
        ]
    
    def get_code_quality_trend(self) -> List[Tuple[datetime, float]]:
        """Get historical code quality scores over time."""
        return [
            (metrics.timestamp, metrics.get_overall_score())
            for metrics in sorted(
                self.code_quality_history,
                key=lambda x: x.timestamp
            )
        ]
