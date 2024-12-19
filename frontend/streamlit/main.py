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
from function.db_calls import checking_ai_search_index, check_database_indexing_status, initialize_index_database
from function.aoai_calls import get_sql_query

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
if "aisearch_info" not in st.session_state:
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
if "aoai_responding" not in st.session_state:
    st.session_state["aoai_responding"] = False
if "aoai_response" not in st.session_state:
    st.session_state["ai_response"] = {}

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
                st.session_state["aisearch_info"] = {
                    "endpoint": search_endpoint,
                    "api_key": search_key,
                    "index_name": search_index
                }
                st.info("Checking AI Search Index...")
                index_ready = checking_ai_search_index(st.session_state["aisearch_info"])
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

        if not aoai_endpoint or not aoai_key or not aoai_model_deployment or not aoai_embedding_deployment or not db_type or not db_server or not db_name or not db_username or not db_password:
            st.button('Missing Fields', disabled=True)
        else: 
            if st.button('Index Database', disabled=st.session_state.running, key='run_button'):
                st.session_state["aoai_info"] = {
                    "endpoint": aoai_endpoint,
                    "api_key": aoai_key,
                    "model_deployment": aoai_model_deployment,
                    "embedding_deployment": aoai_embedding_deployment
                }
                st.session_state["database_info"] = {
                    "type": db_type,
                    "server": db_server,
                    "database": db_name,
                    "username": db_username,
                    "password": db_password
                }
                init_index_db_resp = initialize_index_database(
                    aoai_info=st.session_state["aoai_info"],
                    search_info=st.session_state["aisearch_info"],
                    database_info=st.session_state["database_info"]
                )
                if init_index_db_resp == "success":
                    st.info("Database Indexing Started")
                elif init_index_db_resp == "index_already_running":
                    st.info("Database Indexing Already Running")
                else:
                    st.error("An error occurred")

                with st.status("Creating index...", expanded=True) as status:
                    # polling status every 10 seconds until it return 200
                    i = 1
                    while True:
                        index_status = check_database_indexing_status()
                        if index_status == "ready":
                            status.update(label="indexing complete!", state="complete", expanded=False)
                            break
                        elif index_status == "index_already_running":
                            st.write(f"running indexing... {i}")
                            i += 1
                        else:
                            st.error("An error occurred")
                            status.update(label="Error has occurred", state="error", expanded=False)
                            break
                        time.sleep(15)

                st.session_state["stage"] = "chat_with_ai"
                st.success("Database Indexed Successfully")
                if st.button("Proceed to Chat with AI"):
                    st.rerun()
                  
elif st.session_state["stage"] == "chat_with_ai":
    with st.container():
        st.write("Chat with AI")

        # pre filling aoai info if it exists
        chat_aoai_endpoint = st.text_input(
            "Azure OpenAI Endpoint",
            value=st.session_state["aoai_info"].get("endpoint")
        )
        chat_aoai_key = st.text_input(
            "Azure OpenAI API Key",
            type="password",
            value=st.session_state["aoai_info"].get("api_key")
        )
        chat_aoai_model_deployment = st.text_input(
            "Azure OpenAI Model Deployment",
            value=st.session_state["aoai_info"].get("model_deployment")
        )
        
        st.divider()

        # check if all the fields are filled, then render a container if it is
        if not chat_aoai_endpoint or not chat_aoai_key or not chat_aoai_model_deployment:
            st.warning("Please fill in all the fields")
        else:
            with st.container():
                # Ask AI
                col1, col2 = st.columns([7.5, 1.5])
                with col1:
                    user_question = st.text_input("Generate SQL from database...")
                with col2:
                    if st.button("Ask"):
                        st.session_state["aoai_responding"] = True
                        st.session_state["aoai_info"] = {
                            "endpoint": chat_aoai_endpoint,
                            "api_key": chat_aoai_key,
                            "model_deployment": chat_aoai_model_deployment
                        }
                        st.session_state["ai_response"] = get_sql_query(
                            aisearch_info=st.session_state["aisearch_info"],
                            aoai_info=st.session_state["aoai_info"],
                            user_question=user_question
                        )
                # Chat with AI
                with st.container():
                    st.write(st.session_state["ai_response"])