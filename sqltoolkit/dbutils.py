import json  
import pandas as pd  
  
class DatabaseUtils:  
    def __init__(self, connector):  
        self.connector = connector  
        self.connection = self.connector.get_conn()
  
    @staticmethod  
    def convert_datetime_columns_to_string(df: pd.DataFrame) -> pd.DataFrame:  
        for column in df.columns:  
            if pd.api.types.is_datetime64_any_dtype(df[column]):  
                df[column] = df[column].astype(str)  
        return df  
  
    def list_database_tables(self) -> str:  
        query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"  
        df = pd.read_sql(query, self.connection)  
        return json.dumps(df.to_dict(orient='records'))  
  
    def query(self, query: str) -> str:  
        df = pd.read_sql(query, self.connection)  
        df = self.convert_datetime_columns_to_string(df)  
        return json.dumps(df.to_dict(orient='records'))  
  
    def get_table_schema(self, table_name: str) -> str:  
        query = f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'"  
        df = pd.read_sql(query, self.connection)  
        return json.dumps(df.to_dict(orient='records'))  
  
    def get_table_rows(self, table_name: str) -> str:  
        query = f"SELECT TOP 3 * FROM {table_name}"  
        df = pd.read_sql(query, self.connection)  
        df = self.convert_datetime_columns_to_string(df)  
        return df.to_markdown()  
  
    def get_column_values(self, table_name: str, column_name: str) -> str:  
        query = f"SELECT DISTINCT TOP 50 {column_name} FROM {table_name} ORDER BY {column_name}"  
        df = pd.read_sql(query, self.connection)  
        df = self.convert_datetime_columns_to_string(df)  
        return json.dumps(df.to_dict(orient='records'))
    
    def get_available_tools(self) -> str:
        return {
            "list_database_tables": self.list_database_tables,
            "query": self.query,
            "get_table_schema": self.get_table_schema,
            "get_table_rows": self.get_table_rows,
            "get_column_values": self.get_column_values
        }
    
    def get_tools_manifest(self) -> str:
        return [
        {
            "type": "function",
            "function": {
                "name": "query_azure_sql",
                "description": "Execute a SQL query to retrieve information from a database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SQL query to execute",
                        },
                    },
                    "required": ["query"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_table_schema",
                "description": "Get the schema of a table in Azure SQL",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "The name of the table to get the schema for",
                        },
                    },
                    "required": ["table_name"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_table_rows",
                "description": "Preview the first 5 rows of a table in Azure SQL",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "The name of the table to get the preview for",
                        },
                    },
                    "required": ["table_name"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_column_values",
                "description": "Get the unique values of a column in a table in Azure SQL, only use this if the main query has a WHERE clause",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "The name of the table to get the column values for",
                        },
                        "column_name": {
                            "type": "string",
                            "description": "The name of the column to get the values for",
                        },
                    },
                    "required": ["table_name", "column_name"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "agent_query_validator",
                "description": "Validate a SQL query for common mistakes, always call this before calling query_azure_sql",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SQL query to validate",
                        }
                    },
                    "required": ["query"],
                },
            }
        },
        {"type": "function",
            "function":{
                "name": "plot_data",
                "description": "plot one or multiple timeseries of data points as a line chart, returns a mardown string",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "string",
                            "description": """A JSON string containing the different data series and timestamp axis with the following format:
                            {"timestamp": ["2022-01-01", "2022-01-02", "2022-01-03"],
                            "series1": [10, 20, 30],
                            "series2": [15, 25, 35]}
                            """,
                        },
                    },
                    "required": ["data"],
                },
            }
        }

    ]