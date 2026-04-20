#!/usr/bin/env python3
"""
Generate HTML Skill Audit Report

Converts skill audit eval JSON output to a formatted HTML report.
Supports both single-skill and multi-skill (cumulative) reports.
Uses only Python stdlib - no external dependencies required.

Input formats:
- Single skill (object): {skill_name: ..., summary: ..., ...}
- Multiple skills (array): [{skill1_data}, {skill2_data}, ...]

Usage:
    python generate-report.py audit-output.json
    python generate-report.py - < audit-output.json
    python generate-report.py audit-output.json -o report.html
"""

import argparse
import html
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO


# Color scheme constants
COLORS = {
    "cream": "#FFFBF0",
    "dark": "#2A2A2A",
    "gray": "#6B7280",
    "light_gray": "#E5E7EB",
    "pass": "#10B981",
    "fail": "#EF4444",
    "skip": "#F59E0B",
    "info": "#3B82F6",
    "border": "#D1D5DB",
    "card_bg": "#FFFFFF",
}

# Grade color mapping
GRADE_COLORS = {
    "A": "#10B981",  # Green
    "B": "#3B82F6",  # Blue
    "C": "#F59E0B",  # Amber
    "D": "#EF4444",  # Red
    "F": "#7F1D1D",  # Dark Red
}


def escape(text: str) -> str:
    """Escape HTML special characters."""
    return html.escape(str(text))


def format_percentage(value: float) -> str:
    """Format a float as a percentage."""
    return f"{value * 100:.0f}%"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.0f}s"


def format_tokens(tokens: int) -> str:
    """Format token count with commas."""
    return f"{tokens:,}"


def get_status_color(status: str) -> str:
    """Get color for a status (PASS/FAIL/SKIP)."""
    status_upper = status.upper()
    if status_upper == "PASS":
        return COLORS["pass"]
    elif status_upper == "FAIL":
        return COLORS["fail"]
    elif status_upper == "SKIP":
        return COLORS["skip"]
    return COLORS["gray"]


def get_grade_color(grade: str) -> str:
    """Get color for a grade (A-F)."""
    return GRADE_COLORS.get(grade.upper(), COLORS["gray"])


