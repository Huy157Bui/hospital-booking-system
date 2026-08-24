import json
import time
import urllib.request
import urllib.error

API_URL = "http://127.0.0.1:8000/ai/chat"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

TEST_SUITE = [
    # NHÓM 1: CẤP CỨU KHẨN CẤP
    {
        "name": "TC01 [Cấp cứu]: Khó thở dữ dội + đau ngực",
        "payload": {"message": "Tôi bị khó thở dữ dội và đau ngực, Trung tâm Cấp cứu A9 ở đâu?"},
        "expect_contains": ["cảnh báo", "cấp cứu a9", "78", "giải phóng"],
        "expect_not_contains": []
    },
    {
        "name": "TC02 [Cấp cứu]: Đột quỵ / Bất tỉnh",
        "payload": {"message": "Bố tôi bị đột quỵ, liệt nửa người và bất tỉnh thì đưa đến đâu?"},
        "expect_contains": ["cảnh báo", "cấp cứu", "115"],
        "expect_not_contains": []
    },
    {
        "name": "TC03 [Cấp cứu]: Ngộ độc cấp / Nôn ra máu",
        "payload": {"message": "Người nhà tôi uống nhầm thuốc sâu và đang nôn ra máu tươi!"},
        "expect_contains": ["cảnh báo", "cấp cứu"],
        "expect_not_contains": []
    },

    # NHÓM 2: MULTI-TURN MEMORY
    {
        "name": "TC04 [Đa lượt]: Khám Mắt -> Lọc giá < 400k",
        "payload": {
            "message": "Có bác sĩ nào giá dưới 400k không?",
            "chat_history": [
                {"role": "user", "content": "Tôi muốn khám mắt"},
                {"role": "assistant", "content": "Khoa Mắt Bệnh viện Bạch Mai tiếp nhận khám mắt..."}
            ]
        },
        "expect_contains": ["đào xuân cơ", "385"],
        "expect_not_contains": ["đỗ ngọc sơn", "hồi sức"]
    },
    {
        "name": "TC05 [Đa lượt]: Bé sốt phát ban -> Bác sĩ Nhi",
        "payload": {
            "message": "Cho tôi xem danh sách bác sĩ chuyên khoa này",
            "chat_history": [
                {"role": "user", "content": "Bé nhà tôi 3 tuổi bị sốt cao phát ban"},
                {"role": "assistant", "content": "Bé cần được khám Nhi khoa..."}
            ]
        },
        "expect_contains": ["vũ văn giáp", "nhi khoa", "468"],
        "expect_not_contains": ["da liễu"]
    },
    {
        "name": "TC06 [Đa lượt]: Chuyển đổi chuyên khoa giữa chừng",
        "payload": {
            "message": "Thế còn bên Viện Huyết học thì có bác sĩ nào?",
            "chat_history": [
                {"role": "user", "content": "Tôi muốn khám mắt"},
                {"role": "assistant", "content": "Khoa Mắt có PGS. TS. Đào Xuân Cơ"}
            ]
        },
        "expect_contains": ["nguyễn tuấn tùng", "huyết học", "368"],
        "expect_not_contains": ["đào xuân cơ"]
    },

    # NHÓM 3: CHUYÊN KHOA SÂU
    {
        "name": "TC07 [Chuyên khoa]: Viện Huyết học và Truyền máu Bạch Mai",
        "payload": {"message": "Viện Huyết học và Truyền máu Bạch Mai có bác sĩ nào khám?"},
        "expect_contains": ["nguyễn tuấn tùng", "368"],
        "expect_not_contains": ["không tìm thấy"]
    },
    {
        "name": "TC08 [Chuyên khoa]: Trung tâm Hồi sức tích cực",
        "payload": {"message": "Tôi muốn tìm bác sĩ tại Trung tâm Hồi sức tích cực"},
        "expect_contains": ["đỗ ngọc sơn", "228"],
        "expect_not_contains": ["không tìm thấy"]
    },
    {
        "name": "TC09 [Chuyên khoa]: Trung tâm Cấp Cứu A9 (Bác sĩ chuyên khoa)",
        "payload": {"message": "Bác sĩ đang công tác tại Trung tâm Cấp cứu A9 gồm những ai?"},
        "expect_contains": ["nguyễn anh tuấn", "437"],
        "expect_not_contains": []
    },

    # NHÓM 4: BỘ LỌC GIÁ
    {
        "name": "TC10 [Lọc giá]: Khoa Mắt < 200k (Từ chối đúng)",
        "payload": {"message": "Có bác sĩ Khoa Mắt nào khám dưới 200k không?"},
        "expect_contains": ["không có bác sĩ", "200"],
        "expect_not_contains": ["đào xuân cơ"]
    },
    {
        "name": "TC11 [Lọc giá sàn]: Dưới 100k (Từ chối đúng)",
        "payload": {"message": "Có bác sĩ nào trong viện khám dưới 100k không?"},
        "expect_contains": ["không", "khoa khám bệnh"],
        "expect_not_contains": ["giá khám: 50"]
    },
    {
        "name": "TC12 [Lọc giá trần cao]: Dưới 500k toàn viện",
        "payload": {"message": "Cho tôi xem các bác sĩ có giá khám dưới 500 nghìn"},
        "expect_contains": ["228", "368", "385"],
        "expect_not_contains": ["không tìm thấy"]
    },

    # NHÓM 5: CHỐNG ẢO GIÁC
    {
        "name": "TC13 [Chống ảo giác]: Khoa Da Liễu (Rỗng DB)",
        "payload": {"message": "Tôi bị mẩn ngứa dị ứng, có bác sĩ Da liễu nào khám không?"},
        "expect_contains": ["không", "da liễu", "khoa khám bệnh"],
        "expect_not_contains": []
    },
    {
        "name": "TC14 [Chống ảo giác]: Bác sĩ không tồn tại",
        "payload": {"message": "Bác sĩ Huỳnh Tấn Phát có khám ở viện Bạch Mai không?"},
        "expect_contains": ["không", "khoa khám bệnh"],
        "expect_not_contains": []
    },

    # NHÓM 6: RAG QUY TRÌNH
    {
        "name": "TC15 [RAG]: Giấy tờ tái khám",
        "payload": {"message": "Quy trình tái khám tại Bệnh viện Bạch Mai cần mang những giấy tờ gì?"},
        "expect_contains": ["tái khám"],
        "expect_not_contains": []
    },
    {
        "name": "TC16 [RAG]: Chính sách BHYT trái tuyến",
        "payload": {"message": "Tôi khám bảo hiểm y tế trái tuyến tại Bạch Mai thì được hưởng mức quyền lợi như thế nào?"},
        "expect_contains": ["bảo hiểm y tế"],
        "expect_not_contains": []
    },
    {
        "name": "TC17 [RAG]: Thời gian làm việc của bệnh viện",
        "payload": {"message": "Bệnh viện Bạch Mai có khám thứ 7 và Chủ nhật không? Giờ làm việc ra sao?"},
        "expect_contains": ["thứ"],
        "expect_not_contains": []
    },
    {
        "name": "TC18 [RAG]: Địa chỉ và vị trí cổng vào",
        "payload": {"message": "Bệnh viện Bạch Mai địa chỉ chính xác ở đâu và đi vào bằng cổng nào?"},
        "expect_contains": ["78", "giải phóng"],
        "expect_not_contains": []
    },

    # NHÓM 7: PHÂN LUỒNG TRIỆU CHỨNG
    {
        "name": "TC19 [Triệu chứng]: Tiêu hóa (Ợ chua)",
        "payload": {"message": "Tôi hay bị ợ chua, nóng rát vùng thượng vị sau khi ăn, nên khám khoa nào?"},
        "expect_contains": ["tiêu hóa", "khoa khám bệnh"],
        "expect_not_contains": []
    },
    {
        "name": "TC20 [Triệu chứng]: Cơ Xương Khớp (Đau lưng)",
        "payload": {"message": "Tôi bị đau mỏi thắt lưng lan xuống chân khi cúi người"},
        "expect_contains": ["khoa khám bệnh"],
        "expect_not_contains": []
    },
    {
        "name": "TC21 [Triệu chứng]: Tai Mũi Họng (Ù tai, khàn giọng)",
        "payload": {"message": "Dạo này tôi bị khàn giọng kéo dài và hay bị ù tai"},
        "expect_contains": ["tai mũi họng"],
        "expect_not_contains": []
    },
    {
        "name": "TC22 [Triệu chứng]: Thần Kinh (Đau nửa đầu)",
        "payload": {"message": "Tôi bị đau nửa đầu dữ dội kèm mất ngủ kéo dài 2 tuần nay"},
        "expect_contains": ["thần kinh"],
        "expect_not_contains": []
    },
    {
        "name": "TC23 [Triệu chứng]: Tim Mạch (Đánh trống ngực)",
        "payload": {"message": "Thỉnh thoảng tim tôi đập thình thịch, hồi hộp không rõ nguyên nhân"},
        "expect_contains": ["tim"],
        "expect_not_contains": []
    },
    {
        "name": "TC24 [Triệu chứng]: Thận - Tiết Niệu (Tiểu buốt)",
        "payload": {"message": "Tôi hay bị tiểu đêm nhiều lần và buốt rát khi đi tiểu"},
        "expect_contains": ["tiết niệu"],
        "expect_not_contains": []
    }
]


