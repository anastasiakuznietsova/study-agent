import time
import streamlit as st
import os
import json
import requests
from config import SYSTEM_PROMPT
from helpers_main import add_to_history_user_msg, user_msg_show, show_chat_history, get_llm_responce, process_tools_call, assistant_msg_show


if "messages" not in st.session_state:
    st.session_state.messages = []
if "llm_messages_array" not in st.session_state:
    st.session_state.llm_messages_array = [{
        "role":"system",
        "content":SYSTEM_PROMPT
    }]
os.makedirs("uploads", exist_ok=True)



st.title("Study helper")
show_chat_history()

if prompt := st.chat_input("How can I help you today? ", accept_file=True, accept_audio=False):
    text = prompt.text
    files = prompt.files

    if text == '/end':  st.stop()
    if text == '/raw':
        with st.chat_message("assistant"):
            st.json(st.session_state.messages)
        st.stop()

    user_msg = text
    llm_mgs = text

    if files:
        file_urls = []
        for file in files:
            file_name = file.name
            file_path = os.path.join("uploads", file_name)

            with open(file_path, "wb") as f:
                f.write(file.getbuffer())

            user_msg += "\n\n" + file_name
            llm_mgs += "\n [FILE_PATH]: "+file_path

    user_msg_show(user_msg)

    st.session_state.messages.append(add_to_history_user_msg(user_msg))
    st.session_state.llm_messages_array.append(add_to_history_user_msg(llm_mgs))

while True:
    llm_res = None
    if st.session_state.llm_messages_array[-1]["role"] == "system":    break

    for retry_num in range(5):
        try:
            llm_res = get_llm_responce(st.session_state.llm_messages_array)
        except Exception as e:
            if retry_num == 2:
                st.session_state.llm_messages_array = st.session_state.llm_messages_array[
                                                      :1] + st.session_state.llm_messages_array[-2:]
            if retry_num == 3:
                st.session_state.llm_messages_array = st.session_state.llm_messages_array[
                                                      :1] + st.session_state.llm_messages_array[-1:]
            if retry_num == 4:
                assistant_msg_show("Sorry. The assistant is too dumn for this world. Bye!!")
                st.stop()
            time.sleep(15)
            print(e)
        if llm_res:
            break

    if not llm_res:
        break
    st.session_state.llm_messages_array.append(llm_res)
    st.session_state.messages.append(llm_res)

    llm_tool_calls = llm_res.get("tool_calls")
    if llm_tool_calls:
        tool_calls_history = process_tools_call(llm_tool_calls)
        st.session_state.llm_messages_array.extend(tool_calls_history)
        continue

    content = llm_res.get("content")
    if content:
        assistant_msg_show(content)
    break
