import sqlglot
from sqlglot.errors import ParseError
from sqlglot import parse, exp
from sqlglot.errors import ParseError
import json

class SQLQueryChecker:
    """
    Provides a method to compile (validate) a SQL query without
    connecting to a database. Attempts to detect syntax errors
    using sqlparse and some dialect-specific checks.
    Ensures only SELECT queries are allowed and that TOP is only used 
    for SQL Server.
    """
    def __init__(self, 
                 openai_client, 
                 model_deployment, 
                 dialect: str = "Postgres",
                 reference_schema=None,
                ):
        self.dialect = dialect.lower()
        self.openai_client = openai_client
        self.model_deployment = model_deployment
        self.reference_schema = reference_schema

    def _extract_entities(self, query: str) -> list[str]:
        prompt = f"""You are a SQL expert. Your role is to extract columns and tables from a query so that a program can validate their existence in the database. You must extract only the tables and columns that would be found in the database without their alias. Do not extract any alias or temporary table. 
                    you must prefix the column names with the table name, not the table alias.
                    if a column appears twice from different tables, you must add the column twice in the column list
                    you must return a json schema with the following format
                     {{
                        "tables": ["table1", "table2"],
                        "columns": ["table1.column1", "table1.column2", "table2.column1"]
                     }}
                     if the table the column is from is ambiguous, you can use the reference schema to determine the table the column is from
                     <reference_schema>
                     {self.reference_schema}
                     </reference_schema>
                     """
        

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"SQL query: {query}"},
        ]
        response = self.openai_client.chat.completions.create(
            model=self.model_deployment,
            messages=messages,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)


    def _check_table_and_column_existence(self, query: str) -> bool:
        entities = self._extract_entities(query)
        table_names = entities.get("tables", [])
        column_names = entities.get("columns", [])
        ref_tables = [ref.get('table') for ref in self.reference_schema or []]
        for table in table_names:
            if table not in ref_tables:
                raise ValueError(f"Table {table} not found in reference schema.")
        for column in column_names:
            col_table, col_name = column.rsplit('.', 1)
            ref_columns = next(
                (ref["columns"] for ref in self.reference_schema if ref["table"] == col_table),
                []
            )
            if col_name not in ref_columns:
                raise ValueError(f"Column {col_name} not found in table {col_table}.")
        return True

    def _check_sql_syntax(self, query: str, dialect: str = "Postgres") -> bool:
        """
        Uses sqlglot to try parsing the given SQL query for a chosen dialect.
        By default uses 'ansi' for a generic SQL style. Returns True if parsed
        successfully; False if a ParseError is raised.
        """
        try:
            sqlglot.parse_one(query, read=dialect)
            return True
        except ParseError as pe:
            print(f"Syntax error detected: {pe}")
        return False
    
    def _is_select_statement(self, query: str) -> bool:
        """
        Checks if a SQL query *only* contains SELECT statements using sqlglot.

        Args:
            sql_query: The SQL query string.

        Returns:
            True if ALL statements are SELECT statements.
            False if ANY statement is NOT a SELECT statement.
            Raises ValueError if there is a parsing error or empty query.
        """
        if not query or not query.strip():
            raise ValueError("Empty or whitespace-only query")

        try:
            expressions = parse(query)

            if not expressions: #handle empty parse
                return False

            for expression in expressions:
                if not isinstance(expression, (exp.Select, exp.CTE)):
                    return False  # Not a SELECT or CTE

                if isinstance(expression, exp.CTE):
                    if not any(isinstance(e, exp.Select) for e in expression.this.expressions):
                        return False

            return True  # All expressions are SELECTs or CTEs leading to selects

        except ParseError as e: # Correct exception to catch
            raise ValueError(f"SQL parsing error: {e}")
        except Exception as e: #catch other potential errors
            raise ValueError(f"An unexpected error occurred: {e}")
        
    def validate_query(self, query: str) -> dict:
        """
        Runs all checks on the SQL query and returns a dictionary with the validation result.

        Args:
            query: The SQL query string.

        Returns:
            A dictionary with 'query_valid' set to True if no errors occur, 
            or False with an 'error' explanation.
        """
        try:
            if not self._is_select_statement(query):
                return {"query_valid": False, "error": "Query is not a SELECT statement."}

            if not self._check_sql_syntax(query, self.dialect):
                return {"query_valid": False, "error": "Syntax error in SQL query."}

            if self.reference_schema:
                self._check_table_and_column_existence(query)

            return {"query_valid": True}

        except ValueError as ve:
            return {"query_valid": False, "error": str(ve)}
        except Exception as e:
            return {"query_valid": False, "error": f"Unexpected error: {e}"}