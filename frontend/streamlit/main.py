from dotenv import load_dotenv
import os 
import requests
from openai import AzureOpenAI
import pandas as pd
import streamlit as st
import pyodbc, struct
from sqlalchemy import create_engine
import urllib
import json
import io
# import matplotlib.pyplot as plt
import numpy as np
import time
from azure.identity import DefaultAzureCredential
from function.db_calls import checking_ai_search_index

load_dotenv(override=True)

# variable
api_endpoint = "http://localhost:8000/api/v1"

def create_booklet():
    st.session_state["stage"] = "final_parameters"

def final_parameters():
    st.session_state["stage"] = "story_generation"

#sessions
if "stage" not in st.session_state:
    st.session_state["stage"] = "ai_search_index"
if "ai_search_index_info" not in st.session_state:
    st.session_state["ai_search_index_info"] = {}
if "aoai_info" not in st.session_state:
    st.session_state["aoai_info"] = {}
if "database_info" not in st.session_state:
    st.session_state["database_info"] = {}
if "database_is_indexed" not in st.session_state:
    st.session_state["database_is_indexed"] = False
if 'run_button' in st.session_state and st.session_state.run_button == True:
    st.session_state.running = True
else:
    st.session_state.running = False

if st.session_state["stage"] == "ai_search_index":
    with st.container():
        # text box for user to input search query with label
        search_endpoint = st.text_input(
            "Azure AI Search Endpoint",
            value="https://jhl-search-s1.search.windows.net"
        )
        # password input for search_key
        search_key = st.text_input("Azure AI Search API Key", type="password")
        search_index = st.text_input(
            "Azure AI Search Index Name",
            value="adventureworks"
        )

        if st.button("Check AI Search"):
            if not search_endpoint or not search_key or not search_index:
                st.warning("Please fill in all the fields")
            else:
                st.session_state["ai_search_index_info"] = {
                    "search_endpoint": search_endpoint,
                    "search_key": search_key,
                    "search_index": search_index
                }
                st.info("Checking AI Search Index...")
                index_ready = checking_ai_search_index(st.session_state["ai_search_index_info"])
                print(index_ready)
                if index_ready == "ready":
                    st.session_state["stage"] = "chat_with_ai"
                    st.success("Index is ready")
                    if st.button("Proceed to Chat with AI"):
                        st.rerun()
                elif index_ready == "index_already_running":
                    st.warning("Indexing is already running, please check after couple of minutes")
                elif index_ready == "index_not_found":
                    st.session_state["stage"] = "index_database"
                    st.warning("Index does not exist or has no data")
                    if st.button("Index Database"):
                        st.rerun()
                else:
                    st.error("An error occurred")

elif st.session_state["stage"] == "index_database":
    with st.container():
        st.write("Index Database")
        # text box for user to input search query with label
        st.divider()
        st.write('Azure Openai Information')
        aoai_endpoint = st.text_input(
            "Azure OpenAI Endpoint",
            value="https://jhl-aoai-west.openai.azure.com/"
        )
        aoai_key = st.text_input(
            "Azure OpenAI API Key",
            type="password"
        )
        aoai_model_deployment = st.text_input(
            "Azure OpenAI Model Deployment",
            value="gpt-4o-global"
        )
        aoai_embedding_deployment = st.text_input(
            "Azure OpenAI Embedding Deployment",
            value="text-embedding-3-small"
        )
        st.divider()
        st.write('Database Information')
        # drop down to select database type
        db_type = st.selectbox(
            "Database Type",
            ["AZURESQL", "MYSQL"]
        )
        db_server = st.text_input(
            "Database Server",
            value="jhl-sql-server.database.windows.net"
        )
        db_name = st.text_input(
            "Database Name",
            value="jhl-sql-db-sample"
        )
        db_username = st.text_input(
            "Database Username",
            value="jhladmin"
        )
        db_password = st.text_input(
            "Database Password",
            type="password"
        )
        st.divider()

        if st.button('Index Database', disabled=st.session_state.running, key='run_button'):
            with st.status("Downloading data...", expanded=True) as status:
                st.write("Searching for data...")
                time.sleep(2)
                st.write("Found URL.")
                time.sleep(1)
                st.write("Downloading data...")
                time.sleep(1)
                status.update(
                    label="Download complete!", state="complete", expanded=False
                )





     

elif st.session_state["stage"] == "chat_with_ai":
    with st.container():
        st.write("Chat with AI")