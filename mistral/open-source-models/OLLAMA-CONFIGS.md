# Ollama Modelfile Configs for Mistral Models

## Standard Pulls (No Custom Config Needed)

```bash
# Volume text generation (Data Factory)
ollama pull mistral:7b

# Code tasks
ollama pull devstral-small

# Balanced general-purpose
ollama pull mistral:14b

# Check for Mistral Small 4 availability:
ollama pull mistral-small
```

## Custom Modelfiles

### Data Factory German Text Generator
Optimized for generating realistic German business text.

```dockerfile
# Save as: Modelfile.datafactory-de
FROM mistral:7b

PARAMETER temperature 0.8
PARAMETER top_p 0.9
PARAMETER num_ctx 4096

SYSTEM """
Du bist ein Experte fuer die Erstellung realistischer deutscher Geschaeftsdaten.
Generiere Texte die authentisch klingen und typisch fuer bayerische Mittelstandsunternehmen sind.
Verwende korrekte Rechtsformen (GmbH, UG, e.K., AG), realistische Firmenbezeichnungen,
und branchenuebliche Formulierungen. Alle Ausgaben auf Deutsch.
"""
```

```bash
ollama create datafactory-de -f Modelfile.datafactory-de
```

### EHCP Compliance Reviewer
For GRUND framework experiments.

```dockerfile
# Save as: Modelfile.ehcp-reviewer
FROM mistral:14b

PARAMETER temperature 0.3
PARAMETER top_p 0.85
PARAMETER num_ctx 8192

SYSTEM """
You are a specialist in UK SEND (Special Educational Needs and Disabilities) law,
specifically the Children and Families Act 2014, the SEND Code of Practice 2015,
and EHCP (Education, Health and Care Plan) compliance requirements.

When reviewing EHCP provisions, assess:
1. Specificity — Are provisions specific rather than vague?
2. Measurability — Can outcomes be objectively measured?
3. Legal compliance — Does the provision meet statutory requirements?
4. Quantification — Are hours, frequency, and duration specified?

Flag any provision that uses words like 'some', 'regular', 'appropriate',
'as needed', or 'access to' without quantification.
"""
```

```bash
ollama create ehcp-reviewer -f Modelfile.ehcp-reviewer
```

### Code Review Assistant
For automated PR review tasks.

```dockerfile
# Save as: Modelfile.code-reviewer
FROM devstral-small

PARAMETER temperature 0.2
PARAMETER num_ctx 8192

SYSTEM """
You are a code reviewer specializing in:
- TypeScript / Next.js applications
- Supabase (RLS policies, edge functions)
- Clerk authentication
- Offline-first PWA patterns (IndexedDB, Service Workers)
- Prompt contract JSON schemas

Review code for:
1. Type safety issues
2. Security concerns (especially RLS policy gaps)
3. Race conditions in async/offline code
4. Missing error handling
5. i18n key completeness

Be concise. Flag issues with severity (critical/warning/suggestion).
"""
```

```bash
ollama create code-reviewer -f Modelfile.code-reviewer
```

## Management Commands

```bash
# List all models
ollama list

# Check running models and VRAM
ollama ps

# Remove a model
ollama rm model-name

# Update a model
ollama pull model-name
```
