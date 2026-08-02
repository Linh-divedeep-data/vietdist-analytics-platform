---
description: Chạy full flow bd + skills cho 1 ticket (claim, branch, plan, thực thi, verify, review, finish) — skill bắt buộc gọi qua Skill tool, không được tự ý bỏ qua trừ khi điều kiện thật rõ.
---

Làm ticket **$ARGUMENTS**. Nếu không có ID, chạy `bd ready` hỏi tôi chọn trước.

**Nguyên tắc:** các skill đánh dấu BẮT BUỘC dưới đây phải gọi qua Skill tool thật sự (không phải chỉ nhắc tên rồi tự làm tay). Chỉ được bỏ qua skill nào đánh dấu ĐIỀU KIỆN, và phải nêu rõ lý do vì sao điều kiện không thỏa trước khi bỏ.

1. **Branch** — nếu ticket CHƯA có branch riêng (`git branch --list`, `git status`):
   ```
   git status
   git checkout develop
   git pull origin develop
   git checkout -b feature/<ticket-id>-<slug>
   ```
   Đã ở branch của ticket này rồi (đang làm dở) → bỏ qua bước này.
   ĐIỀU KIỆN: nếu cần workspace cô lập riêng (vd chạy song song nhiều ticket) → gọi thêm skill `using-git-worktrees`.

2. **Claim** — `bd show <ticket-id>` đọc AC/Technical Notes, rồi `bd update <ticket-id> --claim`.

3. **Explore** [BẮT BUỘC] — gọi skill `explore-codebase` (code-review-graph: `get_architecture_overview_tool`, `query_graph_tool`) trước khi đụng code. Không Grep/Read thủ công trước khi skill này chạy xong.

4. **Spec check** [ĐIỀU KIỆN] — đọc AC/Technical Notes trong bd. Nếu có bất kỳ điểm mơ hồ/thiếu quyết định thiết kế (không chỉ "task nhỏ nên chắc không cần") → gọi skill `brainstorming` hoặc `opsx:propose`. Chỉ bỏ qua khi nêu rõ được từng mục AC đã đủ cụ thể để code thẳng, không cần đoán.

5. **Plan** [BẮT BUỘC] — gọi skill `writing-plans` ra plan bám đúng Technical Notes/AC.

6. **Thực thi** [BẮT BUỘC — chọn 1] — gọi skill `executing-plans` (1 file/ít file liên quan chặt) hoặc `subagent-driven-development` (nhiều task độc lập, nhiều file rời nhau). Không được thực thi tay ngoài 2 skill này.

7. **Test** [ĐIỀU KIỆN] — nếu ticket có logic (hàm, điều kiện, transform dữ liệu...) → gọi skill `test-driven-development` (test trước, code sau), bắt buộc. Chỉ bỏ qua khi ticket thuần config/skeleton không có 1 dòng logic nào để test — khi đó thay bằng verify thủ công cụ thể (uv sync, import test, chạy lệnh thật) chứ không phải bỏ trắng.

8. **Lỗi** [ĐIỀU KIỆN] — gặp lỗi giữa chừng → gọi skill `systematic-debugging`, đừng đoán mò sửa bừa.

9. **Verify** [BẮT BUỘC] — gọi skill `verification-before-completion`: chạy lệnh thật, xem output thật, không tự nhận "xong" khi chưa chạy.

10. **Review diff** [BẮT BUỘC] — gọi skill `review-changes` (code-review-graph `detect_changes_tool` + `get_review_context_tool`).

11. **Finish branch** [BẮT BUỘC] — gọi skill `finishing-a-development-branch` quyết định merge thẳng hay tạo PR.

12. **Đóng phiên** — `bd preflight`, `git status`. Báo cáo: skill nào đã gọi ở mỗi bước, skill điều kiện nào bị bỏ qua kèm lý do, file đổi, kết quả verify, đề xuất lệnh git/bd close cụ thể. **KHÔNG tự `bd close`, KHÔNG tự commit/push** — chờ tôi duyệt.
