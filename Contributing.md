# Contributing to CodeMind AI

Thanks for your interest in improving CodeMind AI.

## Development setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest
cp .env.example .env
```

## Before submitting changes

- Run `python3 -m py_compile app/*.py app/services/*.py app/routers/*.py app/utils/*.py` to confirm everything compiles.
- Test any feature you touch through the web UI (`http://127.0.0.1:8000`) end to end.
- If you add a new feature with correctness risk (like Bug Detection, Code Review, Test Generation, or Documentation), consider whether it needs a deterministic safety net alongside the LLM call - see the "Reliability notes" section in the README for the existing pattern.

## Code style

- Keep service functions in `app/services/` focused on one responsibility each.
- Keep static/deterministic logic (AST checks, graph building) separate from LLM-calling logic, and clearly comment which is which.

## Reporting issues

Open a GitHub issue with steps to reproduce, expected vs actual behavior, and your Ollama model/version if relevant.
EOF
echo "CONTRIBUTING.md created"
