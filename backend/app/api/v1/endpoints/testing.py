"""
API endpoints for adversarial testing and quality assurance
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import asyncio
import logging

from app.services.adversarial_testing import (
    AdversarialTester, TestSuite, AttackType, AttackResult
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/testing", tags=["testing"])

# Initialize tester
tester = AdversarialTester()

class TestRequest(BaseModel):
    text: str
    attack_types: List[str] = []
    parameters: Dict[str, Any] = {}
    run_async: bool = False

class TestSuiteRequest(BaseModel):
    name: str
    description: str
    test_cases: List[Dict[str, Any]]
    expected_robustness: float = 0.8
    metadata: Dict[str, Any] = {}

class TestResult(BaseModel):
    test_id: str
    status: str
    results: Optional[List[AttackResult]] = None
    statistics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Store for async test results
test_results = {}

@router.post("/run-single-test")
async def run_single_test(request: TestRequest):
    """
    Run a single adversarial test on the provided text
    """
    try:
        if not request.attack_types:
            # Run all attack types if none specified
            attack_types = [attack_type.value for attack_type in AttackType]
        else:
            attack_types = request.attack_types
        
        results = []
        
        for attack_type_str in attack_types:
            try:
                attack_type = AttackType(attack_type_str)
                result = await tester.run_attack(
                    attack_type=attack_type,
                    text=request.text,
                    analysis_service=None,  # This would be injected in real implementation
                    **request.parameters
                )
                results.append(result)
            except ValueError:
                logger.warning(f"Invalid attack type: {attack_type_str}")
                continue
            except Exception as e:
                logger.error(f"Error running attack {attack_type_str}: {e}")
                continue
        
        if not results:
            raise HTTPException(status_code=400, detail="No valid attack types provided")
        
        # Calculate statistics
        statistics = tester.analyze_results(results)
        
        return {
            "success": True,
            "results": results,
            "statistics": statistics,
            "message": f"Completed {len(results)} tests"
        }
        
    except Exception as e:
        logger.error(f"Error in run_single_test: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run-test-suite")
async def run_test_suite(request: TestSuiteRequest):
    """
    Run a complete test suite
    """
    try:
        test_suite = TestSuite(
            name=request.name,
            description=request.description,
            test_cases=request.test_cases,
            expected_robustness=request.expected_robustness,
            metadata=request.metadata
        )
        
        results = await tester.run_test_suite(
            test_suite=test_suite,
            analysis_service=None  # This would be injected in real implementation
        )
        
        statistics = tester.analyze_results(results)
        
        return {
            "success": True,
            "test_suite": test_suite.name,
            "results": results,
            "statistics": statistics,
            "message": f"Completed test suite with {len(results)} tests"
        }
        
    except Exception as e:
        logger.error(f"Error in run_test_suite: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run-synthetic-tests")
async def run_synthetic_tests(
    num_cases: int = 100,
    run_async: bool = False
):
    """
    Run synthetic adversarial tests with generated test cases
    """
    try:
        if run_async:
            # Run asynchronously and return test ID
            test_id = f"synthetic_test_{asyncio.get_event_loop().time()}"
            test_results[test_id] = TestResult(
                test_id=test_id,
                status="running",
                results=None,
                statistics=None,
                error=None
            )
            
            # Start background task
            asyncio.create_task(_run_synthetic_tests_async(test_id, num_cases))
            
            return {
                "success": True,
                "test_id": test_id,
                "status": "running",
                "message": "Test started in background"
            }
        else:
            # Run synchronously
            test_suite = tester.generate_synthetic_test_cases(num_cases)
            results = await tester.run_test_suite(
                test_suite=test_suite,
                analysis_service=None  # This would be injected in real implementation
            )
            
            statistics = tester.analyze_results(results)
            
            return {
                "success": True,
                "test_suite": test_suite.name,
                "results": results,
                "statistics": statistics,
                "message": f"Completed {len(results)} synthetic tests"
            }
            
    except Exception as e:
        logger.error(f"Error in run_synthetic_tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _run_synthetic_tests_async(test_id: str, num_cases: int):
    """Background task to run synthetic tests"""
    try:
        test_suite = tester.generate_synthetic_test_cases(num_cases)
        results = await tester.run_test_suite(
            test_suite=test_suite,
            analysis_service=None  # This would be injected in real implementation
        )
        
        statistics = tester.analyze_results(results)
        
        test_results[test_id] = TestResult(
            test_id=test_id,
            status="completed",
            results=results,
            statistics=statistics,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Error in background synthetic test: {e}")
        test_results[test_id] = TestResult(
            test_id=test_id,
            status="failed",
            results=None,
            statistics=None,
            error=str(e)
        )

@router.get("/test-status/{test_id}")
async def get_test_status(test_id: str):
    """
    Get the status of an async test
    """
    if test_id not in test_results:
        raise HTTPException(status_code=404, detail="Test not found")
    
    result = test_results[test_id]
    
    return {
        "test_id": test_id,
        "status": result.status,
        "results": result.results,
        "statistics": result.statistics,
        "error": result.error
    }

@router.get("/test-results/{test_id}")
async def get_test_results(test_id: str):
    """
    Get the results of a completed test
    """
    if test_id not in test_results:
        raise HTTPException(status_code=404, detail="Test not found")
    
    result = test_results[test_id]
    
    if result.status != "completed":
        raise HTTPException(status_code=400, detail="Test not completed yet")
    
    return {
        "test_id": test_id,
        "status": result.status,
        "results": result.results,
        "statistics": result.statistics
    }

@router.get("/attack-types")
async def get_attack_types():
    """
    Get list of available attack types
    """
    return {
        "attack_types": [
            {
                "name": attack_type.value,
                "description": _get_attack_description(attack_type)
            }
            for attack_type in AttackType
        ]
    }

def _get_attack_description(attack_type: AttackType) -> str:
    """Get description for attack type"""
    descriptions = {
        AttackType.NOISE_INJECTION: "Inject character-level and word-level noise into text",
        AttackType.SEMANTIC_PERTURBATION: "Perturb text while maintaining semantic meaning",
        AttackType.LOGICAL_MANIPULATION: "Manipulate logical structure of arguments",
        AttackType.EVIDENCE_POISONING: "Add fake or misleading evidence",
        AttackType.CONFIDENCE_ATTACK: "Attack confidence calibration",
        AttackType.MULTILINGUAL_ATTACK: "Test multilingual processing robustness",
        AttackType.CONTEXT_MANIPULATION: "Manipulate context to test robustness"
    }
    return descriptions.get(attack_type, "Unknown attack type")

@router.get("/test-statistics")
async def get_test_statistics():
    """
    Get overall test statistics
    """
    try:
        total_tests = len(test_results)
        completed_tests = sum(1 for r in test_results.values() if r.status == "completed")
        failed_tests = sum(1 for r in test_results.values() if r.status == "failed")
        running_tests = sum(1 for r in test_results.values() if r.status == "running")
        
        # Calculate overall robustness if we have completed tests
        overall_robustness = None
        if completed_tests > 0:
            all_results = []
            for result in test_results.values():
                if result.results:
                    all_results.extend(result.results)
            
            if all_results:
                overall_robustness = tester.analyze_results(all_results)
        
        return {
            "total_tests": total_tests,
            "completed_tests": completed_tests,
            "failed_tests": failed_tests,
            "running_tests": running_tests,
            "overall_robustness": overall_robustness
        }
        
    except Exception as e:
        logger.error(f"Error getting test statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/test-results/{test_id}")
async def delete_test_results(test_id: str):
    """
    Delete test results
    """
    if test_id not in test_results:
        raise HTTPException(status_code=404, detail="Test not found")
    
    del test_results[test_id]
    
    return {
        "success": True,
        "message": f"Test results {test_id} deleted"
    }

@router.delete("/test-results")
async def clear_all_test_results():
    """
    Clear all test results
    """
    test_results.clear()
    
    return {
        "success": True,
        "message": "All test results cleared"
    }

@router.get("/health")
async def testing_health():
    """
    Health check for testing service
    """
    return {
        "status": "healthy",
        "service": "adversarial_testing",
        "available_attack_types": len(AttackType),
        "active_tests": len(test_results)
    }

