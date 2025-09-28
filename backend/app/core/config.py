from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, List, Dict

import yaml


BASE_DIR = Path(__file__).resolve().parents[2]
ETHICAL_CONFIG_PATH = BASE_DIR / "backend" / "app" / "core" / "ethical_config.yaml"


class Settings:
    app_name: str = "FailSafe API"
    version: str = "0.1.0"
    ethical: dict[str, Any]

    def __init__(self) -> None:
        self.ethical = self._load_ethical()

    # Rate Limiting
    @property
    def rate_limit_per_minute(self) -> int:
        rl = self.ethical.get("rate_limit", {}) if isinstance(self.ethical, dict) else {}
        return int(rl.get("max_per_minute", 120))

    @property
    def rate_limit_per_hour(self) -> int:
        rl = self.ethical.get("rate_limit", {}) if isinstance(self.ethical, dict) else {}
        return int(rl.get("max_per_hour", 1000))

    @property
    def rate_limit_per_day(self) -> int:
        rl = self.ethical.get("rate_limit", {}) if isinstance(self.ethical, dict) else {}
        return int(rl.get("max_per_day", 10000))

    @property
    def rate_limit_burst(self) -> int:
        rl = self.ethical.get("rate_limit", {}) if isinstance(self.ethical, dict) else {}
        return int(rl.get("burst_limit", 20))

    # Logging
    @property
    def logging_level(self) -> str:
        log = self.ethical.get("logging", {}) if isinstance(self.ethical, dict) else {}
        return str(log.get("level", "INFO")).upper()

    @property
    def structured_logging(self) -> bool:
        log = self.ethical.get("logging", {}) if isinstance(self.ethical, dict) else {}
        return bool(log.get("structured_logging", True))

    @property
    def log_format(self) -> str:
        log = self.ethical.get("logging", {}) if isinstance(self.ethical, dict) else {}
        return str(log.get("log_format", "json"))

    # Verification & Anti-Hallucination
    @property
    def verification_calibration(self) -> dict[str, Any]:
        ver = self.ethical.get("verification", {}) if isinstance(self.ethical, dict) else {}
        calib = ver.get("calibration", {}) if isinstance(ver, dict) else {}
        return {
            "a": float(calib.get("a", 6.0)),
            "b": float(calib.get("b", 0.6)),
            "multi_source_boost": float(calib.get("multi_source_boost", 0.05)),
            "decent_hit_threshold": float(calib.get("decent_hit_threshold", 0.6)),
            "truthfulqa_calibration": bool(calib.get("truthfulqa_calibration", True)),
        }

    @property
    def anti_hallucination(self) -> dict[str, Any]:
        ver = self.ethical.get("verification", {}) if isinstance(self.ethical, dict) else {}
        ah = ver.get("anti_hallucination", {}) if isinstance(ver, dict) else {}
        return {
            "max_retries": int(ah.get("max_retries", 1)),
            "retry_threshold": float(ah.get("retry_threshold", 0.7)),
            "min_improvement": float(ah.get("min_improvement", 0.05)),
            "self_reflection_enabled": bool(ah.get("self_reflection_enabled", True)),
            "multi_agent_cross_check": bool(ah.get("multi_agent_cross_check", True)),
            "retrieval_first_pipeline": bool(ah.get("retrieval_first_pipeline", True)),
            "structured_output_validation": bool(ah.get("structured_output_validation", True)),
        }

    @property
    def confidence_thresholds(self) -> dict[str, float]:
        ver = self.ethical.get("verification", {}) if isinstance(self.ethical, dict) else {}
        thresholds = ver.get("confidence_thresholds", {}) if isinstance(ver, dict) else {}
        return {
            "high": float(thresholds.get("high", 0.8)),
            "medium": float(thresholds.get("medium", 0.6)),
            "low": float(thresholds.get("low", 0.4)),
            "minimum": float(thresholds.get("minimum", 0.1)),
        }

    @property
    def evidence_requirements(self) -> dict[str, Any]:
        ver = self.ethical.get("verification", {}) if isinstance(self.ethical, dict) else {}
        req = ver.get("evidence_requirements", {}) if isinstance(ver, dict) else {}
        return {
            "min_sources": int(req.get("min_sources", 2)),
            "min_confidence": float(req.get("min_confidence", 0.6)),
            "cross_validation_required": bool(req.get("cross_validation_required", True)),
        }

    # Retrieval & Caching
    @property
    def retrieval_cache(self) -> dict[str, Any]:
        r = self.ethical.get("retrieval", {}) if isinstance(self.ethical, dict) else {}
        cache = r.get("cache", {}) if isinstance(r, dict) else {}
        return {
            "ttl_seconds": int(cache.get("ttl_seconds", 600)),
            "max_entries": int(cache.get("max_entries", 256)),
            "compression_enabled": bool(cache.get("compression_enabled", True)),
        }

    @property
    def source_prioritization(self) -> dict[str, float]:
        r = self.ethical.get("retrieval", {}) if isinstance(self.ethical, dict) else {}
        priority = r.get("source_prioritization", {}) if isinstance(r, dict) else {}
        return {
            "academic_sources": float(priority.get("academic_sources", 1.0)),
            "government_sources": float(priority.get("government_sources", 0.9)),
            "news_sources": float(priority.get("news_sources", 0.7)),
            "social_media": float(priority.get("social_media", 0.3)),
            "user_generated": float(priority.get("user_generated", 0.1)),
        }

    @property
    def cache(self) -> dict[str, Any]:
        cache_config = self.ethical.get("cache", {}) if isinstance(self.ethical, dict) else {}
        return {
            "max_memory_items": int(cache_config.get("max_memory_items", 1000)),
            "memory_ttl_seconds": int(cache_config.get("memory_ttl_seconds", 300)),
            "disk_ttl_seconds": int(cache_config.get("disk_ttl_seconds", 3600)),
            "max_disk_size_mb": int(cache_config.get("max_disk_size_mb", 100)),
            "compression": bool(cache_config.get("compression", True)),
            "eviction_policy": str(cache_config.get("eviction_policy", "lru")),
            "distributed_caching": bool(cache_config.get("distributed_caching", False)),
            "cache_warming": bool(cache_config.get("cache_warming", True)),
        }

    # AI Detection
    @property
    def ai_detection(self) -> dict[str, Any]:
        ai = self.ethical.get("ai_detection", {}) if isinstance(self.ethical, dict) else {}
        return {
            "multi_signal_approach": bool(ai.get("multi_signal_approach", True)),
            "ensemble_voting": bool(ai.get("ensemble_voting", True)),
            "active_learning": bool(ai.get("active_learning", True)),
            "noise_injection_test": bool(ai.get("noise_injection_test", True)),
            "detection_methods": ai.get("detection_methods", ["roberta_detector", "stylometry_analysis"]),
            "thresholds": ai.get("thresholds", {"ai_generated": 0.7, "human_written": 0.3, "uncertain": 0.4}),
        }

    # Multilingual Support
    @property
    def multilingual(self) -> dict[str, Any]:
        multi = self.ethical.get("multilingual", {}) if isinstance(self.ethical, dict) else {}
        return {
            "supported_languages": multi.get("supported_languages", ["en", "vi", "es", "fr", "de"]),
            "auto_detection": bool(multi.get("auto_detection", True)),
            "translation_enabled": bool(multi.get("translation_enabled", True)),
            "cross_lingual_embeddings": bool(multi.get("cross_lingual_embeddings", True)),
            "cultural_adaptation": bool(multi.get("cultural_adaptation", True)),
            "language_specific_models": bool(multi.get("language_specific_models", True)),
        }

    # Performance
    @property
    def performance(self) -> dict[str, Any]:
        perf = self.ethical.get("performance", {}) if isinstance(self.ethical, dict) else {}
        return {
            "early_exit_enabled": bool(perf.get("early_exit_enabled", True)),
            "model_quantization": bool(perf.get("model_quantization", True)),
            "batch_processing": bool(perf.get("batch_processing", True)),
            "async_processing": bool(perf.get("async_processing", True)),
            "memory_optimization": bool(perf.get("memory_optimization", True)),
            "gpu_utilization": str(perf.get("gpu_utilization", "auto")),
            "cpu_cores": str(perf.get("cpu_cores", "auto")),
        }

    # Security
    @property
    def security(self) -> dict[str, Any]:
        sec = self.ethical.get("security", {}) if isinstance(self.ethical, dict) else {}
        return {
            "authentication_required": bool(sec.get("authentication_required", False)),
            "api_key_required": bool(sec.get("api_key_required", False)),
            "rate_limiting": bool(sec.get("rate_limiting", True)),
            "input_validation": bool(sec.get("input_validation", True)),
            "output_sanitization": bool(sec.get("output_sanitization", True)),
            "sql_injection_protection": bool(sec.get("sql_injection_protection", True)),
            "xss_protection": bool(sec.get("xss_protection", True)),
            "csrf_protection": bool(sec.get("csrf_protection", True)),
            "encryption_at_rest": bool(sec.get("encryption_at_rest", True)),
            "encryption_in_transit": bool(sec.get("encryption_in_transit", True)),
        }

    # Privacy
    @property
    def privacy(self) -> dict[str, Any]:
        priv = self.ethical.get("privacy", {}) if isinstance(self.ethical, dict) else {}
        return {
            "anonymize_logs": bool(priv.get("anonymize_logs", True)),
            "pii_redaction": bool(priv.get("pii_redaction", True)),
            "data_encryption": bool(priv.get("data_encryption", True)),
            "encryption_algorithm": str(priv.get("encryption_algorithm", "AES-256")),
            "anonymization_methods": priv.get("anonymization_methods", ["tokenization", "hashing"]),
            "data_retention_policy": priv.get("data_retention_policy", {}),
            "gdpr_compliance": priv.get("gdpr_compliance", {}),
        }

    # Fairness
    @property
    def fairness(self) -> dict[str, Any]:
        fair = self.ethical.get("fairness", {}) if isinstance(self.ethical, dict) else {}
        return {
            "demographic_parity_target": float(fair.get("demographic_parity_target", 0.0)),
            "equalized_odds_threshold": float(fair.get("equalized_odds_threshold", 0.1)),
            "calibration_threshold": float(fair.get("calibration_threshold", 0.05)),
            "protected_attributes": fair.get("protected_attributes", ["gender", "race", "age"]),
            "bias_mitigation_strategies": fair.get("bias_mitigation_strategies", ["demographic_parity"]),
            "source_diversity_boost": float(fair.get("source_diversity_boost", 0.1)),
            "global_south_priority": bool(fair.get("global_south_priority", True)),
            "cultural_sensitivity_check": bool(fair.get("cultural_sensitivity_check", True)),
        }

    # Legal
    @property
    def legal(self) -> dict[str, Any]:
        legal = self.ethical.get("legal", {}) if isinstance(self.ethical, dict) else {}
        return {
            "medical_disclaimer": str(legal.get("medical_disclaimer", "Không thay thế tư vấn chuyên môn")),
            "gdpr_compliant": bool(legal.get("gdpr_compliant", True)),
            "hipaa_compliant": bool(legal.get("hipaa_compliant", False)),
            "ccpa_compliant": bool(legal.get("ccpa_compliant", True)),
            "disclaimer_texts": legal.get("disclaimer_texts", {}),
            "jurisdiction": str(legal.get("jurisdiction", "global")),
            "content_moderation": legal.get("content_moderation", {}),
        }

    # Development & Testing
    @property
    def development(self) -> dict[str, Any]:
        dev = self.ethical.get("development", {}) if isinstance(self.ethical, dict) else {}
        return {
            "debug_mode": bool(dev.get("debug_mode", False)),
            "test_mode": bool(dev.get("test_mode", False)),
            "mock_services": bool(dev.get("mock_services", False)),
            "synthetic_data_generation": bool(dev.get("synthetic_data_generation", True)),
            "adversarial_testing": bool(dev.get("adversarial_testing", True)),
            "load_testing": bool(dev.get("load_testing", True)),
            "unit_testing": bool(dev.get("unit_testing", True)),
            "integration_testing": bool(dev.get("integration_testing", True)),
        }

    # Monitoring
    @property
    def monitoring(self) -> dict[str, Any]:
        mon = self.ethical.get("monitoring", {}) if isinstance(self.ethical, dict) else {}
        return {
            "health_checks": bool(mon.get("health_checks", True)),
            "performance_metrics": bool(mon.get("performance_metrics", True)),
            "error_tracking": bool(mon.get("error_tracking", True)),
            "alerting": bool(mon.get("alerting", True)),
            "dashboard": bool(mon.get("dashboard", True)),
            "log_aggregation": bool(mon.get("log_aggregation", True)),
            "metrics_export": bool(mon.get("metrics_export", True)),
            "alert_channels": mon.get("alert_channels", ["email"]),
        }

    def _load_ethical(self) -> dict[str, Any]:
        if ETHICAL_CONFIG_PATH.exists():
            with ETHICAL_CONFIG_PATH.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {"bias_threshold": 0.2, "retention_days": 30, "consent_required": True}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


