# 🔍 AI Crime Investigator

An AI-based investigation support system that analyzes crime-related information such as crime complaints, witness statements, suspects, evidence, locations, and timelines to assist investigators in making informed decisions using Artificial Intelligence techniques.

> **Academic Project**
> Department of Cyber Security
> Rajalakshmi Engineering College

---

## 📌 Project Overview

AI Crime Investigator is an explainable AI-based decision support system designed to help investigators organize and analyze crime case information.

The system accepts case details from users, extracts important entities using Natural Language Processing (NLP), builds relationships between suspects, evidence, locations, and events, searches possible investigation paths using graph algorithms, evaluates uncertain evidence using Bayesian reasoning, detects contradictions using Constraint Satisfaction Problem (CSP), and generates an explainable investigation report.

The system is intended to **support investigation and decision-making** and does **not** determine guilt or replace human investigators.

---

## 🎯 Objective

* Analyze crime-related information using Artificial Intelligence.
* Extract important entities from textual crime descriptions using NLP.
* Represent relationships between suspects, evidence, locations, and events.
* Apply BFS, DFS, and A* algorithms for investigation-path search.
* Use Bayesian reasoning to evaluate uncertain evidence.
* Detect inconsistencies using Constraint Satisfaction Problem (CSP).
* Generate explainable investigation reports for decision support.

---

## ✨ Features

* Crime case information submission
* Witness statement analysis
* NLP-based entity extraction
* Suspect, evidence, location, and timeline identification
* Relationship graph generation
* BFS investigation path search
* DFS investigation path exploration
* A* optimized path search
* Bayesian hypothesis evaluation
* CSP-based contradiction detection
* Explainable AI investigation report
* SQLite/MySQL database support
* User-friendly web interface

---

## 🏗️ System Architecture

```text
                    Investigator
                         │
                         ▼
          ┌──────────────────────────┐
          │       Frontend           │
          │ HTML • CSS • JavaScript  │
          └────────────┬─────────────┘
                       │
                  HTTP / JSON
                       │
                       ▼
          ┌──────────────────────────┐
          │      Flask Backend       │
          │       REST API           │
          └────────────┬─────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   NLP Engine    Graph Engine     Database
   spaCy/NLTK     NetworkX     SQLite/MySQL
        │              │
        └───────┬──────┘
                ▼
      BFS • DFS • A* Search
                │
                ▼
      Bayesian Reasoning Engine
                │
                ▼
      CSP Contradiction Checker
                │
                ▼
      Explainable Investigation
              Report
```

---

## 🧠 Technologies Used

### Frontend

* HTML5
* CSS3
* JavaScript

### Backend

* Python
* Flask
* Flask-CORS

### AI & Data Processing

* spaCy
* NLTK
* NetworkX
* NumPy
* Pandas

### Database

* SQLite
* MySQL

### Development Tools

* VS Code
* Git
* GitHub

---

## 📂 Project Structure

```text
AI-Crime-Investigator/
│
├── frontend/
│   ├── index.html
│   ├── case.html
│   ├── results.html
│   ├── report.html
│   │
│   ├── css/
│   │   └── style.css
│   │
│   └── js/
│       ├── app.js
│       ├── api.js
│       └── results.js
│
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   │
│   ├── routes/
│   │   ├── case_routes.py
│   │   └── analysis_routes.py
│   │
│   ├── services/
│   │   ├── nlp_engine.py
│   │   ├── graph_engine.py
│   │   ├── search_engine.py
│   │   ├── bayesian_engine.py
│   │   ├── csp_engine.py
│   │   └── report_generator.py
│   │
│   ├── models/
│   │   └── case.py
│   │
│   └── database/
│       └── db.py
│
├── database/
│   └── crime_investigator.db
│
├── README.md
└── .gitignore
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/AI-Crime-Investigator.git
```

### 2. Navigate to the Project

```bash
cd AI-Crime-Investigator
```

### 3. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Run Flask Server

```bash
python app.py
```

The backend will start on:

```text
http://127.0.0.1:5000
```

### 5. Open Frontend

Open the `frontend/index.html` file in your browser or run it using the **Live Server** extension in VS Code.

---

## 🔄 Workflow