def generate_css(multi_skill: bool = False) -> str:
    """Generate inline CSS styles."""
    sidebar_styles = ""
    if multi_skill:
        sidebar_styles = f"""
        .layout-with-sidebar {{
            display: flex;
            gap: 2rem;
            margin: 0 auto;
            max-width: 1400px;
        }}

        .sidebar {{
            position: sticky;
            top: 2rem;
            width: 220px;
            height: fit-content;
            max-height: calc(100vh - 4rem);
            overflow-y: auto;
            background: {COLORS["card_bg"]};
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}

        .sidebar h2 {{
            font-size: 0.875rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: {COLORS["gray"]};
            margin: 0 0 1rem 0;
            padding: 0;
            border: none;
        }}

        .sidebar nav {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}

        .sidebar a {{
            display: block;
            padding: 0.5rem 0.75rem;
            color: {COLORS["dark"]};
            text-decoration: none;
            border-radius: 4px;
            font-size: 0.875rem;
            transition: background-color 0.2s;
        }}

        .sidebar a:hover {{
            background-color: {COLORS["light_gray"]};
        }}

        .main-content {{
            flex: 1;
            min-width: 0;
        }}

        .skill-section {{
            margin-bottom: 3rem;
            padding-top: 2rem;
            border-top: 3px solid {COLORS["border"]};
        }}

        .skill-section:first-child {{
            border-top: none;
            padding-top: 0;
        }}

        .summary-table {{
            width: 100%;
            margin: 1rem 0 2rem 0;
        }}

        .summary-table tbody tr {{
            cursor: pointer;
            transition: background-color 0.2s;
        }}

        .summary-table tbody tr:hover {{
            background-color: {COLORS["cream"]};
        }}
        """

    return f"""
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: {COLORS["cream"]};
            color: {COLORS["dark"]};
            line-height: 1.6;
            padding: 2rem;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            background: {COLORS["card_bg"]};
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}

        h1 {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: {COLORS["dark"]};
        }}

        h2 {{
            font-size: 1.5rem;
            font-weight: 600;
            margin: 2rem 0 1rem 0;
            color: {COLORS["dark"]};
            border-bottom: 2px solid {COLORS["light_gray"]};
            padding-bottom: 0.5rem;
        }}

        h3 {{
            font-size: 1.25rem;
            font-weight: 600;
            margin: 1.5rem 0 0.75rem 0;
            color: {COLORS["dark"]};
        }}

        .meta {{
            display: flex;
            gap: 2rem;
            color: {COLORS["gray"]};
            font-size: 0.875rem;
            margin-top: 1rem;
        }}

        .meta-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .meta-label {{
            font-weight: 600;
        }}

        .grade-badge {{
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-size: 1.5rem;
            font-weight: 700;
            color: white;
            margin-left: 1rem;
        }}

        .card {{
            background: {COLORS["card_bg"]};
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            background: {COLORS["card_bg"]};
        }}

        thead {{
            background-color: {COLORS["light_gray"]};
        }}

        th {{
            text-align: left;
            padding: 0.75rem;
            font-weight: 600;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: {COLORS["gray"]};
            border-bottom: 2px solid {COLORS["border"]};
        }}

        td {{
            padding: 0.75rem;
            border-bottom: 1px solid {COLORS["light_gray"]};
            vertical-align: top;
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        .status-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            color: white;
        }}

        .status-pass {{ background-color: {COLORS["pass"]}; }}
        .status-fail {{ background-color: {COLORS["fail"]}; }}
        .status-skip {{ background-color: {COLORS["skip"]}; }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }}

        .stat-card {{
            background: {COLORS["light_gray"]};
            padding: 1rem;
            border-radius: 6px;
            text-align: center;
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: {COLORS["dark"]};
        }}

        .stat-label {{
            font-size: 0.875rem;
            color: {COLORS["gray"]};
            margin-top: 0.25rem;
        }}

        .comparison-table {{
            margin: 1.5rem 0;
        }}

        .comparison-table th {{
            text-align: center;
        }}

        .comparison-table td {{
            text-align: center;
        }}

        .comparison-table td:first-child {{
            text-align: left;
            font-weight: 600;
        }}

        .delta-positive {{
            color: {COLORS["pass"]};
            font-weight: 600;
        }}

        .delta-negative {{
            color: {COLORS["fail"]};
            font-weight: 600;
        }}

        .prompt-card {{
            border: 1px solid {COLORS["border"]};
            border-radius: 6px;
            padding: 1rem;
            margin: 1rem 0;
        }}

        .prompt-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid {COLORS["light_gray"]};
        }}

        .prompt-id {{
            font-weight: 600;
            color: {COLORS["info"]};
        }}

        .prompt-type {{
            font-size: 0.75rem;
            text-transform: uppercase;
            color: {COLORS["gray"]};
            background: {COLORS["light_gray"]};
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
        }}

        .prompt-text {{
            font-size: 0.875rem;
            color: {COLORS["gray"]};
            font-style: italic;
            margin-bottom: 1rem;
            padding: 0.75rem;
            background: {COLORS["cream"]};
            border-radius: 4px;
        }}

        .assertion-list {{
            list-style: none;
            padding: 0;
        }}

        .assertion-item {{
            padding: 0.5rem;
            margin: 0.5rem 0;
            border-radius: 4px;
            display: flex;
            gap: 1rem;
        }}

        .assertion-item.pass {{
            background-color: rgba(16, 185, 129, 0.1);
            border-left: 3px solid {COLORS["pass"]};
        }}

        .assertion-item.fail {{
            background-color: rgba(239, 68, 68, 0.1);
            border-left: 3px solid {COLORS["fail"]};
        }}

        .assertion-id {{
            font-weight: 600;
            min-width: 3rem;
        }}

        .assertion-content {{
            flex: 1;
        }}

        .assertion-text {{
            font-size: 0.875rem;
            margin-bottom: 0.25rem;
        }}

        .assertion-evidence {{
            font-size: 0.75rem;
            color: {COLORS["gray"]};
            font-style: italic;
        }}

        .iteration-header {{
            background: {COLORS["light_gray"]};
            padding: 1rem;
            border-radius: 6px;
            margin: 1.5rem 0 1rem 0;
        }}

        .iteration-title {{
            font-size: 1.125rem;
            font-weight: 600;
            color: {COLORS["dark"]};
        }}

        .iteration-note {{
            font-size: 0.875rem;
            color: {COLORS["gray"]};
            margin-top: 0.25rem;
        }}

        .fix-item {{
            margin: 1rem 0;
            padding: 1rem;
            background: {COLORS["light_gray"]};
            border-radius: 6px;
        }}

        .fix-section {{
            font-weight: 600;
            color: {COLORS["info"]};
            margin-bottom: 0.5rem;
        }}

        .fix-action {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            margin-right: 0.5rem;
        }}

        .fix-action.add {{ background-color: {COLORS["pass"]}; color: white; }}
        .fix-action.edit {{ background-color: {COLORS["info"]}; color: white; }}
        .fix-action.remove {{ background-color: {COLORS["fail"]}; color: white; }}

        .fix-description {{
            font-size: 0.875rem;
            color: {COLORS["dark"]};
            margin-top: 0.5rem;
        }}

        footer {{
            text-align: center;
            color: {COLORS["gray"]};
            font-size: 0.875rem;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid {COLORS["border"]};
        }}

        {sidebar_styles}
    </style>
    """


