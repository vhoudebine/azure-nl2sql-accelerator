# my_module/sample_class.py
import struct
import pyodbc
from azure.identity import DefaultAzureCredential

class AzureSQLConnector:
    def __init__(self, server: str, database: str, use_entra_id: bool = True, username: str = None, password: str = None):
        self.use_entra_id = use_entra_id
        if use_entra_id:
            self.connection_string = f'Driver={{ODBC Driver 18 for SQL Server}};Server=tcp:{server},1433;Database={database};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
        else:
            if not username or not password:
                raise ValueError("Username and password must be provided for user password authentication.")
            self.connection_string = f'Driver={{ODBC Driver 18 for SQL Server}};Server=tcp:{server},1433;Database={database};Uid={username};Pwd={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'

    def get_conn(self):
        try:
            if self.use_entra_id:
                credential = DefaultAzureCredential(exclude_interactive_browser_credential=False)
                token_bytes = credential.get_token("https://database.windows.net/.default").token.encode("UTF-16-LE")
                token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
                SQL_COPT_SS_ACCESS_TOKEN = 1256
                conn = pyodbc.connect(self.connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
            else:
                conn = pyodbc.connect(self.connection_string)
            return conn
        except pyodbc.Error as e:
            raise RuntimeError(f"Error connecting to Azure SQL Database: {e}")

class OdbcConnector:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def get_conn(self):
        try:
            conn = pyodbc.connect(self.connection_string)
            return conn
        except pyodbc.Error as e:
            raise RuntimeError(f"Error connecting to Database: {e}")
