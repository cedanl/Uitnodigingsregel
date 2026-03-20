---
name: migrate-cookiecutter
description: Migrate a Python repository from cookiecutter data science layout to the CEDA package standard. Use when converting existing repos like Uitnodigingsregel or studentprognose.
---

# Migrate Cookiecutter to CEDA Package Standard

Guided migration of existing cookiecutter data science repos to the CEDA package standard.

## Workflow

When the user invokes `/migrate-cookiecutter [optional: repo path]`:

### 1. Analyze current structure

Read the repo and identify:
- Current directory layout (cookiecutter variant)
- Where source code lives (`module/`, `scripts/`, `src/`, or other)
- Data directory naming (`data/raw/`, `data/interim/`, `data/processed/` vs numbered)
- Existing `pyproject.toml` or `setup.py`
- Whether a `Makefile` exists
- Whether there's already an interactive interface
- Config file locations

Report findings to the user before proceeding.

### 2. Read migration standard

Read `standards/migration-cookiecutter.md` and `standards/project-structure.md` from the cedanl/.github repo (or local copy).

Standards location: https://github.com/cedanl/.github/tree/main/standards

### 3. Determine repo type

Ask if not obvious:

| Pattern | Likely type |
|---------|-------------|
| Reads raw files, decodes, exports clean data | Type 1: Ingestion |
| Loads prepared data, analyzes, models, reports | Type 2: Analysis |

### 4. Create migration plan

Present a checklist to the user:

```markdown
## Migration Plan: [project-name]

### Source code
- [ ] Move `[current location]` → `src/project_name/`
- [ ] Add `__init__.py` files
- [ ] Add `src/project_name/metadata/__init__.py`
- [ ] Move metadata/config files → `src/project_name/metadata/`
- [ ] Update all imports to use package paths

### Package setup
- [ ] Update/create `pyproject.toml` with [project] section
- [ ] Add `[tool.uv]`, `[tool.ruff]`, `[tool.pytest]` config
- [ ] Add `.python-version` (3.13)
- [ ] Create `uv.lock` via `uv sync`

### Data directories
- [ ] Rename `data/raw/` → `data/01-raw/`
- [ ] Rename `data/interim/` → `data/02-prepared/`
- [ ] Rename `data/processed/` → `data/03-output/`
- [ ] Add `demo/` subfolders with synthetic data
- [ ] Update `.gitignore` for new data paths

### Interactive app
- [ ] Create `app/main.py` (Streamlit)
- [ ] Create `app/config.toml` with data paths
- [ ] Create `.streamlit/config.toml`
- [ ] Wire app to call package functions (no business logic in app)

### Infrastructure
- [ ] Add `.devcontainer/devcontainer.json`
- [ ] Update `CLAUDE.md` with standards reference
- [ ] Update `README.md`
- [ ] Keep `Makefile` if useful (optional convenience)

### Cleanup
- [ ] Remove old directory structure
- [ ] Verify `uv run pytest` passes
- [ ] Verify `ruff check .` passes
- [ ] Run `/check-style` for final validation
```

Wait for user approval before proceeding.

### 5. Execute migration

Work through the checklist step by step. For each step:
- Show what you're doing
- Make the change
- Mark the step complete

Key migration actions:

#### Move source code to package
```
module/ or scripts/  →  src/project_name/
```
- Rename files to follow `verb_object.py` convention where possible
- Add proper `__init__.py` with key exports
- Update all internal imports

#### Migrate metadata into package
```
config/ or data/metadata/  →  src/project_name/metadata/
```
- Add `__init__.py`
- Update code to use `importlib.resources`:
```python
from importlib.resources import files

path = files("project_name.metadata") / "definitions.csv"
```

#### Create pyproject.toml
Use the template from `standards/python-style.md` with proper `[project]`, `[tool.uv]`, `[tool.ruff]`, `[tool.pytest]` sections.

#### Create Streamlit app
Minimal app that imports and calls package functions. No business logic.

### 6. Verify

After migration:
1. Run `uv sync` to install the package
2. Run `uv run pytest` if tests exist
3. Run `ruff check .` and `ruff format --check .`
4. Suggest running `/check-style` for full standards check

### 7. Report result

```
## Migration Complete: [project-name]

**From:** cookiecutter data science
**To:** CEDA package standard (Type [1/2])

### Changes made
- [summary of moves and renames]

### Next steps
1. Review the migrated code
2. Add demo data to `data/*/demo/` folders
3. Test the Streamlit app: `uv run streamlit run app/main.py`
4. Run `/check-style` for full validation
```

## Important

- Always get user approval before executing the migration plan
- Preserve git history where possible (use `git mv` for renames)
- Keep the `Makefile` if it exists — it's optional but useful
- The migration is a one-time operation; `standards/migration-cookiecutter.md` has the full reference
- After migration, the repo should pass `/check-style`
