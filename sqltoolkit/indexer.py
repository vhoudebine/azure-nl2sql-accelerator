import json
from sqltoolkit.entities import Table
import logging
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes.models import (
    SimpleField,
    ComplexField,
    SearchFieldDataType,
    SearchableField,
    SearchField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SemanticSearch,
    SearchIndex,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters
)
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
import re

class DatabaseIndexer:
    def __init__(self, client, openai_client, aoai_deployment, embedding="text-embedding-3-small", extra_context=None):
        self.client = client
        self.openai_client = openai_client
        self.aoai_deployment = aoai_deployment
        self.embedding = embedding
        self.extra_context = extra_context
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.propagate = False

    def fetch_and_describe_tables(self, table_list: list = None, regex_filter: str = None):

        self.logger.info("Fetching tables from the database.")
        tables = json.loads(self.client.list_database_tables())
        
        if table_list:
            tables = [table.get('TABLE_NAME') for table in tables if table.get('TABLE_NAME') in table_list]
            self.logger.info(f"Filtered tables by list: {tables}")
        else:
            tables = [table_dict.get('TABLE_NAME') for table_dict in tables]
        
        if regex_filter:
            pattern = re.compile(regex_filter)
            tables = [table for table in tables if pattern.match(table)]
            self.logger.info(f"Filtered tables by regex: {tables}")

        table_manifests = []
        for table_name in tables:
            self.logger.info(f"Processing table: {table_name}")
            table = Table(name=table_name)
            table.get_columns(self.client)
            table.extract_column_values(self.client)
            table.extract_llm_column_definitions(self.openai_client, self.aoai_deployment, self.extra_context)
            table.get_table_description(self.openai_client, self.aoai_deployment, self.extra_context)
            table.get_table_readable_name(self.openai_client, self.aoai_deployment, self.extra_context)
            table_manifests.append(table)
            self.logger.info(f"Completed processing table: {table_name}")

        self.tables = table_manifests
        self.logger.info("Completed fetching and processing all tables.")

        return [t.model_dump() for t in table_manifests]
    
    def generate_table_embeddings(self):
        for table in self.tables:
            table.embedding =  self.openai_client.embeddings.create(input=[table.description], model=self.embedding).data[0].embedding
    
    def export_json_manifest(self):
        return json.dumps(
            {"tables":[t.model_dump() for t in self.tables]},
              indent=4)
    
    def create_azure_ai_search_index(self, 
                                     search_endpoint, 
                                     search_credential, 
                                     index_name,
                                     openai_endpoint,
                                     openai_key,
                                     embedding_deployment):
        self.logger.info("Creating Azure AI Search Index.")
        
        self.index_name = index_name
        self.search_endpoint = search_endpoint
        self.search_credential = search_credential
        # Create a search index client
        index_client = SearchIndexClient(endpoint=search_endpoint, credential=AzureKeyCredential(search_credential))
        self.logger.info("SearchIndexClient created.")

        # Check if the index exists
        try:
            index_client.get_index(index_name)
            self.logger.info(f"Index '{index_name}' already exists.")
        except Exception as e:
            self.logger.info(f"Index '{index_name}' does not exist. Creating a new one.")

            fields = [
                SearchableField(name="name_key", type=SearchFieldDataType.String, key=True, sortable=True, filterable=True, facetable=True),
                SearchableField(name="name", type=SearchFieldDataType.String),
                SearchableField(name="business_readable_name", type=SearchFieldDataType.String),
                SearchableField(name="description", type=SearchFieldDataType.String),
                ComplexField(
                    name="columns",
                    collection=True,
                    fields=[
                        SimpleField(name="name", type=SearchFieldDataType.String),
                        SimpleField(name="type", type=SearchFieldDataType.String),
                        SimpleField(name="description", type=SearchFieldDataType.String),
                        SimpleField(name="definition", type=SearchFieldDataType.String),
                        SimpleField(name="primary_key", type=SearchFieldDataType.Boolean),
                        SimpleField(name="sample_values", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
                    ]),
                SearchField(name="embedding", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                            searchable=True, vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile"),
            ]
            self.logger.info("Fields for the index defined.")

            # Configure the vector search configuration  
            vector_search = VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="myHnsw"
                    )
                ],
                profiles=[
                    VectorSearchProfile(
                        name="myHnswProfile",
                        algorithm_configuration_name="myHnsw",
                        vectorizer_name="myVectorizer"
                    )
                ],
                vectorizers=[
                    AzureOpenAIVectorizer(
                        vectorizer_name="myVectorizer",
                        parameters=AzureOpenAIVectorizerParameters(
                            resource_url=openai_endpoint,
                            deployment_name=embedding_deployment,
                            model_name="text-embedding-3-small",
                            api_key=openai_key
                        )
                    )
                ]
            )
            self.logger.info("Vector search configuration defined.")

            semantic_config = SemanticConfiguration(
                name="my-semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="name"),
                    content_fields=[SemanticField(field_name="description"), SemanticField(field_name="business_readable_name")],
                )
            )
            self.logger.info("Semantic configuration defined.")

            # Create the semantic settings with the configuration
            semantic_search = SemanticSearch(configurations=[semantic_config])
            self.logger.info("Semantic search configuration defined.")

            # Create the search index with the semantic settings
            index = SearchIndex(name=index_name, fields=fields,
                                vector_search=vector_search, semantic_search=semantic_search)
            result = index_client.create_or_update_index(index)
            self.logger.info(f"Index '{result.name}' created successfully.")
    
    def push_to_ai_search(self):
        search_client = SearchClient(endpoint=self.search_endpoint, 
                                     index_name=self.index_name, 
                                     credential=AzureKeyCredential(self.search_credential))

        table_metadata = [t.model_dump() for t in self.tables]
        self.logger.info(f"Pushing metadata for {len(table_metadata)} tables to Azure AI Search.")

        # Push each record to the index
        for table in table_metadata:
            print(f"Pushing data for table {table['name']} to the index.")
            table['name_key'] = table['name'].replace(".","__")
            for col in table['columns']:
                col['sample_values'] = [str(val) for val in col['sample_values']]
            try:
                search_client.upload_documents(documents=[table])
                self.logger.info(f"Data for table {table['name']} pushed to the index.")
            except Exception as e:
                self.logger.error(f"Error pushing data for table {table['name']} to the index.")
                break
