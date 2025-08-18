# Evaluator Pipeline (scripts)

Helpers to run the evaluator and do quick checks.

## Files
- **Agentresponse.py** — loads and formats agent outputs for evaluation
- **TF-Eval.py** — The main evalutor :runs the structured evaluator on a model output, writes a JSONL with verdicts and scores
- **validation.py** — lightweight validator for sanity checks  
  *(For full metrics use `validation_final.py` at the repo root.)*

## Prerequisites
```bash
pip install -r requirements.txt
```
