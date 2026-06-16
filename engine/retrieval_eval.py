from typing import List, Dict


class RetrievalEvaluator:
    def calculate_hit_rate(self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = 3) -> float:
        if not expected_ids:
            return 1.0 if not retrieved_ids else 0.0
        top_retrieved = retrieved_ids[:top_k]
        hit = any(doc_id in top_retrieved for doc_id in expected_ids)
        return 1.0 if hit else 0.0

    def calculate_mrr(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        if not expected_ids:
            return 1.0 if not retrieved_ids else 0.0
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_ids:
                return 1.0 / (i + 1)
        return 0.0

    async def evaluate_single(self, expected_ids: List[str], retrieved_ids: List[str]) -> Dict:
        hit_rate = self.calculate_hit_rate(expected_ids, retrieved_ids)
        mrr = self.calculate_mrr(expected_ids, retrieved_ids)
        return {"hit_rate": hit_rate, "mrr": mrr}

    async def evaluate_batch(self, dataset: List[Dict]) -> Dict:
        hit_rates = []
        mrrs = []
        for case in dataset:
            expected = case.get("expected_retrieval_ids", [])
            retrieved = case.get("retrieved_ids", [])
            hr = self.calculate_hit_rate(expected, retrieved)
            mrr = self.calculate_mrr(expected, retrieved)
            hit_rates.append(hr)
            mrrs.append(mrr)
        avg_hit_rate = sum(hit_rates) / len(hit_rates) if hit_rates else 0
        avg_mrr = sum(mrrs) / len(mrrs) if mrrs else 0
        return {"avg_hit_rate": avg_hit_rate, "avg_mrr": avg_mrr}
