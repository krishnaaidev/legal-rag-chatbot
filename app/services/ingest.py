import os
import re
import json
import pdfplumber
from typing import List, Dict, Any
from app.config import settings


def load_text_from_file(file_path: str) -> str:
    """Load text from .txt or .pdf, preserving line breaks."""
    if file_path.endswith(".pdf"):
        text_pages = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_pages.append(page_text)
        return "\n".join(text_pages)
    elif file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {file_path}")


def detect_doc_metadata(filename: str) -> Dict[str, str]:
    """Infer document metadata from filename."""
    name_lower = filename.lower()
    metadata = {
        "doc_type": "statute",
        "jurisdiction": "unknown",
        "effective_date": "unknown"
    }
    if "ipc" in name_lower or "penal" in name_lower:
        metadata.update({"doc_type": "statute", "jurisdiction": "India", "effective_date": "1860-10-06"})
    elif "it_act" in name_lower or "information_technology" in name_lower:
        metadata.update({"doc_type": "statute", "jurisdiction": "India", "effective_date": "2000-06-09"})
    elif "consumer" in name_lower:
        metadata.update({"doc_type": "statute", "jurisdiction": "India", "effective_date": "2019-08-09"})
    elif "gdpr" in name_lower:
        metadata.update({"doc_type": "regulation", "jurisdiction": "EU", "effective_date": "2018-05-25"})
    return metadata


def chunk_legal_document(text: str, source_name: str) -> List[Dict[str, Any]]:
    """
    Structure-aware chunking for real legal PDFs.
    Handles both 'Section 1.' and '1. Title' heading styles.
    """
    # Normalize line breaks
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Try multiple section-heading patterns (real PDFs vary widely)
    patterns = [
        r"(Section\s+\d+[A-Z]?\..*?)(?=\nSection\s+\d+[A-Z]?\.|\Z)",  # "Section 1. Title"
        r"(\n\d+\.\s+[A-Z].*?)(?=\n\d+\.\s+[A-Z]|\Z)",                # "1. Title" (indented)
    ]

    chunks = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        if len(matches) >= 3:  # Accept whichever pattern yields meaningful splits
            for match in matches:
                match = match.strip()
                if len(match) < 20:
                    continue  # Skip too-short fragments

                lines = match.split("\n")
                heading = lines[0].strip()[:200]

                sec_match = re.search(r"(?:Section\s+)?(\d+[A-Z]?)", heading, re.IGNORECASE)
                section_num = sec_match.group(1) if sec_match else "Unknown"

                doc_meta = detect_doc_metadata(source_name)

                chunks.append({
                    "source": source_name,
                    "section": section_num,
                    "heading": heading,
                    "text": match,
                    "char_count": len(match),
                    **doc_meta
                })
            break  # Stop after the first successful pattern

    if not chunks:
        # Fallback: split by paragraph and group ~1500 chars
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        buffer = ""
        for para in paragraphs:
            if len(buffer) + len(para) < 1500:
                buffer += "\n" + para
            else:
                if buffer:
                    chunks.append({
                        "source": source_name,
                        "section": "N/A",
                        "heading": "Unknown",
                        "text": buffer.strip(),
                        "char_count": len(buffer),
                        **detect_doc_metadata(source_name)
                    })
                buffer = para
        if buffer:
            chunks.append({
                "source": source_name,
                "section": "N/A",
                "heading": "Unknown",
                "text": buffer.strip(),
                "char_count": len(buffer),
                **detect_doc_metadata(source_name)
            })

    return chunks


def process_all_documents(output_file_name: str = "chunks.jsonl") -> List[Dict[str, Any]]:
    """Process every .pdf and .txt file in data/raw/."""
    raw_dir = settings.RAW_DATA_DIR
    all_chunks = []

    supported = (".pdf", ".txt")
    files = sorted(f for f in os.listdir(raw_dir) if f.endswith(supported))

    if not files:
        print(f"No documents found in {raw_dir}")
        return []

    for filename in files:
        file_path = os.path.join(raw_dir, filename)
        print(f"\n📄 Processing: {filename}")
        try:
            raw_text = load_text_from_file(file_path)
            print(f"   Extracted {len(raw_text):,} characters.")
            chunks = chunk_legal_document(raw_text, filename)
            print(f"   Created {len(chunks)} semantic chunks.")
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"   ⚠️  Skipped: {e}")

    output_path = os.path.join(settings.PROCESSED_DATA_DIR, output_file_name)
    os.makedirs(settings.PROCESSED_DATA_DIR, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"\n✅ Total chunks: {len(all_chunks)} → {output_path}")
    return all_chunks