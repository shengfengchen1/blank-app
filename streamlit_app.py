import os
import io
import tempfile
from typing import List

import streamlit as st
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

try:
    import psycopg2
    from psycopg2 import Binary
except Exception:
    psycopg2 = None

from dotenv import load_dotenv

load_dotenv()


def create_pdf_from_text(text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    margin = 40
    y = height - margin
    line_height = 12
    for line in text.splitlines():
        if y < margin:
            c.showPage()
            y = height - margin
        c.drawString(margin, y, line)
        y -= line_height
    c.save()
    buf.seek(0)
    return buf.read()


def convert_image_to_pdf_bytes(image_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode in ("RGBA", "LA"):
        img = img.convert("RGB")
    pdf_bytes = io.BytesIO()
    img.save(pdf_bytes, format="PDF")
    pdf_bytes.seek(0)
    return pdf_bytes.read()


def combine_uploaded_files(files: List[st.runtime.uploaded_file_manager.UploadedFile]) -> bytes:
    writer = PdfWriter()
    warnings = []
    for uploaded in files:
        name = uploaded.name.lower()
        data = uploaded.read()
        if name.endswith(".pdf"):
            try:
                reader = PdfReader(io.BytesIO(data))
                for page in reader.pages:
                    writer.add_page(page)
            except Exception as e:
                warnings.append(f"Failed to read PDF {uploaded.name}: {e}")
        elif any(name.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif")):
            try:
                pdf_bytes = convert_image_to_pdf_bytes(data)
                reader = PdfReader(io.BytesIO(pdf_bytes))
                for page in reader.pages:
                    writer.add_page(page)
            except Exception as e:
                warnings.append(f"Failed to convert image {uploaded.name}: {e}")
        elif name.endswith(".txt"):
            try:
                pdf_bytes = create_pdf_from_text(data.decode("utf-8", errors="replace"))
                reader = PdfReader(io.BytesIO(pdf_bytes))
                for page in reader.pages:
                    writer.add_page(page)
            except Exception as e:
                warnings.append(f"Failed to convert text {uploaded.name}: {e}")
        else:
            warnings.append(f"Skipping unsupported file type: {uploaded.name}")

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.getvalue(), warnings


def call_db_procedure(pdf_bytes: bytes) -> str:
    """
    Calls a PostgreSQL stored procedure / function to generate a summary.

    Assumes a function name (default: generate_summary) that accepts a bytea and returns text.
    Configure via environment variables: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_PROC_NAME
    """
    if psycopg2 is None:
        return "psycopg2 not installed; cannot call DB procedure."

    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    proc = os.getenv("DB_PROC_NAME", "generate_summary")

    if not all([host, dbname, user, password]):
        return "Database connection info incomplete; set DB_HOST, DB_NAME, DB_USER, DB_PASSWORD."

    try:
        conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
        cur = conn.cursor()
        # NOTE: function name can't be passed as a parameter; ensure proc is a safe identifier in your env
        sql = f"SELECT {proc}(%s);"
        cur.execute(sql, (Binary(pdf_bytes),))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return row[0] if row[0] is not None else "(no summary returned)"
        return "(no result)"
    except Exception as e:
        return f"DB call failed: {e}"


def main():
    st.set_page_config(page_title="Document Combiner & Summarizer", layout="centered")
    st.title("Document Merge & Consistency Check")

    st.markdown("Upload multiple PDFs. Click 'Combine & AICheck' to create a single PDF and check for field consistencies.")

    uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True)

    call_db = st.checkbox("Call DB stored procedure to summarize combined PDF (requires DB env vars)")

    if "combined_pdf" not in st.session_state:
        st.session_state["combined_pdf"] = None
        st.session_state["summary"] = ""

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Combine & Summarize"):
            if not uploaded_files:
                st.warning("Please upload one or more files first.")
            else:
                with st.spinner("Combining files..."):
                    combined_bytes, warnings = combine_uploaded_files(uploaded_files)
                    st.session_state["combined_pdf"] = combined_bytes
                if warnings:
                    for w in warnings:
                        st.warning(w)

                if call_db:
                    with st.spinner("Calling DB to generate summary..."):
                        summary = call_db_procedure(combined_bytes)
                        st.session_state["summary"] = summary
                else:
                    st.info("DB call skipped (checkbox not selected).")

    with col2:
        if st.session_state.get("combined_pdf"):
            st.download_button("Download combined PDF", data=st.session_state["combined_pdf"], file_name="combined.pdf", mime="application/pdf")

    st.header("Summary")
    st.text_area("AI / DB Summary", value=st.session_state.get("summary", ""), height=200)


if __name__ == "__main__":
    main()
