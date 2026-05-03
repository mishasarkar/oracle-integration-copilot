# Oracle Integration Copilot — Demo Script
**Target: 8–10 minutes | Tone: Confident, honest, enthusiastic**

---

## Opening — The Problem (1 min)

> "Let me start with the problem. When a large company wants to connect two of its systems — say, move new hire data from Workday into Oracle HCM — a consultant has to spend 2–4 hours just on the design document: finding the right API endpoints, figuring out field mappings, designing error handling, writing it all up before a line of code gets written.
>
> I built a tool that produces that first draft in under 2 minutes. You type what you need in plain English. It does the rest.
>
> But what I actually want to show you is *how* I built it — because I think that's what matters for this role."

---

## Live Demo — Streamlit UI (2.5 min)

**Action:** Open [oracle-integration-copilot.streamlit.app](https://oracle-integration-copilot.streamlit.app)

> "This is live — anyone can use it right now. I'll run a real requirement."

**Type into the text box:**
```
Every night at 2am, pull new hires from Workday and create employee
records in Oracle HCM. Skip contractors. Send a Slack alert if any
record fails.
```

**While it loads, narrate the four steps:**
> "Four things are happening right now:
> - The AI reads that sentence and extracts the key facts — scheduled integration, Workday to Oracle HCM
> - It searches 11 Oracle reference documents I curated and pulls the 6 most relevant pages
> - Claude writes the full design using those docs plus 2 worked examples
> - A second AI pass — the critic — reads the design and asks: *what did we assume, what did we miss?*"

**When spec appears, point to:**
1. The Mermaid sequence diagram — *"auto-generated from the integration pattern"*
2. The field mapping table — *"real Oracle HCM field names from the documentation"*
3. The error handling section — *"it picked up the Slack alert from my requirement"*
4. **Assumptions + Open Questions** — *"this is the part I'm most proud of — this came from the second AI pass"*

---

## The Critic Pass — The Clever Bit (1 min)

> "I want to linger on the Assumptions section for a second because it's the design decision I'd defend in any engineering review.
>
> A single AI call is overconfident — when you ask it to produce a complete spec, it fills in the gaps with guesses rather than flagging them. So I added a second call with a completely different prompt: *'What is wrong or missing?'* That activates a different mode entirely.
>
> In practice it surfaces 3–5 things the first pass glossed over — things like 'we assumed the Oracle tenant URL, what is it actually?' That's the question a senior consultant would ask in a design review. The tool asks it *before* the meeting."

---

## The Codebase — 3 Artifacts (2.5 min)

**Action:** Open repo in VS Code or GitHub

**1. `copilot/schemas.py` — 30 sec**
> "Everything passes through two Pydantic models — `IntegrationIntent` and `IntegrationSpec`. They're the contract between every layer. The parser, retriever, designer, and renderer all speak the same language. I can change a prompt without touching the data shape."

**2. `copilot/prompts/` — 30 sec**
> "The prompts are plain text files, not strings buried in Python. A consultant who isn't a developer could open `designer.txt` and change how specs are structured. That's a real design decision, not an accident."

**3. `tests/` — 30 sec**
> "The parser retry logic is fully tested — first call returns bad JSON, the error gets appended to the second prompt, and it self-corrects. All mocked. No API key needed to run the suite. That matters for a CI pipeline."

**Bonus if time:** Show `data/oracle_docs/` — *"11 Oracle reference documents I hand-distilled from public documentation. This is the tool's textbook."*

---

## How I Built This — The Honest Bit (1 min)

> "I want to be upfront: I don't have 10 years of Oracle experience. I've been learning OIC through the documentation and through building this project.
>
> What I do have is the ability to use AI as a genuine development partner. Claude Code was open the whole time — helping me understand what Oracle's REST adapters actually do, reviewing my schema design, writing tests in parallel while I wrote code. The depth this project has is a product of that back-and-forth.
>
> I think that's what the JD is actually asking for — not someone who already knows everything about Oracle, but someone who can learn it fast and build production-quality work while doing it."

---

## Limitations — Shows Maturity (30 sec)

> "This produces a design draft, not production code. Real Oracle environments have hostnames, org codes, and field values that need to be confirmed before anything gets built.
>
> What I'd build next: a mode that posts the generated spec directly into OIC via its REST management API — closing the loop from design to artefact. That would make this a genuine accelerator, not just a documentation tool."

---

## Close

> "The repo is at [your GitHub link]. Happy to go deeper on any part — the retrieval query construction, the critic prompt, the test coverage, whatever's most interesting to you."

---

## Pre-Demo Checklist

- [ ] Streamlit app tab open and ready
- [ ] GitHub repo tab open (or VS Code with repo loaded)
- [ ] `schemas.py` tab pre-opened
- [ ] `copilot/prompts/designer.txt` tab pre-opened
- [ ] `tests/test_parser.py` tab pre-opened
- [ ] `data/oracle_docs/` folder visible
- [ ] `.env` configured with API key if doing a local CLI demo
