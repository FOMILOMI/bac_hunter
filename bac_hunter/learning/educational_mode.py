"""
Educational Mode for BAC Hunter
Provides step-by-step explanations of security testing concepts and tool operations
"""

from __future__ import annotations
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()

class ExplanationLevel(Enum):
    """Different levels of explanation detail"""
    BASIC = "basic"           # Simple explanations for beginners
    INTERMEDIATE = "intermediate"  # More technical details
    ADVANCED = "advanced"     # Deep technical explanations
    EXPERT = "expert"         # Minimal explanations, focus on results

@dataclass
class LearningConcept:
    """Represents a security testing concept to be explained"""
    name: str
    description: str
    why_important: str
    how_it_works: str
    examples: List[str]
    common_mistakes: List[str]
    best_practices: List[str]
    references: List[str]

@dataclass
class StepExplanation:
    """Explanation for a specific testing step"""
    step_name: str
    what_happening: str
    why_doing_this: str
    what_to_look_for: str
    potential_findings: List[str]
    next_steps: List[str]


class EducationalModeManager:
    """Manages educational explanations and interactive learning"""
    
    def __init__(self, explanation_level: ExplanationLevel = ExplanationLevel.BASIC):
        self.explanation_level = explanation_level
        self.concepts_database = self._load_concepts_database()
        self.interactive_mode = True
        self.show_examples = True
        self.pause_between_steps = True
        
    def _load_concepts_database(self) -> Dict[str, LearningConcept]:
        """Load the database of security testing concepts"""
        return {
            "broken_access_control": LearningConcept(
                name="Broken Access Control",
                description="Broken Access Control occurs when restrictions on what authenticated users are allowed to do are not properly enforced.",
                why_important="This is the #1 vulnerability in the OWASP Top 10 2021. It can lead to unauthorized access to sensitive data, functions, and resources.",
                how_it_works="Access control enforces policy such that users cannot act outside of their intended permissions. Common failures include bypassing access control checks by modifying URLs, parameters, or using different HTTP methods.",
                examples=[
                    "Accessing another user's account by changing an ID in the URL",
                    "Viewing admin pages by directly navigating to admin URLs",
                    "Modifying parameters to access unauthorized data"
                ],
                common_mistakes=[
                    "Relying only on client-side access controls",
                    "Not validating permissions on every request",
                    "Using predictable object references without authorization checks"
                ],
                best_practices=[
                    "Implement server-side authorization checks",
                    "Use the principle of least privilege",
                    "Log and monitor access control failures"
                ],
                references=[
                    "OWASP Top 10 2021 - A01 Broken Access Control",
                    "NIST Cybersecurity Framework",
                    "OWASP Access Control Cheat Sheet"
                ]
            ),
            
            "idor": LearningConcept(
                name="Insecure Direct Object Reference (IDOR)",
                description="IDOR occurs when an application provides direct access to objects based on user-supplied input without proper authorization checks.",
                why_important="IDOR vulnerabilities can expose sensitive data and allow unauthorized access to resources belonging to other users.",
                how_it_works="Applications often use direct references to internal objects (like database keys) in URLs or parameters. If authorization isn't checked, attackers can manipulate these references to access unauthorized data.",
                examples=[
                    "Changing user ID in URL: /user/123 to /user/124",
                    "Modifying document ID: /document?id=456 to /document?id=457",
                    "Accessing admin functions: /admin/user/789"
                ],
                common_mistakes=[
                    "Using sequential or predictable IDs",
                    "Not checking if the user has permission to access the object",
                    "Trusting client-side validation only"
                ],
                best_practices=[
                    "Use indirect references (like session-based mapping)",
                    "Implement proper authorization checks",
                    "Use UUIDs instead of sequential IDs"
                ],
                references=[
                    "OWASP Top 10 2021 - A01",
                    "CWE-639: Authorization Bypass Through User-Controlled Key"
                ]
            ),
            
            "privilege_escalation": LearningConcept(
                name="Privilege Escalation",
                description="Privilege escalation occurs when a user gains access to resources or functions that are normally protected from them.",
                why_important="This can allow attackers to gain administrative access, access sensitive data, or perform unauthorized actions.",
                how_it_works="Attackers exploit flaws in access control to gain higher privileges. This can be horizontal (same privilege level, different user) or vertical (higher privilege level).",
                examples=[
                    "Regular user accessing admin functions",
                    "Guest user gaining authenticated user privileges",
                    "User A accessing User B's data"
                ],
                common_mistakes=[
                    "Not validating user roles on each request",
                    "Using client-side role validation",
                    "Improper session management"
                ],
                best_practices=[
                    "Implement role-based access control (RBAC)",
                    "Validate permissions server-side",
                    "Use the principle of least privilege"
                ],
                references=[
                    "OWASP Access Control Testing Guide",
                    "NIST SP 800-53 Access Control"
                ]
            ),
            
            "session_management": LearningConcept(
                name="Session Management",
                description="Session management involves securely handling user sessions from login to logout, including session creation, maintenance, and destruction.",
                why_important="Poor session management can lead to session hijacking, fixation attacks, and unauthorized access.",
                how_it_works="Web applications use sessions to maintain user state across multiple requests. Sessions typically use cookies or tokens to identify users.",
                examples=[
                    "Session tokens in cookies",
                    "JWT tokens for stateless authentication",
                    "Session timeout mechanisms"
                ],
                common_mistakes=[
                    "Using predictable session IDs",
                    "Not invalidating sessions on logout",
                    "Insufficient session timeout"
                ],
                best_practices=[
                    "Use secure, random session IDs",
                    "Implement proper session timeout",
                    "Secure session storage and transmission"
                ],
                references=[
                    "OWASP Session Management Cheat Sheet",
                    "NIST SP 800-63B Authentication Guidelines"
                ]
            ),
            
            "information_disclosure": LearningConcept(
                name="Information Disclosure",
                description="Information disclosure occurs when an application reveals sensitive information to unauthorized users.",
                why_important="Disclosed information can help attackers understand the system better and plan more targeted attacks.",
                how_it_works="Applications may leak information through error messages, debug output, comments in source code, or verbose responses.",
                examples=[
                    "Database error messages revealing table structure",
                    "Debug information showing file paths",
                    "Stack traces revealing application internals"
                ],
                common_mistakes=[
                    "Displaying detailed error messages to users",
                    "Leaving debug mode enabled in production",
                    "Including sensitive data in client-side code"
                ],
                best_practices=[
                    "Use generic error messages for users",
                    "Log detailed errors server-side only",
                    "Remove debug information from production"
                ],
                references=[
                    "OWASP Top 10 2021 - A09 Security Logging and Monitoring Failures",
                    "CWE-200: Information Exposure"
                ]
            )
        }
    
    def explain_concept(self, concept_name: str) -> None:
        """Provide detailed explanation of a security concept"""
        concept = self.concepts_database.get(concept_name.lower())
        if not concept:
            console.print(f"[red]❌ Concept '{concept_name}' not found in knowledge base[/red]")
            return
        
        # Create explanation panel based on user's level
        if self.explanation_level == ExplanationLevel.BASIC:
            self._explain_basic(concept)
        elif self.explanation_level == ExplanationLevel.INTERMEDIATE:
            self._explain_intermediate(concept)
        elif self.explanation_level == ExplanationLevel.ADVANCED:
            self._explain_advanced(concept)
        else:  # EXPERT
            self._explain_expert(concept)
    
    def _explain_basic(self, concept: LearningConcept) -> None:
        """Basic explanation for beginners"""
        console.print(Panel.fit(
            f"[bold blue]🎓 Learning: {concept.name}[/bold blue]\n\n"
            f"[bold]What is it?[/bold]\n{concept.description}\n\n"
            f"[bold]Why should I care?[/bold]\n{concept.why_important}",
            title="Security Concept"
        ))
        
        if self.show_examples and concept.examples:
            console.print("\n[bold yellow]💡 Examples:[/bold yellow]")
            for i, example in enumerate(concept.examples[:3], 1):
                console.print(f"  {i}. {example}")
        
        if self.interactive_mode:
            if Confirm.ask("\nWould you like to see more details?", default=False):
                self._show_detailed_explanation(concept)
    
    def _explain_intermediate(self, concept: LearningConcept) -> None:
        """Intermediate explanation with more technical details"""
        console.print(Panel.fit(
            f"[bold blue]🎓 {concept.name}[/bold blue]\n\n"
            f"[bold]Description:[/bold]\n{concept.description}\n\n"
            f"[bold]How it works:[/bold]\n{concept.how_it_works}\n\n"
            f"[bold]Why it matters:[/bold]\n{concept.why_important}",
            title="Security Concept"
        ))
        
        self._show_examples_and_practices(concept)
    
    def _explain_advanced(self, concept: LearningConcept) -> None:
        """Advanced explanation with comprehensive details"""
        console.print(Panel.fit(
            f"[bold blue]🔬 Advanced Analysis: {concept.name}[/bold blue]",
            title="Security Concept"
        ))
        
        # Create detailed table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Aspect", style="cyan")
        table.add_column("Details", style="white")
        
        table.add_row("Definition", concept.description)
        table.add_row("Mechanism", concept.how_it_works)
        table.add_row("Business Impact", concept.why_important)
        
        console.print(table)
        self._show_examples_and_practices(concept)
        self._show_references(concept)
    
    def _explain_expert(self, concept: LearningConcept) -> None:
        """Minimal explanation for experts"""
        console.print(f"[bold blue]🔧 {concept.name}:[/bold blue] {concept.description}")
        if concept.examples:
            console.print(f"[dim]Examples: {'; '.join(concept.examples[:2])}[/dim]")
    
    def _show_detailed_explanation(self, concept: LearningConcept) -> None:
        """Show additional details about a concept"""
        console.print(f"\n[bold green]🔍 How {concept.name} Works:[/bold green]")
        console.print(concept.how_it_works)
        
        self._show_examples_and_practices(concept)
    
    def _show_examples_and_practices(self, concept: LearningConcept) -> None:
        """Show examples and best practices"""
        if concept.examples:
            console.print(f"\n[bold yellow]💡 Examples:[/bold yellow]")
            for i, example in enumerate(concept.examples, 1):
                console.print(f"  {i}. {example}")
        
        if concept.common_mistakes:
            console.print(f"\n[bold red]⚠️  Common Mistakes:[/bold red]")
            for mistake in concept.common_mistakes:
                console.print(f"  • {mistake}")
        
        if concept.best_practices:
            console.print(f"\n[bold green]✅ Best Practices:[/bold green]")
            for practice in concept.best_practices:
                console.print(f"  • {practice}")
    
    def _show_references(self, concept: LearningConcept) -> None:
        """Show references and further reading"""
        if concept.references:
            console.print(f"\n[bold cyan]📚 References:[/bold cyan]")
            for ref in concept.references:
                console.print(f"  • {ref}")
    
    def explain_step(self, step: StepExplanation) -> None:
        """Explain what's happening in a specific testing step"""
        if self.explanation_level == ExplanationLevel.EXPERT:
            console.print(f"[dim]🔄 {step.step_name}[/dim]")
            return
        
        console.print(Panel.fit(
            f"[bold green]🔄 Current Step: {step.step_name}[/bold green]\n\n"
            f"[bold]What's happening:[/bold]\n{step.what_happening}\n\n"
            f"[bold]Why we're doing this:[/bold]\n{step.why_doing_this}",
            title="Step Explanation"
        ))
        
        if self.explanation_level in [ExplanationLevel.INTERMEDIATE, ExplanationLevel.ADVANCED]:
            if step.what_to_look_for:
                console.print(f"\n[bold yellow]👀 What to look for:[/bold yellow]\n{step.what_to_look_for}")
            
            if step.potential_findings:
                console.print(f"\n[bold cyan]🎯 Potential findings:[/bold cyan]")
                for finding in step.potential_findings:
                    console.print(f"  • {finding}")
        
        if self.pause_between_steps and self.interactive_mode:
            if self.explanation_level != ExplanationLevel.BASIC or Confirm.ask("\nContinue to next step?", default=True):
                pass
            else:
                console.print("[dim]Pausing... Press Ctrl+C to stop or Enter to continue[/dim]")
                input()
    
    def show_finding_explanation(self, finding: Dict[str, Any]) -> None:
        """Explain a security finding that was discovered"""
        finding_type = finding.get("type", "unknown")
        severity = finding.get("severity", "medium")
        
        # Map severity to emoji and color
        severity_map = {
            "critical": ("🚨", "red"),
            "high": ("⚠️", "yellow"),
            "medium": ("ℹ️", "blue"),
            "low": ("💡", "green")
        }
        emoji, color = severity_map.get(severity.lower(), ("❓", "white"))
        
        console.print(Panel.fit(
            f"[bold {color}]{emoji} Finding Discovered![/bold {color}]\n\n"
            f"[bold]Type:[/bold] {finding_type}\n"
            f"[bold]Severity:[/bold] {severity}\n"
            f"[bold]Description:[/bold] {finding.get('description', 'No description available')}",
            title="Security Finding"
        ))
        
        # Explain the concept if available
        if finding_type in self.concepts_database:
            if self.interactive_mode and Confirm.ask("Would you like to learn more about this vulnerability type?", default=True):
                self.explain_concept(finding_type)
        
        # Show exploitation guidance
        if self.explanation_level in [ExplanationLevel.INTERMEDIATE, ExplanationLevel.ADVANCED]:
            self._show_exploitation_guidance(finding)
    
    def _show_exploitation_guidance(self, finding: Dict[str, Any]) -> None:
        """Show guidance on how to exploit or investigate the finding"""
        finding_type = finding.get("type", "").lower()
        
        guidance_map = {
            "idor": [
                "Try changing ID parameters to access other users' data",
                "Test with sequential numbers (1, 2, 3, etc.)",
                "Check if you can access admin or system objects",
                "Document what sensitive data is exposed"
            ],
            "access_control": [
                "Test with different user roles and permissions",
                "Try accessing the resource without authentication",
                "Check if HTTP method changes bypass restrictions",
                "Test parameter pollution attacks"
            ],
            "privilege_escalation": [
                "Try modifying role or permission parameters",
                "Test accessing admin endpoints directly",
                "Check if you can perform admin actions",
                "Test batch operations with elevated privileges"
            ]
        }
        
        guidance = guidance_map.get(finding_type, [
            "Investigate the finding manually",
            "Try different attack vectors",
            "Document the impact and scope",
            "Consider business context"
        ])
        
        console.print(f"\n[bold cyan]🔍 Investigation Steps:[/bold cyan]")
        for i, step in enumerate(guidance, 1):
            console.print(f"  {i}. {step}")
    
    def show_progress_with_explanation(self, operation: str, total_items: int, 
                                     explanation: str, process_func: Callable) -> Any:
        """Show progress with educational explanations"""
        
        # Show initial explanation
        if self.explanation_level != ExplanationLevel.EXPERT:
            console.print(Panel.fit(
                f"[bold blue]🚀 Starting: {operation}[/bold blue]\n\n{explanation}",
                title="Operation Explanation"
            ))
        
        # Run with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"[cyan]{operation}...", total=total_items)
            
            result = process_func(progress, task)
            
            progress.update(task, completed=total_items)
        
        return result
    
    def create_interactive_tutorial(self, tutorial_name: str) -> None:
        """Create an interactive tutorial for a specific topic"""
        tutorials = {
            "idor_testing": self._idor_tutorial,
            "access_control_basics": self._access_control_tutorial,
            "session_testing": self._session_tutorial
        }
        
        tutorial_func = tutorials.get(tutorial_name)
        if tutorial_func:
            tutorial_func()
        else:
            console.print(f"[red]❌ Tutorial '{tutorial_name}' not found[/red]")
    
    def _idor_tutorial(self) -> None:
        """Interactive IDOR testing tutorial"""
        console.print(Panel.fit(
            "[bold blue]🎓 Interactive IDOR Testing Tutorial[/bold blue]\n\n"
            "This tutorial will guide you through testing for Insecure Direct Object Reference vulnerabilities.",
            title="Tutorial"
        ))
        
        steps = [
            ("Understanding IDOR", "idor"),
            ("Identifying Potential Targets", "Look for URLs with ID parameters like /user/123 or /document?id=456"),
            ("Testing Different IDs", "Try changing the ID to access other users' data"),
            ("Documenting Findings", "Record what data you can access and its sensitivity")
        ]
        
        for i, (step_name, content) in enumerate(steps, 1):
            console.print(f"\n[bold green]Step {i}: {step_name}[/bold green]")
            
            if content in self.concepts_database:
                self.explain_concept(content)
            else:
                console.print(content)
            
            if self.interactive_mode and i < len(steps):
                input("\nPress Enter to continue to the next step...")
    
    def _access_control_tutorial(self) -> None:
        """Interactive access control testing tutorial"""
        console.print(Panel.fit(
            "[bold blue]🎓 Access Control Testing Tutorial[/bold blue]\n\n"
            "Learn how to systematically test access control mechanisms.",
            title="Tutorial"
        ))
        
        # Explain concept first
        self.explain_concept("broken_access_control")
        
        # Then show testing methodology
        console.print(f"\n[bold green]🧪 Testing Methodology:[/bold green]")
        methodology = [
            "Map all accessible resources and functions",
            "Identify different user roles and permissions",
            "Test horizontal access (same level, different user)",
            "Test vertical access (different privilege levels)",
            "Document and verify findings"
        ]
        
        for i, step in enumerate(methodology, 1):
            console.print(f"  {i}. {step}")
            if self.interactive_mode:
                input(f"\nPress Enter when you understand step {i}...")
    
    def _session_tutorial(self) -> None:
        """Interactive session management testing tutorial"""
        console.print(Panel.fit(
            "[bold blue]🎓 Session Management Testing Tutorial[/bold blue]\n\n"
            "Understanding how to test session security.",
            title="Tutorial"
        ))
        
        self.explain_concept("session_management")
        
        # Show testing areas
        console.print(f"\n[bold green]🔍 Key Testing Areas:[/bold green]")
        areas = [
            "Session token randomness and entropy",
            "Session timeout and invalidation",
            "Session fixation vulnerabilities",
            "Cross-site request forgery (CSRF) protection",
            "Secure cookie attributes"
        ]
        
        for area in areas:
            console.print(f"  • {area}")
    
    def set_explanation_level(self, level: ExplanationLevel) -> None:
        """Set the explanation detail level"""
        self.explanation_level = level
        console.print(f"[green]✅ Explanation level set to: {level.value}[/green]")
    
    def toggle_interactive_mode(self) -> None:
        """Toggle interactive mode on/off"""
        self.interactive_mode = not self.interactive_mode
        status = "enabled" if self.interactive_mode else "disabled"
        console.print(f"[green]✅ Interactive mode {status}[/green]")
    
    def show_help(self) -> None:
        """Show help for educational mode"""
        help_text = """
# Educational Mode Help

## Explanation Levels
- **basic**: Simple explanations for beginners
- **intermediate**: More technical details  
- **advanced**: Deep technical explanations
- **expert**: Minimal explanations, focus on results

## Commands
- `explain <concept>`: Get explanation of a security concept
- `tutorial <name>`: Start an interactive tutorial
- `level <basic|intermediate|advanced|expert>`: Set explanation level
- `interactive`: Toggle interactive mode
- `help`: Show this help

## Available Concepts
- broken_access_control
- idor
- privilege_escalation
- session_management
- information_disclosure

## Available Tutorials
- idor_testing
- access_control_basics
- session_testing
"""
        
        console.print(Markdown(help_text))