def generate_header_single(data: Dict[str, Any]) -> str:
    """Generate HTML header section for single-skill report."""
    skill_name = escape(data.get("skill_name", "Unknown Skill"))
    timestamp = data.get("timestamp", "")
    model = escape(data.get("model", "Unknown Model"))
    summary = data.get("summary", {})
    grade = escape(summary.get("grade", "N/A"))
    grade_color = get_grade_color(grade)

    # Format timestamp
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        formatted_date = dt.strftime("%B %d, %Y at %I:%M %p")
    except (ValueError, AttributeError):
        formatted_date = timestamp

    return f"""
    <header>
        <h1>
            {skill_name}
            <span class="grade-badge" style="background-color: {grade_color};">Grade: {grade}</span>
        </h1>
        <div class="meta">
            <div class="meta-item">
                <span class="meta-label">Generated:</span>
                <span>{escape(formatted_date)}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Model:</span>
                <span>{model}</span>
            </div>
        </div>
    </header>
    """


def generate_header_multi(skills: List[Dict[str, Any]]) -> str:
    """Generate HTML header section for multi-skill report."""
    num_skills = len(skills)

    # Find latest timestamp
    latest_timestamp = ""
    for skill in skills:
        ts = skill.get("timestamp", "")
        if ts > latest_timestamp:
            latest_timestamp = ts

    # Format timestamp
    try:
        dt = datetime.fromisoformat(latest_timestamp.replace("Z", "+00:00"))
        formatted_date = dt.strftime("%B %d, %Y at %I:%M %p")
    except (ValueError, AttributeError):
        formatted_date = latest_timestamp

    return f"""
    <header>
        <h1>Skill Audit Report</h1>
        <div class="meta">
            <div class="meta-item">
                <span class="meta-label">{num_skills} skills audited</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Last updated:</span>
                <span>{escape(formatted_date)}</span>
            </div>
        </div>
    </header>
    """


