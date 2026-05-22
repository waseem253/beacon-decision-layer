"""Sample knowledge corpus for a consulting firm — Meridian Consulting Group.

This stands in for the multiple internal sources a real deployment would index
(document stores, project systems, client databases, deliverable archives).
The shape — a flat list of source-tagged documents — is what the retriever
indexes, so wiring real connectors later means feeding this same structure
from live systems instead of from this file.
"""

from __future__ import annotations

from dataclasses import dataclass, field

FIRM = "Meridian Consulting Group"

# The logical sources the knowledge layer federates over.
SOURCES: dict[str, dict[str, str]] = {
    "project-records": {
        "name": "Project Records",
        "description": "Engagement records — scope, status, team, decisions, outcomes.",
    },
    "methodology": {
        "name": "Methodology Playbooks",
        "description": "Internal frameworks and how-to guidance for delivery.",
    },
    "client-kb": {
        "name": "Client Knowledge Base",
        "description": "Per-client context — stakeholders, history, preferences.",
    },
    "deliverables": {
        "name": "Past Deliverables",
        "description": "Summaries of completed work products and their findings.",
    },
}


@dataclass(frozen=True)
class Document:
    id: str
    source: str
    title: str
    date: str
    text: str
    tags: tuple[str, ...] = field(default_factory=tuple)

    @property
    def source_name(self) -> str:
        return SOURCES.get(self.source, {}).get("name", self.source)


