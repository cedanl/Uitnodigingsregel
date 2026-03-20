---
name: check-style
description: Check code against CEDA R or Python style standards. Use when reviewing code, after writing code, or when the user asks to check style/conventions.
---

# Check CEDA Style Standards

Review code in the current repository against the CEDA technical standards.

## Workflow

When the user invokes `/check-style [optional: file or directory]`:

### 1. Detect language

Determine whether this is an R or Python project:

| Indicator | Language |
|-----------|----------|
| `DESCRIPTION`, `NAMESPACE`, `renv.lock`, `R/` directory | R |
| `pyproject.toml`, `uv.lock`, `src/` directory | Python |

If both are present, ask the user which to check.

### 2. Read the relevant standard

- R projects: read `standards/r-style.md` from the cedanl/.github repo (or local copy)
- Python projects: read `standards/python-style.md` from the cedanl/.github repo (or local copy)
- Always also check against `standards/principles.md` and `standards/data-conventions.md`

Standards location: https://github.com/cedanl/.github/tree/main/standards

### 3. Scope the check

- If a file or directory is specified, check only that
- If nothing specified, check the main source files:
  - R: files in `R/`, `main.R`, `inst/app/app.R`
  - Python: files in `src/`, `app/main.py`

### 4. Run automated checks (if available)

- R: check if `styler` and `lintr` are available, run them
- Python: run `ruff check .` and `ruff format --check .`

Report linting results first.

### 5. Manual review against standards

Check the following categories and report findings:

#### Package structure
- Is the repo a proper package? (DESCRIPTION/NAMESPACE for R, pyproject.toml with src/ layout for Python)
- Is there an interactive app? (Shiny in `inst/app/` for R, Streamlit in `app/` for Python)
- Is there a `main.R` or `main.py` entrypoint?
- Is there a `.devcontainer/`?

#### Code style
- **R**: `<-` assignment, `|>` pipe, explicit `return()`, roxygen2 docs, `cli`/`rlang` for messages/errors
- **Python**: type hints on functions, Google-style docstrings, Polars preferred over Pandas, `Path` over `os.path`

#### Naming
- Functions start with a verb (`snake_case`)
- Descriptive variable names
- File names match primary function

#### Data conventions
- Numbered data directories (`data/01-raw/`, etc.)
- Source column names preserved
- Parquet for internal steps, Parquet + CSV for output
- `;` delimiter for CSV

#### Documentation
- README.md present and useful
- CLAUDE.md present with standards reference
- Functions documented (roxygen2 / docstrings)

### 6. Report findings

Format output as:

```
## Style Check: [project-name]

**Language:** R / Python
**Linter output:** [summary or "clean"]

### Findings

#### [Category]
- [finding with file:line reference]
- ...

### Summary
X issues found across Y categories.
```

Group findings by severity:
1. **Must fix**: Violations of core standards (no package structure, missing devcontainer, wrong pipe operator)
2. **Should fix**: Style issues (missing type hints, inconsistent naming, missing docstrings)
3. **Consider**: Suggestions for improvement (better abstractions, missing tests)

## Important

- Be pragmatic: existing repos are being migrated, not everything will conform yet
- Focus on actionable feedback, not nitpicking
- Reference the specific standard document and section for each finding
- If the project uses `/init-repo` structure, it should already pass most checks
