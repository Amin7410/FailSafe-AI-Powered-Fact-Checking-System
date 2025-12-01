# ./factcheck/__init__.py

import time
import tiktoken
import json
from dataclasses import asdict

from factcheck.utils.llmclient import CLIENTS, model2client
from factcheck.utils.prompt import prompt_mapper
from factcheck.utils.logger import CustomLogger
from factcheck.utils.api_config import load_api_config
from factcheck.utils.data_class import PipelineUsage, FactCheckOutput, ClaimDetail, FCSummary
from factcheck.utils.graph_utils import sag_to_graph, get_claims_from_graph, graph_to_networkx_dict 

from .core.Screening import MetadataAnalyzer, StylometryAnalyzer, ScreeningAdvisor
from .core.Coreference import ReferenceResolver
from factcheck.core import (
    Decompose,
    Checkworthy,
    QueryGenerator,
    retriever_mapper,
    ClaimVerify,
)
from factcheck.core.KnowledgeBase import FactKnowledgeBase

logger = CustomLogger(__name__).getlog()


class FactCheck:
    """
    Core Controller of the FailSafe System.
    Refactored to use Dependency Injection.
    """
    def __init__(
        self,
        metadata_analyzer: MetadataAnalyzer,
        stylometry_analyzer: StylometryAnalyzer,
        screening_advisor: ScreeningAdvisor,
        reference_resolver: ReferenceResolver,
        decomposer: Decompose,
        checkworthy: Checkworthy,
        query_generator: QueryGenerator,
        evidence_crawler, 
        claimverify: ClaimVerify,
        knowledge_base: FactKnowledgeBase,
        prompt_handler,
        encoding=None,
        num_seed_retries: int = 3,
    ):
        self.metadata_analyzer = metadata_analyzer
        self.stylometry_analyzer = stylometry_analyzer
        self.screening_advisor = screening_advisor
        self.reference_resolver = reference_resolver
        
        self.decomposer = decomposer
        self.checkworthy = checkworthy
        self.query_generator = query_generator
        self.evidence_crawler = evidence_crawler
        self.claimverify = claimverify
        
        self.knowledge_base = knowledge_base
        self.prompt = prompt_handler
        
        self.num_seed_retries = num_seed_retries
        self.encoding = encoding if encoding else tiktoken.get_encoding("cl100k_base")

        self.llm_components = {
            "decomposer": self.decomposer,
            "checkworthy": self.checkworthy,
            "query_generator": self.query_generator,
            "evidence_crawler": self.evidence_crawler,
            "claimverify": self.claimverify
        }

        logger.info("=== FactCheck Core Initialized (DI Mode) ===")

    def _get_usage(self) -> PipelineUsage:
        """Collect token usage from all LLM-based components."""
        total_usage = {}
        for name, component in self.llm_components.items():
            if hasattr(component, 'llm_client'):
                total_usage[name] = component.llm_client.usage
       
        return PipelineUsage(
            decomposer=total_usage.get('decomposer'),
            checkworthy=total_usage.get('checkworthy'),
            query_generator=total_usage.get('query_generator'),
            evidence_crawler=total_usage.get('evidence_crawler'),
            claimverify=total_usage.get('claimverify')
        )

    def _reset_usage(self):
        """Reset token counters for a new request."""
        for component in self.llm_components.values():
            if hasattr(component, 'llm_client'):
                component.llm_client.reset_usage()

    def _screen_input(self, raw_text: str):
        logger.info("--- Running Layer 0: Rapid Screening ---")
        metadata_result = self.metadata_analyzer.analyze(raw_text)
        style_result = self.stylometry_analyzer.analyze(raw_text)

        trust_level = metadata_result.get("trust_level")
        sensationalism_score = style_result.get("sensationalism_score", 0.0)

        logger.info(f"Screening results: Trust={trust_level}, Sensationalism Score={sensationalism_score:.2f}")

        if trust_level == 'low' and sensationalism_score > 0.5:
            warning_message = (
                f"Early Warning: This content originates from a low-trust source "
                f"('{metadata_result.get('reason')}') and exhibits a highly sensationalist writing style "
                f"(score: {sensationalism_score:.2f}). There is a high probability of misinformation."
            )
            logger.warning(f"Early Exit triggered: {warning_message}")
            
            early_exit_output = self._finalize_factcheck(
                raw_text=raw_text,
                claim_detail=[],
                summary_override={"message": warning_message, "status": "SCREENED_OUT"}
            )
            return True, early_exit_output

        analysis_data = {"metadata": metadata_result, "style": style_result}
        return False, analysis_data

    def _merge_claim_details(
        self, original_claims: list, claim2checkworthy: dict, claim2queries: dict, claim2verifications: dict
    ) -> list[ClaimDetail]:
        claim_details = []
        
        for i, claim in enumerate(original_claims):
            if claim in claim2verifications:
                evidences = claim2verifications.get(claim, [])
                labels = [e.relationship for e in evidences] if evidences else []
                support_count = labels.count("SUPPORTS")
                refute_count = labels.count("REFUTES")
                
                if support_count + refute_count == 0:
                    factuality = "No conclusive evidence found."
                else:
                    factuality = support_count / (support_count + refute_count)

                claim_obj = ClaimDetail(
                    id=i + 1, claim=claim, checkworthy=True,
                    checkworthy_reason=claim2checkworthy.get(claim, "No reason provided."),
                    origin_text=claim,
                    start=-1, end=-1, 
                    queries=claim2queries.get(claim, []), evidences=evidences, factuality=factuality,
                )
            else:
                claim_obj = ClaimDetail(
                    id=i + 1, claim=claim, checkworthy=(claim in claim2checkworthy),
                    checkworthy_reason=claim2checkworthy.get(claim, "Not considered check-worthy."),
                    origin_text=claim, 
                    start=-1, end=-1,
                    queries=[], evidences=[], factuality="Nothing to check.",
                )
            claim_details.append(claim_obj)
        return claim_details

    def _generate_comprehensive_report(self, raw_text: str, claim_details: list[ClaimDetail]) -> str:
        logger.info("--- Running Layer 4: Synthesis & Reporting (The Editor-in-Chief) ---")
        
        claims_data_for_llm = []
        for c in claim_details:
            if c.factuality == "Nothing to check.":
                continue
                
            evidence_summary = []
            if c.evidences:
                for e in c.evidences:
                    evidence_summary.append({
                        "source_url": e.url,
                        "council_debate_log": e.reasoning
                    })
            
            claims_data_for_llm.append({
                "claim_id": c.id,
                "claim_text": c.claim,
                "verdict_score": c.factuality, 
                "evidence_analysis": evidence_summary
            })
        
        if not claims_data_for_llm:
            return "No verifiable claims found to report on."

        claims_json_str = json.dumps(claims_data_for_llm, indent=2)
        prompt_content = self.prompt.report_prompt.format(
            raw_text=raw_text,
            claims_json=claims_json_str
        )

        messages = self.claimverify.llm_client.construct_message_list([prompt_content])
        
        try:
            report_markdown = self.claimverify.llm_client.call(messages, num_retries=2)
            if report_markdown.startswith("```markdown"):
                report_markdown = report_markdown[11:-3].strip()
            elif report_markdown.startswith("```"):
                report_markdown = report_markdown[3:-3].strip()
            return report_markdown
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return "Failed to generate comprehensive report due to an unexpected error."

    def _finalize_factcheck(
        self, raw_text: str, sag: dict = None, claim_detail: list[ClaimDetail] = None, return_dict: bool = True, summary_override: dict = None
    ) -> FactCheckOutput:

        if summary_override:
            summary = FCSummary(
                num_claims=0, num_checkworthy_claims=0, num_verified_claims=0,
                num_supported_claims=0, num_refuted_claims=0, num_controversial_claims=0,
                factuality=summary_override.get("message")
            )
            final_report_markdown = None
        else:
            claim_detail = claim_detail or []
            verified_claims = [c for c in claim_detail if isinstance(c.factuality, float)]
            num_claims = len(claim_detail)
            num_checkworthy_claims = len([c for c in claim_detail if c.factuality != "Nothing to check."])
            num_verified_claims = len(verified_claims)       
            num_supported_claims = len([c for c in verified_claims if c.factuality >= 0.75])
            num_refuted_claims = len([c for c in verified_claims if c.factuality <= 0.25])
            num_controversial_claims = len([c for c in verified_claims if 0.25 < c.factuality < 0.75])
            
            factuality_sum = sum(c.factuality for c in verified_claims)
            overall_factuality = factuality_sum / num_verified_claims if num_verified_claims > 0 else "N/A"

            summary = FCSummary(
                num_claims, num_checkworthy_claims, num_verified_claims,
                num_supported_claims, num_refuted_claims, num_controversial_claims,
                factuality=overall_factuality,
            )
            final_report_markdown = self._generate_comprehensive_report(raw_text, claim_detail)

        num_tokens = len(self.encoding.encode(raw_text))
        
        output = FactCheckOutput(
            raw_text=raw_text, token_count=num_tokens,
            usage=self._get_usage(), claim_detail=claim_detail, summary=summary,
            final_report=final_report_markdown
        )

        logger.info(f"== Overall Factuality: {output.summary.factuality}\n")

        output_dict = asdict(output)
        output_dict['sag'] = sag or {"nodes": [], "edges": []}
        output_dict['final_report'] = final_report_markdown

        self.screening_advisor.learn_from_result(raw_text, output_dict)

        if return_dict:
            return output_dict
        else:
            output.sag = sag or {"nodes": [], "edges": []} 
            return output
        
    def check_text_with_progress(self, raw_text: str, progress_callback):
        self._reset_usage()

        progress_callback('PROGRESS', 'Step 1/5: Screening for obvious misinformation...')
        logger.info("--- Running Layer 0: Rapid Screening ---")
    
        advice = self.screening_advisor.get_advice(raw_text)
        logger.info("Screening Advisor's advice: '%s'", advice)

        should_exit, screen_result = self._screen_input(raw_text)
        if should_exit:
            progress_callback('SUCCESS', 'Screening complete. Early exit triggered.')
            return screen_result

        progress_callback('PROGRESS', 'Step 2/5: Decomposing text into claims...')
        logger.info("--- Layer 0 passed. Proceeding with full pipeline. ---")
        st_time = time.time()
        
        logger.info("Resolving coreferences to improve context...")
        resolved_text = self.reference_resolver.resolve(raw_text)
        
        logger.info("Decomposing text into a Structured Argumentation Graph (SAG)...")
        sag_jsonld = self.decomposer.create_sag(
            doc=resolved_text, 
            num_retries=self.num_seed_retries
        )

        sag_graph = sag_to_graph(sag_jsonld)
        extracted_claims_info = get_claims_from_graph(sag_graph)
        claims_from_nodes = [item['label'] for item in extracted_claims_info]
        sag_dict_for_output = graph_to_networkx_dict(sag_graph)
        
        if not claims_from_nodes:
            logger.warning("SAG decomposition did not return any verifiable claims.")
            progress_callback('SUCCESS', 'Analysis complete. No verifiable claims found.')
            return self._finalize_factcheck(raw_text=raw_text, sag=sag_dict_for_output, claim_detail=[], return_dict=True)

        original_count = len(claims_from_nodes)
        claims_from_nodes = self.decomposer.deduplicate_claims(claims_from_nodes, threshold=0.85)
        if len(claims_from_nodes) < original_count:
            logger.info(f"Deduplicated claims: {original_count} -> {len(claims_from_nodes)}")
            progress_callback('PROGRESS', f'Step 2.5: Optimized claims (Removed {original_count - len(claims_from_nodes)} duplicates)...')

        logger.info("Identifying check-worthy claims from SAG nodes...")
        checkworthy_claims, claim2checkworthy = self.checkworthy.identify_checkworthiness(
            claims_from_nodes, num_retries=self.num_seed_retries
        )

        preview_claims = []
        for i, txt in enumerate(claims_from_nodes):
            status = "PENDING"
            if txt not in checkworthy_claims:
                status = "SKIPPED"
            preview_claims.append({"id": i + 1, "text": txt, "status": status})
        
        progress_callback('PROGRESS', 'Claims identified. Starting verification...', {
            "event": "CLAIMS_READY",
            "claims": preview_claims
        })

        if not checkworthy_claims:
            logger.info("No check-worthy claims found after analysis.")
            claim_detail = self._merge_claim_details(
                original_claims=claims_from_nodes,
                claim2checkworthy=claim2checkworthy,
                claim2queries={}, claim2verifications={}
            )
            progress_callback('SUCCESS', 'Analysis complete. No check-worthy claims found.')
            return self._finalize_factcheck(raw_text=raw_text, sag=sag_dict_for_output, claim_detail=claim_detail, return_dict=True)

        progress_callback('PROGRESS', 'Step 2.8: Checking Knowledge Base for existing facts...')
        claims_to_process = []
        cached_results_map = {} 

        for claim in checkworthy_claims:
            cached_detail = self.knowledge_base.check_cache(claim)
            if cached_detail:
                cached_results_map[claim] = cached_detail
                c_id = claims_from_nodes.index(claim) + 1 if claim in claims_from_nodes else 0
                progress_callback('PROGRESS', f"Found cached result for claim #{c_id}", {
                    "event": "BATCH_DONE",
                    "updates": [{"id": c_id, "status": "CACHED_TRUE" if cached_detail.factuality > 0.5 else "CACHED_FALSE"}]
                })
            else:
                claims_to_process.append(claim)
        
        if cached_results_map:
            logger.info(f"Skipping verification for {len(cached_results_map)} claims found in cache.")

        new_claim_verifications_dict = {}
        new_claim_queries_dict = {}

        if claims_to_process:
            progress_callback('PROGRESS', f'Step 3/5: Generating search queries for {len(claims_to_process)} new claims...')
            new_claim_queries_dict = self.query_generator.generate_query(claims=claims_to_process)
            
            progress_callback('PROGRESS', 'Step 4/5: Retrieving evidence (Deep Search)...')
            new_claim_evidences_dict = self.evidence_crawler.retrieve_evidence(claim_queries_dict=new_claim_queries_dict)
            
            progress_callback('PROGRESS', 'Step 5/5: Verifying claims with AI council...')
            
            batch_size = 5
            for i in range(0, len(claims_to_process), batch_size):
                batch_claims = claims_to_process[i : i + batch_size]
                batch_evidence_input = {k: new_claim_evidences_dict[k] for k in batch_claims if k in new_claim_evidences_dict}
                
                if not batch_evidence_input: 
                    continue

                batch_result = self.claimverify.verify_claims(batch_evidence_input)
                new_claim_verifications_dict.update(batch_result)
                
                verified_updates = []
                for claim_txt, evidences in batch_result.items():
                    c_id = -1
                    if claim_txt in claims_from_nodes:
                        c_id = claims_from_nodes.index(claim_txt) + 1
                    
                    labels = [e.relationship for e in evidences]
                    if "REFUTES" in labels: 
                        status = "REFUTED"
                    elif "SUPPORTS" in labels: 
                        status = "SUPPORTED"
                    else: 
                        status = "INCONCLUSIVE"
                    
                    verified_updates.append({"id": c_id, "status": status})

                progress_callback('PROGRESS', f'Verified {min(i + batch_size, len(claims_to_process))}/{len(claims_to_process)} new claims...', {
                    "event": "BATCH_DONE",
                    "updates": verified_updates
                })
            step5_time = time.time()
        else:
            logger.info("All claims resolved from Cache.")
            step5_time = time.time()

        logger.info(
            "== State: Done! \n Total time: %.2fs.",
            step5_time - st_time
        )
        
        progress_callback('PROGRESS', 'Finalizing report (Editor-in-Chief is writing)...')

        new_claim_details_objects = self._merge_claim_details(
            original_claims=claims_to_process,
            claim2checkworthy=claim2checkworthy,
            claim2queries=new_claim_queries_dict,
            claim2verifications=new_claim_verifications_dict,
        )

        for detail in new_claim_details_objects:
            self.knowledge_base.save_knowledge(detail)

        final_claim_details = []
        
        for i, original_claim in enumerate(claims_from_nodes):
            if original_claim not in checkworthy_claims:
                detail = ClaimDetail(
                    id=i + 1, claim=original_claim, checkworthy=False,
                    checkworthy_reason=claim2checkworthy.get(original_claim, "Not check-worthy"),
                    origin_text=original_claim, start=-1, end=-1,
                    queries=[], evidences=[], factuality="Nothing to check."
                )
                final_claim_details.append(detail)
                continue

            if original_claim in cached_results_map:
                detail = cached_results_map[original_claim]
                detail.id = i + 1 
                final_claim_details.append(detail)
                continue

            found = False
            for d in new_claim_details_objects:
                if d.claim == original_claim:
                    d.id = i + 1
                    final_claim_details.append(d)
                    found = True
                    break
            if not found:
                logger.warning(f"Claim '{original_claim}' was lost during processing.")

        return self._finalize_factcheck(raw_text=raw_text, sag=sag_dict_for_output, claim_detail=final_claim_details, return_dict=True)
    
    def check_text(self, raw_text: str):
        def no_op_callback(state, message, payload=None):
            pass
        return self.check_text_with_progress(raw_text, no_op_callback)


