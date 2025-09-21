import streamlit as st
from langgraph_database_backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage
import uuid

# **************************************** utility functions *************************

def generate_thread_id():
    return str(uuid.uuid4())   # keep as string for mapping

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []
    st.session_state['thread_titles'][thread_id] = "New Chat"  # default title

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])

# **************************************** Session Setup ******************************
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

if 'thread_titles' not in st.session_state:   # store titles here
    st.session_state['thread_titles'] = {}

add_thread(st.session_state['thread_id'])
if st.session_state['thread_id'] not in st.session_state['thread_titles']:
    st.session_state['thread_titles'][st.session_state['thread_id']] = "New Chat"

# **************************************** Sidebar UI *********************************
st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversations')

# Make a copy since we may modify chat_threads while iterating
for thread_id in st.session_state['chat_threads'][::-1]:
    cols = st.sidebar.columns([3, 1])  # one wide col for title, one small col for delete button
    title = st.session_state['thread_titles'].get(thread_id, str(thread_id))

    with cols[0]:
        if st.button(title, key=f"select_{thread_id}"):
            st.session_state['thread_id'] = thread_id
            messages = load_conversation(thread_id)

            temp_messages = []
            for msg in messages:
                role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
                temp_messages.append({'role': role, 'content': msg.content})
            st.session_state['message_history'] = temp_messages

    with cols[1]:
        if st.button("🗑", key=f"delete_{thread_id}"):
        # remove from chat_threads
           st.session_state['chat_threads'].remove(thread_id)
        # remove title mapping
           if thread_id in st.session_state['thread_titles']:
              del st.session_state['thread_titles'][thread_id]
        # if current thread deleted, reset to new chat
           if st.session_state['thread_id'] == thread_id:
             reset_chat()
           st.rerun()  # refresh UI

    



# **************************************** Main UI ************************************
# for message in st.session_state['message_history']:
#     with st.chat_message(message['role']):
#         st.text(message['content'])


# --- Theme Switch ---
theme = st.sidebar.radio("Theme", ["Dark", "Light"], index=0)

# --- Chat Styling (with theme support) ---
if theme == "Dark":
    st.markdown(
        """
        <style>
        body {
            background-color: #0e1117;
            color: white;
        }
        .chat-container {
            max-width: 800px;
            margin: auto;
            padding: 20px;
        }
        .user-msg {
            background-color: #005cbb;
            color: white;
            padding: 10px 15px;
            border-radius: 12px;
            margin: 5px 0;
            text-align: left;          
            max-width: 70%;            
            margin-left: auto;         
            margin-right: 0;           
        }
        .ai-msg {
            background-color: #262730;
            color: white;
            padding: 10px 15px;
            border-radius: 12px;
            margin: 5px 0;
            text-align: left;
            max-width: 100%;            
            margin-right: auto;        
            margin-left: 0;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
else:  # Light Mode
    st.markdown(
        """
        <style>
        body {
            background-color: #ffffff;
            color: black;
        }
        .chat-container {
            max-width: 800px;
            margin: auto;
            padding: 20px;
        }
        .user-msg {
            background-color: #1976d2;
            color: white;
            padding: 10px 15px;
            border-radius: 18px 18px 4px 18px;
            margin: 5px 0;
            text-align: left;          
            max-width: 70%;            
            margin-left: auto;         
            margin-right: 0;           
        }
        .ai-msg {
            background-color: #f1f1f1;
            color: black;
            padding: 10px 15px;
            border-radius: 18px 18px 18px 4px;
            margin: 5px 0;
            text-align: left;
            max-width: 100%;            
            margin-right: auto;        
            margin-left: 0;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# --- Chat Display (unchanged) ---
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

for message in st.session_state['message_history']:
    if message['role'] == 'user':
        st.markdown(f"<div class='user-msg'>{message['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai-msg'>{message['content']}</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)


user_input = st.chat_input('Type here')

if user_input:
    # update thread title if still default
    if st.session_state['thread_titles'][st.session_state['thread_id']] == "New Chat":
        st.session_state['thread_titles'][st.session_state['thread_id']] = user_input[:30]  # first 30 chars

    # add user input
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata": {"thread_id": st.session_state["thread_id"]},
        "run_name": "chat_turn",
    }

    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            message_chunk.content for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
        )

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
