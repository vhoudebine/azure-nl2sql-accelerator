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