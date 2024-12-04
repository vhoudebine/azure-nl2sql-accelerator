import json
from sqltoolkit.entities import Table
import logging

class DatabaseIndexer:
    def __init__(self, client, openai_client):
        self.client = client
        self.openai_client = openai_client

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def fetch_and_describe_tables(self, table_list: list = None):
        self.logger.info("Fetching tables from the database.")
        tables = json.loads(self.client.list_database_tables())
        if table_list:
            tables = [table.get('TABLE_NAME') for table in tables if table.get('TABLE_NAME') in table_list]
            self.logger.info(f"Filtered tables: {tables}")

        table_manifests = []
        for table_name in tables:
            self.logger.info(f"Processing table: {table_name}")
            table = Table(name=table_name)
            table.get_columns(self.client)
            table.extract_column_values(self.client)
            table.extract_llm_column_definitions(self.openai_client)
            table.get_table_description(self.openai_client)
            table.get_table_readable_name(self.openai_client)
            table_manifests.append(table)
            self.logger.info(f"Completed processing table: {table_name}")

        self.tables = table_manifests
        self.logger.info("Completed fetching and processing all tables.")

        return [t.model_dump() for t in table_manifests]
    
    def generate_table_embeddings(self):
        for table in self.tables:
            table.embedding =  self.openai_client.embeddings.create(input=[table.description], model="text-embedding-3-small").data[0].embedding
    
    def export_json_manifest(self):
        return json.dumps(
            {"tables":[t.model_dump() for t in self.tables]},
              indent=4)
    