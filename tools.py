import urllib.parse
from ddgs import DDGS
import time
import os
import json
import csv
import pypdf
import requests
import docx


GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FILE_DIR = 'uploads/'

def get_file_text(file_path: str) -> str:
    file_path = os.path.normpath(file_path)
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' not found."
    try:
        if file_path.endswith((".py", ".md", ".txt", ".json")):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        elif file_path.endswith(".pdf"):
            reader = pypdf.PdfReader(file_path)
            text = []

            for i, page in enumerate(reader.pages):
                extracted = page.extract_text()
                if extracted:
                    text.append(f"--- Page {i + 1} ---\n{extracted}")

            content = "\n".join(text) if text else "PDF contains no selectable text."
        elif file_path.endswith(".docx"):
            doc = docx.Document(file_path)
            full_text = []

            for p in doc.paragraphs:
                if p.text.strip():
                    full_text.append(p.text.strip())

            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_text:
                        full_text.append(" | ".join(row_text))

            content = "\n".join(full_text)
        else:
            return "Unsupported file type."
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

def extract_document_keypoints(file_path: str, focus: str = "all key terms, definitions, formulas, and core concepts") -> str:
    full_text = get_file_text(file_path)

    payload = {
        "model": "gemini-3.5-flash-lite",
        "temperature": 0.1,
        "messages": [
            {
                "role": "system",
                "content": ("""
                    You are a technical document extractor. Extract a comprehensive, dense list of key concepts, terms, definitions, methods, and facts from the provided text. 
                    Keep the exact language of the source document (e.g., Ukrainian). Preserve technical accuracy and omit filler.
                """),
            },
            {
                "role": "user",
                "content": f"Focus: {focus}\n\nDOCUMENT TEXT:\n{full_text}",
            },
        ],
    }

    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json",
    }
    res = None
    for retry_num in range(3):
        try:
            res = requests.post(GEMINI_URL, headers=headers, json=payload, timeout=60)
        except Exception as e:
            print(e)
            time.sleep(5)
        if res:
            break
    if not res:
        print(f"[Reader fallback triggered]")
        return full_text[:12000]

    data = res.json()

    if res.status_code == 200 and "choices" in data:
        return data["choices"][0]["message"]["content"]

    err = data.get("error", {}).get("message", res.text)
    print(f"[Reader fallback triggered]: {err}")
    return full_text[:12000]

def read_file(file_path: str) -> str:
    full_text = get_file_text(file_path)
    if len(full_text)>4000:
        return f"The file content was too long. Truncated from {len(full_text)} to first 4000 characters. Truncated text: {full_text[:4000]}"
    return full_text

def search_in_file(file_path: str, query: str) -> str:
    full_text = read_file(file_path)
    paragraphs = full_text.split("\n\n")

    matches = [p for p in paragraphs if query.lower() in p.lower()]

    if not matches:
        return f"No results found for query '{query}'."
    return "\n---\n".join(matches)


def flashcards_to_file(tsv_input:str, filename: str = "flashcards.tsv") -> str:
    cleaned = tsv_input.strip().removeprefix("```tsv").removeprefix("```").removesuffix("```").strip()

    if not filename.endswith(".tsv"):
        filename += ".tsv"
    path = os.path.join(FILE_DIR, filename)

    rows = [line.split("\t") for line in cleaned.splitlines() if line.strip()]

    with open(path, "w", newline="", encoding="utf-8") as f:
        tsv_writer = csv.writer(f, delimiter="\t")
        tsv_writer.writerows(rows)

    return path


def web_search(query: str, max_results: int = 3) -> str:
    time.sleep(1)
    try:
        results = list(DDGS().text(query, max_results=max_results))
        if not results:
            encoded_query = str(urllib.parse.quote(query))
            return (
                f"No direct page snippets found.\n"
                f"YouTube Link: https://www.youtube.com/results?search_query={encoded_query}\n"
            )

        output = []
        for r in results:
            title = r.get('title', '')
            url = r.get('href', '')
            snippet = r.get('body', '')[:200]
            output.append(f"Title: {title}\nURL: {url}\nSnippet: {snippet}...\n")

        return "\n---\n".join(output)

    except Exception as e:
        return f"Error executing search: {str(e)}"