def send_chat_request(payload: dict) -> tuple[int, dict, float]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            elapsed = time.time() - start_time
            res_body = json.loads(resp.read().decode("utf-8"))
            return resp.status, res_body, elapsed
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start_time
        try:
            res_body = json.loads(e.read().decode("utf-8"))
        except Exception:
            res_body = {"raw_error": str(e)}
        return e.code, res_body, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        return 500, {"error": str(e)}, elapsed


def run_automation_suite():
    print(f"\n{BOLD}{CYAN}=================================================================={RESET}")
    print(f"{BOLD}{CYAN}   BẮT ĐẦU CHẠY MASTER TEST SUITE MỞ RỘNG (24 KỊCH BẢN Y TẾ)     {RESET}")
    print(f"{BOLD}{CYAN}=================================================================={RESET}\n")

    passed_count = 0
    failed_count = 0
    total_time = 0.0

    for idx, tc in enumerate(TEST_SUITE, 1):
        print(f"{BOLD}[{idx:02d}/{len(TEST_SUITE)}] Đang chạy:{RESET} {tc['name']} ... ", end="", flush=True)

        status_code, resp, duration = send_chat_request(tc["payload"])
        total_time += duration

        reply = resp.get("reply", "")
        reply_lower = reply.lower() if isinstance(reply, str) else str(resp).lower()

        is_pass = True
        fail_reasons = []

        if status_code != 200:
            is_pass = False
            fail_reasons.append(f"HTTP Status {status_code}")

        for kw in tc.get("expect_contains", []):
            if kw.lower() not in reply_lower:
                is_pass = False
                fail_reasons.append(f"Thiếu từ khóa: '{kw}'")

        for kw in tc.get("expect_not_contains", []):
            if kw.lower() in reply_lower:
                is_pass = False
                fail_reasons.append(f"Xuất hiện từ cấm: '{kw}'")

        if is_pass:
            passed_count += 1
            print(f"{GREEN}{BOLD}PASSED{RESET} ({duration:.2f}s)")
        else:
            failed_count += 1
            print(f"{RED}{BOLD}FAILED{RESET} ({duration:.2f}s)")
            print(f"   {YELLOW}↳ Lý do lỗi:{RESET} {', '.join(fail_reasons)}")
            print(f"   {YELLOW}↳ AI phản hồi:{RESET} {reply[:120]}...\n")

    pass_rate = (passed_count / len(TEST_SUITE)) * 100
    color_rate = GREEN if pass_rate == 100 else (YELLOW if pass_rate >= 80 else RED)

    print(f"\n{BOLD}------------------------------------------------------------------{RESET}")
    print(f"{BOLD}BÁO CÁO TỔNG HỢP KIỂM THỬ:{RESET}")
    print(f" • Tổng số kịch bản test: {len(TEST_SUITE)}")
    print(f" • {GREEN}Số ca thành công (PASS):{RESET} {passed_count}")
    print(f" • {RED}Số ca thất bại (FAIL):{RESET}   {failed_count}")
    print(f" • Tỷ lệ hoàn thành:       {BOLD}{color_rate}{pass_rate:.1f}%{RESET}")
    print(f" • Tổng thời gian thực thi:{total_time:.2f}s (TB: {total_time/len(TEST_SUITE):.2f}s/kịch bản)")
    print(f"{BOLD}------------------------------------------------------------------{RESET}\n")


if __name__ == "__main__":
    run_automation_suite()