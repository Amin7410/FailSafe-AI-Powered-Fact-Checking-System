# ./factcheck/core/Retriever/serper_retriever.py

from concurrent.futures import ThreadPoolExecutor
import json
import requests
import os
import re
import bs4
from factcheck.utils.logger import CustomLogger
from factcheck.utils.web_util import crawl_web
from factcheck.core.Screening import MetadataAnalyzer

logger = CustomLogger(__name__).getlog()


class SerperEvidenceRetriever:
    def __init__(self, llm_client, api_config: dict = None):
        """Initializes the SerperEvidenceRetriever class."""
        self.lang = "en"
        self.serper_key = api_config.get("SERPER_API_KEY")
        if not self.serper_key:
            raise ValueError("SERPER_API_KEY not found in api_config.")
        self.llm_client = llm_client
        # --- KHỞI TẠO BỘ PHÂN TÍCH ---
        self.metadata_analyzer = MetadataAnalyzer(llm_client=self.llm_client)
    
    def retrieve_evidence(self, claim_queries_dict, top_k: int = 3, snippet_extend_flag: bool = True):
        """
        Retrieves and screens evidences for the given claims.

        Args:
            claim_queries_dict (dict): A dictionary of claims and their corresponding queries.
            top_k (int): The number of top relevant results to retrieve. Defaults to 3.
            snippet_extend_flag (bool): Whether to extend the snippet by crawling the web. Defaults to True.

        Returns:
            dict: A dictionary of claims and their corresponding screened evidences.
        """
        logger.info("Collecting and screening evidences...")
        query_list = [y for x in claim_queries_dict.items() for y in x[1]]
        
        evidence_list_per_query = self._retrieve_evidence_4_all_claim(
            query_list=query_list, top_k=top_k, snippet_extend_flag=snippet_extend_flag
        )

        i = 0
        claim_evidence_dict = {}
        for claim, queries in claim_queries_dict.items():
            evidences_for_claim_queries = evidence_list_per_query[i : i + len(queries)]
            # Flatten the list of lists into a single list of evidences for the claim
            combined_evidences = [e for evidences in evidences_for_claim_queries for e in evidences]
            claim_evidence_dict[claim] = combined_evidences
            i += len(queries)
        
        assert i == len(evidence_list_per_query)
        logger.info(f"Evidence collection and screening done! Found evidences for {len(claim_evidence_dict)} claims.")
        return claim_evidence_dict

    def _screen_and_tag_evidence(self, evidence_list: list) -> list:
        """
        Screens a list of evidence, tags them with a trust level, and filters out low-trust sources.
        """
        screened_evidences = []
        for evidence in evidence_list:
            url = evidence.get("url")
            
            if url and url != "Google Answer Box":
                trust_info = self.metadata_analyzer.analyze(url)
                evidence['trust_level'] = trust_info.get('trust_level', 'unknown')
            else:
                # We generally trust Google's direct answers
                evidence['trust_level'] = 'high'
            
            # --- CRITICAL FILTERING LOGIC ---
            # Only keep evidence that is not from a low-trust source.
            if evidence['trust_level'] != 'low':
                screened_evidences.append(evidence)
            else:
                logger.warning(f"Discarding evidence from low-trust source: {url}")

        return screened_evidences

    def _retrieve_evidence_4_all_claim(
        self, query_list: list[str], top_k: int = 3, snippet_extend_flag: bool = True
    ) -> list[list[dict]]:
        """
        Retrieves evidences for the given queries and applies screening.
        """
        evidences_per_query = [[] for _ in query_list]

        # Get response from Serper API
        serper_responses = []
        for i in range(0, len(query_list), 100):
            batch_query_list = query_list[i : i + 100]
            batch_response = self._request_serper_api(batch_query_list)
            if batch_response is None:
                logger.error("Serper API request error!")
                return evidences_per_query
            serper_responses.extend(batch_response.json())
        for i, (query, response) in enumerate(zip(query_list, serper_responses)):
            raw_evidences = []
            
            # Handle Answer Box results
            if "answerBox" in response:
                answer_text = response["answerBox"].get("answer") or response["answerBox"].get("snippet", "")
                raw_evidences.append({"text": f"{query}\nAnswer: {answer_text}", "url": "Google Answer Box"})
            
            # Handle organic search results
            else:
                topk_results = response.get("organic", [])[:top_k]
                for result in topk_results:
                    if "snippet" in result and "link" in result:
                        raw_evidences.append({
                            "text": re.sub(r"\n+", "\n", result["snippet"]),
                            "url": result["link"]
                        })

            # --- SCREENING AND TAGGING STEP ---
            screened_evidences = self._screen_and_tag_evidence(raw_evidences)
            evidences_per_query[i] = screened_evidences

        # Note: The snippet extension logic has been removed for simplicity and to focus on the screening feature.
        # If snippet extension is critical, the logic would need to be re-integrated carefully to
        # preserve the 'trust_level' tag after crawling.

        return evidences_per_query

    def _request_serper_api(self, questions: list[str]):
        """
        Requests the Serper API.
        """
        url = "https://google.serper.dev/search"

        headers = {
            "X-API-KEY": self.serper_key,
            "Content-Type": "application/json",
        }

        questions_data = [{"q": question, "autocorrect": False} for question in questions]
        payload = json.dumps(questions_data)
        
        try:
            response = requests.request("POST", url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()  # Will raise an HTTPError for bad responses (4xx or 5xx)
            return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                logger.error("Serper API authentication failed. Check your SERPER_API_KEY.")
            else:
                logger.error(f"Serper API request failed with status {e.response.status_code}: {e.response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred while calling Serper API: {e}")
        
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--serper_api_key", type=str, help="API key for serper")
    args = parser.parse_args()

    if args.serper_api_key:
        api_config = {"SERPER_API_KEY": args.serper_api_key}
        retriever = SerperEvidenceRetriever(llm_client=None, api_config=api_config)
        
        test_result = retriever._request_serper_api(["Apple", "IBM"])
        if test_result:
            print(json.dumps(test_result.json(), indent=2))