def build_fact_check_system(
    default_model: str = "gemini-pro",
    client: str = None,
    prompt_name: str = "gemini_prompt",
    retriever_name: str = "hybrid",
    api_config: dict = None,
    step_models: dict = None 
) -> FactCheck:

    final_api_config = load_api_config(api_config)
    prompt = prompt_mapper(prompt_name=prompt_name)
    
    if step_models is None:
        step_models = {}

    steps_needing_llm = [
        "decompose_model", 
        "checkworthy_model", 
        "query_generator_model", 
        "evidence_retrieval_model", 
        "claim_verify_model"
    ]
    
    clients = {}
    for key in steps_needing_llm:
        _model_name = step_models.get(key, default_model)
        
        if client is not None:
            LLMClientClass = CLIENTS[client]
        else:
            LLMClientClass = model2client(_model_name)
            
        print(f"== [Factory] Init {key} with model: {_model_name}")
        clients[key] = LLMClientClass(model=_model_name, api_config=final_api_config)

    metadata_analyzer = MetadataAnalyzer(llm_client=clients['checkworthy_model'])
    stylometry_analyzer = StylometryAnalyzer()
    screening_advisor = ScreeningAdvisor()
    reference_resolver = ReferenceResolver()
    
    decomposer = Decompose(llm_client=clients['decompose_model'], prompt=prompt)
    checkworthy = Checkworthy(llm_client=clients['checkworthy_model'], prompt=prompt)
    query_generator = QueryGenerator(llm_client=clients['query_generator_model'], prompt=prompt)
    
    RetrieverClass = retriever_mapper(retriever_name=retriever_name)
    evidence_crawler = RetrieverClass(
        llm_client=clients['evidence_retrieval_model'], 
        api_config=final_api_config
    )
    
    claimverify = ClaimVerify(llm_client=clients['claim_verify_model'], prompt=prompt)
    knowledge_base = FactKnowledgeBase()

    return FactCheck(
        metadata_analyzer=metadata_analyzer,
        stylometry_analyzer=stylometry_analyzer,
        screening_advisor=screening_advisor,
        reference_resolver=reference_resolver,
        decomposer=decomposer,
        checkworthy=checkworthy,
        query_generator=query_generator,
        evidence_crawler=evidence_crawler,
        claimverify=claimverify,
        knowledge_base=knowledge_base,
        prompt_handler=prompt
    )