# ./factcheck/core/Retriever/serper_retriever.py 

import json
import requests
import re
from factcheck.utils.logger import CustomLogger
from factcheck.core.Screening import MetadataAnalyzer
from factcheck.utils.deep_scraper import DeepScraper

logger = CustomLogger(__name__).getlog()


class SerperEvidenceRetriever:
    def __init__(self, llm_client, api_config: dict = None):
        self.lang = "en"
        self.serper_key = api_config.get("SERPER_API_KEY")
        if not self.serper_key:
            raise ValueError("SERPER_API_KEY not found in api_config.")
        self.llm_client = llm_client
        self.metadata_analyzer = MetadataAnalyzer(llm_client=self.llm_client)
        self.scraper = DeepScraper(max_workers=5)

    def retrieve_evidence(self, claim_queries_dict, top_k: int = 3, **kwargs):
        logger.info("Collecting and screening evidences...")
        query_list = [y for x in claim_queries_dict.items() for y in x[1]]
        
        evidence_list_per_query = self._retrieve_evidence_4_all_claim(
            query_list=query_list, top_k=top_k
        )

        i = 0
        claim_evidence_dict = {}
        for claim, queries in claim_queries_dict.items():
            evidences_for_claim_queries = evidence_list_per_query[i : i + len(queries)]
            combined_evidences = [e for evidences in evidences_for_claim_queries for e in evidences]
            claim_evidence_dict[claim] = combined_evidences
            i += len(queries)
        
        assert i == len(evidence_list_per_query)
        logger.info(f"Evidence collection and screening done! Found evidences for {len(claim_evidence_dict)} claims.")
        return claim_evidence_dict
    
    def _retrieve_evidence_4_all_claim(
        self, query_list: list[str], top_k: int = 3
    ) -> list[list[dict]]:
        all_raw_evidences_map = {}  
        
        serper_responses = []
        for i in range(0, len(query_list), 100):
            batch_query_list = query_list[i : i + 100]
            batch_response = self._request_serper_api(batch_query_list)
            if batch_response is None:
                logger.error("Serper API request error!")
                return [[] for _ in query_list]
            serper_responses.extend(batch_response.json())
            
        for i, (query, response) in enumerate(zip(query_list, serper_responses)):
            raw_evidences = []
            if "answerBox" in response:
                answer_text = response["answerBox"].get("answer") or response["answerBox"].get("snippet", "")
                raw_evidences.append({"text": f"{query}\nAnswer: {answer_text}", "url": "Google Answer Box"})
            else:
                topk_results = response.get("organic", [])[:top_k]
                for result in topk_results:
                    if "snippet" in result and "link" in result:
                        raw_evidences.append({
                            "text": re.sub(r"\n+", "\n", result["snippet"]),
                            "url": result["link"]
                        })
            all_raw_evidences_map[i] = raw_evidences
        all_urls_to_analyze = [
            ev['url'] for evidences in all_raw_evidences_map.values() for ev in evidences 
            if ev.get('url') and ev.get('url') != 'Google Answer Box'
        ]
        logger.info(f"Batch analyzing trust level for {len(set(all_urls_to_analyze))} unique URLs...")
        url_trust_info = self.metadata_analyzer.analyze_batch(all_urls_to_analyze)
        
        high_trust_urls = []
        for url, info in url_trust_info.items():
            if info.get('trust_level') == 'high':
                high_trust_urls.append(url)
        logger.info(f"Deep scraping contents for {len(high_trust_urls)} high-trust URLs...")
        scraped_contents = self.scraper.scrape_batch(high_trust_urls)

        evidences_per_query = [[] for _ in query_list]
        for query_index, evidences in all_raw_evidences_map.items():
            screened_evidences = []
            for evidence in evidences:
                url = evidence.get("url")
                if url == "Google Answer Box":
                    evidence['trust_level'] = 'high'
                elif url in url_trust_info:
                    trust_info = url_trust_info[url]
                    evidence['trust_level'] = trust_info.get('trust_level', 'unknown')
                else:
                    evidence['trust_level'] = 'unknown'
                if url in scraped_contents:
                    full_text = scraped_contents[url]
                    evidence['text'] = f"[FULL CONTENT EXTRACTED]\n{full_text}"
                    logger.info(f"Enriched evidence for {url} with deep content ({len(full_text)} chars).")
                if evidence['trust_level'] != 'low':
                    screened_evidences.append(evidence)
            
            evidences_per_query[query_index] = screened_evidences

        return evidences_per_query

    def _request_serper_api(self, questions: list[str]):
        """
        Requests the Serper API.
        """
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": self.serper_key, "Content-Type": "application/json"}
        questions_data = [{"q": question, "autocorrect": False} for question in questions]
        payload = json.dumps(questions_data)
        
        try:
            response = requests.request("POST", url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
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