# my_module/sample_class.py
import struct
import pyodbc
from azure.identity import DefaultAzureCredential
import psycopg2
from psycopg2 import OperationalError
import snowflake.connector


class AzureSQLConnector:
    def __init__(self, server: str, database: str, use_entra_id: bool = True, username: str = None, password: str = None):
        self.type = 'AZURE_SQL'
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
        
class PostgreSQLConnector:
    def __init__(self, host: str, database: str, username: str, password: str, port: int = 5432):
        self.type = 'POSTGRESQL'
        self.connection_string = f"dbname='{database}' user='{username}' password='{password}' host='{host}' port='{port}'"

    def get_conn(self):
        try:
            conn = psycopg2.connect(self.connection_string)
            return conn
        except OperationalError as e:
            raise RuntimeError(f"Error connecting to PostgreSQL Database: {e}")

class OdbcConnector:
    def __init__(self, connection_string: str):
        self.type = 'ODBC'
        self.connection_string = connection_string

    def get_conn(self):
        try:
            conn = pyodbc.connect(self.connection_string)
            return conn
        except pyodbc.Error as e:
            raise RuntimeError(f"Error connecting to Database: {e}")

class SnowflakeConnector:
    def __init__(self, user: str, password: str, account: str, warehouse: str, database: str, schema: str, role: str = None, **kwargs):
        """
        Initialize a Snowflake connector.
        
        Required parameters:
          - user: Snowflake username.
          - password: Snowflake password.
          - account: Snowflake account identifier.
          - warehouse: Warehouse name.
          - database: Database name.
          - schema: Schema name.
        
        Optional:
          - role: Snowflake role.
          - kwargs: Additional parameters for snowflake.connector.connect.
        """
        self.type = 'SNOWFLAKE'
        self.connection_params = {
            'user': user,
            'password': password,
            'account': account,
            'warehouse': warehouse,
            'database': database,
            'schema': schema,
        }
        if role:
            self.connection_params['role'] = role
        # Include any additional optional parameters
        self.connection_params.update(kwargs)
    
    def get_conn(self):
        """
        Establish and return a connection to Snowflake.
        """
        try:
            conn = snowflake.connector.connect(**self.connection_params)
            return conn
        except Exception as e:
            raise RuntimeError(f"Error connecting to Snowflake: {e}")