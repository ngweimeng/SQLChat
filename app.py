from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI
from langchain.callbacks import StreamlitCallbackHandler
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine
import streamlit as st
import pandas as pd
import os

file_formats = {
    "csv": pd.read_csv,
    "xls": pd.read_excel,
    "xlsx": pd.read_excel,
    "xlsm": pd.read_excel,
    "xlsb": pd.read_excel,
}

def clear_submit():
    """
    Clear the Submit Button State
    Returns:

    """
    st.session_state["submit"] = False


@st.cache_data(ttl="2h")
def load_data(uploaded_file):
    try:
        ext = os.path.splitext(uploaded_file.name)[1][1:].lower()
    except:
        ext = uploaded_file.split(".")[-1]
    if ext in file_formats:
        return file_formats[ext](uploaded_file)
    else:
        st.error(f"Unsupported file format: {ext}")
        return None

st.set_page_config(page_title="SQLChat", page_icon="🧑‍💻")
st.title("🧑‍💻🛢️🌐 SQLChat: Natural Language Queries and Insights via SQL")
# Sidebar with app explanation and GitHub repo link
st.sidebar.title("About SQLChat")
st.sidebar.info(
    """
    **SQLChat** is a web application designed to:

    - **Convert Natural Language to SQL**: Users can input queries in natural language, which the app processes into SQL commands.
    - **Execute SQL Queries**: The app executes these SQL commands on uploaded data files.
    - **Display Insights**: Insights from the SQL queries are displayed back to the user in natural language.

    **Development Stage**: This application is currently in a beta testing phase and may contain errors. Use with caution.

    **Learn More and Contribute**:
    Visit the [GitHub repository](https://github.com/ngweimeng/SQLChat/tree/main) for more details and source code.
    """
)


uploaded_file = st.file_uploader(
    " ",
    type=list(file_formats.keys()),
    help="Various File formats are Supported",
    on_change=clear_submit,
)

if not uploaded_file:
    st.warning(
        "Please note: This application is in a beta testing phase and may contain errors. Use caution in deploying and verify all outputs."
    )

if uploaded_file:
    df = load_data(uploaded_file)
    engine = create_engine("sqlite:///test.db")
    df.to_sql("test", engine, index=False, if_exists='replace')
    db = SQLDatabase(engine=engine)

#openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
if "messages" not in st.session_state or st.sidebar.button("Clear conversation history"):
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input(placeholder="Start your conversation here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    #if not openai_api_key:
    #    st.info("Please add your OpenAI API key to continue.")
    #    st.stop()

    llm = ChatOpenAI(
        temperature=0, model="gpt-3.5-turbo-0613", openai_api_key=st.secrets["openai_api_key"], streaming=True
    )

    sql_db_agent = create_sql_agent(
    llm,
    db=db,  
    agent_type="openai-tools", 
    verbose=True
    )
    
    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
        response = sql_db_agent.run(st.session_state.messages, callbacks=[st_cb])
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.write(response)