def generate_summary_table(skills: List[Dict[str, Any]]) -> str:
    """Generate summary table for all skills."""
    rows = []
    for skill in skills:
        skill_name = escape(skill.get("skill_name", "Unknown"))
        skill_id = skill_name.lower().replace(" ", "-")
        summary = skill.get("summary", {})
        checklist = skill.get("checklist", {})

        grade = escape(summary.get("grade", "N/A"))
        grade_color = get_grade_color(grade)

        passed = checklist.get("passed", 0)
        total = checklist.get("total", 30)
        checklist_score = f"{passed}/{total}"

        with_skill_rate = summary.get("with_skill_pass_rate", "N/A")
        without_skill_rate = summary.get("without_skill_pass_rate", "N/A")
        delta = escape(summary.get("delta", "N/A"))

        delta_class = ""
        if isinstance(delta, str) and delta.startswith("+"):
            delta_class = "delta-positive"
        elif isinstance(delta, str) and delta.startswith("-"):
            delta_class = "delta-negative"

        rows.append(f"""
            <tr onclick="window.location.hash='#{skill_id}'">
                <td style="font-weight: 600;">{skill_name}</td>
                <td style="text-align: center;">
                    <span class="grade-badge" style="background-color: {grade_color}; font-size: 1rem; padding: 0.25rem 0.75rem;">{grade}</span>
                </td>
                <td style="text-align: center;">{checklist_score}</td>
                <td style="text-align: center;">{with_skill_rate}</td>
                <td style="text-align: center;">{without_skill_rate}</td>
                <td style="text-align: center;" class="{delta_class}">{delta}</td>
            </tr>
        """)

    return f"""
    <div class="card">
        <h2>Summary</h2>
        <table class="summary-table">
            <thead>
                <tr>
                    <th>Skill Name</th>
                    <th style="text-align: center;">Grade</th>
                    <th style="text-align: center;">Checklist Score</th>
                    <th style="text-align: center;">With-Skill Pass Rate</th>
                    <th style="text-align: center;">Without-Skill Pass Rate</th>
                    <th style="text-align: center;">Delta</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
    """


def generate_sidebar(skills: List[Dict[str, Any]]) -> str:
    """Generate navigation sidebar for multi-skill report."""
    links = []
    for skill in skills:
        skill_name = escape(skill.get("skill_name", "Unknown"))
        skill_id = skill_name.lower().replace(" ", "-")
        links.append(f'<a href="#{skill_id}">{skill_name}</a>')

    return f"""
    <aside class="sidebar">
        <h2>Skills</h2>
        <nav>
            {''.join(links)}
        </nav>
    </aside>
    """


def generate_summary_stats(data: Dict[str, Any]) -> str:
    """Generate summary statistics cards."""
    summary = data.get("summary", {})
    checklist = data.get("checklist", {})

    pre_fix = escape(summary.get("pre_fix_score", "N/A"))
    post_fix = escape(summary.get("post_fix_score", "N/A"))
    with_skill_rate = escape(summary.get("with_skill_pass_rate", "N/A"))
    without_skill_rate = escape(summary.get("without_skill_pass_rate", "N/A"))
    delta = escape(summary.get("delta", "N/A"))

    passed = checklist.get("passed", 0)
    total = checklist.get("total", 30)

    return f"""
    <div class="card">
        <h2>Summary</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{passed}/{total}</div>
                <div class="stat-label">Checklist Items Passed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{pre_fix}</div>
                <div class="stat-label">Pre-Fix Score</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{post_fix}</div>
                <div class="stat-label">Post-Fix Score</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{with_skill_rate}</div>
                <div class="stat-label">With Skill Pass Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{without_skill_rate}</div>
                <div class="stat-label">Without Skill Pass Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: {COLORS['pass']}">{delta}</div>
                <div class="stat-label">Improvement Delta</div>
            </div>
        </div>
    </div>
    """


def generate_checklist_table(data: Dict[str, Any]) -> str:
    """Generate checklist results table."""
    checklist = data.get("checklist", {})
    items = checklist.get("items", [])

    if not items:
        return ""

    rows = []
    for item in items:
        number = item.get("number", "")
        text = escape(item.get("text", ""))
        category = escape(item.get("category", ""))
        check_type = escape(item.get("type", ""))
        status = item.get("status", "SKIP").upper()
        reason = escape(item.get("reason", ""))

        status_class = status.lower()
        status_badge = f'<span class="status-badge status-{status_class}">{status}</span>'

        rows.append(f"""
            <tr>
                <td>{number}</td>
                <td>{category}</td>
                <td>{text}</td>
                <td>{check_type}</td>
                <td>{status_badge}</td>
                <td>{reason}</td>
            </tr>
        """)

    return f"""
    <div class="card">
        <h2>Checklist Results</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Category</th>
                    <th>Requirement</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Reason</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
    """


