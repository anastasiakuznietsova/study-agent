import streamlit as st
import json
import requests
import re
from config import TOOLS
from tools import web_search, search_in_file, extract_document_keypoints, flashcards_to_file
import os
import re
import time


API_KEY= os.getenv("API_KEY")
MODEL_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "openai/gpt-oss-20b"

def add_to_history_user_msg(content):
    return {
        "role":"user",
        "content":content
    }

def add_to_history_tool_msg(tool_name, tool_call_id, content):
    return {
        "role": "tool",
        "name": tool_name,
        "tool_call_id": tool_call_id,
        "content": content
    }

def user_msg_show(msg):
    with st.chat_message("user"):
        st.markdown(msg)
def assistant_msg_show(msg):
    with st.chat_message("assistant"):
        if '```' in msg:
            idx = len(st.session_state.get("messages", [])) - 1
            render_quizlet_export(msg, idx)
            # st.code(msg, language="text")
        else:
            st.markdown(msg)

def show_chat_history():
    for idx, message in enumerate(st.session_state.get("messages", [])):
        if isinstance(message, dict) and message.get("role") in ["user", "assistant"] and message.get("content"):
            content = message["content"]
            with st.chat_message(message["role"]):
                if message["role"] == "assistant" and "```" in content:
                    render_quizlet_export(content, idx)
                elif "tsv_path" in message:
                    st.markdown(content)
                    with open(message["tsv_path"], "rb") as f:
                        st.download_button(
                            label=f"Download {os.path.basename(message['tsv_path'])}",
                            data=f,
                            file_name=os.path.basename(message["tsv_path"]),
                            mime="text/tab-separated-values",
                            key=f"dl_{idx}",
                        )
                else:
                    st.markdown(content)
        else:
            continue


def get_llm_responce(messages):
    request = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 3500,
        "reasoning_effort": "low",
        "include_reasoning": False,
        "tools": TOOLS,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    llm_responce = requests.post(
        url=MODEL_URL,
        headers=headers,
        json = request
    ).json()

    if "error" in llm_responce:
        raise Exception(llm_responce.get('error'))
    return llm_responce['choices'][0]['message']


def process_tools_call(tools):
    tool_calls_history = []
    # print(tools)
    for tool in tools:

        tool_call_id = tool["id"]
        tool_name = tool["function"]["name"]
        tool_args = json.loads(tool["function"]["arguments"])

        if tool_name == "web_search":
            q = tool_args.get("query")
            if not q: continue
            data = web_search(q)
            tool_calls_history.append(add_to_history_tool_msg(tool_name = tool_name, tool_call_id=tool_call_id, content=data))
        elif tool_name == "extract_document_keypoints":
            file_path = tool_args.get("file_path")
            if not file_path: continue
            data = extract_document_keypoints(file_path)
            tool_calls_history.append(add_to_history_tool_msg(tool_name = tool_name, tool_call_id=tool_call_id, content=data))
        elif tool_name == "search_in_file":
            file_path = tool_args.get("file_path")
            file_query = tool_args.get("query")
            if not file_path or not file_query: continue
            data = search_in_file(file_path, file_query)
            tool_calls_history.append(add_to_history_tool_msg(tool_name=tool_name, tool_call_id=tool_call_id, content=data))
        elif tool_name == "flashcards_to_file":
            filename = tool_args.get("filename") or "flashcards.tsv"
            tsv_input = tool_args.get("tsv_input")
            if not tsv_input: continue
            data = flashcards_to_file(tsv_input=tsv_input, filename=filename)
            tool_calls_history.append(add_to_history_tool_msg(tool_name=tool_name, tool_call_id=tool_call_id, content=data))

    return tool_calls_history

def render_quizlet_export(tsv_text: str, idx: int = 0):
    match = re.search(r"```(?:[^\n]*\r?\n)?(.*?)(?:```|$)", tsv_text, re.DOTALL)
    cleaned = match.group(1).strip() if match else tsv_text.strip()

    st.caption("1. Copy for Quizlet → 2. Or download `.tsv` for Anki.")
    st.code(cleaned, language=None)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Download .tsv (Anki)",
            data=cleaned.encode("utf-8"),
            file_name="flashcards.tsv",
            mime="text/tab-separated-values",
            key=f"quizlet_dl_{idx}",
        )
    with col2:
        st.link_button("Open Quizlet Set Creator ↗", "https://quizlet.new")