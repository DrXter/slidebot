"""Worked examples shown to the model (few-shot). Generic content, written to the standard we want.

Each example pairs a short source excerpt with the slide JSON a strong consultant would write.
Small local models copy tone, length and structure from examples far better than from rules alone.
"""

EXAMPLES = {
    "columns": {
        "source": """Phase 1 Foundation (Nov-Dec): assess CIS Level 1 applicability across the estate, develop
technology-specific hardening standards, define exception and compensating-control criteria, establish a
compliance scoring model. Milestone: CIS standards and technology baselines approved.
Phase 2 Intelligence (Dec-Jan): analyse Nessus findings, identify recurring control failures, create technology
heatmaps, rationalise findings into remediation work packages. Milestone: enterprise remediation backlog established.
Phase 3 Enterprise hardening (Jan-Jun): GPO optimisation, Intune policy updates, AD hardening, Windows and Linux
baselines, gold image refresh, firewall baselines, Azure policy. Milestone: core infrastructure hardening completed.
Phase 4 Continuous assurance (May-Jun): drift monitoring, compliance dashboards, quarterly reviews, standards refresh.
Milestone: configuration assurance operating model established.""",
        "slide": {
            "layout": "columns",
            "title": "Phase-by-phase approach to configuration assurance",
            "subtitle": "Each phase builds on the last, from standards to continuous assurance",
            "sequential": True,
            "columns": [
                {"header": "Foundation", "timing": "Nov to Dec", "icon": "check", "tagline": "Standards and remediation-ready baselines",
                 "items_label": "Key activities",
                 "items": ["Assess CIS Level 1 applicability across the estate", "Build technology-specific hardening standards",
                           "Define exception and compensating-control criteria", "Set a common compliance scoring model"],
                 "panel_label": "Key deliverables", "panel_items": ["Hardening standards library", "Compliance scoring framework", "Technology baselines"],
                 "outcome": "Remediation planning starts before findings analysis ends",
                 "dark_label": "Milestone 1", "dark_text": "CIS standards and baselines approved"},
                {"header": "Intelligence", "timing": "Dec to Jan", "icon": "search", "tagline": "Thousands of findings into a few work packages",
                 "items_label": "Key activities",
                 "items": ["Analyse Nessus findings", "Identify recurring control failures", "Create technology heatmaps",
                           "Rationalise findings into remediation work packages"],
                 "panel_label": "Key deliverables", "panel_items": ["Configuration risk heatmaps", "Root cause analysis", "Remediation work packages"],
                 "outcome": "Engineering teams receive a short, prioritised backlog",
                 "dark_label": "Milestone 2", "dark_text": "Enterprise remediation backlog established"},
                {"header": "Enterprise hardening", "timing": "Jan to Jun", "icon": "shield", "tagline": "Fix at estate level, not asset by asset",
                 "items_label": "Key activities",
                 "items": ["Policy: GPO optimisation and Intune updates", "Platform: AD, Windows and Linux baselines, gold images",
                           "Network and cloud: firewall baselines, Azure Policy"],
                 "panel_label": "Key deliverables", "panel_items": ["Risk reduction dashboard", "Closure validation evidence"],
                 "outcome": "Thousands of findings closed through central controls",
                 "dark_label": "Milestone 3", "dark_text": "Core infrastructure hardening completed"},
                {"header": "Continuous assurance", "timing": "May to Jun", "icon": "refresh", "tagline": "Compliance that sustains itself",
                 "items_label": "Key activities",
                 "items": ["Drift monitoring", "Compliance dashboards", "Quarterly review process", "Standards refresh cycle"],
                 "panel_label": "Key deliverables", "panel_items": ["Continuous compliance reporting", "Technology risk scorecards"],
                 "outcome": "Hardening gains protected from configuration drift",
                 "dark_label": "Milestone 4", "dark_text": "Assurance operating model established"},
            ],
            "banner_left_label": "Business outcome",
            "banner_left": "Each phase ends with a clear milestone, so progress is visible: standards, backlog, hardening, then assurance.",
            "banner_right_label": "Deloitte differentiator",
            "banner_right": "Thousands of findings become a few technology-led work packages delivered through central controls.",
        },
    },
    "grid": {
        "source": """Why we can accelerate: standards are developed before remediation starts, so planning begins the day
results arrive. Findings are rationalised into technology work packages before engineering is engaged. Remediation is
estate-based (GPOs, Intune, gold images, Azure Policy) rather than asset by asset. We already know the environment from
the baseline work, configuration reviews and ownership mapping.""",
        "slide": {
            "layout": "grid",
            "title": "Why Deloitte can accelerate remediation",
            "subtitle": "Four reasons remediation starts faster and finishes sooner",
            "cards": [
                {"icon": "check", "title": "Standards ready before remediation", "text": "Hardening standards are built first, so planning starts the day assessment results arrive."},
                {"icon": "network", "title": "Findings rationalised first", "text": "Engineering teams receive a few technology work packages, not thousands of individual findings."},
                {"icon": "layers", "title": "Estate-based remediation", "text": "Fixes land through GPOs, Intune, gold images and Azure Policy instead of asset-by-asset changes."},
                {"icon": "history", "title": "Existing knowledge of the environment", "text": "Builds on baseline work, configuration reviews and ownership mapping, cutting onboarding effort."},
            ],
            "banner": "Standards and intelligence from the early phases cut planning effort and make delivery predictable.",
        },
    },
    "timeline": {
        "source": """Foundation Nov-Dec. Findings intelligence Dec-Jan. Exception governance Nov-Jun. Policy hardening Jan-Mar.
Platform hardening Feb-May. Continuous assurance May-Jun. Milestones: standards approved (Dec), backlog established (Jan),
core hardening complete (Jun). Protection: central controls first, parallel exception governance, monthly reviews.""",
        "slide": {
            "layout": "timeline",
            "title": "Accelerated delivery timeline",
            "subtitle": "Standards, intelligence, enterprise hardening and continuous assurance from November to June",
            "periods": ["Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "rows": [
                {"name": "Foundation", "icon": "check", "start": 0, "end": 1},
                {"name": "Findings intelligence", "icon": "search", "start": 1, "end": 2},
                {"name": "Exception governance", "icon": "user-shield", "start": 0, "end": 7},
                {"name": "Policy hardening", "icon": "executive", "start": 2, "end": 4},
                {"name": "Platform hardening", "icon": "layers", "start": 3, "end": 6},
                {"name": "Continuous assurance", "icon": "refresh", "start": 6, "end": 7},
            ],
            "milestones": [
                {"label": "Standards approved", "period": 1},
                {"label": "Remediation backlog established", "period": 2},
                {"label": "Core hardening complete", "period": 7},
            ],
            "side_boxes": [
                {"title": "Timeline protection", "items": ["Central controls before asset-level fixes", "Exception governance runs in parallel", "Monthly dependency reviews"]},
            ],
            "outcome": "Standards by December, a backlog by January, and core infrastructure hardened by June.",
        },
    },
    "cover": {
        "source": "Proposal for Example Client on a configuration assurance and remediation programme, November 2026.",
        "slide": {"layout": "cover", "kicker": "Prepared for Example Client", "title": "Configuration Assurance Programme",
                  "subtitle": "From configuration findings to measurable cyber risk reduction",
                  "date_line": "Proposal for discussion, November 2026"},
    },
}

