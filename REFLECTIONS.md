# Reflections

## 1. Human rewrite trước routing

Nếu email vừa được generate xong nhưng chưa routing, có thể dùng `interrupt_after` ở generation node. LangGraph sẽ checkpoint output của node đó và dừng sau khi node hoàn tất; reviewer có thể sửa nội dung rồi resume để routing đọc bản đã chỉnh. Tương đương về mặt thiết kế là `interrupt_before` routing node: generation đã hoàn tất, checkpoint nằm ngay trước routing, nên resume sẽ chạy routing với state đã được human cập nhật. Khác biệt chính là vị trí ngữ nghĩa của pause: `interrupt_after` gắn với việc kiểm duyệt output generation, còn `interrupt_before` gắn với việc chặn bước routing sắp xảy ra. Cả hai đều cần cùng checkpointer và `thread_id` ổn định; không nên giả lập bằng boolean return trong node.

## 2. Alert fatigue

Không nên đưa mọi confidence thấp vào một hàng đợi phẳng. Có thể gom batch các case tương tự để reviewer xử lý theo mẫu, xếp queue theo mức độ rủi ro và giá trị khách hàng, đồng thời theo dõi calibration của confidence. Threshold có thể động theo loại action/risk. Quyết định approve/reject/edit của reviewer trở thành dữ liệu active learning để cải thiện engine. Những category đủ an toàn có thể auto-execute; với phần còn lại dùng sampling và audit định kỳ thay vì review 100%. Các cơ chế này giảm số interrupt nhưng vẫn giữ được kiểm soát ở điểm có hậu quả lớn.

## 3. Confidence calibration

Confidence do LLM tự báo cáo không mặc nhiên là xác suất đã calibrated: model có thể overconfident và điểm 0.9 không có nghĩa 90% đúng. Cần đánh giá trên historical labelled data bằng calibration curve, Brier score và Expected Calibration Error (ECE). Nếu dữ liệu phù hợp, Platt scaling hoặc isotonic regression có thể biến score thô thành probability tốt hơn. Nên kết hợp external evidence và business validation thay vì chỉ tin self-report. Dù đã calibrated, confidence không được vượt qua hard policy: `increase_credit_limit` vẫn luôn cần human review.
