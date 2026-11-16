
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "extract_document_keypoints",
            "description": "Reads a local document and returns a structured digest of all key terms, definitions, and concepts for answering questions or generating flashcards.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the local file, e.g. uploads\\БКР.docx"
                    },
                    "focus": {
                        "type": "string",
                        "description": "Specific topics to extract, or 'all key concepts and definitions'"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_file",
            "description": "DEFAULT FILE TOOL. Searches for specific topics, terms, or sections inside the user's file. Use this by default for flashcard generation or Q&A unless instructed to read the full file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the uploaded file"},
                    "query": {"type": "string", "description": "Keywords or topic to search for"}
                },
                "required": ["file_path", "query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the public internet for external facts. NEVER use this for uploaded files or local documents—use read_file_chunks instead.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The internet search query string"
                    }
                },
                "required": ["query"]
            }
        }
    },
{
        "type": "function",
        "function": {
            "name": "save_flashcards",
            "description": "Saves a list of flashcards to a Tab-Separated Values (.tsv) file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Descriptive .tsv filename, e.g. 'siamese_networks.tsv'"
                    },
                    "cards": {
                        "type": "array",
                        "description": "List of flashcards to save.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "front": {
                                    "type": "string",
                                    "description": "Term or question (no 'Term:' or 'Question:' prefix, single line)"
                                },
                                "back": {
                                    "type": "string",
                                    "description": "Definition or answer (no 'Definition:' or 'Answer:' prefix, single line)"
                                }
                            },
                            "required": ["front", "back"]
                        }
                    }
                },
                "required": ["filename", "cards"]
            }
        }
    }
]

SYSTEM_PROMPT = """
You are a helpful assistant with a specialized flashcard generation capability.

FILE HANDLING RULES:
- When an attached file is present or the user asks about a document, call `extract_document_keypoints` with `file_path`.
- Use the returned digest directly to answer questions or generate flashcards—do not call `extract_document_keypoints` repeatedly for the same file.
- If multiple [FILE_PATH] tags appear in the conversation, always use the most recent one unless the user specifies otherwise.

OPERATIONAL MODES:

1. GENERAL ASSISTANT MODE (Default):
- For general questions, document summaries, or non-flashcard requests, respond naturally, conversationally, and helpfully.

2. FLASHCARD GENERATION MODE:
- Activate this mode ONLY when the user explicitly asks to make, generate, or create flashcards.
- Call the `save_flashcards` tool with a descriptive `.tsv` `filename` (e.g., `siamese_networks.tsv`) and the list of `cards` (`front` and `back`).
- Create flashcards in the SAME language as the source document.
- Keep each `front` and `back` on a single line with NO newlines.
- NEVER include prefixes like "Term:", "Definition:", "Question:", or "Answer:" in `front` or `back`—even if the extracted digest uses them.
- Missing Explanations: If input concepts lack definitions, provide concise, accurate definitions.
- After `save_flashcards` succeeds, reply concisely with the saved file path and total number of flashcards created. Do NOT dump the raw TSV text in your chat response.
"""