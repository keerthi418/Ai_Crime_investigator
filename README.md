# 🕵️ AI Crime Investigator

### Turning scattered crime information into connected investigative intelligence.

**AI Crime Investigator** is an AI-powered investigation-support system designed to transform unstructured crime information into a **connected case representation**.

Instead of treating a crime complaint, witness statement, evidence, suspect, location, and timeline as separate pieces of information, the system connects them and analyzes how they relate to one another.

The objective is not simply to predict *who is guilty*.

The objective is to help answer:

> **“What connections exist in this case, what investigation paths are possible, what evidence supports each hypothesis, and where are the inconsistencies?”**

---

## 🧩 The Core Idea

A real investigation can contain hundreds of small pieces of information.

```text
Complaint
   ↓
Witness Statement
   ↓
Suspect
   ↓
Location
   ↓
Evidence
   ↓
Timeline
   ↓
Events
```

Individually, these pieces may not reveal much.

But when they are connected:

```text
                 ┌──────────────┐
                 │   Witness    │
                 └──────┬───────┘
                        │
                     reports
                        │
                        ↓
┌──────────┐       ┌───────────┐       ┌──────────┐
│  Suspect │──────→│   Event   │←──────│ Evidence │
└────┬─────┘       └─────┬─────┘       └─────┬────┘
     │                   │                   │
     │                   ↓                   │
     │              ┌──────────┐             │
     └─────────────→│ Location │←────────────┘
                    └──────────┘
```

**AI Crime Investigator converts these connections into an investigation graph and uses AI reasoning to explore the case.**

---

# 🎯 What Makes It Different?

Most crime-related AI systems focus mainly on **crime prediction or classification**.

This project focuses on something different:

### 🔎 Investigation Reasoning

The system combines several AI approaches to support the investigation process:

```text
          CRIME INFORMATION
                  │
                  ▼
         ┌─────────────────┐
         │  NLP PROCESSING │
         └────────┬────────┘
                  ▼
        Entity & Relationship
             Extraction
                  │
                  ▼
         ┌─────────────────┐
         │   CASE GRAPH    │
         └────────┬────────┘
                  ▼
       ┌──────────┼──────────┐
       ▼          ▼          ▼
      BFS        DFS         A*
       └──────────┼──────────┘
                  ▼
       ┌────────────────────┐
       │ Bayesian Reasoning │
       └──────────┬─────────┘
                  ▼
       ┌────────────────────┐
       │ CSP Contradiction  │
       │     Detection      │
       └──────────┬─────────┘
                  ▼
       ┌────────────────────┐
       │ Explainable Result │
       └────────────────────┘
```

The project review identifies this combination as its proposed novelty, including state-space investigation, multi-algorithm search, evidence relationships, Bayesian hypothesis evaluation, CSP contradiction detection, and explainable results.

---

# 🧠 Intelligence Behind the System

## 01 — Understand

### Natural Language Processing

Crime information is often written as natural language.

The NLP layer extracts meaningful entities and relationships from this information.

For example:

```text
"Ravi was seen near the warehouse at 10 PM.
A fingerprint was discovered at the location."
```

can be transformed into:

```text
Person      → Ravi
Location    → Warehouse
Time        → 10 PM
Evidence    → Fingerprint
```

The proposed system specifically includes entity extraction and relationship building from case information.

---

# 02 — Connect

### Case Relationship Graph

The extracted information is converted into a connected representation.

For example:

```text
Ravi
 │
 ├── seen_near ──→ Warehouse
 │
 └── associated_with ──→ Evidence A
                              │
                              ↓
                         Fingerprint
```

This makes hidden relationships within a case easier to explore.

---

# 03 — Explore

### Investigation as a Search Problem

The project treats investigation as a **state-space search problem**.

Different search strategies can explore possible paths through the case:

### BFS

Useful for exploring relationships level by level.

```text
Suspect
   ↓
Evidence
   ↓
Location
   ↓
Event
```

### DFS

Explores one investigative path deeply before moving to another.

### A*

Uses a heuristic to search for a promising path more efficiently.

The project proposes BFS, DFS, and A* as investigation-path search techniques.

---

# 04 — Reason

### Bayesian Hypothesis Evaluation

Not every piece of evidence provides the same level of certainty.

The system uses Bayesian reasoning to reason about uncertain evidence and possible hypotheses.

Conceptually:

```text
Evidence
   +
Existing Knowledge
   ↓
Probability Update
   ↓
Investigation Hypothesis
```

This allows the system to reason about evidence rather than simply matching keywords.

---

# 05 — Challenge

### CSP-Based Contradiction Detection

Investigations can contain conflicting information.

For example:

