# ./factcheck/__init__.py

import concurrent.futures
import time
import tiktoken
from dataclasses import asdict
from factcheck.utils.llmclient import CLIENTS, model2client
from factcheck.utils.prompt import prompt_mapper
from factcheck.utils.logger import CustomLogger
from factcheck.utils.api_config import load_api_config
from factcheck.utils.data_class import PipelineUsage, FactCheckOutput, ClaimDetail, FCSummary
from factcheck.core import (
    Decompose,
    Checkworthy,
    QueryGenerator,
    retriever_mapper,
    ClaimVerify,
)
from .core.Screening import MetadataAnalyzer, StylometryAnalyzer

logger = CustomLogger(__name__).getlog()


class FactCheck:
    def __init__(
        self,
        default_model: str = "gemini-2.5-flash", 
        client: str = None,
        prompt: str = "gemini_prompt",
        retriever: str = "hybrid",
        decompose_model: str = None,
        checkworthy_model: str = None,
        query_generator_model: str = None,
        evidence_retrieval_model: str = None,
        claim_verify_model: str = None,
        api_config: dict = None,
        num_seed_retries: int = 3,
    ):
        
        self.encoding = tiktoken.get_encoding("cl100k_base")

        self.prompt = prompt_mapper(prompt_name=prompt)
        
        self.load_config(api_config=api_config)

        step_models = {
            "decompose_model": decompose_model,
            "checkworthy_model": checkworthy_model,
            "query_generator_model": query_generator_model,
            "evidence_retrieval_model": evidence_retrieval_model,
            "claim_verify_model": claim_verify_model,
        }

        for key, _model_name in step_models.items():
            _model_name = default_model if _model_name is None else _model_name
            print(f"== Init {key} with model: {_model_name}")
            if client is not None:
                logger.info(f"== Use specified client: {client}")
                LLMClient = CLIENTS[client]
            else:
                logger.info("== LLMClient is not specified, use default llm client.")
                LLMClient = model2client(_model_name)
            setattr(self, key, LLMClient(model=_model_name, api_config=self.api_config))

        self.metadata_analyzer = MetadataAnalyzer()
        self.stylometry_analyzer = StylometryAnalyzer()

        self.decomposer = Decompose(llm_client=self.decompose_model, prompt=self.prompt)
        self.checkworthy = Checkworthy(llm_client=self.checkworthy_model, prompt=self.prompt)
        self.query_generator = QueryGenerator(llm_client=self.query_generator_model, prompt=self.prompt)
        self.evidence_crawler = retriever_mapper(retriever_name=retriever)(
            llm_client=self.evidence_retrieval_model, api_config=self.api_config
        )
        self.claimverify = ClaimVerify(llm_client=self.claim_verify_model, prompt=self.prompt)
        self.attr_list = ["decomposer", "checkworthy", "query_generator", "evidence_crawler", "claimverify"]
        self.num_seed_retries = num_seed_retries

        logger.info("===Sub-modules Init Finished===")

    def load_config(self, api_config: dict) -> None:
        self.api_config = load_api_config(api_config)

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

    def check_text(self, raw_text: str):
        self._reset_usage()

        should_exit, screen_result = self._screen_input(raw_text)
        if should_exit:
            return screen_result

        logger.info("--- Layer 0 passed. Proceeding with full pipeline. ---")
        st_time = time.time()
        
        logger.info("Decomposing text into a Structured Argumentation Graph (SAG)...")
        sag = self.decomposer.create_sag(doc=raw_text, num_retries=self.num_seed_retries)
        
        ### SỬA ĐỔI 1: Trích xuất claims từ các node có type là "Claim" ###
        claims_from_nodes = [node['label'] for node in sag.get('nodes', []) if node.get('type') == 'Claim']

        if not claims_from_nodes:
            logger.warning("SAG decomposition did not return any verifiable claims. Finalizing report.")
            # ### SỬA ĐỔI 2: Truyền sag vào finalize để sau này có thể dùng ###
            return self._finalize_factcheck(raw_text=raw_text, sag=sag, claim_detail=[], return_dict=True)

        ### SỬA ĐỔI 3: Loại bỏ restore_claims song song vì nó không còn phù hợp ###
        # Thay vào đó, chúng ta sẽ chạy Checkworthy một cách tuần tự.
        # Trong tương lai, restore có thể được điều chỉnh để hoạt động với node_id.
        logger.info("Identifying check-worthy claims from SAG nodes...")
        checkworthy_claims, claim2checkworthy = self.checkworthy.identify_checkworthiness(
            claims_from_nodes, num_retries=self.num_seed_retries
        )

        if not checkworthy_claims:
            logger.info("No check-worthy claims found after analysis. Finalizing report.")
            # Chúng ta vẫn cần tạo claim_detail cho các claim không đáng kiểm chứng
            claim_detail = self._merge_claim_details(
                original_claims=claims_from_nodes, # Dùng list claims gốc
                claim2checkworthy=claim2checkworthy,
                claim2queries={}, 
                claim2verifications={}
            )
            return self._finalize_factcheck(raw_text=raw_text, sag=sag, claim_detail=claim_detail, return_dict=True)
        
        logger.info(f"Generating queries for {len(checkworthy_claims)} check-worthy claims...")
        claim_queries_dict = self.query_generator.generate_query(claims=checkworthy_claims)
        step123_time = time.time()
        
        logger.info("Retrieving evidence...")
        claim_evidences_dict = self.evidence_crawler.retrieve_evidence(claim_queries_dict=claim_queries_dict)
        step4_time = time.time()
        
        logger.info("Verifying claims against evidence...")
        claim_verifications_dict = self.claimverify.verify_claims(claim_evidences_dict=claim_evidences_dict)
        step5_time = time.time()

        logger.info(
            f"== State: Done! \n Total time: {step5_time - st_time:.2f}s. "
            f"(create claims:{step123_time - st_time:.2f}s ||| "
            f"retrieve:{step4_time - step123_time:.2f}s ||| "
            f"verify:{step5_time - step4_time:.2f}s)"
        )

        claim_detail = self._merge_claim_details(
            original_claims=claims_from_nodes, # Dùng list claims gốc
            claim2checkworthy=claim2checkworthy,
            claim2queries=claim_queries_dict,
            claim2verifications=claim_verifications_dict,
        )

        # ### SỬA ĐỔI 4: Truyền cả sag và claim_detail vào hàm cuối cùng ###
        return self._finalize_factcheck(raw_text=raw_text, sag=sag, claim_detail=claim_detail, return_dict=True)

    def _get_usage(self):
        total_usage = {}
        for attr in self.attr_list:
            module = getattr(self, attr)
            if hasattr(module, 'llm_client'):
                total_usage[attr] = module.llm_client.usage
        return PipelineUsage(**total_usage)

    def _reset_usage(self):
        for attr in self.attr_list:
            module = getattr(self, attr)
            if hasattr(module, 'llm_client'):
                module.llm_client.reset_usage()

    ### SỬA ĐỔI 5: Cập nhật hàm _merge_claim_details để không phụ thuộc vào `claim2doc` ###
    def _merge_claim_details(
        self, original_claims: list, claim2checkworthy: dict, claim2queries: dict, claim2verifications: dict
    ) -> list[ClaimDetail]:
        claim_details = []
        
        for i, claim in enumerate(original_claims):
            # Kiểm tra xem claim có được xác minh không (tức là nó có trong `claim2verifications`)
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
                # Đây là các claim không đáng kiểm chứng hoặc không có trong kết quả verify
                claim_obj = ClaimDetail(
                    id=i + 1, claim=claim, checkworthy=(claim in claim2checkworthy),
                    checkworthy_reason=claim2checkworthy.get(claim, "Not considered check-worthy."),
                    origin_text=claim, 
                    start=-1, end=-1,
                    queries=[], evidences=[], factuality="Nothing to check.",
                )
            claim_details.append(claim_obj)
        return claim_details

    def _finalize_factcheck(
        self, raw_text: str, sag: dict = None, claim_detail: list[ClaimDetail] = None, return_dict: bool = True, summary_override: dict = None
) -> FactCheckOutput:

        if summary_override:
            summary = FCSummary(
                num_claims=0, num_checkworthy_claims=0, num_verified_claims=0,
                num_supported_claims=0, num_refuted_claims=0, num_controversial_claims=0,
                factuality=summary_override.get("message")
            )
        else:
            claim_detail = claim_detail or []
            verified_claims = [c for c in claim_detail if isinstance(c.factuality, float)]
            num_claims = len(claim_detail)
            num_checkworthy_claims = len([c for c in claim_detail if c.factuality != "Nothing to check."])
            num_verified_claims = len(verified_claims)
            
            # --- THAY ĐỔI LOGIC TÍNH TOÁN TẠI ĐÂY ---
            
            # Một claim được coi là "hỗ trợ tốt" nếu điểm xác thực của nó từ 75% trở lên.
            num_supported_claims = len([c for c in verified_claims if c.factuality >= 0.75])
            
            # Một claim được coi là "bị bác bỏ/mâu thuẫn" nếu điểm xác thực của nó từ 25% trở xuống.
            num_refuted_claims = len([c for c in verified_claims if c.factuality <= 0.25])
            
            # Một claim được coi là "gây tranh cãi" nếu điểm nằm giữa hai ngưỡng trên.
            # Logic này linh hoạt hơn: num_verified_claims có thể không bằng tổng 3 loại kia nếu có claim có điểm chính xác 0.25 hoặc 0.75
            # Do đó, cách tính trực tiếp là tốt nhất.
            num_controversial_claims = len([c for c in verified_claims if 0.25 < c.factuality < 0.75])
            
            # --- KẾT THÚC THAY ĐỔI LOGIC ---

            factuality_sum = sum(c.factuality for c in verified_claims)
            overall_factuality = factuality_sum / num_verified_claims if num_verified_claims > 0 else "N/A"

            summary = FCSummary(
                num_claims, num_checkworthy_claims, num_verified_claims,
                num_supported_claims, num_refuted_claims, num_controversial_claims,
                factuality=overall_factuality,
            )

        num_tokens = len(self.encoding.encode(raw_text))
        
        output = FactCheckOutput(
            raw_text=raw_text, token_count=num_tokens,
            usage=self._get_usage(), claim_detail=claim_detail, summary=summary,
        )

        logger.info(f"== Overall Factuality: {output.summary.factuality}\n")

        if return_dict:
            output_dict = asdict(output)
            output_dict['sag'] = sag or {"nodes": [], "edges": []}
            return output_dict
        else:
            return output