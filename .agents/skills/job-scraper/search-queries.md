# Search Queries for Job Scraper

Profile baseline: [candidate name], targeting machine learning engineer,
software engineer, quantitative trading / quantitative research, and
structural engineer roles. Search geography priority:
[primary region] first, [secondary region] second, [country] third.
Visa sponsorship / work-authorization support is a must-have when relevant.
Default target level: early-career to mid-level. Avoid senior/staff/principal/
lead/manager/architect roles and postings requiring roughly 6+ years of
experience unless the candidate explicitly asks for stretch roles.

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

Run the top four priority categories by default. Use `broad` to include all
categories. Prefer jobs posted within the last 14 days.

### Priority 1: Machine Learning Engineer / Applied AI

These match the candidate's strongest AI/data direction.

```text
site:jobindex.dk "machine learning engineer" [location]
site:jobindex.dk "machine learning engineer" [country]
site:jobindex.dk "AI engineer" [country]
site:jobindex.dk "data scientist" [location]
site:jobindex.dk "data scientist" [country]
site:linkedin.com/jobs "machine learning engineer" [country]
site:linkedin.com/jobs "AI engineer" [country]
site:linkedin.com/jobs "data scientist" [country]
site:jobbank.dk "machine learning" [country]
site:jobnet.dk "machine learning" [country]
```

Useful variants when results are thin:
- applied machine learning
- computer vision
- PyTorch
- scikit-learn
- Python data science
- MLOps, but only if the posting does not require senior platform ownership
- junior machine learning engineer
- associate data scientist

### Priority 2: Software Engineer / Engineering Software

These match full-stack and engineering-tool experience from EuroTec and Awatif.

```text
site:jobindex.dk "software engineer" [location]
site:jobindex.dk "software developer" [location]
site:jobindex.dk "software engineer" "[region]"
site:jobindex.dk "Python developer" [country]
site:jobindex.dk "TypeScript developer" [country]
site:linkedin.com/jobs "software engineer" [country]
site:linkedin.com/jobs "Python developer" [country]
site:jobbank.dk "software engineer" [country]
site:jobnet.dk "software developer" [country]
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

These match the candidate's structural engineering, timber, finite element modelling,
and sustainability background.

```text
site:jobindex.dk "structural engineer" [location]
site:jobindex.dk "structural engineer" [country]
site:jobindex.dk "civil engineer" [location]
site:jobindex.dk "timber" "structural engineer" [country]
site:jobindex.dk "finite element" [country]
site:linkedin.com/jobs "structural engineer" [country]
site:linkedin.com/jobs "civil engineer" [country]
site:jobbank.dk "structural engineer" [country]
site:jobnet.dk "bygningsingenior" [country]
```

Useful variants:
- computational engineering
- finite element modelling
- timber structures
- sustainability engineer
- structural analysis
- Abaqus

### Priority 4: Quantitative Trading / Quantitative Research

These match the candidate's mathematical modelling, Python, machine learning,
optimization, statistics, and data-driven decision-making interests. Treat as a
new career direction, so prioritize junior, graduate, analyst, researcher, and
ordinary quant roles over senior trader roles.

```text
site:jobindex.dk "quantitative analyst" [country]
site:jobindex.dk "quantitative developer" [country]
site:jobindex.dk "quantitative researcher" [country]
site:jobindex.dk "trading analyst" [country]
site:linkedin.com/jobs "quantitative analyst" [country]
site:linkedin.com/jobs "quantitative developer" [country]
site:linkedin.com/jobs "quantitative researcher" [country]
site:linkedin.com/jobs "trading analyst" [country]
site:jobbank.dk "quantitative analyst" [country]
site:jobnet.dk "quantitative analyst" [country]
```

Useful variants:
- quant developer
- algorithmic trading
- systematic trading
- market risk analyst
- energy trading analyst
- Python finance
- stochastic modelling
- optimization

### Priority 5: Technical Consultant / Solutions Engineer

Use in broad searches. These roles may fit if they involve engineering,
software, data, or applied AI rather than generic sales.

```text
site:jobindex.dk "technical consultant" Python [country]
site:jobindex.dk "solutions engineer" software [country]
site:jobindex.dk "technical advisor" engineering [country]
site:linkedin.com/jobs "technical consultant" [country]
site:linkedin.com/jobs "solutions engineer" [country]
site:jobbank.dk "technical consultant" [country]
```

### Priority 6: Visa Sponsorship / International Candidate Filters

Use these as additional checks, not as the only search strategy. Many relevant
postings do not mention sponsorship directly.

```text
"visa sponsorship" [country] "software engineer"
"visa sponsorship" [country] "machine learning engineer"
"work permit" [country] "software engineer"
"relocation" [country] "machine learning engineer"
"relocation package" [country] engineer
```

## Location Filter

When evaluating results, verify the role is compatible with the candidate's location
and work authorization needs.

- **Ideal:** [primary city/region], or remote/hybrid with a realistic base.
- **Acceptable:** [secondary city/region] and nearby commute options.
- **Broader search:** [country-wide area], especially roles with relocation support, remote/hybrid options, or strong visa/work-authorization support.
- **Borderline:** Other major hubs if office presence is frequent and relocation details are unclear.
- **Too far / likely skip:** roles outside the target geography unless explicitly remote or clearly offering relocation and visa support.

## Must-Have Filters

- Visa sponsorship / work-authorization support must be feasible.
- Prefer roles in English, or roles where intermediate Danish is acceptable.
- For Danish-heavy postings, flag language as a risk unless the employer clearly accepts English-speaking candidates.
- Hide senior/staff/principal/lead/manager/architect roles by default.
- Hide roles asking for 6+ years, many years, or equivalent senior ownership by default.
- Prefer junior, graduate, associate, early-career, and ordinary mid-level roles over stretch senior roles.
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
- `$job-scraper quant` -> Priority 4 plus Python finance / optimization variants.
- `$job-scraper broad` -> all priority categories.
