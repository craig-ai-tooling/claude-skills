---
name: doc-writer
description: Generate long-form branded Spectro Cloud documents -- customer assessments, solution briefs, technical writeups, POC reports, and migration plans. Outputs Markdown with YAML frontmatter, brand-consistent formatting, and co-branding support.
---

# Spectro Cloud Document Writer

PDF route: none

Generate polished, long-form documents for Spectro Cloud customer engagements. Output is Markdown with YAML frontmatter suitable for Google Docs, static sites, or PDF conversion.

**Brand foundation:** READ the `spectrocloud-brand` skill for colors, logos, typography, messaging, and tone before generating any document. This skill defines structure and templates; `spectrocloud-brand` is the source of truth for visual identity and messaging.

## When to Use

- Customer Assessment -- evaluate a prospect's Kubernetes environment and recommend Palette
- Solution Brief -- concise value-focused document for a specific use case or vertical
- Technical Architecture -- detailed design for a proposed or active deployment
- POC Report -- document findings, results, and next steps from a proof of concept
- Migration Plan -- phased plan for moving workloads to Palette (often VMware exit)

## Output Format

Every document starts with YAML frontmatter for metadata, followed by Markdown body:

```yaml
---
title: "Document Title"
subtitle: "Optional Subtitle"
type: assessment | solution-brief | architecture | poc-report | migration-plan
customer: "Customer Name"
author: "Author Name, Spectro Cloud"
date: "YYYY-MM-DD"
version: "1.0"
classification: confidential | internal | public
---
```

### Formatting Conventions

- **Headings:** H1 for document title (one only), H2 for major sections, H3 for subsections
- **Tables:** Use Markdown tables for comparisons, timelines, and structured data
- **Callouts:** Use blockquotes with bold lead-in for emphasis:
  > **Key Finding:** Description of the finding or recommendation.
- **Quotes:** Customer or analyst quotes use standard blockquotes with attribution:
  > "Quote text here."
  > -- Name, Title, Company
- **Lists:** Bullet lists for qualitative points, numbered lists for sequential steps or ranked items
- **Bold:** For product names on first mention (e.g., **Palette**, **Palette VerteX**) and key terms
- **Horizontal rules:** `---` to separate major document sections (before appendices, boilerplate)

## Document Templates

### 1. Customer Assessment

Purpose: Evaluate current state, identify pain points, recommend Spectro Cloud solutions.

**Sections:**

1. **Executive Summary** -- 2-3 paragraphs. Current state, key findings, recommended path forward. Write this last but place it first.
2. **Current Environment** -- Infrastructure inventory: clusters, distributions, cloud providers, edge sites, VM estate. Use tables.
3. **Challenges and Pain Points** -- Map observed issues to the three pillars (Choice, Control, Scale). Reference specific operational friction.
4. **Recommended Solution** -- Which Palette products address each pain point. Include architecture-level overview.
5. **Value Projection** -- Expected outcomes with proof points from similar customers (reference `spectrocloud-brand` messaging for customer quotes and metrics).
6. **Proposed Engagement** -- Timeline, phases, success criteria. Use a phased table.
7. **Appendix: About Spectro Cloud** -- Standard boilerplate (see Boilerplate Sections below).

**Tone:** Consultative, not salesy. Acknowledge complexity before offering solutions.

### 2. Solution Brief

Purpose: Concise, use-case-focused document that maps a customer problem to Palette capabilities.

**Sections:**

1. **The Challenge** -- 1-2 paragraphs on the industry or use-case pain point. Use real tech terms.
2. **The Solution** -- How Palette addresses it. Reference specific features (Cluster Profiles, full-stack management, edge provisioning, VMO).
3. **Key Capabilities** -- 3-5 bullet points with bold lead-ins mapping to value pillars.
4. **Customer Proof Point** -- One relevant case study with quantified outcome.
5. **Architecture Overview** -- High-level description of how Palette fits into the target environment.
6. **Getting Started** -- Next steps: POC, demo, contact.

**Tone:** Direct and benefit-led. Every paragraph should answer "so what?" for the reader.

### 3. Technical Architecture

Purpose: Detailed design document for a proposed or active Palette deployment.

**Sections:**

1. **Overview** -- Deployment scope, goals, constraints.
2. **Architecture Design** -- Environment topology (cloud, data center, edge). Describe cluster layout, networking, storage, and security boundaries. Use tables for component inventory.
3. **Cluster Profile Design** -- Infrastructure profiles vs. add-on profiles. List packs, versions, and configuration rationale.
4. **Networking** -- Load balancing, ingress, service mesh, CNI selection.
5. **Storage** -- CSI drivers, persistence strategy, backup approach.
6. **Security and Governance** -- RBAC, OPA/Gatekeeper policies, secrets management, compliance requirements.
7. **Operations** -- Day-2 lifecycle: upgrades, scaling, monitoring, drift detection.
8. **Deployment Plan** -- Phased rollout with milestones.
9. **Risks and Mitigations** -- Table format: Risk | Impact | Likelihood | Mitigation.

**Tone:** Precise and technical. Assume the reader is a platform engineer or architect.

### 4. POC Report

Purpose: Document what was tested, what was learned, and what comes next.

**Sections:**

