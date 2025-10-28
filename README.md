# Document Combiner & GenAI Summarizer

This is a small Streamlit app that lets users upload multiple documents, combine them into a single PDF, download the combined PDF, and (optionally) call a database stored procedure that triggers a Gen AI summarization for the combined PDF.

Features
- Upload multiple files (PDF, images, TXT).
- Combine uploaded files into a single PDF in-memory.
- Download the combined PDF.
- Optionally call a PostgreSQL stored procedure (e.g. `generate_summary`) that accepts the PDF as `bytea` and returns a text summary. The returned summary is shown in a text area.

Quick start

1. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Set environment variables (if you want DB summarization):

```bash
export DB_HOST=your-db-host
export DB_PORT=5432
export DB_NAME=your_db
export DB_USER=your_user
export DB_PASSWORD=your_password
# Optional: name of the stored proc/function that accepts bytea and returns text
export DB_PROC_NAME=generate_summary
```

You can also create a `.env` file with these keys and the app will read it.

3. Run the app:

```bash
streamlit run streamlit_app.py
```

Notes & Assumptions
- The app currently supports PDFs, common image formats (converted to PDF pages), and plain text files. Other document formats (DOCX, PPTX) are not automatically converted. You can extend the app to use LibreOffice conversion or other conversion services.
- The DB call is implemented for PostgreSQL via `psycopg2`. The stored procedure name must be set in `DB_PROC_NAME` (default `generate_summary`) and must accept a single `bytea` argument and return a `text` result.
- For production use, validate and sanitize the stored-proc name before interpolating into SQL to avoid injection; the current implementation expects a trusted value from environment variables.

Next steps / improvements
- Add support for DOCX/PPTX conversions (e.g., via LibreOffice headless or cloud conversion).
- Add file type previews and page reordering.
- Add progress indicators for large files and streaming uploads.
# 🎈 Blank app template

A simple Streamlit app template for you to modify!

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://blank-app-template.streamlit.app/)

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```