def generate_prompt_results(prompt_data: Dict[str, Any]) -> str:
    """Generate results for a single prompt."""
    prompt_id = escape(prompt_data.get("id", ""))
    prompt_text = escape(prompt_data.get("text", ""))
    prompt_type = escape(prompt_data.get("type", ""))
    results = prompt_data.get("results", {})

    with_skill = results.get("with_skill", {})
    without_skill = results.get("without_skill", {})

    html_parts = [f"""
    <div class="prompt-card">
        <div class="prompt-header">
            <span class="prompt-id">{prompt_id}</span>
            <span class="prompt-type">{prompt_type}</span>
        </div>
        <div class="prompt-text">{prompt_text}</div>
    """]

    # With Skill Results
    with_assertions = with_skill.get("assertions", [])
    with_pass = with_skill.get("pass_count", 0)
    with_total = with_skill.get("total", 0)
    with_duration = with_skill.get("duration_seconds", 0)
    with_tokens = with_skill.get("token_count", 0)

    html_parts.append(f"""
        <h3>With Skill ({with_pass}/{with_total} passed)</h3>
        <ul class="assertion-list">
    """)

    for assertion in with_assertions:
        a_id = escape(assertion.get("id", ""))
        a_text = escape(assertion.get("text", ""))
        a_verdict = assertion.get("verdict", "FAIL").upper()
        a_evidence = escape(assertion.get("evidence", ""))

        verdict_class = "pass" if a_verdict == "PASS" else "fail"

        html_parts.append(f"""
            <li class="assertion-item {verdict_class}">
                <span class="assertion-id">{a_id}</span>
                <div class="assertion-content">
                    <div class="assertion-text">{a_text}</div>
                    <div class="assertion-evidence">{a_evidence}</div>
                </div>
            </li>
        """)

    html_parts.append(f"""
        </ul>
        <p style="font-size: 0.875rem; color: {COLORS['gray']};">
            Duration: {format_duration(with_duration)} | Tokens: {format_tokens(with_tokens)}
        </p>
    """)

    # Without Skill Results
    without_assertions = without_skill.get("assertions", [])
    without_pass = without_skill.get("pass_count", 0)
    without_total = without_skill.get("total", 0)
    without_duration = without_skill.get("duration_seconds", 0)
    without_tokens = without_skill.get("token_count", 0)

    html_parts.append(f"""
        <h3>Without Skill ({without_pass}/{without_total} passed)</h3>
        <ul class="assertion-list">
    """)

    for assertion in without_assertions:
        a_id = escape(assertion.get("id", ""))
        a_text = escape(assertion.get("text", ""))
        a_verdict = assertion.get("verdict", "FAIL").upper()
        a_evidence = escape(assertion.get("evidence", ""))

        verdict_class = "pass" if a_verdict == "PASS" else "fail"

        html_parts.append(f"""
            <li class="assertion-item {verdict_class}">
                <span class="assertion-id">{a_id}</span>
                <div class="assertion-content">
                    <div class="assertion-text">{a_text}</div>
                    <div class="assertion-evidence">{a_evidence}</div>
                </div>
            </li>
        """)

    html_parts.append(f"""
        </ul>
        <p style="font-size: 0.875rem; color: {COLORS['gray']};">
            Duration: {format_duration(without_duration)} | Tokens: {format_tokens(without_tokens)}
        </p>
    </div>
    """)

    return ''.join(html_parts)


