# Internal Announcement — Taleemabad Data Navigator v0.16

**Date:** 2026-04-16
**Audience:** Internal Taleemabad teams (product, data, engineering)
**Channels:** Email + MS Teams
**Screenshots:** Dashboard overview page, multi-region dataset table

---

## MS Teams Version

---

**Taleemabad Data Navigator v0.16 — All Regions. One Question. Governed Answers.**

Hi team,

We're excited to share that the **Taleemabad Data Navigator** is now live across all three program regions — and it's ready for your daily workflow.

**What is it?**
A governed data layer built into Claude Code. Ask a question in plain English — get the right number, every time. No SQL. No credentials. No guessing which table to use. Every query is audited, cost-controlled, and follows our governance rules automatically.

**What's covered?**

| Region | Datasets | Domains |
|--------|----------|---------|
| **ICT / Islamabad** | `tbproddb` | Teachers, Lesson Plans, Coaching (FICO), Training, ACR & Promotion Policy, Student Results |
| **Rawalpindi** | `RUMI_DB` + `TaleemHub_DB` | Teachers, AI Lesson Plans, Human & AI Coaching, Reading Assessments, ASER |
| **Moawin / Akhuwat** | `Muawin_Akhuwat_db` + `Zavia_db` | Teachers, AI Lesson Plans, AI Coaching, Student Assessments, Attendance, Schools |

5 active datasets. 9 tools. 32 governance rule files covering every KPI domain.

*[Screenshot 1: Dashboard — Project Status Overview]*

*[Screenshot 2: Multi-Region Dataset Table]*

---

**How to Install (5 minutes)**

Prerequisites: [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) + your work email (`@taleemabad.com`, `@niete.edu.pk`, or `@niete.pk`)

```
Step 1: claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
Step 2: claude plugin install taleemabad-data@Orenda-Project
Step 3: Open Claude Code → type /taleemabad-setup → enter your work email
Step 4: Restart Claude Code (Ctrl+R) → type /mcp → confirm "taleemabad-data · connected"
```

No Python. No credentials file. No local dependencies. Works on Windows, macOS, Linux, and iOS.

---

**How to Update**

Rules and agents **auto-update on every session start** — no action needed.

To manually force a plugin update:
```
claude plugin update taleemabad-data@Orenda-Project
```

---

**Try These**

- *"How many active PRIMARY teachers are in ICT/Islamabad?"*
- *"Show me FICO Section B scores for ICT schools this month"*
- *"How many teachers passed Level 1 training?"*
- *"Show me AI coaching session counts for Moawin/Akhuwat"*
- *"What's the LP adoption rate for Rawalpindi this week?"*

---

**Need help?** Reach out to the data team for access issues or questions. If you see "Setup required" after install, just run `/taleemabad-setup` again.

---

## Email Version

---

**Subject:** Taleemabad Data Navigator v0.16 — All Regions Live. Your Data, One Question Away.

Hi team,

I'm pleased to share that the **Taleemabad Data Navigator** (v0.16) is now live and covering all three program regions. This is a milestone we've been building toward — a single, governed data layer that gives every team member direct access to our program data through natural language.

### What This Means for You

Instead of writing SQL, requesting exports, or guessing which table holds the number you need — you ask a question in plain English inside Claude Code. The system reads our governance rules, generates the correct query, runs it against BigQuery with cost guardrails, and returns the answer with a full audit trail.

Every query is:
- **Governed** — follows our 32 rule files across all KPI domains
- **Audited** — immutable log of who asked what, when, and at what cost
- **Cost-controlled** — dry-run estimates before execution, hard byte limits enforced
- **Consistent** — the same question always produces the same governed answer

### What's Covered

| Region | Datasets | Key Domains |
|--------|----------|-------------|
| **ICT / Islamabad** | `tbproddb` | Teachers, Lesson Plans, Coaching (FICO B/C/D), Training Levels, ACR & Promotion Policy, Student Results |
| **Rawalpindi** | `RUMI_DB` + `TaleemHub_DB` | Teachers, AI Lesson Plans, Human Mentoring, AI Coaching, Reading Assessments (WCPM), ASER |
| **Moawin / Akhuwat** | `Muawin_Akhuwat_db` + `Zavia_db` | Teachers, AI Lesson Plans, AI Coaching (with Lesson Fidelity), School Assessments, Teacher & Student Attendance, School Profiles |

That's **5 active datasets**, **9 tools**, and **32 governance rule files** — all accessible through a single interface.

*[Screenshot 1: Dashboard — Project Status Overview]*

*[Screenshot 2: Multi-Region Dataset Table]*

### Installation (5 Minutes)

**Prerequisites:** [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) installed + your work email (`@taleemabad.com`, `@niete.edu.pk`, or `@niete.pk`)

**Step 1** — Register the marketplace source:
```
claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
```

**Step 2** — Install the plugin:
```
claude plugin install taleemabad-data@Orenda-Project
```

**Step 3** — Run setup (one time):
Open Claude Code in any project directory and type:
```
/taleemabad-setup
```
Enter your work email when prompted. This configures audit logging and syncs governance rules.

**Step 4** — Restart and verify:
Restart Claude Code (`Ctrl+R`), then type `/mcp`. You should see:
```
taleemabad-data · connected
```

That's it. No Python, no credentials file, no local dependencies. Works on **Windows, macOS, Linux, and iOS**.

### Staying Updated

**Automatic:** Rules and agents auto-update on every Claude Code session start. No action needed.

**Manual** (if you want to force an update):
```
claude plugin update taleemabad-data@Orenda-Project
```

### Try It

Once installed, try asking:

- *"How many active PRIMARY teachers are in ICT/Islamabad?"*
- *"Show me FICO Section B scores for ICT schools this month"*
- *"How many teachers passed Level 1 training?"*
- *"Show me AI coaching session counts for Moawin/Akhuwat"*
- *"What's the LP adoption rate for Rawalpindi this week?"*
- *"What are the average ACR KPI scores by school for ICT?"*

### Troubleshooting

| Issue | Fix |
|-------|-----|
| Plugin not found after install | Make sure you ran both `marketplace add` and `plugin install` commands |
| `/taleemabad-setup` not recognized | Restart Claude Code after installing the plugin |
| MCP shows "Setup required" | Run `/taleemabad-setup` and enter your work email |
| MCP shows "disconnected" | Check internet connection; server may be restarting — wait a minute |
| "Unauthorized domain" error | You must use a `@taleemabad.com`, `@niete.edu.pk`, or `@niete.pk` email |

### Need Help?

Reach out to the data team for access issues, questions, or feature requests.

---

*Taleemabad Data Navigator v0.16.4 — Built by the Data Team*
