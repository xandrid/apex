from google.cloud import bigquery
import os

def check_schema():
    try:
        client = bigquery.Client(project="majestic-cairn-480103-f1")
        table_ref = "patents-public-data.patents.publications"
        table = client.get_table(table_ref)
        
        print(f"Table: {table_ref}")
        for field in table.schema:
            if "date" in field.name.lower():
                print(f" - {field.name} ({field.field_type})")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