1. Investigator enters crime case details.
2. Frontend sends the information to Flask API.
3. Backend receives the JSON request.
4. NLP extracts important entities.
5. Graph engine builds relationships.
6. BFS, DFS, and A* search investigation paths.
7. Bayesian reasoning evaluates evidence.
8. CSP checks timeline and logical contradictions.
9. Backend generates an explainable report.
10. Frontend displays the final investigation analysis.

---

## 🧾 Example Input

**Crime Description**

```text
A robbery occurred at Anna Nagar around 9 PM.
A mobile phone was stolen from the victim.
```

**Witness Statement**

```text
Ravi was seen talking to Kumar near the crime location before the incident.
```

---

## 📊 Example Output

```text
Case ID: CASE001

Extracted Entities

Suspects:
- Ravi
- Kumar

Location:
- Anna Nagar

Time:
- 9 PM

Evidence:
- Mobile Phone

Investigation Path

Ravi → Kumar → Anna Nagar → Evidence

Bayesian Analysis

Hypothesis Support Score: 72%

Constraint Analysis

No contradiction detected.

Explanation

The generated result is based on the relationships,
available evidence, witness information, and logical analysis
to support the investigator's decision-making process.
```

> **Note:** The hypothesis score is an AI-generated analytical support value and must not be interpreted as proof of guilt.

---

## 🤖 AI Modules

### 1. Natural Language Processing

Extracts entities such as:

* Persons
* Suspects
* Witnesses
* Locations
* Time
* Evidence
* Events

### 2. Knowledge Representation

Creates a relationship graph connecting all case entities.

Example:

```text
Ravi
 │
 ├── met ── Kumar
 │
 └── seen at ── Anna Nagar
                     │
                     ▼
                  Evidence
```

### 3. Search Algorithms

**BFS**

Explores nearby connected evidence step-by-step.

**DFS**

Explores deeper investigation paths.

**A***

Finds an optimized investigation path using heuristic search.

### 4. Bayesian Reasoning

Evaluates uncertain evidence and provides hypothesis support for investigation.

### 5. Constraint Satisfaction Problem

Detects contradictions in:

* Timeline
* Location
* Witness statements
* Event relationships

### 6. Explainable AI

Generates a human-readable investigation report explaining why the system produced its analytical results.

---

## 🌐 API Example

### Request

```json
POST /api/analyze
```

```json
{
  "case_id": "CASE001",
  "description": "Robbery occurred at Anna Nagar",
  "statement": "Ravi was seen near the location"
}
```

### Response

```json
{
  "status": "success",
  "entities": {
    "suspects": ["Ravi"],
    "locations": ["Anna Nagar"]
  },
  "investigation_path": [
    "Ravi → Anna Nagar → Evidence"
  ],
  "hypothesis_score": 72,
  "contradictions": [],
  "report": "Generated successfully"
}
```

---

## 🗄️ Database Design

The project stores case information using SQLite/MySQL.

### Main Tables

* Cases
* Suspects
* Witnesses
* Evidence
* Locations
* Investigation Results

This allows efficient storage and retrieval of investigation records.

---

## 🚀 Future Enhancements

* Voice-based crime complaint input
* Image evidence analysis
* Face recognition integration
* Real-time crime data integration
* Multi-language NLP support
* Interactive relationship visualization
* Investigator dashboard
* PDF report generation
* Role-based authentication
* Cloud deployment

---

## ⚠️ Ethical Disclaimer

AI Crime Investigator is developed as an **academic AI decision-support project**.

* It assists investigators by analyzing supplied information.
* It does not replace police officers or legal authorities.
* It does not establish guilt or innocence.
* Final investigation decisions must always be made by qualified human investigators.

---

## 👩‍💻 Authors

**Keerthisri D**
Department of Cyber Security
Rajalakshmi Engineering College

**Subathra Devi R**
Department of Cyber Security
Rajalakshmi Engineering College

---

## 👩‍🏫 Guided By

**Mrs. R. Divya**
Assistant Professor
Department of Cyber Security
Rajalakshmi Engineering College

---

## 📄 License

This project is developed for **educational and academic purposes** as part of the Foundations of Artificial Intelligence course.
