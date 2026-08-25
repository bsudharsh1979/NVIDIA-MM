# Source ingestion

- Discover `.ipynb`, `.pdf`, `.pptx` under `COURSE_MATERIALS_DIR` (default `/course-materials`).
- Notebooks: `nbformat` only. **Never execute cells.**
- PDF: PyMuPDF (`fitz`) page text.
- PPTX: `python-pptx` text + notes.
- Dangerous tokens (`kubectl`, `helm`, `docker`, `rm -rf`, `os.system`, `requests.post`) flagged on cells.
- Embeddings: deterministic hashed vectors, regenerated only when checksum changes.