1. **Executive Summary** -- Scope, key results, recommendation (proceed / adjust / stop).
2. **POC Objectives** -- What was being evaluated, mapped to success criteria. Use a table: Objective | Success Criteria | Result | Status (Pass/Partial/Fail).
3. **Environment** -- Infrastructure used: cloud provider, node specs, networking, Palette tenant details.
4. **Test Scenarios** -- What was deployed and tested. For each scenario: description, steps taken, observations, result.
5. **Findings** -- Categorized: Strengths, Areas for Improvement, Blockers. Be honest about limitations encountered.
6. **Performance Data** -- If applicable: deployment times, resource utilization, upgrade durations. Use tables.
7. **Recommendations** -- Go/no-go with conditions. Proposed production architecture and next steps.
8. **Appendix: Detailed Logs** -- Reference any supporting data, screenshots, or configuration files.

**Tone:** Objective and evidence-based. Acknowledge issues candidly -- credibility matters more than spin.

### 5. Migration Plan

Purpose: Phased plan for moving workloads to Palette, often in the context of VMware exit or multi-cloud consolidation.

**Sections:**

1. **Executive Summary** -- Migration scope, timeline, expected outcomes.
2. **Current State** -- Existing infrastructure, workload inventory, dependencies. Use tables for workload categorization.
3. **Target State** -- Palette-managed architecture. Describe how VMs and containers coexist via Palette VMO where applicable.
4. **Migration Strategy** -- Approach: lift-and-shift, re-platform, or re-architect per workload category. Decision matrix table.
5. **Phase Plan** -- Phased timeline with:
   - Phase 0: Foundation (Palette deployment, cluster profiles, governance)
   - Phase 1: Pilot (non-critical workloads, validation)
   - Phase 2: Migration waves (grouped by dependency and risk)
   - Phase 3: Optimization (cost tuning, advanced Day-2 operations)
6. **Risk Management** -- Risk register table. Include rollback strategy for each phase.
7. **Success Criteria** -- Measurable KPIs: uptime, deployment velocity, cost reduction, cluster count.
8. **Resource Requirements** -- Team, tooling, Palette licensing, infrastructure.

**Tone:** Pragmatic and structured. Emphasize de-risking and phased validation.

## Tone and Voice Guidelines

Follow the `spectrocloud-brand` tone principles:

- **Mature enterprise** -- We are a technology scale-up, not a startup. No hype, no breathless excitement.
- **Platform-forward** -- Lead with Palette capabilities, not abstract promises.
- **Pain-then-solution** -- Name the operational pain (complexity, drift, vendor lock-in, manual toil) before introducing the solution.
- **Real tech terms** -- Say Kubernetes, clusters, bare metal, CNI, CSI, RBAC. The audience is technical.
- **Non-opinionated positioning** -- Palette gives customers choice. Never say "opinionated."
- **Consultative, not salesy** -- Especially in assessments and POC reports. Credibility comes from honesty about trade-offs.

### Co-Branding Approach

When writing for a specific customer:

1. **Lead with their context** -- Open sections with the customer's environment, goals, and terminology before introducing Spectro Cloud solutions.
2. **Mirror their language** -- If they say "platform engineering team," use that phrase, not "DevOps team."
3. **Map to their pain** -- Use the three pillars (Choice, Control, Scale) as a framework but express them in the customer's terms.
4. **Include their data** -- Reference their cluster counts, environments, team sizes, compliance requirements.
5. **Balance branding** -- The document should feel like a joint effort, not a Spectro Cloud sales pitch. Customer name appears in the title; Spectro Cloud appears in authorship and boilerplate.

## Boilerplate Sections

Include these at the end of every document, separated by a horizontal rule.

### About Spectro Cloud

Use this standard block (adapt length to document type -- full version for assessments and migration plans, shortened for solution briefs):

> Spectro Cloud delivers simplicity and control to organizations running Kubernetes at any scale. With its Palette management platform, Spectro Cloud empowers businesses to deploy, manage, and scale Kubernetes clusters effortlessly -- from edge to data center to cloud -- while maintaining the freedom to build their perfect stack. Designed for mission-critical environments, Palette combines the flexibility of non-opinionated design with enterprise-grade governance, security, and repeatability.
>
> Spectro Cloud is a leader and outperformer in GigaOm's 2024 Radars for Edge Kubernetes and Managed Kubernetes, a Gartner Cool Vendor, and an AWS Differentiated Partner.

### Contact

```
Spectro Cloud
spectrocloud.com
info@spectrocloud.com
```

### Confidentiality Notice

For documents classified as `confidential`:

> This document contains confidential and proprietary information of Spectro Cloud and [Customer Name]. It is intended solely for the use of the named recipient(s). Unauthorized distribution, copying, or disclosure is strictly prohibited.

### Copyright

```
© [Year] Spectro Cloud®. All rights reserved.
```

For confidential documents:

```
© [Year] Spectro Cloud® Confidential. All rights reserved.
```

## Generation Checklist

Before finalizing any document, verify:

- [ ] YAML frontmatter is complete with all required fields
- [ ] Executive summary is written last, placed first, and can stand alone
- [ ] Three pillars (Choice, Control, Scale) are referenced where relevant, not forced
- [ ] At least one customer proof point or quantified outcome is included
- [ ] Tables are used for structured data (not buried in prose)
- [ ] Product names are bolded on first mention
- [ ] Tone is consultative and technical, not marketing copy
- [ ] Boilerplate sections (About, Contact, Copyright) are present
- [ ] Confidentiality notice is included if classification is confidential
- [ ] No cartoons, emojis, or off-the-shelf illustration references
- [ ] No "opinionated" -- Palette is "non-opinionated"
- [ ] Customer context leads, Spectro Cloud solutions follow
