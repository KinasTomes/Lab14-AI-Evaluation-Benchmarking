# Individual Reflection — Hung

## 1. Tổng quan đóng góp

Xây dựng toàn bộ hệ thống **AI Evaluation Factory** từ skeleton code, bao gồm:
- Synthetic Data Generator (61 test cases, bao gồm adversarial/hard cases)
- Multi-Judge Consensus Engine (gpt-5.5 + gpt-5.4)
- Retrieval Evaluator (Hit Rate & MRR)
- Async Benchmark Runner với retry logic
- Regression Testing & Release Gate tự động

## 2. Kỹ thuật đã áp dụng

### MRR (Mean Reciprocal Rank)
- MRR đo vị trí trung bình của document đúng trong kết quả retrieval
- MRR = 0.80 → document đúng thường xuất hiện ở vị trí ~1.25
- Ảnh hưởng trực tiếp đến chất lượng Generation vì LLM chỉ đọc được top-K context

### Multi-Judge Agreement Rate
- Sử dụng 2 model khác nhau (gpt-5.5 + gpt-4) để đánh giá khách quan
- Agreement Rate = 98.9% cho V1 → 2 judge gần như đồng thuận hoàn toàn
- Khi scores lệch > 1 điểm → conflict resolution bằng trung bình
- Điểm yếu: chưa implement Cohen's Kappa (chỉ dùng agreement rate đơn giản)

### Position Bias
- Implement `check_position_bias()` trong LLMJudge
- Kiểm tra xem việc đổi thứ tự 2 câu trả lời có thay đổi kết quả judge không
- Chưa được chạy thực tế trong benchmark nhưng code đã sẵn sàng

### Async & Rate Limiting
- Pipeline chạy bất đồng bộ với Semaphore(2) để tránh rate limit
- Retry logic exponential backoff (5s → 10s → 20s → ...) khi gặp 429
- zonetoken API rate limit rất gắt, cần delay 0.3s giữa mỗi request

## 3. Trade-off Chi phí vs Chất lượng

| Factor | Chi phí | Chất lượng |
|--------|---------|------------|
| Thêm Judge thứ 2 | Tăng 2x tokens | Tăng độ tin cậy lên 98.9% |
| V2 safety prompt | Tăng tokens (+35%) | Giảm hallucination nhưng tăng refusal rate |
| Keyword retrieval | Miễn phí | Hit Rate 83.6% — chấp nhận được |
| Vector retrieval | Cần FAISS/Embedding | Hit Rate dự kiến >95% |

## 4. Vấn đề phát sinh & cách giải quyết

| Vấn đề | Nguyên nhân | Giải pháp |
|--------|-------------|-----------|
| OpenAI SDK trả về SSE stream thay vì structured response | zonetoken API mặc định streaming | Thêm `stream=False` explicit trong every API call |
| Rate limit 429 liên tục | zonetoken rate limit gắt | Thêm exponential backoff + Semaphore(2) + 0.3s delay |
| Unicode encoding error (cp1252) | PowerShell default encoding | Set `PYTHONIOENCODING=utf-8` |
| V2 score thấp hơn V1 | Safety prompt quá chặt → refusal nhiều hơn | Thêm safety_refusal flag để phân biệt "từ chối đúng" vs "trả lời sai" |
| Hit Rate = 0.0 | Agent không trả về retrieved_ids | Thêm keyword retrieval layer trong MainAgent |
