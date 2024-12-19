from typing import List, Optional, Any  
from pydantic import BaseModel, Field
from sqltoolkit.client import DatabaseClient
from sqltoolkit.prompts import COLUMN_DEFINITION_PROMPT, TABLE_SUMMARY_PROMPT, TABLE_READABLE_NAME_PROMPT
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
    
    def get_llm_definition(self, table_json, aoai_client, aoai_deployment, extra_context) -> str:
        """Returns the description of the column from the LLM."""
        prompt = COLUMN_DEFINITION_PROMPT.format(column_name=self.name, table_json=table_json, extra_context=extra_context)
        
        messages = [{"role":"system", "content": "You are a data analyst that can help summarize SQL tables."}, 
        {"role": "user", "content": prompt}]

        response = aoai_client.chat.completions.create(
                model=aoai_deployment,
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
  
    def get_table_description(self, aoai_client, aoai_deployment, extra_context) -> str:  
        """Returns the description of the table."""

        table_summary_prompt = TABLE_SUMMARY_PROMPT.format(table_json=self.model_dump(exclude=['db_client']), 
                                                           extra_context=extra_context)

        messages = [{"role":"system", "content": "You are a data analyst that can help summarize SQL tables."}, 
                    {"role": "user", "content": table_summary_prompt}]

        response = aoai_client.chat.completions.create(
                model=aoai_deployment,
                messages=messages)

        response_message = response.choices[0].message.content  
        
        self.description = response_message

    def get_table_readable_name(self, aoai_client, aoai_deployment, extra_context) -> str:
        """Returns the business readable name of the table."""
        table_name = self.name
        table_readable_name_prompt = TABLE_READABLE_NAME_PROMPT.format(
            table_name=table_name,
            extra_context=extra_context,
            table_json=self.model_dump(exclude=['db_client'])
        )

        messages = [{"role":"system", "content": "You are a data analyst that can help summarize SQL tables."}, 
                    {"role": "user", "content": table_readable_name_prompt}]

        response = aoai_client.chat.completions.create(
                model=aoai_deployment,
                messages=messages)

        response_message = response.choices[0].message.content  
        
        self.business_readable_name = response_message

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

    def extract_llm_column_definitions(self, aoai_client, aoai_deployment, extra_context) -> None:
        """Extracts AI generated definitions for each column in the table."""
        table_json = self.json(exclude=['db_client'])
        for column in self.columns:
            column.get_llm_definition(table_json, aoai_client, aoai_deployment, extra_context)
    

  
