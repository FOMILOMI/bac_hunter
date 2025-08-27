"""
Enhanced Setup Wizard for BAC Hunter
Provides guided configuration for beginners with pre-configured profiles
"""

from __future__ import annotations
import os
import json
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown

console = Console()

class SetupWizard:
    """Advanced setup wizard for BAC Hunter configuration"""
    
    def __init__(self):
        self.config = {}
        self.profiles = self._load_profiles()
        
    def _load_profiles(self) -> Dict[str, Any]:
        """Load pre-configured profiles for different scenarios"""
        return {
            "quick_scan": {
                "name": "Quick Scan",
                "description": "Fast 15-minute assessment for basic vulnerabilities",
                "mode": "standard",
                "max_rps": 2.0,
                "timeout": 15,
                "phases": ["recon", "access"],
                "recommended_for": "Beginners, quick assessments"
            },
            "comprehensive": {
                "name": "Comprehensive Scan",
                "description": "Full security assessment with all modules",
                "mode": "standard",
                "max_rps": 1.5,
                "timeout": 120,
                "phases": ["recon", "scan", "access", "audit", "exploit"],
                "recommended_for": "Professional security testing"
            },
            "stealth": {
                "name": "Stealth Mode",
                "description": "Low-noise scanning for production environments",
                "mode": "conservative",
                "max_rps": 0.5,
                "timeout": 180,
                "phases": ["recon", "access"],
                "recommended_for": "Production environments"
            },
            "aggressive": {
                "name": "Aggressive Testing",
                "description": "Maximum coverage with higher risk tolerance",
                "mode": "aggressive",
                "max_rps": 5.0,
                "timeout": 60,
                "phases": ["recon", "scan", "access", "audit", "exploit"],
                "recommended_for": "Test environments only"
            },
            "api_focused": {
                "name": "API Security Testing",
                "description": "Specialized for REST/GraphQL API testing",
                "mode": "standard",
                "max_rps": 2.0,
                "timeout": 90,
                "phases": ["recon", "access", "audit"],
                "api_specific": True,
                "recommended_for": "API endpoints and microservices"
            },
            "web_app": {
                "name": "Web Application Testing",
                "description": "Traditional web application security assessment",
                "mode": "standard",
                "max_rps": 2.0,
                "timeout": 90,
                "phases": ["recon", "scan", "access", "audit"],
                "web_specific": True,
                "recommended_for": "Traditional web applications"
            }
        }
    
    def run(self, output_dir: str = ".") -> None:
        """Run the interactive setup wizard"""
        console.print(Panel.fit(
            "[bold blue]🚀 BAC Hunter Setup Wizard[/bold blue]\n"
            "Welcome! This wizard will help you configure BAC Hunter for your security testing needs.\n"
            "We'll guide you through the process step by step.",
            title="Welcome"
        ))
        
        # Step 1: Experience level
        experience_level = self._get_experience_level()
        
        # Step 2: Choose profile or custom setup
        if experience_level == "beginner":
            profile = self._choose_profile_guided()
        else:
            setup_type = Prompt.ask(
                "Would you like to use a pre-configured profile or create a custom configuration?",
                choices=["profile", "custom"],
                default="profile"
            )
            if setup_type == "profile":
                profile = self._choose_profile()
            else:
                profile = self._create_custom_profile()
        
        # Step 3: Target configuration
        targets = self._configure_targets()
        
        # Step 4: Authentication setup
        auth_config = self._configure_authentication()
        
        # Step 5: Advanced options (if not beginner)
        advanced_config = {}
        if experience_level != "beginner":
            advanced_config = self._configure_advanced_options()
        
        # Step 6: Generate configuration files
        self._generate_config_files(profile, targets, auth_config, advanced_config, output_dir)
        
        # Step 7: Show next steps
        self._show_next_steps(profile, output_dir)
    
    def _get_experience_level(self) -> str:
        """Determine user's experience level"""
        console.print("\n[bold]What's your experience with security testing tools?[/bold]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Level", style="cyan")
        table.add_column("Description", style="white")
        
        table.add_row("beginner", "New to security testing or BAC Hunter")
        table.add_row("intermediate", "Some experience with security tools")
        table.add_row("advanced", "Experienced security professional")
        
        console.print(table)
        
        return Prompt.ask(
            "Select your experience level",
            choices=["beginner", "intermediate", "advanced"],
            default="beginner"
        )
    
    def _choose_profile_guided(self) -> Dict[str, Any]:
        """Guided profile selection for beginners"""
        console.print("\n[bold]Let's choose the right scanning profile for you![/bold]")
        console.print("Here are some questions to help us recommend the best option:\n")
        
        # Ask guiding questions
        target_type = Prompt.ask(
            "What type of application are you testing?",
            choices=["web", "api", "both", "unsure"],
            default="web"
        )
        
        environment = Prompt.ask(
            "Is this a production environment?",
            choices=["yes", "no", "unsure"],
            default="no"
        )
        
        time_constraint = Prompt.ask(
            "How much time do you have for testing?",
            choices=["quick (15 min)", "moderate (1-2 hours)", "extensive (3+ hours)"],
            default="quick (15 min)"
        )
        
        # Recommend profile based on answers
        if environment == "yes":
            recommended = "stealth"
        elif time_constraint.startswith("quick"):
            recommended = "quick_scan"
        elif target_type == "api":
            recommended = "api_focused"
        elif target_type == "web":
            recommended = "web_app"
        else:
            recommended = "comprehensive"
        
        console.print(f"\n[green]✅ Based on your answers, we recommend: {self.profiles[recommended]['name']}[/green]")
        console.print(f"[dim]{self.profiles[recommended]['description']}[/dim]\n")
        
        if Confirm.ask("Would you like to use this recommended profile?", default=True):
            return self.profiles[recommended]
        else:
            return self._choose_profile()
    
    def _choose_profile(self) -> Dict[str, Any]:
        """Let user choose from available profiles"""
        console.print("\n[bold]Available Scanning Profiles:[/bold]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Profile", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Recommended For", style="yellow")
        table.add_column("Duration", style="green")
        
        profile_keys = list(self.profiles.keys())
        for key in profile_keys:
            profile = self.profiles[key]
            table.add_row(
                profile["name"],
                profile["description"],
                profile["recommended_for"],
                f"{profile['timeout']} min"
            )
        
        console.print(table)
        
        choice = Prompt.ask(
            "Select a profile",
            choices=profile_keys,
            default="quick_scan"
        )
        
        return self.profiles[choice]
    
    def _create_custom_profile(self) -> Dict[str, Any]:
        """Create a custom scanning profile"""
        console.print("\n[bold]Creating Custom Profile[/bold]\n")
        
        profile = {
            "name": "Custom",
            "description": "User-defined configuration"
        }
        
        profile["mode"] = Prompt.ask(
            "Scanning mode",
            choices=["conservative", "standard", "aggressive"],
            default="standard"
        )
        
        profile["max_rps"] = float(Prompt.ask(
            "Maximum requests per second",
            default="2.0"
        ))
        
        profile["timeout"] = int(Prompt.ask(
            "Maximum scan duration (minutes)",
            default="60"
        ))
        
        # Phase selection
        available_phases = ["recon", "scan", "access", "audit", "exploit"]
        console.print(f"\nAvailable phases: {', '.join(available_phases)}")
        phases_input = Prompt.ask(
            "Select phases (comma-separated)",
            default="recon,access"
        )
        profile["phases"] = [p.strip() for p in phases_input.split(",")]
        
        return profile
    
    def _configure_targets(self) -> List[str]:
        """Configure target URLs"""
        console.print("\n[bold]Target Configuration[/bold]\n")
        
        targets = []
        while True:
            target = Prompt.ask("Enter target URL (or press Enter to finish)")
            if not target:
                break
            
            # Basic URL validation
            if not target.startswith(('http://', 'https://')):
                target = f"https://{target}"
            
            targets.append(target)
            console.print(f"[green]✅ Added target: {target}[/green]")
        
        if not targets:
            targets.append("https://example.com")
            console.print("[yellow]⚠️  No targets specified, using example.com[/yellow]")
        
        return targets
    
    def _configure_authentication(self) -> Dict[str, Any]:
        """Configure authentication settings"""
        console.print("\n[bold]Authentication Configuration[/bold]\n")
        
        auth_config = {
            "semi_auto_login": True,
            "identities": []
        }
        
        if Confirm.ask("Do you need to test with authentication?", default=False):
            # Anonymous identity
            auth_config["identities"].append({
                "name": "anonymous",
                "headers": {"User-Agent": "BAC-Hunter/2.0"},
                "description": "Unauthenticated requests"
            })
            
            # Authenticated identity
            auth_method = Prompt.ask(
                "Authentication method",
                choices=["browser", "cookie", "header", "basic"],
                default="browser"
            )
            
            if auth_method == "browser":
                auth_config["semi_auto_login"] = True
                auth_config["identities"].append({
                    "name": "authenticated",
                    "headers": {"User-Agent": "BAC-Hunter/2.0"},
                    "description": "Authenticated via browser login"
                })
            elif auth_method == "cookie":
                cookie_value = Prompt.ask("Enter cookie value")
                auth_config["identities"].append({
                    "name": "authenticated",
                    "headers": {"User-Agent": "BAC-Hunter/2.0"},
                    "cookie": cookie_value,
                    "description": "Authenticated via cookie"
                })
            elif auth_method == "header":
                header_name = Prompt.ask("Header name (e.g., Authorization)")
                header_value = Prompt.ask("Header value")
                auth_config["identities"].append({
                    "name": "authenticated",
                    "headers": {
                        "User-Agent": "BAC-Hunter/2.0",
                        header_name: header_value
                    },
                    "description": "Authenticated via header"
                })
        else:
            # Just anonymous identity
            auth_config["identities"].append({
                "name": "anonymous",
                "headers": {"User-Agent": "BAC-Hunter/2.0"},
                "description": "Unauthenticated requests"
            })
        
        return auth_config
    
    def _configure_advanced_options(self) -> Dict[str, Any]:
        """Configure advanced options for experienced users"""
        console.print("\n[bold]Advanced Configuration[/bold]\n")
        
        advanced = {}
        
        if Confirm.ask("Configure proxy settings?", default=False):
            proxy = Prompt.ask("Proxy URL (e.g., http://127.0.0.1:8080)")
            advanced["proxy"] = proxy
        
        if Confirm.ask("Enable AI-powered features?", default=True):
            advanced["ai_enabled"] = True
            advanced["anomaly_detection"] = Confirm.ask("Enable anomaly detection?", default=True)
            advanced["smart_recommendations"] = Confirm.ask("Enable smart recommendations?", default=True)
        
        if Confirm.ask("Configure custom headers?", default=False):
            headers = {}
            while True:
                header_name = Prompt.ask("Header name (or press Enter to finish)")
                if not header_name:
                    break
                header_value = Prompt.ask(f"Value for {header_name}")
                headers[header_name] = header_value
            advanced["custom_headers"] = headers
        
        return advanced
    
    def _generate_config_files(self, profile: Dict[str, Any], targets: List[str], 
                             auth_config: Dict[str, Any], advanced_config: Dict[str, Any], 
                             output_dir: str) -> None:
        """Generate configuration files"""
        console.print("\n[bold]Generating Configuration Files...[/bold]\n")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Generate identities.yaml
        identities_file = output_path / "identities.yaml"
        identities_data = {"identities": auth_config["identities"]}
        
        with open(identities_file, 'w') as f:
            yaml.dump(identities_data, f, default_flow_style=False)
        console.print(f"[green]✅ Generated {identities_file}[/green]")
        
        # Generate tasks.yaml
        tasks_file = output_path / "tasks.yaml"
        tasks = []
        
        for i, phase in enumerate(profile.get("phases", ["recon"])):
            task = {
                "type": phase,
                "priority": i,
                "params": {
                    "target": targets[0] if targets else "https://example.com",
                    "mode": profile.get("mode", "standard"),
                    "max_rps": profile.get("max_rps", 2.0)
                }
            }
            
            if auth_config["identities"] and len(auth_config["identities"]) > 1:
                task["params"]["identities_yaml"] = "identities.yaml"
                task["params"]["unauth_name"] = "anonymous"
                task["params"]["auth_name"] = "authenticated"
            
            tasks.append(task)
        
        tasks_data = {"tasks": tasks}
        with open(tasks_file, 'w') as f:
            yaml.dump(tasks_data, f, default_flow_style=False)
        console.print(f"[green]✅ Generated {tasks_file}[/green]")
        
        # Generate .bac-hunter.yml for CI integration
        ci_config_file = output_path / ".bac-hunter.yml"
        ci_config = {
            "targets": targets,
            "identities": "identities.yaml",
            "mode": profile.get("mode", "standard"),
            "smart": True,
            "max_rps": profile.get("max_rps", 2.0),
            "timeout": profile.get("timeout", 60)
        }
        
        if advanced_config:
            ci_config.update(advanced_config)
        
        with open(ci_config_file, 'w') as f:
            yaml.dump(ci_config, f, default_flow_style=False)
        console.print(f"[green]✅ Generated {ci_config_file}[/green]")
        
        # Generate quick start script
        script_file = output_path / "run_scan.sh"
        script_content = f"""#!/bin/bash
# BAC Hunter Quick Start Script
# Generated by Setup Wizard

echo "🚀 Starting BAC Hunter scan with {profile['name']} profile..."

# Set environment variables
export BH_SEMI_AUTO_LOGIN={str(auth_config['semi_auto_login']).lower()}

# Run the scan
python -m bac_hunter smart-auto \\
  --mode {profile.get('mode', 'standard')} \\
  --max-rps {profile.get('max_rps', 2.0)} \\
  --identities-yaml identities.yaml \\
  {targets[0] if targets else 'https://example.com'}

echo "✅ Scan completed! Check the results in the web dashboard:"
echo "python -m bac_hunter dashboard --host 0.0.0.0 --port 8000"
"""
        
        with open(script_file, 'w') as f:
            f.write(script_content)
        os.chmod(script_file, 0o755)
        console.print(f"[green]✅ Generated {script_file}[/green]")
    
    def _show_next_steps(self, profile: Dict[str, Any], output_dir: str) -> None:
        """Show next steps to the user"""
        console.print("\n[bold green]🎉 Setup Complete![/bold green]\n")
        
        next_steps = f"""
## Next Steps:

### 1. Quick Start (Recommended for beginners)
```bash
cd {output_dir}
./run_scan.sh
```

### 2. Manual Execution
```bash
# Run a quick scan
python -m bac_hunter smart-auto --identities-yaml identities.yaml --mode {profile.get('mode', 'standard')} <target>

# View results in web dashboard
python -m bac_hunter dashboard --host 0.0.0.0 --port 8000
```

### 3. Advanced Usage
```bash
# Use orchestrator for complex workflows
python -m bac_hunter orchestrate --tasks-yaml tasks.yaml

# Generate detailed reports
python -m bac_hunter report --output report.html
```

### 4. Learning Mode
```bash
# Run with educational explanations
python -m bac_hunter smart-auto --learning-mode <target>
```

## Files Created:
- `identities.yaml` - Authentication configurations
- `tasks.yaml` - Scan workflow definitions  
- `.bac-hunter.yml` - CI/CD integration config
- `run_scan.sh` - Quick start script

## Need Help?
- Run `python -m bac_hunter --help` for command reference
- Use `--verbose 2` for detailed logging
- Check the web dashboard at http://localhost:8000 for real-time results

Happy hunting! 🎯
"""
        
        console.print(Markdown(next_steps))


def run_wizard(output_dir: str = ".") -> None:
    """Entry point for the setup wizard"""
    wizard = SetupWizard()
    wizard.run(output_dir)


if __name__ == "__main__":
    run_wizard()