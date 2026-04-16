import os
from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

class BigQueryClient:
    def __init__(self):
        # We don't need to set credentials explicitly if using 'gcloud auth application-default login'
        try:
            project_id = os.getenv("GCP_PROJECT_ID")
            if project_id:
                self.client = bigquery.Client(project=project_id)
            else:
                print("WARNING: GCP_PROJECT_ID not found in env. Trying default auth...")
                self.client = bigquery.Client()
        except Exception as e:
            print(f"WARNING: Could not initialize BigQuery Client: {e}")
            self.client = None

    def estimate_query_cost(self, query: str) -> int:
        """
        Returns the estimated bytes processed for the given query.
        """
        if not self.client:
            return 0
            
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        try:
            query_job = self.client.query(query, job_config=job_config)
            return query_job.total_bytes_processed
        except Exception as e:
            print(f"Error estimating query cost: {e}")
            return 0

    def fetch_patents(self, 
                      limit: int = 100, 
                      country_code: str = 'US',
                      cpc_prefixes: List[str] = None,
                      start_date: int = 20240101,
                      dry_run: bool = False) -> Any:
        """
        Fetches patents from the public dataset with filtering.
        If dry_run is True, returns the estimated bytes processed (int).
        Otherwise returns List[Dict].
        """
        if not self.client:
            print("BigQuery Client not initialized. Returning empty list.")
            return [] if not dry_run else 0

        # Construct CPC filter clause
        cpc_clause = ""
        if cpc_prefixes:
            conditions = [f"STARTS_WITH(c.code, '{prefix}')" for prefix in cpc_prefixes]
            or_condition = " OR ".join(conditions)
            if or_condition:
                cpc_clause = f"AND EXISTS(SELECT 1 FROM UNNEST(cpc) AS c WHERE {or_condition})"

        query = f"""
            SELECT
                publication_number,
                title_localized,
                abstract_localized,
                claims_localized,
                description_localized,
                publication_date,
                cpc,
                citation
            FROM
                `patents-public-data.patents.publications`
            WHERE
                country_code = '{country_code}'
                AND kind_code = 'B2' -- Granted patents
                AND publication_date >= {start_date}
                {cpc_clause}
            LIMIT {limit}
        """
        
        if dry_run:
            print(f"DEBUG: Dry Run Query Estimation:\n{query}")
            return self.estimate_query_cost(query)
            
        print(f"DEBUG: Executing Query:\n{query}")

        try:
            query_job = self.client.query(query)
            results = []
            for row in query_job:
                # Helper to extract English text if available
                def get_english(localized_list):
                    if not localized_list: return ""
                    for item in localized_list:
                        if item.get('language') == 'en':
                            return item.get('text', '')
                    return localized_list[0].get('text', '') if localized_list else ""

                patent_data = {
                    "publication_number": row.publication_number,
                    "title": get_english(row.title_localized),
                    "abstract": get_english(row.abstract_localized),
                    "claims": get_english(row.claims_localized),
                    "description": get_english(row.description_localized),
                    "publication_date": str(row.publication_date) if row.publication_date else None,
                    "cpc": [c.get('code') for c in row.cpc] if row.cpc else [],
                    "citations": [c.get('publication_number') for c in row.citation] if row.citation else []
                }
                results.append(patent_data)
            
            return results

        except Exception as e:
            print(f"Error executing BigQuery query: {e}")
            return []

    def fetch_by_ids(self, publication_numbers: List[str], dry_run: bool = False) -> Any:
        """
        Fetches specific patents by their publication numbers.
        If dry_run is True, returns estimated bytes.
        """
        if not self.client:
            return [] if not dry_run else 0
            
        if not publication_numbers:
            return [] if not dry_run else 0

        formatted_ids = ",".join([f"'{pid}'" for pid in publication_numbers])
        
        query = f"""
            SELECT
                publication_number,
                title_localized,
                abstract_localized,
                claims_localized,
                description_localized,
                publication_date,
                cpc
            FROM
                `patents-public-data.patents.publications`
            WHERE
                country_code = 'US'
                AND publication_number IN ({formatted_ids})
        """
        
        if dry_run:
             return self.estimate_query_cost(query)

        try:
            query_job = self.client.query(query)
            results = []
            for row in query_job:
                # Helper to extract English text if available
                def get_english(localized_list):
                    if not localized_list: return ""
                    for item in localized_list:
                        if item.get('language') == 'en':
                            return item.get('text', '')
                    return localized_list[0].get('text', '') if localized_list else ""

                patent_data = {
                    "publication_number": row.publication_number,
                    "title": get_english(row.title_localized),
                    "abstract": get_english(row.abstract_localized),
                    "claims": get_english(row.claims_localized),
                    "description": get_english(row.description_localized),
                    "publication_date": str(row.publication_date) if row.publication_date else None,
                    "cpc": [c.get('code') for c in row.cpc] if row.cpc else []
                }
                results.append(patent_data)
            
            return results
        except Exception as e:
            print(f"Error fetching specific patents: {e}")
            return []

if __name__ == "__main__":
    # Test
    bq = BigQueryClient()
    # Test Cost
    cost = bq.fetch_patents(limit=5, cpc_prefixes=['G06N'], dry_run=True)
    print(f"Estimated bytes for test query: {cost/1e6:.2f} MB")
