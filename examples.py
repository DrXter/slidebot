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
