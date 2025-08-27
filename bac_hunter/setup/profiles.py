"""
Profile management and recommendations for BAC Hunter
"""

from __future__ import annotations
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ScanProfile:
    """Represents a scanning profile with its configuration"""
    name: str
    description: str
    mode: str
    max_rps: float
    timeout: int
    phases: List[str]
    recommended_for: str
    tags: List[str]
    difficulty: str  # beginner, intermediate, advanced
    risk_level: str  # low, medium, high
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "mode": self.mode,
            "max_rps": self.max_rps,
            "timeout": self.timeout,
            "phases": self.phases,
            "recommended_for": self.recommended_for,
            "tags": self.tags,
            "difficulty": self.difficulty,
            "risk_level": self.risk_level
        }


class ProfileManager:
    """Manages scanning profiles and provides recommendations"""
    
    def __init__(self):
        self.profiles = self._load_default_profiles()
    
    def _load_default_profiles(self) -> Dict[str, ScanProfile]:
        """Load default scanning profiles"""
        profiles = {}
        
        # Quick Scan Profile
        profiles["quick_scan"] = ScanProfile(
            name="Quick Scan",
            description="Fast 15-minute assessment for basic vulnerabilities",
            mode="standard",
            max_rps=2.0,
            timeout=15,
            phases=["recon", "access"],
            recommended_for="Beginners, quick assessments, time-constrained testing",
            tags=["fast", "basic", "beginner-friendly"],
            difficulty="beginner",
            risk_level="low"
        )
        
        # Comprehensive Profile
        profiles["comprehensive"] = ScanProfile(
            name="Comprehensive Scan",
            description="Full security assessment with all modules enabled",
            mode="standard", 
            max_rps=1.5,
            timeout=120,
            phases=["recon", "scan", "access", "audit", "exploit"],
            recommended_for="Professional security testing, thorough assessments",
            tags=["complete", "thorough", "professional"],
            difficulty="intermediate",
            risk_level="medium"
        )
        
        # Stealth Profile
        profiles["stealth"] = ScanProfile(
            name="Stealth Mode",
            description="Low-noise scanning for production environments",
            mode="conservative",
            max_rps=0.5,
            timeout=180,
            phases=["recon", "access"],
            recommended_for="Production environments, sensitive systems",
            tags=["stealth", "production", "low-noise"],
            difficulty="intermediate",
            risk_level="low"
        )
        
        # Aggressive Profile
        profiles["aggressive"] = ScanProfile(
            name="Aggressive Testing",
            description="Maximum coverage with higher risk tolerance",
            mode="aggressive",
            max_rps=5.0,
            timeout=60,
            phases=["recon", "scan", "access", "audit", "exploit"],
            recommended_for="Test environments only, maximum coverage needed",
            tags=["aggressive", "comprehensive", "test-only"],
            difficulty="advanced",
            risk_level="high"
        )
        
        # API Focused Profile
        profiles["api_focused"] = ScanProfile(
            name="API Security Testing",
            description="Specialized for REST/GraphQL API security testing",
            mode="standard",
            max_rps=2.0,
            timeout=90,
            phases=["recon", "access", "audit"],
            recommended_for="API endpoints, microservices, REST/GraphQL APIs",
            tags=["api", "rest", "graphql", "microservices"],
            difficulty="intermediate",
            risk_level="medium"
        )
        
        # Web Application Profile
        profiles["web_app"] = ScanProfile(
            name="Web Application Testing",
            description="Traditional web application security assessment",
            mode="standard",
            max_rps=2.0,
            timeout=90,
            phases=["recon", "scan", "access", "audit"],
            recommended_for="Traditional web applications, CMS systems",
            tags=["web", "traditional", "cms"],
            difficulty="beginner",
            risk_level="medium"
        )
        
        # Mobile Backend Profile
        profiles["mobile_backend"] = ScanProfile(
            name="Mobile Backend Testing",
            description="Testing mobile application backend APIs",
            mode="standard",
            max_rps=1.5,
            timeout=75,
            phases=["recon", "access", "audit"],
            recommended_for="Mobile app backends, API gateways",
            tags=["mobile", "backend", "api"],
            difficulty="intermediate",
            risk_level="medium"
        )
        
        # CI/CD Pipeline Profile
        profiles["ci_cd"] = ScanProfile(
            name="CI/CD Integration",
            description="Lightweight scanning for CI/CD pipelines",
            mode="conservative",
            max_rps=1.0,
            timeout=30,
            phases=["recon", "access"],
            recommended_for="Continuous integration, automated testing",
            tags=["ci", "cd", "automation", "lightweight"],
            difficulty="intermediate",
            risk_level="low"
        )
        
        return profiles
    
    def get_profile(self, profile_name: str) -> Optional[ScanProfile]:
        """Get a specific profile by name"""
        return self.profiles.get(profile_name)
    
    def list_profiles(self, difficulty: Optional[str] = None, 
                     risk_level: Optional[str] = None,
                     tags: Optional[List[str]] = None) -> List[ScanProfile]:
        """List profiles with optional filtering"""
        filtered_profiles = []
        
        for profile in self.profiles.values():
            if difficulty and profile.difficulty != difficulty:
                continue
            if risk_level and profile.risk_level != risk_level:
                continue
            if tags and not any(tag in profile.tags for tag in tags):
                continue
            
            filtered_profiles.append(profile)
        
        return filtered_profiles
    
    def get_recommendations(self, target_type: str = "web", 
                          environment: str = "test",
                          experience: str = "beginner",
                          time_constraint: str = "moderate") -> List[ScanProfile]:
        """Get profile recommendations based on user requirements"""
        recommendations = []
        
        # Score profiles based on requirements
        scored_profiles = []
        for profile in self.profiles.values():
            score = self._calculate_profile_score(
                profile, target_type, environment, experience, time_constraint
            )
            scored_profiles.append((profile, score))
        
        # Sort by score and return top recommendations
        scored_profiles.sort(key=lambda x: x[1], reverse=True)
        return [profile for profile, score in scored_profiles[:3]]
    
    def _calculate_profile_score(self, profile: ScanProfile, target_type: str,
                               environment: str, experience: str, 
                               time_constraint: str) -> float:
        """Calculate recommendation score for a profile"""
        score = 0.0
        
        # Target type scoring
        if target_type == "api" and "api" in profile.tags:
            score += 3.0
        elif target_type == "web" and "web" in profile.tags:
            score += 3.0
        elif target_type == "mobile" and "mobile" in profile.tags:
            score += 3.0
        
        # Environment scoring
        if environment == "production":
            if profile.risk_level == "low":
                score += 2.0
            elif profile.risk_level == "medium":
                score += 0.5
            else:
                score -= 2.0
        else:  # test environment
            if profile.risk_level == "high":
                score += 1.0
            elif profile.risk_level == "medium":
                score += 1.5
        
        # Experience scoring
        if experience == "beginner":
            if profile.difficulty == "beginner":
                score += 2.0
            elif profile.difficulty == "intermediate":
                score += 0.5
            else:
                score -= 1.0
        elif experience == "intermediate":
            if profile.difficulty == "intermediate":
                score += 2.0
            else:
                score += 1.0
        else:  # advanced
            if profile.difficulty == "advanced":
                score += 2.0
            else:
                score += 1.0
        
        # Time constraint scoring
        if time_constraint == "quick":
            if profile.timeout <= 30:
                score += 2.0
            elif profile.timeout <= 60:
                score += 1.0
        elif time_constraint == "moderate":
            if 30 < profile.timeout <= 120:
                score += 2.0
        else:  # extensive
            if profile.timeout > 120:
                score += 2.0
        
        return score
    
    def create_custom_profile(self, name: str, **kwargs) -> ScanProfile:
        """Create a custom profile"""
        profile = ScanProfile(
            name=name,
            description=kwargs.get("description", "Custom profile"),
            mode=kwargs.get("mode", "standard"),
            max_rps=kwargs.get("max_rps", 2.0),
            timeout=kwargs.get("timeout", 60),
            phases=kwargs.get("phases", ["recon", "access"]),
            recommended_for=kwargs.get("recommended_for", "Custom use case"),
            tags=kwargs.get("tags", ["custom"]),
            difficulty=kwargs.get("difficulty", "intermediate"),
            risk_level=kwargs.get("risk_level", "medium")
        )
        
        self.profiles[name] = profile
        return profile
    
    def save_profiles(self, file_path: str) -> None:
        """Save profiles to file"""
        profiles_data = {
            name: profile.to_dict() 
            for name, profile in self.profiles.items()
        }
        
        with open(file_path, 'w') as f:
            json.dump(profiles_data, f, indent=2)
    
    def load_profiles(self, file_path: str) -> None:
        """Load profiles from file"""
        try:
            with open(file_path, 'r') as f:
                profiles_data = json.load(f)
            
            for name, data in profiles_data.items():
                self.profiles[name] = ScanProfile(**data)
        except FileNotFoundError:
            pass  # Use default profiles


def get_profile_recommendations(target_type: str = "web", 
                              environment: str = "test",
                              experience: str = "beginner",
                              time_constraint: str = "moderate") -> List[ScanProfile]:
    """Convenience function to get profile recommendations"""
    manager = ProfileManager()
    return manager.get_recommendations(target_type, environment, experience, time_constraint)