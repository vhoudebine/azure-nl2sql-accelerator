# prompts.py  
  
COLUMN_DEFINITION_PROMPT = """  
You are an expert in SQL Entity analysis. You must generate a brief definition for this SQL Column. This definition will be used to generate a SQL query with the correct values. Make sure to include a definition of the data contained in this column.  
- The definition should be a brief summary of the column as a whole. 
- The definition should be 3-5 sentences long. 
- Apply NO formatting to the definition. 
- The definition should be in plain text without line breaks or special characters.
- The definition should not contain the table name or column name.

## Please use this additional context about the database provided to help make the business readable name more accurate: 
# {extra_context}  

You will use this definition later to generate a SQL query. Make sure it will be useful for this purpose in determining the values that should be used in the query and any filtering that should be applied. Do not include column values in the description  
### Column to summarize: {column_name}  
### Table Schema: {table_json}  
"""  
  
TABLE_SUMMARY_PROMPT = """  
You must generate a brief definition of the table below. The definition will be used to generate a SQL query based on input questions.  
## Please use this additional context about the database provided to help make the business readable name more accurate: {extra_context}  
DO NOT list the columns in the definition. The columns will be listed separately. The definition should be a brief summary of the entity as a whole.  
The definition should be 3-5 sentences long. Apply NO formatting to the definition. The definition should be in plain text without line breaks or special characters.  
===Table Schema  
{table_json}  
"""  
  
TABLE_READABLE_NAME_PROMPT = """  
You are a data analyst that can help generate a business readable name for a SQL table. 
The table name is {table_name}.   
## This is additional context about the database provided to help make the business readable name more accurate: 
{extra_context}  

# YOU MUST FOLLOW THESE INSTRUCTIONS TO COMPLETE THIS TASK:   
# You must generate a business readable name for this table.   
# The business readable name should be a short, descriptive name that is easy to understand and remember.   
# The business readable name should be 2-5 words long.   
# The business readable name should be in plain text without line breaks or special characters.   
# Do not output anything other than the business readable name. Your answer should only contain the business readable name.  
# Here are examples of table names and expected outputs:  
- Table Name: "customer_info_table"  
- Business Readable Name: "Customer Information"  
===Table Schema  
{table_json}  
"""  