EXAMPLES.update({
    "flow": {
        "source": """Every work package follows the same path: prioritise by risk reduction versus effort; select a central lever
(GPO, Intune, gold image, golden config, IaC, Azure Policy) before any asset-level fix; pilot on a test group; approve and roll
out through change management in the tower's change window; revalidate through reassessment; close with evidence on the risk
reduction dashboard. Findings still open go back for another lever. Constraints found in the pilot go to exception governance.""",
        "slide": {
            "layout": "flow", "title": "How remediation flows end to end",
            "subtitle": "Every work package follows the same controlled path",
            "steps": [
                {"icon": "inbox", "title": "Prioritised work package", "text": "Ranked by risk reduction versus implementation effort", "label": "Owner: programme team"},
                {"icon": "layers", "title": "Select central lever", "text": "GPO, Intune, gold image, golden config, IaC or Azure Policy first", "label": "Owner: tower lead"},
                {"icon": "search", "title": "Pilot and test", "text": "Apply to a pilot group and check compatibility", "label": "Owner: tower lead"},
                {"icon": "clock", "title": "Approve and roll out", "text": "Through change management, in the tower's change window", "label": "Owner: tower lead"},
                {"icon": "shield", "title": "Revalidate", "text": "Reassessment confirms the control is applied estate-wide", "label": "Owner: programme team"},
                {"icon": "check", "title": "Close with evidence", "text": "Evidence logged; progress shown on the risk reduction dashboard", "label": "Reported monthly"},
            ],
            "loop_note": "Findings still open go back for another lever", "loop_from": 5, "loop_to": 2,
            "branch_from": 3, "branch_label": "Constraint found", "branch_text": "Exception governance: a time-bound exception with an owner and review date",
            "principles": ["Risk-ranked sequencing", "Central lever before asset fix", "Tested before rollout", "Evidence-based closure"],
            "banner": "One repeatable path: fixed centrally, proven by reassessment, or governed as an exception.",
        },
    },
    "stack": {
        "source": """Clients already hold SOC 2: security and access controls, privacy, change management, incident management,
operational governance. AI adds new risks traditional frameworks do not test: hallucinations, prompt injection, unsafe autonomous
actions, data leakage, adversarial manipulation, harmful outputs. The joint offer adds AI governance, AI risk management,
independent AI assurance, adversarial testing, quarterly validation and board reporting. SOC 2 validates the organisation and its
controls; the AI standard validates AI systems and agent behaviour. The question is now: can we trust your AI?""",
        "slide": {
            "layout": "stack", "title": "Trusted AI starts where SOC 2 ends",
            "subtitle": "SOC 2 proves the environment is secure; stakeholders now ask whether the AI can be trusted",
            "layers": [
                {"kicker": "What clients have today", "title": "SOC 2 foundation", "icon": "shield", "dashed": False,
                 "chips": ["Security and access", "Privacy", "Change management", "Incident management", "Operational governance"]},
                {"kicker": "Not tested by SOC 2", "title": "The AI assurance gap", "icon": "warning", "dashed": True,
                 "chips": ["Hallucinations", "Prompt injection", "Unsafe autonomous actions", "Data leakage", "Adversarial manipulation", "Harmful outputs"]},
                {"kicker": "What we add", "title": "AI trust layer", "icon": "robot", "dashed": False,
                 "chips": ["AI governance", "AI risk management", "Independent AI assurance", "Adversarial testing", "Quarterly validation", "Board reporting"]},
            ],
            "side_title": "What each one proves", "side_left_label": "SOC 2", "side_right_label": "AI standard",
            "side_pairs": [["The organisation and its controls", "AI systems and agent behaviour"], ["Security and privacy", "AI trust and safety"], ["Operational resilience", "AI reliability"]],
            "callout": "Can we trust your AI?",
            "banner": "Move from 'our systems are secure' to 'our AI can be trusted'.",
        },
    },
    "comparison": {
        "source": "Today remediation is asset by asset, findings arrive in thousands, exceptions are informal and assessments are periodic. With the programme: estate-wide fixes through central controls, a few work packages, a governed exception register, continuous monitoring.",
        "slide": {
            "layout": "comparison", "title": "From periodic findings to continuous assurance",
            "subtitle": "What changes for engineering teams and risk owners",
            "left_label": "Today", "right_label": "With the programme", "left_icon": "document", "right_icon": "refresh",
            "rows": [{"before": "Asset-by-asset remediation", "after": "Estate-wide fixes through central controls"},
                     {"before": "Thousands of individual findings", "after": "A few prioritised work packages"},
                     {"before": "Informal exceptions", "after": "Governed, time-bound exception register"},
                     {"before": "Periodic assessments", "after": "Continuous compliance monitoring"}],
            "highlight_title": "Why it matters",
            "highlight_text": "Engineering effort goes into a small number of high-impact changes, and residual risk is visible to leadership.",
            "banner": "Less effort for technology teams, more evidence for risk owners.",
        },
    },
})