def generate_iteration_section(iteration: Dict[str, Any]) -> str:
    """Generate section for one iteration."""
    iteration_num = iteration.get("iteration", 1)
    note = escape(iteration.get("note", ""))
    prompts = iteration.get("prompts", [])
    aggregate = iteration.get("aggregate", {})

    html_parts = [f"""
    <div class="iteration-header">
        <div class="iteration-title">Iteration {iteration_num}</div>
        <div class="iteration-note">{note}</div>
    </div>
    """]

    # Aggregate comparison table
    with_agg = aggregate.get("with_skill", {})
    without_agg = aggregate.get("without_skill", {})
    delta = escape(aggregate.get("delta", ""))

    delta_class = "delta-positive" if delta.startswith("+") else "delta-negative"

    html_parts.append(f"""
    <table class="comparison-table">
        <thead>
            <tr>
                <th>Metric</th>
                <th>With Skill</th>
                <th>Without Skill</th>
                <th>Delta</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Pass Rate</td>
                <td>{format_percentage(with_agg.get('pass_rate', 0))}</td>
                <td>{format_percentage(without_agg.get('pass_rate', 0))}</td>
                <td class="{delta_class}">{delta}</td>
            </tr>
            <tr>
                <td>Assertions Passed</td>
                <td>{with_agg.get('passed', 0)}/{with_agg.get('total_assertions', 0)}</td>
                <td>{without_agg.get('passed', 0)}/{without_agg.get('total_assertions', 0)}</td>
                <td>—</td>
            </tr>
            <tr>
                <td>Avg Duration</td>
                <td>{format_duration(with_agg.get('avg_duration', 0))}</td>
                <td>{format_duration(without_agg.get('avg_duration', 0))}</td>
                <td>—</td>
            </tr>
            <tr>
                <td>Avg Tokens</td>
                <td>{format_tokens(with_agg.get('avg_tokens', 0))}</td>
                <td>{format_tokens(without_agg.get('avg_tokens', 0))}</td>
                <td>—</td>
            </tr>
        </tbody>
    </table>
    """)

    # Individual prompt results
    for prompt in prompts:
        html_parts.append(generate_prompt_results(prompt))

    return ''.join(html_parts)


def generate_eval_section(data: Dict[str, Any]) -> str:
    """Generate evaluation results section."""
    eval_data = data.get("eval", {})
    iterations = eval_data.get("iterations", [])

    if not iterations:
        return ""

    html_parts = ["""
    <div class="card">
        <h2>Evaluation Results</h2>
    """]

    for iteration in iterations:
        html_parts.append(generate_iteration_section(iteration))

    html_parts.append("</div>")

    return ''.join(html_parts)


def generate_fixes_section(data: Dict[str, Any]) -> str:
    """Generate fixes applied section."""
    fixes = data.get("fixes", [])

    if not fixes:
        return ""

    html_parts = ["""
    <div class="card">
        <h2>Fixes Applied</h2>
    """]

    for fix in fixes:
        iteration = fix.get("iteration", 1)
        changes = fix.get("changes", [])

        html_parts.append(f"""
        <h3>Iteration {iteration}</h3>
        """)

        for change in changes:
            section = escape(change.get("section", ""))
            action = change.get("action", "edit")
            description = escape(change.get("description", ""))

            html_parts.append(f"""
            <div class="fix-item">
                <div class="fix-section">{section}</div>
                <span class="fix-action {action}">{action}</span>
                <div class="fix-description">{description}</div>
            </div>
            """)

    html_parts.append("</div>")

    return ''.join(html_parts)


def generate_skill_section(data: Dict[str, Any], multi_skill: bool = False) -> str:
    """Generate complete section for a single skill."""
    skill_name = escape(data.get("skill_name", "Unknown"))
    skill_id = skill_name.lower().replace(" ", "-")
    summary = data.get("summary", {})
    grade = escape(summary.get("grade", "N/A"))
    grade_color = get_grade_color(grade)

    section_open = f'<section id="{skill_id}" class="skill-section">' if multi_skill else '<div class="skill-section">'
    section_close = '</section>' if multi_skill else '</div>'

    header_html = ""
    if multi_skill:
        header_html = f"""
        <h2 style="font-size: 1.75rem; margin-top: 0;">
            {skill_name}
            <span class="grade-badge" style="background-color: {grade_color};">Grade: {grade}</span>
        </h2>
        """

    return f"""
    {section_open}
        {header_html}
        {generate_summary_stats(data)}
        {generate_checklist_table(data)}
        {generate_eval_section(data)}
        {generate_fixes_section(data)}
    {section_close}
    """


