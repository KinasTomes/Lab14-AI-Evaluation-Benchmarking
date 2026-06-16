import asyncio
import time
from typing import List, Dict
from engine.retrieval_eval import RetrievalEvaluator


class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge
        self.retrieval_eval = RetrievalEvaluator()
        self.semaphore = asyncio.Semaphore(2)

    async def _run_with_retry(self, test_case: Dict, max_retries: int = 5) -> Dict:
        for attempt in range(max_retries):
            try:
                return await self._run_single(test_case)
            except Exception as e:
                if "429" in str(e) or "RateLimit" in str(e):
                    wait = 10 * (2 ** attempt)
                    print(f"  Rate limited, đợi {wait}s... (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait)
                else:
                    raise
        raise Exception(f"Failed after {max_retries} retries: {test_case['question'][:50]}")

    async def _run_single(self, test_case: Dict) -> Dict:
        async with self.semaphore:
            await asyncio.sleep(0.3)
            start_time = time.perf_counter()

            response = await self.agent.query(test_case["question"])
            latency = time.perf_counter() - start_time

            ragas_scores = await self.evaluator.score(test_case, response)

            judge_result = await self.judge.evaluate_multi_judge(
                test_case["question"],
                response["answer"],
                test_case.get("expected_answer", "")
            )

            expected_ids = test_case.get("expected_retrieval_ids", [])
            retrieved_ids = response.get("metadata", {}).get("retrieved_ids", [])
            retrieval_metrics = await self.retrieval_eval.evaluate_single(expected_ids, retrieved_ids)

            tokens_used = response.get("metadata", {}).get("tokens_used", 0)
            cost_estimate = (tokens_used / 1000) * 0.002

            return {
                "test_case": test_case["question"],
                "expected_answer": test_case.get("expected_answer", ""),
                "agent_response": response["answer"],
                "latency": round(latency, 3),
                "tokens_used": tokens_used,
                "cost_estimate": round(cost_estimate, 6),
                "ragas": ragas_scores,
                "retrieval": retrieval_metrics,
                "judge": judge_result,
                "difficulty": test_case.get("metadata", {}).get("difficulty", "unknown"),
                "type": test_case.get("metadata", {}).get("type", "unknown"),
                "status": "fail" if judge_result["final_score"] < 3 else "pass"
            }

    async def run_all(self, dataset: List[Dict]) -> List[Dict]:
        results = []
        total = len(dataset)
        for i, case in enumerate(dataset):
            result = await self._run_with_retry(case)
            results.append(result)
            print(f"  Tiến độ: {i + 1}/{total}")
        return results
