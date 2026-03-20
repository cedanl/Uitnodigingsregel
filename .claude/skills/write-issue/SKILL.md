---
name: write-issue
description: Writing and maintaining GitHub issues and pull requests for cedanl repositories. Use when creating new issues, editing issue titles/bodies, creating PRs, or cleaning up issue metadata.
---

# Writing and maintaining GitHub issues and PRs

Standards for issues and pull requests in cedanl repositories.

## Workflow

When the user invokes `/write-issue [description]`:

### 1. Bepaal issue type op basis van input

| Input bevat | Type |
|-------------|------|
| Bug, fout, broken, kapot, error | Bug |
| Groot werk, meerdere dagen, architectuur, evaluatie | Pitch |
| Al het andere | Task |

### 2. Formateer de issue body

Gebruik het juiste template (zie secties hieronder). Neem de input van de user als basis en vul aan met context uit de codebase waar nodig.

### 3. Bepaal labels

Kies labels op basis van inhoud uit de beschikbare domein- en statuslabels hieronder.

### 4. Maak de issue aan via gh

```bash
gh issue create \
  --title "<titel>" \
  --label "<label1>,<label2>" \
  --body "$(cat <<'EOF'
<geformatteerde body>
EOF
)"
```

### 5. Rapporteer het resultaat

Toon de issue URL die `gh issue create` teruggeeft.

## Issue Types

| Type | Use for |
|------|---------|
| Bug | Rapporteer een bug of probleem |
| Task | Taak, item of werk unit |
| Pitch | Shape Up pitch voor een groter stuk werk |

## Issue Templates

### Bug

Simpel template voor bug reports.

```markdown
### Beschrijving

**Wat gaat er mis?**
...

**Stappen om te reproduceren:**
1. ...

**Screenshots / Logs (optioneel):**
...
```

### Task

Voor taken en werk items.

```markdown
### Beschrijving

Wat moet er gedaan worden?

### Acceptatiecriteria

- [ ] ...
- [ ] ...
```

### Pitch (Shape Up)

Voor grotere stukken werk die planning en afstemming nodig hebben.

```markdown
### Problem / Opportunity

Wat is het echte probleem? Voor wie? Evidence, voorbeelden, context.

### Appetite (timebox)

Kies uit: Small (1-2 dagen) | Medium (3-4 dagen) | Large (5-6 dagen)

### Solution

High-level aanpak, misschien enkele key elements.

### Risks / Rabbit holes

Welke valkuilen moeten we vermijden?

### No-Gos

Wat doen we expliciet NIET in deze versie?

### Gevalideerd met

@username

### Sparring partner

@username
```

## Labels

### Domein labels

| Label | Beschrijving |
|-------|--------------|
| `instroom` | Instroomprognose MBO |
| `uitval` | Uitval analyses |
| `tech` | Technische verbeteringen |
| `project` | Project organisatie |

### Status labels

| Label | Beschrijving |
|-------|--------------|
| `needs-shaping` | Pitch die nog gevormd moet worden |

## Pull Request Template

When creating PRs, use this structure:

```markdown
## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Enhancement
- [ ] Documentation update

## Description of Changes

## Related Issues
<!-- Link using #issue-number -->

## Before / After

### Before:

### After:

## Checklist
- [ ] I have tested these changes locally
- [ ] My code follows the project's coding standards
```

## Title Standards

- Be specific and descriptive
- Use sentence case
- No prefixes like [FEATURE], [BUG] - use labels instead

### Good titles

- `Add export functionality for enrollment data`
- `Data pipeline fails when processing empty CSV files`
- `Verbeter dagstart workflow met GitHub integratie`

### Bad titles

- `Bug` (vague)
- `Fix thing` (vague)
- `NEW FEATURE` (vague, all caps)

## Repository Configuration

- **Blank issues zijn uitgeschakeld** - gebruik altijd een template
- **CEDA Board**: https://github.com/orgs/cedanl/projects/2
- Issues worden automatisch aan het project board toegevoegd

## R-specific validation

For R projects, ensure before submitting PRs:
- Run `styler::style_active_file()` on modified files
- Follow tidyverse style guide
- Use `|>` pipe operator
- Use snake_case naming

## Important

- Never include "Generated with Claude Code" in issues/PRs unless directly relevant
- Link related issues using `#issue-number` syntax
- Provide context - explain the "why" not just the "what"
- Gebruik `@username` voor validatie en sparring partners in pitches
