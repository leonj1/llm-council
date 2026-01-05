#!/usr/bin/env python3
# ~/.claude/hooks/skill_discovery_hook.py

import json
import os
import urllib.request

SKILL_API_URL = os.environ.get(
    "SKILL_API_URL", "https://external-claude-skills-production.up.railway.app/"
)


def should_check_skills(prompt: str) -> bool:
    """Determine if this prompt needs skill discovery."""
    # Keywords that indicate skill discovery is needed
    action_keywords = [
        "create",
        "build",
        "deploy",
        "set up",
        "configure",
        "implement",
        "make",
        "generate",
        "scaffold",
        "initialize",
        "provision",
        "migrate",
        "upgrade",
        "install",
        "establish",
    ]

    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in action_keywords)


def discover_skills(prompt: str) -> dict:
    """Call the skill discovery API."""
    try:
        req = urllib.request.Request(
            f"{SKILL_API_URL}/discover",
            data=json.dumps({"query": prompt}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read())
    except Exception as e:
        return {"error": str(e), "skills": []}


def main():
    prompt = os.environ.get("PROMPT", "")

    if not should_check_skills(prompt):
        return  # No output = no injection

    result = discover_skills(prompt)

    if result.get("error"):
        print(f"\n⚠️ Skill discovery unavailable: {result['error']}")
        print("Proceeding without organizational skills.\n")
        return

    if not result.get("execution_order"):
        return  # No matching skills

    # Inject skill context
    print("\n" + "=" * 60)
    print("🔧 ORGANIZATIONAL SKILLS LOADED")
    print("=" * 60)
    print(
        f"\nMatched: {result.get('route_type', 'unknown')} → {result.get('matched', 'unknown')}"
    )
    print(f"Skills to apply (in order): {' → '.join(result['execution_order'])}")
    print("\n⚠️ YOU MUST FOLLOW THESE SKILL INSTRUCTIONS ⚠️\n")

    for skill in result.get("skill_definitions", []):
        marker = "📌 PRIMARY" if skill.get("is_primary") else "📎 DEPENDENCY"
        print(f"\n### {skill['name']} [{marker}]")
        print(skill.get("content", "(content unavailable)"))
        print("\n" + "-" * 40)

    print("\n" + "=" * 60)
    print("END OF SKILL CONTEXT - Follow instructions above")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