```text
Statement A:
Person X was at Location A at 9:00 PM.

Statement B:
Person X was at Location B at 9:00 PM.
```

Instead of ignoring the conflict, the system can treat the information as constraints and search for inconsistencies.

```text
Case Information
       ↓
   Constraints
       ↓
Constraint Checking
       ↓
Possible Contradiction
```

The proposed system specifically identifies CSP-based contradiction detection as one of its novelty areas.

---

# 06 — Explain

### From Result → Reasoning

The system is designed around **explainable investigation support**.

Rather than providing only:

```text
"Possible connection found."
```

the intended result is closer to:

```text
Possible Connection

Suspect A
     ↓
was associated with
     ↓
Evidence B
     ↓
which was found at
     ↓
Location C

Supporting Information:
- Witness statement
- Evidence relationship
- Location relationship

Potential Issue:
- Timeline inconsistency detected
```

This makes the AI output easier for a human investigator to inspect.

---

# 🧬 Investigation Pipeline

The complete concept can be summarized as:

```text
INPUT
  │
  ▼
Crime Complaints
Witness Statements
Evidence
Suspects
Locations
Timelines
  │
  ▼
┌─────────────────────┐
│   PREPROCESSING     │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│        NLP          │
│ Entities + Relations│
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│     CASE GRAPH      │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  SEARCH & REASONING │
│ BFS | DFS | A*      │
│ Bayesian | CSP      │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ EXPLAINABLE OUTPUT  │
└─────────────────────┘
```

---

# 🔬 Example Scenario

Imagine an investigation contains:

```text
Suspect A was seen near Location X.

Witness B reported seeing Suspect A.

Evidence C was found at Location X.

The timeline indicates that Suspect A
was supposedly at Location Y at the same time.
```

The system can transform this into:

```text
                  Witness B
                      │
                    reports
                      ↓
                  Suspect A
                  /       \
                 /         \
             seen_at      timeline
               ↓             ↓
          Location X     Location Y
               │
            contains
               ↓
           Evidence C
```

The reasoning layer can then:

* Explore the relationships.
* Search possible investigation paths.
* Evaluate evidence uncertainty.
* Identify the timeline conflict.
* Present the reasoning in an explainable form.

---

# 🚨 The Problem It Addresses

Traditional investigation can become difficult when case information grows.

The project review identifies several challenges:

* Large amounts of case information are difficult to analyze.
* Relationships between evidence may not be explicit.
* Uncertain evidence is difficult to evaluate.
* Investigation paths can depend heavily on human analysis.
* Existing approaches may focus on prediction rather than investigation reasoning.

### AI Crime Investigator addresses these challenges through:

```text
Unstructured Information
          ↓
       NLP
          ↓
Connected Case Knowledge
          ↓
Search + Reasoning
          ↓
Contradiction Detection
          ↓
Explainable Investigation Support
```

---

# 💡 Central Innovation

The central idea of this project can be expressed in one sentence:

> **Don't just predict the crime — reconstruct the connections, explore the possibilities, challenge the evidence, and explain the reasoning.**

This makes **AI Crime Investigator** an investigation-support concept rather than simply a crime-prediction system.

---

# 🧠 AI Techniques

| Technique                    | Purpose                                              |
| ---------------------------- | ---------------------------------------------------- |
| **NLP**                      | Extract meaningful information from text             |
| **Named Entity Recognition** | Identify suspects, locations, evidence, events, etc. |
| **Relation Extraction**      | Discover relationships between entities              |
| **Graph Representation**     | Connect and organize case information                |
| **BFS**                      | Breadth-first investigation path search              |
| **DFS**                      | Depth-first investigation path search                |
| **A***                       | Heuristic investigation path search                  |
| **Bayesian Reasoning**       | Evaluate uncertain evidence                          |
| **CSP**                      | Detect contradictions and inconsistencies            |
| **Explainable AI**           | Present understandable investigation reasoning       |

---

# 🎯 Final Vision

AI Crime Investigator aims to create a system where a complex crime case can be transformed from:

```text
📄 Pages of Information
```

into:

```text
🕸️ Connected Case Knowledge
        +
🔎 Investigation Paths
        +
📊 Evidence Reasoning
        +
⚠️ Contradiction Detection
        +
💡 Explainable Insights
```

The final goal is **human-in-the-loop investigation support** — AI assists investigators in discovering connections and reasoning about information, while final decisions remain with human experts.

---

## ⚠️ Disclaimer

AI Crime Investigator is an **academic investigation-support project**.

Its outputs are intended to assist analysis and should not be treated as proof of criminal activity or as a replacement for professional investigators, forensic experts, legal procedures, or judicial decisions.