# Convenience functions for integration with main tool
def create_educational_mode(level: str = "basic") -> EducationalModeManager:
    """Create educational mode manager with specified level"""
    level_map = {
        "basic": ExplanationLevel.BASIC,
        "intermediate": ExplanationLevel.INTERMEDIATE,
        "advanced": ExplanationLevel.ADVANCED,
        "expert": ExplanationLevel.EXPERT
    }
    
    explanation_level = level_map.get(level.lower(), ExplanationLevel.BASIC)
    return EducationalModeManager(explanation_level)


def explain_finding_interactively(finding: Dict[str, Any], level: str = "basic") -> None:
    """Explain a finding interactively"""
    edu_mode = create_educational_mode(level)
    edu_mode.show_finding_explanation(finding)


def run_educational_step(step_name: str, explanation: str, level: str = "basic") -> None:
    """Run a step with educational explanation"""
    edu_mode = create_educational_mode(level)
    
    step = StepExplanation(
        step_name=step_name,
        what_happening=explanation,
        why_doing_this="This step helps identify potential security vulnerabilities",
        what_to_look_for="Unusual responses, errors, or unexpected behavior",
        potential_findings=["Access control issues", "Information disclosure", "Authentication bypasses"],
        next_steps=["Analyze results", "Test additional scenarios", "Document findings"]
    )
    
    edu_mode.explain_step(step)