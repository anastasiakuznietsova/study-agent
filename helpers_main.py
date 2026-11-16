import streamlit as st
import json
import requests
from config import TOOLS
from tools import web_search, search_in_file, extract_document_keypoints, save_flashcards
import os


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
        if '\t' in msg:
            render_quizlet_export(msg)
            # st.code(msg, language="text")
        else:
            st.markdown(msg)

def show_chat_history():
    for message in st.session_state.get("messages", []):
        if isinstance(message, dict) and message.get("role") in ["user", "assistant"] and message.get("content"):
            content = message["content"]
            with st.chat_message(message["role"]):
                if message["role"] == "assistant" and "\t" in content:
                    st.code(content, language=None)
                else:
                    st.markdown(content)
        else:
            print("ERROR: ", message)


def get_llm_responce(messages):
    request = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.2,
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
    print(tools)
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
        elif tool_name == "save_flashcards":
            filename = tool_args.get("filename")
            cards = tool_args.get("cards")
            if not filename or not cards:
                data = "Error: 'filename' and 'cards' are required."
            else:
                data = save_flashcards(filename, cards)
            tool_calls_history.append(
                add_to_history_tool_msg(tool_name=tool_name, tool_call_id=tool_call_id, content=data)
            )

    return tool_calls_history

def render_quizlet_export(tsv_text: str):
    st.caption("1. Copy the TSV below → 2. Open Quizlet → 3. Click **+ Import** and paste.")
    st.code(tsv_text, language=None)
    st.link_button("Open Quizlet Set Creator ↗", "https://quizlet.new")