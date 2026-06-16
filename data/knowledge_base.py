DOCUMENTS = [
    {"id": "doc_001", "title": "Hướng dẫn đổi mật khẩu", "content": "Để đổi mật khẩu, nhân viên cần truy cập vào hệ thống portal, chọn mục 'Cài đặt bảo mật', sau đó chọn 'Đổi mật khẩu'. Hệ thống yêu cầu nhập mật khẩu cũ, mật khẩu mới (tối thiểu 8 ký tự, bao gồm chữ hoa, chữ thường và số), và xác nhận mật khẩu mới. Quá trình này mất khoảng 2 phút."},
    {"id": "doc_002", "title": "Chính sách nghỉ phép", "content": "Nhân viên chính thức được nghỉ 12 ngày phép năm. Để xin nghỉ, nhân viên cần gửi đơn qua hệ thống HR trước ít nhất 3 ngày làm việc. Nghỉ phép đột xuất cần thông báo trước ít nhất 2 giờ. Nghỉ ốm cần có giấy khám bệnh nếu nghỉ trên 2 ngày liên tiếp."},
    {"id": "doc_003", "title": "Quy trình bảo mật dữ liệu", "content": "Tất cả dữ liệu khách hàng phải được mã hóa AES-256. Nhân viên không được phép sao chép dữ liệu ra thiết bị cá nhân. Việc truy cập dữ liệu nhạy cảm được ghi log và giám sát 24/7. Vi phạm chính sách bảo mật có thể dẫn đến sa thải."},
    {"id": "doc_004", "title": "Hướng dẫn cài đặt VPN", "content": "Nhân viên cần cài đặt VPN để truy cập hệ thống nội bộ từ xa. Tải ứng dụng 'SecureConnect' từ IT Portal. Sử dụng tài khoản công ty để đăng nhập. VPN tự động ngắt kết nối sau 8 giờ không hoạt động. Liên hệ IT nếu gặp lỗi xác thực."},
    {"id": "doc_005", "title": "Chính sách mua sắm", "content": "Đơn mua sắm dưới 5 triệu cần quản lý trực tiếp phê duyệt. Từ 5-50 triệu cần trưởng phòng phê duyệt. Trên 50 triệu cần giám đốc phê duyệt. Tất cả đơn mua sắm phải có 3 báo giá cạnh tranh. Hàng hóa trên 100 triệu phải qua đấu thầu."},
    {"id": "doc_006", "title": "Quy định sử dụng email", "content": "Email công ty chỉ được sử dụng cho mục đích công việc. Không gửi email spam, email cá nhân hoặc chia sẻ thông tin nhạy cảm qua email không mã hóa. Kích thước tệp đính kèm tối đa là 25MB. Email nội bộ cần trả lời trong vòng 4 giờ làm việc."},
    {"id": "doc_007", "title": "Đào tạo nhân viên mới", "content": "Nhân viên mới sẽ trải qua 3 tuần đào tạo: Tuần 1 - Văn hóa công ty và quy trình, Tuần 2 - Đào tạo kỹ thuật và công cụ, Tuần 3 - Shadowing và đánh giá. Sau đào tạo, nhân viên mới sẽ có bài kiểm tra với điểm đạt tối thiểu 70%."},
    {"id": "doc_008", "title": "Xử lý khiếu nại khách hàng", "content": "Tiếp nhận khiếu nại qua hệ thống ticketing. Phân loại: Mức 1 (phản hồi trong 4 giờ), Mức 2 (phản hồi trong 2 giờ), Mức 3 (phản hồi ngay lập tức). Khiếu nại phải được giải quyết trong vòng 48 giờ. Khách hàng không hài lòng có thể yêu cầu lên cấp trên."},
    {"id": "doc_009", "title": "Chính sách làm việc từ xa", "content": "Nhân viên được làm việc từ xa tối đa 2 ngày/tuần. Cần đăng ký trước với quản lý. Yêu cầu có kết nối internet ổn định và không gian làm việc riêng tư. Giờ làm việc từ xa: 8:00-17:00, có check-in qua Zoom lúc 8:30."},
    {"id": "doc_010", "title": "Quy trình báo cáo sự cố IT", "content": "Sự cố IT được phân loại: Critical (ngừng hoạt động toàn bộ), Major (ảnh hưởng nhiều người dùng), Minor (ảnh hưởng cá nhân). Critical được ưu tiên xử lý trong 30 phút. Gọi hotline IT để báo cáo khẩn cấp. Theo dõi trạng thái qua IT Portal."},
]

DOCUMENTS_BY_ID = {doc["id"]: doc for doc in DOCUMENTS}

CHUNKS = []
for doc in DOCUMENTS:
    words = doc["content"].split()
    chunk_size = 30
    for i in range(0, len(words), chunk_size):
        chunk_words = words[i:i+chunk_size]
        chunk_text = " ".join(chunk_words)
        chunk_id = f"{doc['id']}_chunk_{i//chunk_size}"
        CHUNKS.append({"id": chunk_id, "doc_id": doc["id"], "title": doc["title"], "content": chunk_text})
