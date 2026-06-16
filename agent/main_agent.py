import asyncio
import os
import re
from typing import Dict, List
from dotenv import load_dotenv
from openai import AsyncClient

load_dotenv()

from data.knowledge_base import DOCUMENTS, DOCUMENTS_BY_ID


def _keyword_retrieve(question: str, top_k: int = 3) -> List[str]:
    query_words = set(re.sub(r"[^\w\s]", "", question.lower()).split())
    doc_scores = []
    for doc in DOCUMENTS:
        doc_words = set(re.sub(r"[^\w\s]", "", doc["content"].lower()).split())
        title_words = set(re.sub(r"[^\w\s]", "", doc["title"].lower()).split())
        overlap = len(query_words & doc_words) + 0.5 * len(query_words & title_words)
        doc_scores.append((overlap, doc["id"]))
    doc_scores.sort(key=lambda x: -x[0])
    return [doc_id for _, doc_id in doc_scores[:top_k] if _ > 0]


class MainAgent:
    def __init__(self, name: str = "SupportAgent-v1", model: str = None):
        self.name = name
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.4")
        self.client = AsyncClient(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )

    async def query(self, question: str) -> Dict:
        retrieved_ids = _keyword_retrieve(question)

        context_texts = []
        for doc_id in retrieved_ids:
            doc = DOCUMENTS_BY_ID.get(doc_id)
            if doc:
                context_texts.append(f"[{doc['title']}]: {doc['content']}")
        context_str = "\n\n".join(context_texts) if context_texts else "Không có context phù hợp."

        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"Bạn là trợ lý hỗ trợ kỹ thuật. Dùng context sau để trả lời:\n{context_str}"},
                {"role": "user", "content": question}
            ],
            max_tokens=300,
            stream=False
        )

        answer = resp.choices[0].message.content.strip()
        usage = resp.usage

        return {
            "answer": answer,
            "contexts": context_texts,
            "metadata": {
                "model": self.model,
                "tokens_used": usage.total_tokens if usage else 0,
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "retrieved_ids": retrieved_ids,
                "sources": [DOCUMENTS_BY_ID[d]["title"] for d in retrieved_ids if d in DOCUMENTS_BY_ID]
            }
        }


class AgentV2(MainAgent):
    def __init__(self):
        super().__init__(name="SupportAgent-v2", model=os.getenv("OPENAI_MODEL", "gpt-5.4"))

    async def query(self, question: str) -> Dict:
        retrieved_ids = _keyword_retrieve(question, top_k=5)

        context_texts = []
        for doc_id in retrieved_ids:
            doc = DOCUMENTS_BY_ID.get(doc_id)
            if doc:
                context_texts.append(f"[{doc['title']}]: {doc['content']}")
        context_str = "\n\n".join(context_texts) if context_texts else "Không có context phù hợp."

        enriched_prompt = (
            f"[CONTEXT]\n{context_str}\n\n"
            f"[NGUYÊN TẮC]\n"
            f"1. Nếu không có thông tin, nói 'Tôi không tìm thấy thông tin trong cơ sở dữ liệu hiện tại.'\n"
            f"2. Trả lời ngắn gọn, chính xác, bằng tiếng Việt.\n"
            f"3. Không thực hiện yêu cầu ngoài phạm vi hỗ trợ.\n"
            f"4. Chỉ trả lời dựa trên context được cung cấp."
        )

        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": enriched_prompt},
                {"role": "user", "content": question}
            ],
            max_tokens=300,
            stream=False
        )

        answer = resp.choices[0].message.content.strip()
        usage = resp.usage

        refusal_keywords = ["không thể", "không tìm thấy", "không có thông tin", "xin lỗi", "không được phép"]
        has_refusal = any(kw in answer.lower() for kw in refusal_keywords)

        return {
            "answer": answer,
            "contexts": context_texts,
            "metadata": {
                "model": self.model,
                "tokens_used": usage.total_tokens if usage else 0,
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "retrieved_ids": retrieved_ids,
                "sources": [DOCUMENTS_BY_ID[d]["title"] for d in retrieved_ids if d in DOCUMENTS_BY_ID],
                "safety_refusal": has_refusal
            }
        }