EXAMPLES.update({
    "hub": {
        "source": "Four service areas: assess (readiness, AI inventory, control mapping, gap assessment); design (governance framework, risk taxonomy, policies); implement (technical controls, monitoring, human oversight, guardrails); validate (audit readiness, evidence, control testing, certification support). Standard covers six domains: security, data and privacy, reliability, safety, accountability, societal impact; 50+ requirements, 130+ controls, quarterly technical evaluations.",
        "slide": {
            "layout": "hub", "title": "How we help clients achieve AI assurance",
            "subtitle": "End-to-end enablement around a single trust outcome", "centre": "Independent AI assurance",
            "spokes": [
                {"icon": "search", "title": "Assess", "items": ["AI readiness and inventory", "Control mapping", "Gap assessment"]},
                {"icon": "diagram", "title": "Design", "items": ["Governance framework", "AI risk taxonomy", "Policies and procedures"]},
                {"icon": "layers", "title": "Implement", "items": ["Technical controls", "Monitoring and oversight", "AI guardrails"]},
                {"icon": "user-check", "title": "Validate", "items": ["Audit readiness and evidence", "Control testing", "Certification support"]},
            ],
            "panel_title": "Standard coverage",
            "panel_tiles": [["shield", "Security"], ["database", "Data and privacy"], ["refresh", "Reliability"], ["user-shield", "Safety"], ["check", "Accountability"], ["team", "Societal impact"]],
            "panel_stats": [{"value": "50+", "label": "requirements"}, {"value": "130+", "label": "controls"}, {"value": "6", "label": "trust domains"}],
            "panel_note": "Six trust domains, independently tested.",
            "banner": "One assurance journey from readiness to certification.",
        },
    },
    "quad": {
        "source": "Deloitte designs, implements and operationalises AI governance. The independent standard validates that AI operates responsibly, securely and reliably. Together: build stakeholder trust, accelerate AI adoption, differentiate in the market, strengthen AI governance.",
        "slide": {
            "layout": "quad", "title": "Accelerating trusted AI adoption", "subtitle": "Business trust and adoption, not just another certification",
            "block_a_title": "Deloitte", "block_a_text": "Designs, implements and operationalises AI governance and controls",
            "block_b_title": "Independent standard", "block_b_text": "Validates that AI operates responsibly, securely and reliably",
            "centre": "Trusted AI at scale",
            "cards": [
                {"icon": "team", "title": "Build stakeholder trust", "text": "Show responsible AI practices to customers, boards and regulators."},
                {"icon": "robot", "title": "Accelerate AI adoption", "text": "Deploy AI with greater confidence and less risk."},
                {"icon": "shield", "title": "Differentiate in the market", "text": "Independent assurance that eases procurement reviews."},
                {"icon": "user-shield", "title": "Strengthen AI governance", "text": "Oversight and risk management that scale with every use case."},
            ],
            "tagline": "Trust is the new currency of AI.",
        },
    },
})
