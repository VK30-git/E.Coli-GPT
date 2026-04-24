# Checkpoint: Revert to Simulated Data (before PubMed)

This checkpoint lets you restore the `/api/analyze` endpoint to use **simulated** data instead of real PubMed extraction.

## Files

- **`main_checkpoint_before_pubmed.py`** – Contains the old simulated logic
- **`main.py`** – Current file (uses real PubMed)

## How to revert

### Step 1: Update imports in main.py

**Remove:**
```python
from pipeline import ScientificPubMedEColiExtractor
```

**Add:**
```python
import random
```

### Step 2: Remove the helper function

Delete the entire `_transform_to_api_format` function from `main.py`.

### Step 3: Replace the analyze_papers endpoint

Replace the current `@app.get("/api/analyze")` endpoint (and its `analyze_papers` function) with the code from `main_checkpoint_before_pubmed.py`.

The simulated version uses:
- `random.choice()` for strains, products, medium
- `random.uniform()` for yield and pH
- `random.random()` for temperature/pH presence

## To go back to PubMed (current behavior)

1. Add: `from pipeline import ScientificPubMedEColiExtractor`
2. Remove: `import random`
3. Add back `_transform_to_api_format` and the real PubMed logic
