# Search Queries for Job Scraper

Profile baseline: Musaab Mahjoub, Aalborg-based engineer targeting machine
learning engineer, software engineer, and structural engineer roles. Search
geography priority: Aalborg first, North Jutland second, all Denmark third.
Visa sponsorship / work-authorization support is a must-have.

## Search Sites

Primary:
- **jobindex.dk** - broad Danish job board
- **jobnet.dk** - Danish public job portal
- **jobbank.dk** - Akademikernes Jobbank
- **jobdanmark.dk** - Danish job portal
- **linkedin.com/jobs** - public LinkedIn job listings, keep volume low

Secondary:
- **karriere.dk** - IDA's job board for engineering/science roles
- **jobfinder.dk** - engineering and specialist roles
- Direct company career pages when a promising company appears in search results

## Query Categories

Run the top three priority categories by default. Use `broad` to include all
categories. Prefer jobs posted within the last 14 days.

### Priority 1: Machine Learning Engineer / Applied AI

These match Musaab's strongest AI/data direction.

```text
site:jobindex.dk "machine learning engineer" Aalborg
site:jobindex.dk "machine learning engineer" Denmark
site:jobindex.dk "AI engineer" Denmark
site:jobindex.dk "data scientist" Aalborg
site:jobindex.dk "data scientist" Denmark
site:linkedin.com/jobs "machine learning engineer" Denmark
site:linkedin.com/jobs "AI engineer" Denmark
site:linkedin.com/jobs "data scientist" Denmark
site:jobbank.dk "machine learning" Denmark
site:jobnet.dk "machine learning" Denmark
```

Useful variants when results are thin:
- applied machine learning
- computer vision
- PyTorch
- scikit-learn
- Python data science
- MLOps, but only if the posting does not require senior platform ownership

### Priority 2: Software Engineer / Engineering Software

These match full-stack and engineering-tool experience from EuroTec and Awatif.

```text
site:jobindex.dk "software engineer" Aalborg
site:jobindex.dk "software developer" Aalborg
site:jobindex.dk "software engineer" "North Jutland"
site:jobindex.dk "Python developer" Denmark
site:jobindex.dk "TypeScript developer" Denmark
site:linkedin.com/jobs "software engineer" Denmark
site:linkedin.com/jobs "Python developer" Denmark
site:jobbank.dk "software engineer" Denmark
site:jobnet.dk "software developer" Denmark
```

Useful variants:
- full stack developer
- backend developer
- engineering software
- scientific software
- simulation software
- Django
- TypeScript

### Priority 3: Structural Engineer / Computational Engineering

These match Musaab's structural engineering, timber, finite element modelling,
and sustainability background.

```text
site:jobindex.dk "structural engineer" Aalborg
site:jobindex.dk "structural engineer" Denmark
site:jobindex.dk "civil engineer" Aalborg
site:jobindex.dk "timber" "structural engineer" Denmark
site:jobindex.dk "finite element" Denmark
site:linkedin.com/jobs "structural engineer" Denmark
site:linkedin.com/jobs "civil engineer" Denmark
site:jobbank.dk "structural engineer" Denmark
site:jobnet.dk "bygningsingenior" Denmark
```

Useful variants:
- computational engineering
- finite element modelling
- timber structures
- sustainability engineer
- structural analysis
- Abaqus

### Priority 4: Technical Consultant / Solutions Engineer

Use in broad searches. These roles may fit if they involve engineering,
software, data, or applied AI rather than generic sales.

```text
site:jobindex.dk "technical consultant" Python Denmark
site:jobindex.dk "solutions engineer" software Denmark
site:jobindex.dk "technical advisor" engineering Denmark
site:linkedin.com/jobs "technical consultant" Denmark
site:linkedin.com/jobs "solutions engineer" Denmark
site:jobbank.dk "technical consultant" Denmark
```

### Priority 5: Visa Sponsorship / International Candidate Filters

Use these as additional checks, not as the only search strategy. Many relevant
postings do not mention sponsorship directly.

```text
"visa sponsorship" Denmark "software engineer"
"visa sponsorship" Denmark "machine learning engineer"
"work permit" Denmark "software engineer"
"relocation" Denmark "machine learning engineer"
"relocation package" Denmark engineer
```

## Location Filter

When evaluating results, verify the role is compatible with Musaab's location
and work authorization needs.

- **Ideal:** Aalborg, Aalborg kommune, or remote/hybrid with realistic Aalborg base.
- **Acceptable:** North Jutland / Nordjylland, including N Aalborg, Aalborg, Bronderslev, Hjorring, Frederikshavn, Hobro, Randers, Aarhus if hybrid/relocation makes sense.
- **Broader search:** all Denmark, especially roles with relocation support, remote/hybrid options, or strong visa/work-authorization support.
- **Borderline:** Copenhagen, Odense, Vejle, Kolding, Esbjerg, or Aarhus if the role requires frequent office presence and relocation details are unclear.
- **Too far / likely skip:** roles outside Denmark unless explicitly remote from Denmark or clearly offering relocation and visa support.

## Must-Have Filters

- Visa sponsorship / work-authorization support must be feasible.
- Prefer roles in English, or roles where intermediate Danish is acceptable.
- For Danish-heavy postings, flag language as a risk unless the employer clearly accepts English-speaking candidates.
- Exclude closed postings, expired deadlines, and roles that are clearly not open to international candidates when work authorization is required.

## Date Filter

Only include jobs posted within the last 14 days, or with an application deadline
that has not yet passed. If a posting date cannot be determined, include it but
flag as "date unknown".

## Adapting Queries

If the user specifies a focus area, select queries from the matching category and
generate 2-3 custom queries for that focus.

Examples:
- `$job-scraper machine learning` -> Priority 1 plus computer vision / Python variants.
- `$job-scraper software` -> Priority 2 plus Django / TypeScript variants.
- `$job-scraper structural` -> Priority 3 plus timber / finite element variants.
- `$job-scraper broad` -> all priority categories.
