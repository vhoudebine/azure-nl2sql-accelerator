from typing import Dict

# Define queries for Azure SQL Server
AZURE_SQL_QUERIES = {
    'list_database_tables': "SELECT TABLE_SCHEMA + '.' + TABLE_NAME AS TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'",

    'get_table_schema': lambda table_name: f"""
    SELECT  
        c.COLUMN_NAME as name,  
        c.DATA_TYPE as type,  
        c.IS_NULLABLE as is_nullable,  
        CAST(ep.value AS VARCHAR) AS column_description,  
        CASE  
            WHEN tc.CONSTRAINT_TYPE = 'PRIMARY KEY' THEN 'PRIMARY KEY'  
            WHEN tc.CONSTRAINT_TYPE = 'FOREIGN KEY' THEN 'FOREIGN KEY'  
            ELSE NULL  
        END AS key_type,  
        fk.referenced_table_name AS foreign_table,  
        fk.referenced_column_name AS foreign_column  
    FROM
        INFORMATION_SCHEMA.COLUMNS c
    LEFT JOIN
        sys.columns sc ON sc.object_id = OBJECT_ID(c.TABLE_NAME) AND sc.name = c.COLUMN_NAME
    LEFT JOIN
        sys.extended_properties ep ON ep.major_id = sc.object_id AND ep.minor_id = sc.column_id AND ep.name = 'MS_Description'
    LEFT JOIN
        INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu ON c.TABLE_NAME = kcu.TABLE_NAME AND c.COLUMN_NAME = kcu.COLUMN_NAME
    LEFT JOIN
        INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc ON tc.TABLE_NAME = kcu.TABLE_NAME AND tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
    LEFT JOIN
        (SELECT
            fkc.parent_column_id,
            fk.parent_object_id,
            fk.name AS constraint_name,
            fk.referenced_object_id,
            OBJECT_NAME(fk.referenced_object_id) AS referenced_table_name,
            COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS referenced_column_name
        FROM
            sys.foreign_keys fk
        INNER JOIN
            sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id) fk
    ON fk.parent_object_id = OBJECT_ID(c.TABLE_NAME) AND fk.parent_column_id = sc.column_id
    WHERE
        c.TABLE_SCHEMA+'.'+c.TABLE_NAME = '{table_name}'
    ORDER BY
        c.TABLE_NAME, c.ORDINAL_POSITION; """,

    'get_table_rows': lambda table_name: f"SELECT TOP 3 * FROM {table_name}",

    'get_column_values': lambda table_name, column_name: f"""
    SELECT DISTINCT TOP 10 
        {column_name} 
    FROM {table_name} 
    ORDER BY {column_name}"""
}

# Define queries for PostgreSQL
POSTGRESQL_QUERIES = {
    'list_database_tables': """SELECT   
    table_schema || '.' || table_name AS "TABLE_NAME"   
FROM   
    information_schema.tables   
WHERE   
    table_type = 'BASE TABLE'  
    AND table_catalog = current_database()  
    AND table_schema NOT IN ('pg_catalog', 'information_schema');""",

    'get_table_schema': lambda table_name: f"""SELECT  
    cols.column_name AS name,  
    cols.data_type AS type,  
    cols.is_nullable,  
    col_description(pgc.oid, cols.ordinal_position) AS column_description,  
    CASE  
        WHEN tc.constraint_type = 'PRIMARY KEY' THEN 'PRIMARY KEY'  
        WHEN tc.constraint_type = 'FOREIGN KEY' THEN 'FOREIGN KEY'  
        ELSE NULL  
    END AS key_type,  
    ccu.table_name AS foreign_table,  
    ccu.column_name AS foreign_column  
FROM  
    information_schema.columns AS cols  
    LEFT JOIN information_schema.key_column_usage AS kcu  
        ON cols.table_name = kcu.table_name  
        AND cols.column_name = kcu.column_name  
        AND cols.table_schema = kcu.table_schema  
    LEFT JOIN information_schema.table_constraints AS tc  
        ON kcu.constraint_name = tc.constraint_name  
        AND kcu.table_schema = tc.table_schema  
    LEFT JOIN information_schema.constraint_column_usage AS ccu  
        ON tc.constraint_name = ccu.constraint_name  
        AND tc.table_schema = ccu.table_schema  
    LEFT JOIN pg_class AS pgc  
        ON cols.table_name = pgc.relname  
        AND pgc.relkind = 'r'  
    LEFT JOIN pg_namespace AS pgn  
        ON pgc.relnamespace = pgn.oid  
        AND pgn.nspname = cols.table_schema  
WHERE  
    cols.table_schema || '.' || cols.table_name = '{table_name}'
ORDER BY  
    cols.ordinal_position;  """,

    'get_table_rows': lambda table_name: f"SELECT * FROM {table_name} LIMIT 3",

    'get_column_values': lambda table_name, column_name: f"""
    SELECT DISTINCT 
        {column_name} 
    FROM {table_name} 
    ORDER BY {column_name}
    LIMIT 10"""
}

# Function to get the appropriate query based on database type and query name
def get_query(db_type: str, query_name: str, **kwargs) -> str:
    if db_type == 'AZURE_SQL':
        queries = AZURE_SQL_QUERIES
    elif db_type == 'POSTGRESQL':
        queries = POSTGRESQL_QUERIES
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

    query = queries.get(query_name)
    if query is None:
        raise ValueError(f"Query '{query_name}' not found for database type '{db_type}'.")

    if callable(query):
        return query(**kwargs)
    else:
        return query