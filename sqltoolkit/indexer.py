import json
from sqltoolkit.entities import Table

class DatabaseIndexer:
    def __init__(self, client, openai_client):
        self.client = client
        self.openai_client = openai_client

    def get_tables_manifest(self, table_list: list = None):
        tables = json.loads(self.client.list_database_tables())
        if table_list:
            tables = [table.get('TABLE_NAME') for table in tables if table.get('TABLE_NAME') in table_list]

        table_manifests = []
        for table_name in tables:
            table = Table(name=table_name)
            table.get_columns(self.client)
            table.extract_column_values(self.client)
            table.extract_llm_column_definitions(self.openai_client)
            table.get_table_description(self.openai_client)
            table_manifests.append(table)

        self.tables = table_manifests
        
        return [t.model_dump() for t in table_manifests]
    
    def get_tables_embeddings(self):
        for table in self.tables:
            table.embedding =  self.openai_client.embeddings.create(input=[table.description], model="text-embedding-3-small").data[0].embedding
    
    def get_json_manifest(self):
        return json.dumps({"tables":[t.model_dump() for t in self.tables]})
    