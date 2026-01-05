#!/usr/bin/env python3
"""
Agent Run Summary Script
Analyzes Claude Code JSONL transcript files to show:
- How many times each agent was invoked
- Total duration per agent
- Average duration per agent
"""

import sys
import json
import os
from collections import defaultdict
from pathlib import Path

def fmt_time(ms):
    """Format milliseconds to human readable time"""
    if ms >= 60000:
        return f"{ms/60000:.1f}m"
    elif ms >= 1000:
        return f"{ms/1000:.1f}s"
    else:
        return f"{ms}ms"

def analyze_jsonl_files(jsonl_paths):
    """Parse JSONL files and extract agent run stats"""
    agent_stats = defaultdict(lambda: {'count': 0, 'total_duration_ms': 0})
    pending_agents = {}  # tool_use_id -> agent_type

    for jsonl_path in jsonl_paths:
        try:
            with open(jsonl_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())

                        # Track Task tool invocations
                        if data.get('type') == 'assistant':
                            msg = data.get('message', {})
                            if isinstance(msg, dict):
                                content_list = msg.get('content', [])
                                if isinstance(content_list, list):
                                    for content in content_list:
                                        if isinstance(content, dict) and content.get('type') == 'tool_use' and content.get('name') == 'Task':
                                            inp = content.get('input', {})
                                            if isinstance(inp, dict):
                                                agent_type = inp.get('subagent_type')
                                                tool_use_id = content.get('id')
                                                if agent_type and tool_use_id:
                                                    pending_agents[tool_use_id] = agent_type
                                                    agent_stats[agent_type]['count'] += 1

                        # Match tool results back to agent invocations
                        if data.get('type') == 'user':
                            msg = data.get('message', {})
                            if isinstance(msg, dict):
                                content_list = msg.get('content', [])
                                if isinstance(content_list, list):
                                    for content in content_list:
                                        if isinstance(content, dict) and content.get('type') == 'tool_result':
                                            tool_use_id = content.get('tool_use_id')
                                            if tool_use_id in pending_agents:
                                                agent_type = pending_agents[tool_use_id]
                                                # Get duration from toolUseResult
                                                tr = data.get('toolUseResult', {})
                                                if isinstance(tr, dict):
                                                    duration = tr.get('totalDurationMs', 0)
                                                    agent_stats[agent_type]['total_duration_ms'] += duration
                                                del pending_agents[tool_use_id]

                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error reading {jsonl_path}: {e}", file=sys.stderr)

    return agent_stats

def print_summary(agent_stats):
    """Print formatted summary table"""
    print()
    print("Claude Code Agent Run Summary")
    print("=" * 70)
    print(f"{'Agent Type':<30} {'Runs':>8} {'Total Time':>14} {'Avg Time':>14}")
    print("-" * 70)

    total_runs = 0
    total_time = 0

    for agent, stats in sorted(agent_stats.items()):
        runs = stats['count']
        total_ms = stats['total_duration_ms']
        avg_ms = total_ms // runs if runs > 0 else 0

        print(f"{agent:<30} {runs:>8} {fmt_time(total_ms):>14} {fmt_time(avg_ms):>14}")
        total_runs += runs
        total_time += total_ms

    print("-" * 70)
    print(f"{'TOTAL':<30} {total_runs:>8} {fmt_time(total_time):>14}")
    print()

def main():
    # Default: look in ~/.claude/projects/
    claude_dir = Path.home() / ".claude" / "projects"

    if len(sys.argv) > 1:
        # Use provided paths
        jsonl_paths = [Path(p) for p in sys.argv[1:]]
    else:
        # Find all JSONL files
        jsonl_paths = list(claude_dir.rglob("*.jsonl"))

    if not jsonl_paths:
        print("No JSONL files found.")
        print(f"Searched in: {claude_dir}")
        sys.exit(1)

    print(f"Analyzing {len(jsonl_paths)} transcript file(s)...")

    agent_stats = analyze_jsonl_files(jsonl_paths)

    if not agent_stats:
        print("No agent invocations found in transcripts.")
        sys.exit(0)

    print_summary(agent_stats)

if __name__ == "__main__":
    main()
