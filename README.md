# azure-nl2sql-accelerator
Accelerator to interact with database in natural language

## Sqltoolkit
detail description of sqltoolkit tba

## Backend
the backend is written in python fastapi.\
backend is currently designed to take in all the required information (such as Azure OpenAI Api Keys, Azure AI Search information) instead of loading it from env variables

#### getting started with backend

1. change the directory to backend and install all the requirements
    ```
      cd backend
      pip install -r requirements.txt
    ```
2. go to the app directory
    ```
        cd app
    ```
3. run the fastapi application in dev mode
    ```
        fastapi dev main.py
    ```
4. to see the api definition, open the browser and move to http://localhost:8000/docs

## Frontend
you can attach any frontend application to call the backend api\
on this repo, we will be using streamlit to render a simple single page app.

#### getting started with frontend

1. move to streamlit app directory
    ```
        cd frontend/streamlit
        pip install -r requiements.txt
    ```
2. run the streamlit app
    ```
        streamlit run main.py
    ```
