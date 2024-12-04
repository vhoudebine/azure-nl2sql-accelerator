from typing import List, Optional, Any  
from pydantic import BaseModel, Field
from sqltoolkit.client import DatabaseClient
import json


class TableColumn(BaseModel):  
    name: str = Field(..., description="The name of the column")  
    type: str = Field(..., description="The data type of the column")
    description: Optional[str] = Field(None, description="A description of the column")
    definition: Optional[str] = Field(None, description="An AI generated description of the column")  
    sample_values: Optional[List[Any]] = Field(None, description="Sample values of the column")
    primary_key: bool = Field(False, description="Indicates if the column is a primary key")  
  
    def get_column_values(self, sql_client, table_name) -> list:  
        """Populates the sample values for the column."""
        values = json.loads(sql_client.get_column_values(table_name, self.name))
        self.sample_values = [ val.get(self.name) for val in values if val.get(self.name) is not None]
    
    def get_llm_definition(self, table_json, aoai_client) -> str:
        """Returns the description of the column from the LLM."""
        prompt = f"""
You are an expert in SQL Entity analysis. You must generate a brief definition for this SQL Column. This definition will be used to generate a SQL query with the correct values. Make sure to include a definition of the data contained in this column.

The definition should be a brief summary of the column as a whole. The definition should be 3-5 sentences long. Apply NO formatting to the definition. The definition should be in plain text without line breaks or special characters.

You will use this definition later to generate a SQL query. Make sure it will be useful for this purpose in determining the values that should be used in the query and any filtering that should be applied.
Do not include column values in the description

### Column to summarize: {self.name}

### Table Schema:
{table_json}
"""
        messages = [{"role":"system", "content": "You are a data analyst that can help summarize SQL tables."}, 
        {"role": "user", "content": prompt}]

        response = aoai_client.chat.completions.create(
                model="gpt-4o-global",
                messages=messages)
        
        response_message = response.choices[0].message.content
        self.definition = response_message

  
class Table(BaseModel):  
    name: str = Field(..., description="The name of the table")
    business_readable_name: Optional[str] = Field(None, description="The business readable name of the table")  
    description: Optional[str] = Field(None, description="A description of the table")  
    columns: Optional[List[TableColumn]] = Field(None, description="The columns of the table")
    embedding: Optional[Any] = Field(None, description="An embedding of the table")

    class Config:  
        arbitrary_types_allowed = True 
  
    def get_table_description(self, aoai_client) -> str:  
        """Returns the description of the table."""

        table_summary_prompt = f"""
        You must generate a brief definition of the table below. The definition will be used to generate a SQL query based on input questions.

        DO NOT list the columns in the definition. The columns will be listed separately. The definition should be a brief summary of the entity as a whole.

        The definition should be 3-5 sentences long. Apply NO formatting to the definition. The definition should be in plain text without line breaks or special characters.

        ===Table Schema

        {self.json(exclude=['db_client'])}

        """

        messages = [{"role":"system", "content": "You are a data analyst that can help summarize SQL tables."}, 
                    {"role": "user", "content": table_summary_prompt}]

        response = aoai_client.chat.completions.create(
                model="gpt-4o-global",
                messages=messages)

        response_message = response.choices[0].message.content  
        
        self.description = response_message

    def get_columns(self, sql_client) -> List[TableColumn]:  
        """Returns the columns of the table."""  
        table_schema = json.loads(sql_client.get_table_schema(self.name))
        column_list = table_schema.get("Columns")
        
        self.columns = [TableColumn(
            name=column["name"],
            type=column["type"],
            primary_key=column["key_type"]=='PRIMARY KEY',
            description=column["column_description"],
        ) for column in column_list]
    
    def extract_column_values(self, sql_client) -> None:  
        """Extracts sample values for each column in the table."""  
        for column in self.columns:  
            column.get_column_values(sql_client, self.name)

    def extract_llm_column_definitions(self, aoai_client) -> None:
        """Extracts AI generated definitions for each column in the table."""
        table_json = self.json(exclude=['db_client'])
        for column in self.columns:
            column.get_llm_definition(table_json, aoai_client)
    

  
