# Source grounding

Tutor Course Mode retrieves `SourceSpan` rows (hybrid lexical + hashed embedding) and must display **View Source** locators:

```json
{ "source_type": "notebook", "file": "02a_Intermediate_Fusion.ipynb", "cell_index": 25 }
```

If retrieval is empty, the demo tutor says the fact is not established by the supplied material. Research Mode may add `EXTERNAL_RESEARCH` but must not silently replace 01a/02a fusion definitions.