_RAW: list[dict] = [
    # -- Project Records ---------------------------------------------------
    {
        "id": "PR-101",
        "source": "project-records",
        "title": "Engagement: Atterly Retail — Supply Chain Optimization",
        "date": "2026-01-14",
        "tags": ["atterly-retail", "supply-chain", "active"],
        "text": (
            "Active engagement with Atterly Retail to redesign their regional "
            "distribution network. Scope covers warehouse consolidation, carrier "
            "renegotiation and a demand-forecasting pilot. The team is four "
            "consultants led by engagement manager Priya Anand. Status: in delivery, "
            "week 7 of 14. Key decision logged in week 5: defer the warehouse "
            "consolidation to phase two because lease break costs exceeded the "
            "first-year savings. The client sponsor is the COO, who wants weekly "
            "progress against a hard March board deadline."
        ),
    },
    {
        "id": "PR-102",
        "source": "project-records",
        "title": "Engagement: Northwind Bank — Operating Model Redesign",
        "date": "2025-11-03",
        "tags": ["northwind-bank", "operating-model", "closed"],
        "text": (
            "Completed engagement redesigning Northwind Bank's retail operating "
            "model across 60 branches. Scope included role rationalisation, a new "
            "service tiering model and a branch-to-digital migration plan. Closed "
            "in February 2026. Outcome: the client adopted 80 percent of the "
            "recommendations; the branch-closure recommendation was held back by "
            "the board for regulatory-relations reasons. Engagement manager was "
            "Daniel Cho. A follow-on phase on digital channel enablement is under "
            "discussion for Q3."
        ),
    },
    {
        "id": "PR-103",
        "source": "project-records",
        "title": "Engagement: Halcyon Health — Cost Base Review",
        "date": "2026-03-09",
        "tags": ["halcyon-health", "cost-reduction", "active"],
        "text": (
            "Active cost-base review for Halcyon Health, a regional hospital "
            "group. Scope is procurement, agency-staffing spend and back-office "
            "shared services. The team is three consultants led by Priya Anand, "
            "who is therefore split across Atterly and Halcyon — a known capacity "
            "risk flagged at the last portfolio review. Status: week 3 of 10. "
            "Early finding: agency-staffing spend is 22 percent above peer "
            "benchmark and is the single largest savings lever."
        ),
    },
    {
        "id": "PR-104",
        "source": "project-records",
        "title": "Engagement: Vance Manufacturing — Pricing Strategy",
        "date": "2026-02-20",
        "tags": ["vance-manufacturing", "pricing", "active"],
        "text": (
            "Active pricing-strategy engagement with Vance Manufacturing. Scope "
            "covers value-based pricing for their industrial components line and a "
            "discount-governance overhaul. Engagement manager is Daniel Cho. "
            "Status: week 5 of 8. Key decision: the team recommended retiring "
            "volume-tier discounting in favour of value-based pricing, which the "
            "client's sales leadership is resisting. Escalation to the client CEO "
            "is planned if alignment is not reached by week 6."
        ),
    },
    {
        "id": "PR-105",
        "source": "project-records",
        "title": "Portfolio Review — Q1 2026 Capacity & Risk Notes",
        "date": "2026-03-31",
        "tags": ["portfolio", "capacity", "risk"],
        "text": (
            "Quarterly portfolio review notes. Four engagements are active: "
            "Atterly Retail, Halcyon Health, Vance Manufacturing and a small "
            "advisory retainer. The principal capacity risk is Priya Anand being "
            "staffed on two engagements at once. Recommendation from the review: "
            "do not start any new engagement before the Atterly delivery ends in "
            "April unless a fifth engagement manager is brought in. Utilisation "
            "across the consulting team is running at 91 percent."
        ),
    },
    # -- Methodology Playbooks --------------------------------------------
    {
        "id": "MP-201",
        "source": "methodology",
        "title": "Discovery & Scoping Playbook",
        "date": "2025-09-01",
        "tags": ["discovery", "scoping", "playbook"],
        "text": (
            "Meridian's standard discovery runs two to three weeks before any "
            "fixed scope is agreed. It has three steps: stakeholder interviews "
            "(eight to twelve), a data request covering the last two years, and a "
            "hypothesis workshop. The deliverable is a scoping memo with a problem "
            "statement, a value hypothesis and three to five workstreams. Rule of "
            "thumb: never commit a fixed price before discovery closes, because "
            "scope risk is highest when the problem is still vague."
        ),
    },
    {
        "id": "MP-202",
        "source": "methodology",
        "title": "Engagement Pricing Model",
        "date": "2025-09-01",
        "tags": ["pricing", "commercial", "playbook"],
        "text": (
            "Meridian prices engagements three ways. Fixed-price is used only "
            "after discovery, with a 15 percent contingency built in. "
            "Time-and-materials is used for open-ended advisory work. "
            "Outcome-linked pricing ties a portion of the fee to a measured "
            "result and is used only when the client controls the levers and the "
            "baseline is agreed in writing. Standard blended day rate is in the "
            "2,400 to 3,200 range depending on engagement-manager seniority."
        ),
    },
    {
        "id": "MP-203",
        "source": "methodology",
        "title": "Delivery Governance Framework",
        "date": "2025-10-12",
        "tags": ["governance", "delivery", "playbook"],
        "text": (
            "Every engagement over six weeks runs a weekly internal delivery "
            "review and a fortnightly client steering meeting. A RAID log "
            "(risks, assumptions, issues, decisions) is mandatory and is the "
            "single source of truth for engagement decisions. Any decision that "
            "changes scope, timeline or fee must be logged and countersigned by "
            "the engagement manager and the client sponsor. Engagements that miss "
            "two consecutive weekly reviews are escalated to the partner group."
        ),
    },
    {
        "id": "MP-204",
        "source": "methodology",
        "title": "Stakeholder Mapping Method",
        "date": "2025-10-12",
        "tags": ["stakeholder", "change", "playbook"],
        "text": (
            "Stakeholders are mapped on two axes: influence over the decision and "
            "exposure to the change. High-influence, high-exposure stakeholders "
            "get a named relationship owner on the Meridian team and a weekly "
            "touchpoint. The method exists to prevent the most common failure "
            "mode on operating-model work: a recommendation that is analytically "
            "correct but dies because a powerful stakeholder was not engaged "
            "early. Map at discovery and revisit at every steering meeting."
        ),
    },
    {
        "id": "MP-205",
        "source": "methodology",
        "title": "Recommendation Quality Bar",
        "date": "2025-11-20",
        "tags": ["recommendations", "quality", "playbook"],
        "text": (
            "A recommendation is only ready to present when it states the "
            "decision asked of the client, the evidence behind it, the options "
            "considered, the expected impact with a range, and the risks of "
            "acting and of not acting. Recommendations without a clear owner and "
            "a first action are not accepted into a steering pack. When evidence "
            "is thin the recommendation must say so explicitly rather than "
            "overstate confidence."
        ),
    },
    # -- Client Knowledge Base --------------------------------------------
    {
        "id": "CK-301",
        "source": "client-kb",
        "title": "Client Profile: Atterly Retail",
        "date": "2026-01-08",
        "tags": ["atterly-retail", "client-profile"],
        "text": (
            "Atterly Retail is a mid-market omnichannel retailer, roughly 140 "
            "stores. Meridian's relationship is two years old and this is the "
            "third engagement. The COO is the primary sponsor and is "
            "detail-oriented, expects data behind every claim, and dislikes "
            "surprises in steering meetings. The CFO is sceptical of consultants "
            "and must be shown hard numbers early. Preference: short written "
            "updates over long decks. Sensitivity: a previous consultancy "
            "over-promised on a forecasting project, so credibility is earned "
            "slowly here."
        ),
    },
    {
        "id": "CK-302",
        "source": "client-kb",
        "title": "Client Profile: Northwind Bank",
        "date": "2025-10-28",
        "tags": ["northwind-bank", "client-profile"],
        "text": (
            "Northwind Bank is a regional retail bank. Heavily regulated and "
            "board-cautious; any recommendation touching branches, jobs or "
            "customer access is reviewed for regulatory-relations impact before "
            "it goes to the board. The transformation director is Meridian's "
            "champion and is pro-change. Preference: recommendations staged so "
            "the board can approve them incrementally rather than as one large "
            "programme. History: the firm declined to recommend mass branch "
            "closures despite the analytics supporting it."
        ),
    },
    {
        "id": "CK-303",
        "source": "client-kb",
        "title": "Client Profile: Halcyon Health",
        "date": "2026-03-02",
        "tags": ["halcyon-health", "client-profile"],
        "text": (
            "Halcyon Health is a regional hospital group, public-sector adjacent "
            "and politically sensitive. This is the first Meridian engagement, so "
            "the relationship is new and unproven. The COO sponsors the work; the "
            "clinical leadership is wary of cost-cutting language and responds far "
            "better to framing around 'released capacity' than 'cuts'. "
            "Procurement and agency-staffing are safe to address; anything "
            "touching clinical headcount is politically radioactive and should be "
            "flagged before raising."
        ),
    },
    {
        "id": "CK-304",
        "source": "client-kb",
        "title": "Client Profile: Vance Manufacturing",
        "date": "2026-02-15",
        "tags": ["vance-manufacturing", "client-profile"],
        "text": (
            "Vance Manufacturing is a family-owned industrial-components maker. "
            "The CEO is the decision-maker and is data-driven but loyal to a "
            "long-tenured sales leadership team that is resistant to pricing "
            "change. Second Meridian engagement. Preference: the CEO wants the "
            "commercial case made directly to him, not filtered through the sales "
            "VP. Sensitivity: framing matters — 'discount discipline' lands "
            "better than 'removing discounts' with this audience."
        ),
    },
    # -- Past Deliverables -------------------------------------------------
    {
        "id": "DL-401",
        "source": "deliverables",
        "title": "Deliverable: Cost Reduction Analysis — Atterly Retail (2024)",
        "date": "2024-12-05",
        "tags": ["atterly-retail", "cost-reduction", "deliverable"],
        "text": (
            "This deliverable is from Meridian's first Atterly Retail "
            "engagement, completed in 2024. The analysis identified 6.8 million "
            "in annual cost-out across store labour scheduling, shrink reduction "
            "and head-office overhead. Realised savings after one year were 4.1 "
            "million — labour scheduling delivered, but shrink reduction "
            "underperformed because the loss-prevention technology was not "
            "funded. Lesson recorded: savings estimates should be split into "
            "'committed' and 'conditional on investment' so the client is not "
            "surprised."
        ),
    },
    {
        "id": "DL-402",
        "source": "deliverables",
        "title": "Deliverable: Operating Model Blueprint — Northwind Bank",
        "date": "2026-01-30",
        "tags": ["northwind-bank", "operating-model", "deliverable"],
        "text": (
            "The blueprint defined four service tiers, a revised branch role "
            "structure and a 24-month migration roadmap. It quantified a 12 to 16 "
            "percent cost-to-serve reduction. The branch-network section was "
            "delivered as a standalone annex so the board could consider it "
            "separately — a deliberate structuring choice given Northwind's "
            "regulatory sensitivity. This annex approach is now cited in the "
            "methodology as good practice for politically sensitive findings."
        ),
    },
    {
        "id": "DL-403",
        "source": "deliverables",
        "title": "Deliverable: Pricing Diagnostic — Vance Manufacturing",
        "date": "2026-03-12",
        "tags": ["vance-manufacturing", "pricing", "deliverable"],
        "text": (
            "The diagnostic showed Vance was leaving an estimated 9 to 11 percent "
            "of margin on the table through inconsistent, rep-by-rep discounting. "
            "It modelled three pricing options: tightened discount governance, "
            "value-based pricing, and a hybrid. The hybrid was recommended as the "
            "lowest-resistance path to most of the margin, specifically because "
            "the client knowledge base flagged sales-team resistance to a full "
            "value-based move."
        ),
    },
    {
        "id": "DL-404",
        "source": "deliverables",
        "title": "Deliverable: Shared Services Benchmark — Cross-Client",
        "date": "2025-08-19",
        "tags": ["shared-services", "benchmark", "deliverable"],
        "text": (
            "A cross-client benchmark of back-office shared services covering "
            "finance, HR and procurement operations. It established peer cost and "
            "headcount ratios that Meridian now reuses on cost engagements. The "
            "Halcyon Health cost review is using this benchmark as its reference "
            "for back-office shared services. The benchmark is refreshed annually; "
            "the next refresh is due in August 2026."
        ),
    },
]

DOCUMENTS: list[Document] = [Document(**raw) for raw in _RAW]


def documents() -> list[Document]:
    return list(DOCUMENTS)


def source_catalog() -> list[dict]:
    """Sources with their live document counts — used by the dashboard."""
    counts: dict[str, int] = {}
    for doc in DOCUMENTS:
        counts[doc.source] = counts.get(doc.source, 0) + 1
    return [
        {
            "id": sid,
            "name": meta["name"],
            "description": meta["description"],
            "document_count": counts.get(sid, 0),
        }
        for sid, meta in SOURCES.items()
    ]
