import asyncio
import json
import os
import time
from engine.runner import BenchmarkRunner
from engine.llm_judge import LLMJudge
from agent.main_agent import MainAgent, AgentV2


class ExpertEvaluator:
    async def score(self, case, resp):
        faithfulness_scores = []
        relevancy_scores = []
        expected = case.get("expected_answer", "")
        actual = resp.get("answer", "")
        words_expected = set(expected.lower().split()) if expected else set()
        words_actual = set(actual.lower().split()) if actual else set()
        overlap = words_expected & words_actual if words_expected else set()
        faithfulness = len(overlap) / max(len(words_expected), 1) if words_expected else 0.5
        relevancy = len(overlap) / max(len(words_actual), 1) if words_actual else 0.5
        faithfulness_scores.append(faithfulness)
        relevancy_scores.append(relevancy)
        return {
            "faithfulness": round(faithfulness, 4),
            "relevancy": round(relevancy, 4),
            "retrieval": {"hit_rate": 0.0, "mrr": 0.0}
        }


def compute_summary(results: list, version: str) -> dict:
    total = len(results)
    if total == 0:
        return {"metadata": {"version": version, "total": 0}, "metrics": {}}

    avg_score = sum(r["judge"]["final_score"] for r in results) / total
    avg_hit_rate = sum(r["retrieval"]["hit_rate"] for r in results) / total
    avg_mrr = sum(r["retrieval"]["mrr"] for r in results) / total
    avg_agreement = sum(r["judge"]["agreement_rate"] for r in results) / total
    avg_latency = sum(r["latency"] for r in results) / total
    avg_cost = sum(r["cost_estimate"] for r in results) / total
    total_tokens = sum(r["tokens_used"] for r in results)
    pass_count = sum(1 for r in results if r["status"] == "pass")
    fail_count = total - pass_count
    pass_rate = pass_count / total

    return {
        "metadata": {
            "version": version,
            "total": total,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "pass_rate": round(pass_rate, 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "metrics": {
            "avg_score": round(avg_score, 4),
            "hit_rate": round(avg_hit_rate, 4),
            "mrr": round(avg_mrr, 4),
            "agreement_rate": round(avg_agreement, 4),
            "avg_latency": round(avg_latency, 3),
            "avg_cost_per_case": round(avg_cost, 6),
            "total_tokens": total_tokens,
            "total_cost": round(avg_cost * total, 6)
        }
    }


def make_release_decision(v1_summary: dict, v2_summary: dict) -> dict:
    v1_score = v1_summary["metrics"]["avg_score"]
    v2_score = v2_summary["metrics"]["avg_score"]
    v1_hit = v1_summary["metrics"]["hit_rate"]
    v2_hit = v2_summary["metrics"]["hit_rate"]
    v1_mrr = v1_summary["metrics"]["mrr"]
    v2_mrr = v2_summary["metrics"]["mrr"]
    v1_agree = v1_summary["metrics"]["agreement_rate"]
    v2_agree = v2_summary["metrics"]["agreement_rate"]

    delta_score = v2_score - v1_score
    delta_hit = v2_hit - v1_hit
    delta_mrr = v2_mrr - v1_mrr
    delta_agree = v2_agree - v1_agree

    reasons = []
    if delta_score > 0:
        reasons.append(f"Score tăng {delta_score:+.4f}")
    else:
        reasons.append(f"Score giảm {delta_score:+.4f}")

    quality_pass = delta_score > 0
    retrieval_pass = delta_hit >= 0 and delta_mrr >= 0
    reliability_pass = delta_agree >= 0

    all_pass = quality_pass and retrieval_pass and reliability_pass

    decision = "APPROVE" if all_pass else "BLOCK_RELEASE"
    if decision == "APPROVE":
        reasons.append("Tất cả chỉ số đều cải thiện hoặc giữ nguyên")
    else:
        if not quality_pass:
            reasons.append("Chất lượng giảm")
        if not retrieval_pass:
            reasons.append("Retrieval giảm")
        if not reliability_pass:
            reasons.append("Độ tin cậy Judge giảm")

    return {
        "release_decision": decision,
        "delta_score": round(delta_score, 4),
        "delta_hit_rate": round(delta_hit, 4),
        "delta_mrr": round(delta_mrr, 4),
        "delta_agreement_rate": round(delta_agree, 4),
        "quality_pass": quality_pass,
        "retrieval_pass": retrieval_pass,
        "reliability_pass": reliability_pass,
        "reasoning": ". ".join(reasons)
    }


async def run_benchmark(agent, version: str):
    print(f"Khởi động Benchmark cho {version}...")

    if not os.path.exists("data/golden_set.jsonl"):
        print("Thiếu data/golden_set.jsonl. Hãy chạy 'python data/synthetic_gen.py' trước.")
        return None, None

    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    if not dataset:
        print("File data/golden_set.jsonl rỗng.")
        return None, None

    judge = LLMJudge()
    evaluator = ExpertEvaluator()
    runner = BenchmarkRunner(agent, evaluator, judge)
    results = await runner.run_all(dataset)

    summary = compute_summary(results, version)
    return results, summary


async def main():
    print("=== AI EVALUATION FACTORY ===")
    print()

    v1_results, v1_summary = await run_benchmark(MainAgent(), "Agent_V1_Base")
    if not v1_summary:
        return

    print()
    print("--- Benchmark V1 hoàn tất ---")
    print(f"Score: {v1_summary['metrics']['avg_score']}, Hit Rate: {v1_summary['metrics']['hit_rate']}, MRR: {v1_summary['metrics']['mrr']}")
    print()

    v2_results, v2_summary = await run_benchmark(AgentV2(), "Agent_V2_Optimized")
    if not v2_summary:
        return

    print()
    print("--- Benchmark V2 hoàn tất ---")
    print(f"Score: {v2_summary['metrics']['avg_score']}, Hit Rate: {v2_summary['metrics']['hit_rate']}, MRR: {v2_summary['metrics']['mrr']}")
    print()

    print("=" * 60)
    print("KẾT QUẢ SO SÁNH (REGRESSION)")
    print("=" * 60)
    print(f"{'Chỉ số':<25} {'V1':<12} {'V2':<12} {'Delta':<12}")
    print("-" * 60)
    metrics_keys = ["avg_score", "hit_rate", "mrr", "agreement_rate", "avg_latency", "avg_cost_per_case"]
    for key in metrics_keys:
        v1_val = v1_summary["metrics"].get(key, 0)
        v2_val = v2_summary["metrics"].get(key, 0)
        delta = v2_val - v1_val
        label = key.replace("_", " ").title()
        print(f"{label:<25} {v1_val:<12.4f} {v2_val:<12.4f} {delta:<+12.4f}")

    print("-" * 60)
    print(f"Total Tokens V1: {v1_summary['metrics']['total_tokens']}, V2: {v2_summary['metrics']['total_tokens']}")
    print()

    release_decision = make_release_decision(v1_summary, v2_summary)
    print(f"QUYẾT ĐỊNH: {release_decision['release_decision']}")
    print(f"Lý do: {release_decision['reasoning']}")
    print()

    os.makedirs("reports", exist_ok=True)
    v2_flat = {
        "metadata": v2_summary["metadata"],
        "metrics": v2_summary["metrics"]
    }
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_flat, f, ensure_ascii=False, indent=2)
    with open("reports/regression_report.json", "w", encoding="utf-8") as f:
        json.dump({"v1": v1_summary, "v2": v2_summary, "regression": release_decision}, f, ensure_ascii=False, indent=2)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump({"v1_results": v1_results, "v2_results": v2_results}, f, ensure_ascii=False, indent=2)

    print("Đã lưu reports/summary.json và reports/benchmark_results.json")


if __name__ == "__main__":
    asyncio.run(main())