def generate_html_report_single(data: Dict[str, Any]) -> str:
    """Generate complete HTML report for single skill."""
    html_parts = [
        "<!DOCTYPE html>",
        "<html lang=\"en\">",
        "<head>",
        "    <meta charset=\"UTF-8\">",
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
        f"    <title>Skill Audit Report - {escape(data.get('skill_name', 'Unknown'))}</title>",
        generate_css(multi_skill=False),
        "</head>",
        "<body>",
        "    <div class=\"container\">",
        generate_header_single(data),
        generate_skill_section(data, multi_skill=False),
        "        <footer>",
        "            <p>Generated by GMM Nexus Skill Audit Plugin</p>",
        "        </footer>",
        "    </div>",
        "</body>",
        "</html>",
    ]

    return '\n'.join(html_parts)


def generate_html_report_multi(skills: List[Dict[str, Any]]) -> str:
    """Generate complete HTML report for multiple skills."""
    # Generate all skill sections
    skill_sections = []
    for skill in skills:
        skill_sections.append(generate_skill_section(skill, multi_skill=True))

    html_parts = [
        "<!DOCTYPE html>",
        "<html lang=\"en\">",
        "<head>",
        "    <meta charset=\"UTF-8\">",
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
        "    <title>Skill Audit Report</title>",
        generate_css(multi_skill=True),
        "</head>",
        "<body>",
        "    <div class=\"container\">",
        generate_header_multi(skills),
        generate_summary_table(skills),
        "        <div class=\"layout-with-sidebar\">",
        generate_sidebar(skills),
        "            <main class=\"main-content\">",
        '\n'.join(skill_sections),
        "            </main>",
        "        </div>",
        "        <footer>",
        "            <p>Generated by GMM Nexus Skill Audit Plugin</p>",
        "        </footer>",
        "    </div>",
        "</body>",
        "</html>",
    ]

    return '\n'.join(html_parts)


def read_json_input(input_path: str) -> Dict[str, Any] | List[Dict[str, Any]]:
    """Read JSON input from file or stdin."""
    if input_path == "-":
        # Read from stdin
        content = sys.stdin.read()
    else:
        # Read from file
        file_path = Path(input_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        content = file_path.read_text(encoding="utf-8")

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON input: {e}")


def write_output(html: str, output_path: Optional[str]) -> None:
    """Write HTML output to file or stdout."""
    if output_path:
        # Write to file
        file_path = Path(output_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(html, encoding="utf-8")
        print(f"Report generated: {file_path}", file=sys.stderr)
    else:
        # Write to stdout
        print(html)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate HTML report from skill audit eval JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate-report.py audit-output.json
  python generate-report.py audit-output.json -o report.html
  cat audit-output.json | python generate-report.py -

Input formats:
  Single skill: {skill_name: ..., summary: ..., ...}
  Multiple skills: [{skill1}, {skill2}, ...]
        """,
    )

    parser.add_argument(
        "input",
        help="Input JSON file path (use '-' for stdin)",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output HTML file path (default: stdout)",
        default=None,
    )

    args = parser.parse_args()

    try:
        # Read input
        data = read_json_input(args.input)

        # Auto-detect input format and generate appropriate report
        if isinstance(data, list):
            # Multi-skill report (array input)
            if not data:
                raise ValueError("Input array is empty")
            html = generate_html_report_multi(data)
        elif isinstance(data, dict):
            # Single-skill report (object input)
            html = generate_html_report_single(data)
        else:
            raise ValueError(f"Invalid input format: expected object or array, got {type(data)}")

        # Write output
        write_output(html, args.output)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
