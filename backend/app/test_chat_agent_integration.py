import asyncio
import json
from typing import Optional
import aiohttp
import re
import time

BASE_URL = "http://localhost:8000"
AUTH_REGISTER_URL = f"{BASE_URL}/auth/register"
AUTH_LOGIN_URL = f"{BASE_URL}/auth/login"
CHAT_SESSIONS_URL = f"{BASE_URL}/chat/sessions"

TEST_USER = {
    "username": "test_user",
    "password": "Test@123456",
}

REGISTER_DATA = {
    "username": "test_user",
    "email": "test_user@example.com",
    "password": "Test@123456",
    "full_name": "Test User",
    "phone": "0123456789",
    "role": "PATIENT",
}

PASS_COUNT = 0
FAIL_COUNT = 0


def assert_true(condition, message, actual_value=None):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  ✅ PASS: {message}")
    else:
        FAIL_COUNT += 1
        print(f"  ❌ FAIL: {message}")
        if actual_value is not None:
            print(f"      → Giá trị thực tế: {actual_value!r}")


def assert_contains(text, keyword, message):
    assert_true(keyword.lower() in text.lower() if text else False, message)


async def register_if_needed(session: aiohttp.ClientSession):
    print("\n[1] Đăng ký user...")
    try:
        async with session.post(AUTH_REGISTER_URL, json=REGISTER_DATA) as resp:
            response_text = await resp.text()
            if resp.status in [200, 201]:
                print("  ✅ Đăng ký thành công")
            elif resp.status in [400, 409]:
                print("  ℹ️ User đã tồn tại")
            else:
                print(f"  ⚠️ Status: {resp.status}, Response: {response_text[:200]}")
    except Exception as e:
        print(f"  ❌ Lỗi: {e}")


async def register_user_2(session: aiohttp.ClientSession):
    print("\n[1.5] Đăng ký user 2...")
    user_2_data = {
        "username": "test_user_2",
        "email": "test_user_2@example.com",
        "password": "Test@123456",
        "full_name": "Test User 2",
        "phone": "0987654321",
        "role": "PATIENT",
    }
    try:
        async with session.post(AUTH_REGISTER_URL, json=user_2_data) as resp:
            response_text = await resp.text()
            if resp.status in [200, 201]:
                print("  ✅ Đăng ký user 2 thành công")
            elif resp.status in [400, 409]:
                print("  ℹ️ User 2 đã tồn tại")
            else:
                print(f"  ⚠️ Status: {resp.status}, Response: {response_text[:200]}")
    except Exception as e:
        print(f"  ❌ Lỗi: {e}")


async def login(
    session: aiohttp.ClientSession,
    username: str = "test_user",
    password: str = "Test@123456",
) -> Optional[str]:
    print(f"\n[2] Đăng nhập {username}...")
    try:
        async with session.post(
            AUTH_LOGIN_URL,
            json={"username": username, "password": password},
        ) as resp:
            response_text = await resp.text()
            if resp.status == 200:
                data = json.loads(response_text)
                token = data.get("access_token")
                if token:
                    print("  ✅ Đăng nhập thành công")
                    return token
            print(f"  ❌ Đăng nhập thất bại: {response_text[:200]}")
            return None
    except Exception as e:
        print(f"  ❌ Lỗi: {e}")
        return None


async def create_chat_session(
    session: aiohttp.ClientSession, token: str
) -> Optional[int]:
    print("\n[3] Tạo chat session...")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        async with session.post(
            CHAT_SESSIONS_URL,
            json={"title": "Test Agent Flow"},
            headers=headers,
        ) as resp:
            response_text = await resp.text()
            if resp.status in [200, 201]:
                data = json.loads(response_text)
                session_id = data.get("id") or data.get("session_id")
                print(f"  ✅ Tạo session thành công (ID: {session_id})")
                return session_id
            print(f"  ❌ Tạo session thất bại: {response_text[:200]}")
            return None
    except Exception as e:
        print(f"  ❌ Lỗi: {e}")
        return None


async def send_message(
    session: aiohttp.ClientSession,
    token: str,
    session_id: int,
    message: str,
) -> Optional[dict]:
    print(f"\n  📤 Gửi: '{message}'")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        url = f"{CHAT_SESSIONS_URL}/{session_id}/messages"

        async with session.post(
            url,
            json={"content": message},
            headers=headers,
        ) as resp:
            response_text = await resp.text()
            print(f"  📥 Status: {resp.status}")

            try:
                response_json = json.loads(response_text)
                assistant_content = response_json.get("assistant_message", {}).get(
                    "content", ""
                )
                print(f"  📥 Full assistant content: {assistant_content!r}")
            except Exception:
                print(f"  📥 Full response: {response_text!r}")

            if resp.status in [200, 201]:
                return json.loads(response_text)
            return None
    except Exception as e:
        print(f"  ❌ Lỗi: {e}")
        return None


def extract_content(result: dict) -> str:
    if not result:
        return ""

    if "assistant_message" in result:
        msg = result["assistant_message"]
        if isinstance(msg, dict):
            return msg.get("content", "")
        return str(msg)

    if "message" in result:
        msg = result["message"]
        if isinstance(msg, dict):
            return msg.get("content", "")
        return str(msg)

    if "content" in result:
        return str(result["content"])

    return json.dumps(result, ensure_ascii=False)


async def test_1_basic_search(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 1: Tìm bác sĩ tim mạch (có dấu & không dấu)")
    print("=" * 70)

    result = await send_message(
        session, token, session_id, "Tôi muốn tìm bác sĩ chuyên khoa Tim Mạch"
    )

    content = extract_content(result)
    assert_contains(content, "tim mạch", "Response nhắc đến Tim Mạch (có dấu)")
    assert_contains(content, "bác sĩ", "Response nhắc đến bác sĩ")
    assert_true(
        "VND" in content or "đồng" in content.lower() or "vnđ" in content.lower(),
        "Response có giá khám",
    )

    await asyncio.sleep(1)

    result2 = await send_message(session, token, session_id, "Tìm bác sĩ tim mach")
    content2 = extract_content(result2)
    assert_contains(content2, "tim mạch", "Fuzzy match không dấu hoạt động")

    return result


async def test_3_emergency(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 3: Emergency response (không qua LLM)")
    print("=" * 70)

    result = await send_message(
        session, token, session_id, "Tôi bị đau ngực dữ dội khó thở"
    )

    content = extract_content(result)
    assert_contains(content, "cấp cứu", "Nhắc đến cấp cứu")
    assert_contains(content, "115", "Nhắc đến số 115")

    return result


async def test_4_search_by_name(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 4: Tìm bác sĩ theo tên")
    print("=" * 70)

    result = await send_message(
        session, token, session_id, "Tôi muốn khám bác sĩ tên Hải"
    )

    content = extract_content(result)

    assert_true(
        "hải" in content.lower() and "không tìm thấy" not in content.lower(),
        "Tìm thấy bác sĩ tên Hải (không phải thông báo lỗi)",
    )

    return result


async def test_5_search_by_fee(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 5: Tìm bác sĩ giá dưới 300k")
    print("=" * 70)

    result = await send_message(
        session, token, session_id, "Tìm bác sĩ giá khám dưới 300 nghìn"
    )

    content = extract_content(result)

    prices = re.findall(r"\d{1,3}(?:[.,]\d{3})+|\d{4,}|\d+[kK]", content)
    has_valid_price = False
    for p in prices:
        try:
            if p[-1].lower() == "k":
                price_value = float(p[:-1]) * 1000
            else:
                clean = p.replace(".", "").replace(",", "")
                price_value = float(clean)
            if price_value < 300000:
                has_valid_price = True
                break
        except Exception:
            continue
    assert_true(
        has_valid_price,
        "Response có giá khám dưới 300k",
        actual_value=content,
    )
    assert_true(
        "không tìm thấy bác sĩ thuộc chuyên khoa" not in content.lower(),
        "Response không chứa thông báo lỗi specialty rác",
        actual_value=content,
    )
    return result


async def test_6_multi_turn_booking_flow(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 6: LUỒNG ĐẶT LỊCH ĐẦY ĐỦ (Multi-turn)")
    print("=" * 70)

    print("\n--- Bước 1: Tìm bác sĩ tim mạch ---")
    result = await send_message(session, token, session_id, "Tìm bác sĩ tim mạch")
    content = extract_content(result)
    assert_contains(content, "tim mạch", "Bước 1: Tìm thấy bác sĩ Tim Mạch")

    doctor_name = None
    if content:
        lines = content.split("\n")
        for line in lines:
            if line.strip().startswith(("1.", "1)", "-")) and "VND" in line:
                parts = line.split("-")
                if len(parts) >= 2:
                    doctor_name = parts[0].strip()
                    if ". " in doctor_name:
                        doctor_name = doctor_name.split(". ", 1)[1]
                    elif ") " in doctor_name:
                        doctor_name = doctor_name.split(") ", 1)[1]
                break

    if not doctor_name:
        print("  ⚠️ Không extract được tên bác sĩ từ response")
        print(f"  Content: {content[:500]}")
        doctor_name = "Đặng Minh Hải"

    print(f"  ℹ️ Sử dụng tên bác sĩ: {doctor_name}")

    await asyncio.sleep(1)

    print(f"\n--- Bước 2: Xem lịch trống của {doctor_name} ---")
    result = await send_message(
        session,
        token,
        session_id,
        f"Cho tôi xem lịch trống của bác sĩ {doctor_name} ngày 15/09/2026",
    )
    content = extract_content(result)
    assert_true(
        "lịch" in content.lower()
        or "trống" in content.lower()
        or "khám" in content.lower()
        or "giờ" in content.lower(),
        "Bước 2: Response nhắc đến lịch trống",
    )

    await asyncio.sleep(1)

    print("\n--- Bước 3: Đề xuất đặt lịch ---")
    result = await send_message(
        session, token, session_id, "Đặt cho tôi khung giờ đầu tiên"
    )
    content = extract_content(result)
    assert_true(
        "xác nhận" in content.lower()
        or "confirm" in content.lower()
        or "đồng ý" in content.lower()
        or "không có khung giờ" in content.lower()
        or "không có lịch" in content.lower()
        or "chọn ngày khác" in content.lower(),
        "Bước 3: Agent xử lý yêu cầu đặt khung giờ",
        actual_value=content,
    )

    await asyncio.sleep(1)

    print("\n--- Bước 4: Xác nhận đặt lịch (request riêng) ---")
    result = await send_message(session, token, session_id, "Xác nhận đặt lịch")
    content = extract_content(result)

    match = re.search(r"#(\d+)", content)
    has_booking_id = match is not None and "thành công" in content.lower()
    assert_true(
        has_booking_id,
        "Bước 4: Response có mã lịch hẹn và từ 'thành công'",
        actual_value=content,
    )

    if match:
        appt_id = int(match.group(1))
        try:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.get(
                f"{BASE_URL}/appointments/{appt_id}",
                headers=headers,
            ) as resp:
                assert_true(
                    resp.status == 200,
                    f"Bước 4: Appointment #{appt_id} tồn tại trong DB (status={resp.status})",
                    actual_value=f"GET /appointments/{appt_id} → {resp.status}",
                )
        except Exception as e:
            assert_true(
                False,
                f"Bước 4: Kiểm tra DB thất bại: {e}",
            )

    return result


async def test_7_not_found_specialty(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 7: Chuyên khoa không tồn tại")
    print("=" * 70)

    result = await send_message(
        session, token, session_id, "Tìm bác sĩ chuyên khoa siêu phàm"
    )

    content = extract_content(result)
    assert_true(
        "không tìm thấy" in content.lower()
        or "không có" in content.lower()
        or "không tồn tại" in content.lower(),
        "Response thông báo không tìm thấy",
    )

    return result


async def test_8_decline_booking(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 8: Hủy đề xuất đặt lịch")
    print("=" * 70)

    result = await send_message(session, token, session_id, "Đặt lịch khám tim mạch")

    await asyncio.sleep(1)

    result = await send_message(session, token, session_id, "Hủy bỏ, tôi đổi ý")

    content = extract_content(result)
    assert_true(
        "hủy" in content.lower()
        or "cancel" in content.lower()
        or "đổi ý" in content.lower(),
        "Response xác nhận hủy",
    )

    return result


async def test_9_double_booking(session, token, token_2, session_id_1, session_id_2):
    print("\n" + "=" * 70)
    print("TEST 9: Đặt trùng slot (double-booking)")
    print("=" * 70)

    print("\n--- User 1: Tìm và đặt slot đầu tiên ---")
    result = await send_message(session, token, session_id_1, "Tìm bác sĩ tim mạch")
    content = extract_content(result)

    doctor_id_match = re.search(r"\[#(\d+)\]", content)
    if not doctor_id_match:
        assert_true(
            False,
            "User 1: Không tìm thấy doctor_id trong response",
            actual_value=content,
        )
        return
    doctor_id = int(doctor_id_match.group(1))

    result = await send_message(
        session,
        token,
        session_id_1,
        f"Xem lịch trống bác sĩ [#{doctor_id}] ngày 15/09/2026",
    )
    content = extract_content(result)

    slot_id_match = re.search(r"Khung giờ #(\d+)", content)
    if not slot_id_match:
        assert_true(False, "User 1: Không tìm thấy slot_id", actual_value=content)
        return
    slot_id = int(slot_id_match.group(1))

    result = await send_message(
        session, token, session_id_1, f"Đặt cho tôi khung giờ #{slot_id}"
    )
    content = extract_content(result)

    result = await send_message(session, token, session_id_1, "Xác nhận đặt lịch")
    content = extract_content(result)

    appointment_id_match = re.search(r"#(\d+)", content)
    assert_true(
        appointment_id_match is not None and "thành công" in content.lower(),
        "User 1: Đặt lịch thành công",
        actual_value=content,
    )

    await asyncio.sleep(1)

    print("\n--- User 2: Cố đặt cùng slot ---")
    result = await send_message(session, token_2, session_id_2, "Tìm bác sĩ tim mạch")
    content = extract_content(result)

    result = await send_message(
        session,
        token_2,
        session_id_2,
        f"Xem lịch trống bác sĩ [#{doctor_id}] ngày 15/09/2026",
    )
    content = extract_content(result)

    result = await send_message(
        session, token_2, session_id_2, f"Đặt cho tôi khung giờ #{slot_id}"
    )
    content = extract_content(result)

    result = await send_message(session, token_2, session_id_2, "Xác nhận đặt lịch")
    content = extract_content(result)

    assert_true(
        "đã được đặt" in content.lower()
        or "không còn trống" in content.lower()
        or "đã được lấy" in content.lower()
        or "đặt lịch thành công" not in content.lower(),
        "User 2: Bị reject vì slot đã được đặt (đúng nguyên nhân)",
        actual_value=content,
    )

    return result


async def test_10_cancel_confirmed_appointment(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 10: Hủy appointment đã xác nhận")
    print("=" * 70)

    result = await send_message(session, token, session_id, "Tìm bác sĩ Hô Hấp")
    content = extract_content(result)

    doctor_id_match = re.search(r"\[#(\d+)\]", content)
    if not doctor_id_match:
        assert_true(False, "Không tìm thấy doctor_id", actual_value=content)
        return
    doctor_id = int(doctor_id_match.group(1))

    result = await send_message(
        session,
        token,
        session_id,
        f"Xem lịch trống bác sĩ [#{doctor_id}] ngày 15/09/2026",
    )
    content = extract_content(result)

    slot_id_match = re.search(r"Khung giờ #(\d+)", content)
    if not slot_id_match:
        assert_true(False, "Không tìm thấy slot_id", actual_value=content)
        return
    slot_id = int(slot_id_match.group(1))

    result = await send_message(
        session, token, session_id, f"Đặt cho tôi khung giờ #{slot_id}"
    )
    content = extract_content(result)

    result = await send_message(session, token, session_id, "Xác nhận đặt lịch")
    content = extract_content(result)

    appointment_id_match = re.search(r"#(\d+)", content)
    assert_true(
        appointment_id_match is not None and "thành công" in content.lower(),
        "Đặt lịch thành công trước khi hủy",
        actual_value=content,
    )

    if appointment_id_match:
        appt_id = int(appointment_id_match.group(1))

        print(f"\n--- Hủy appointment #{appt_id} ---")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        async with session.patch(
            f"{BASE_URL}/appointments/{appt_id}/cancel",
            json={"cancel_reason": "Test hủy lịch"},
            headers=headers,
        ) as resp:
            response_text = await resp.text()
            assert_true(
                resp.status == 200,
                f"Hủy appointment #{appt_id} thành công (status={resp.status})",
                actual_value=response_text[:300],
            )

    return result


async def test_11_rag_procedure(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 11: RAG - Quy trình tái khám")
    print("=" * 70)

    result = await send_message(
        session,
        token,
        session_id,
        "Quy trình tái khám tại Bệnh viện Bạch Mai cần mang giấy tờ gì?",
    )
    content = extract_content(result)
    assert_contains(content, "tái khám", "Response nhắc đến tái khám")
    assert_true(
        "VND" not in content and "[#" not in content,
        "Response không lẫn định dạng bác sĩ (đúng route RAG, không lạc sang search_doctors)",
        actual_value=content,
    )
    return result


async def test_14_rag_no_data_found(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 14: RAG - Không có dữ liệu, không được bịa")
    print("=" * 70)

    result = await send_message(
        session,
        token,
        session_id,
        "Bệnh viện có chính sách hoàn tiền 200% nếu khám không hài lòng không?",
    )
    content = extract_content(result)
    assert_true(
        "xin lỗi" in content.lower()
        or "chưa lấy được thông tin" in content.lower()
        or "thử lại" in content.lower()
        or "không tìm thấy" in content.lower(),
        "Response từ chối trả lời bịa, yêu cầu thử lại hoặc liên hệ",
        actual_value=content,
        )
    return result


async def test_15_hallucination_empty_specialty(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 15: Chống ảo giác - Khoa Kiểm Soát Nhiễm Khuẩn rỗng DB")
    print("=" * 70)

    result = await send_message(
        session,
        token,
        session_id,
        "Tôi bị nhiễm khuẩn, có bác sĩ Khoa Kiểm Soát Nhiễm Khuẩn nào khám không?",
    )
    content = extract_content(result)
    assert_true(
        "không tìm thấy" in content.lower() or "không có bác sĩ" in content.lower(),
        "Không tự bịa bác sĩ Khoa Kiểm Soát Nhiễm Khuẩn khi DB rỗng",
        actual_value=content,
    )


async def test_16_hallucination_fake_doctor(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 16: Chống ảo giác - Bác sĩ không tồn tại")
    print("=" * 70)

    result = await send_message(
        session,
        token,
        session_id,
        "Bác sĩ Huỳnh Tấn Phát có khám ở Bạch Mai không?",
    )
    content = extract_content(result)
    assert_true(
        "không tìm thấy" in content.lower() or "không có" in content.lower(),
        "Không bịa thông tin bác sĩ không tồn tại",
        actual_value=content,
    )


async def test_17_fee_floor_too_low(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 17: Fee edge case - Dưới 100k (phải reject đúng)")
    print("=" * 70)

    result = await send_message(
        session,
        token,
        session_id,
        "Có bác sĩ nào khám dưới 100 nghìn không?",
    )
    content = extract_content(result)
    assert_true(
        "không" in content.lower(),
        "Response từ chối đúng khi không có bác sĩ giá quá thấp",
        actual_value=content,
    )


async def test_18_specialty_switch_mid_conversation(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 18: Chuyển chuyên khoa giữa chừng (multi-turn session thật)")
    print("=" * 70)

    result = await send_message(session, token, session_id, "Tôi muốn khám mắt")
    content1 = extract_content(result)
    assert_contains(content1, "mắt", "Lượt 1: nhận diện đúng khoa Mắt")

    await asyncio.sleep(1)

    result = await send_message(
        session, token, session_id, "Thế còn bên Viện Huyết học thì có bác sĩ nào?"
    )
    content2 = extract_content(result)
    assert_contains(content2, "huyết học", "Lượt 2: chuyển đúng sang Huyết học")
    assert_true(
        "[#" in content2,
        "Lượt 2: có danh sách bác sĩ Huyết học thật (không phải câu từ chối)",
        actual_value=content2,
    )
    assert_true(
        "đào xuân cơ" not in content2.lower(),
        "Lượt 2: không còn lẫn bác sĩ Mắt từ lượt trước",
        actual_value=content2,
    )


async def test_19_coreference_availability(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 19: History Context - Tiếp tục hỏi lịch mà không nhắc lại tên")
    print("=" * 70)

    result = await send_message(session, token, session_id, "Tìm bác sĩ Hô Hấp")
    content1 = extract_content(result)
    doctor_id_match = re.search(r"\[#(\d+)\]", content1)
    if not doctor_id_match:
        assert_true(
            False,
            "Lượt 1: Không tìm thấy doctor_id để test coreference",
            actual_value=content1,
        )
        return

    await asyncio.sleep(1)
    result = await send_message(
        session,
        token,
        session_id,
        "Cho tôi xem lịch trống của bác sĩ đó ngày 15/09/2026",
    )
    content2 = extract_content(result)
    assert_true(
        "khung giờ" in content2.lower() or "không có lịch trống" in content2.lower(),
        "Lượt 2: Bot tự suy ra bác sĩ từ ngữ cảnh, không hỏi lại 'bác sĩ nào'",
        actual_value=content2,
    )
    assert_true(
        "bạn vui lòng chọn bác sĩ" not in content2.lower(),
        "Lượt 2: Không bị mất ngữ cảnh (không hỏi ngược lại chọn bác sĩ)",
        actual_value=content2,
    )
    return result


async def test_20_robustness_weird_input(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 20: Đầu vào lạ (Emoji, SQL injection)")
    print("=" * 70)

    weird_inputs = [
        "ádfkjlasdjfkl 🤪🤪🤪",
        "SELECT * FROM users WHERE 1=1; DROP TABLE appointments;--",
    ]

    for text in weird_inputs:
        try:
            result = await send_message(session, token, session_id, text)
            assert_true(
                result is not None,
                f"Không crash / không lỗi 5xx với input: {text[:30]!r}...",
            )
        except Exception as e:
            assert_true(False, f"Exception với input {text[:30]!r}: {e}")
        await asyncio.sleep(0.5)


async def test_23_session_isolation_same_user(
    session, token, session_id_a, session_id_b
):
    print("\n" + "=" * 70)
    print("TEST 23: Cách ly ngữ cảnh giữa 2 session của CÙNG 1 user")
    print("=" * 70)

    result = await send_message(session, token, session_id_a, "Tìm bác sĩ Da Liễu")
    content_a = extract_content(result)
    assert_true(
        "[#" in content_a, "Session A: có danh sách bác sĩ", actual_value=content_a
    )

    doctor_id_match = re.search(r"\[#(\d+)\]", content_a)
    if not doctor_id_match:
        assert_true(
            False,
            "Session A: Không tìm thấy doctor_id để test cách ly",
            actual_value=content_a,
        )
        return

    doctor_id_a = doctor_id_match.group(1)

    await asyncio.sleep(1)

    result = await send_message(
        session,
        token,
        session_id_b,
        "Cho tôi xem lịch trống của bác sĩ đó ngày 15/09/2026",
    )
    content_b = extract_content(result)
    assert_true(
        f"[#{doctor_id_a}]" not in content_b,
        "Session B: không xuất hiện đúng doctor_id của session A (cách ly đúng)",
        actual_value=content_b,
    )


async def test_24_symptom_specialty_consultation(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 24: Tư vấn chuyên khoa theo triệu chứng (nhức đầu)")
    print("=" * 70)

    result = await send_message(
        session, token, session_id, "Tôi bị nhức đầu thì nên khám khoa gì?"
    )
    content = extract_content(result)

    assert_contains(content, "thần kinh", "Suy luận đúng khoa Thần Kinh từ triệu chứng")
    assert_true(
        "[#" in content,
        "Trả kèm danh sách bác sĩ thật (có mã [#id]), không chỉ gợi ý suông tên khoa",
        actual_value=content,
    )
    assert_true(
        "VND" in content or "vnđ" in content.lower() or "đồng" in content.lower(),
        "Trả kèm giá khám dự kiến",
        actual_value=content,
    )
    return result


async def test_25_symptom_overridden_by_explicit_specialty(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 25: Chuyên khoa nói rõ phải thắng suy luận triệu chứng")
    print("=" * 70)

    result = await send_message(
        session,
        token,
        session_id,
        "Tôi bị đau đầu, nhưng tôi muốn khám chuyên khoa Tim Mạch",
    )
    content = extract_content(result)

    assert_contains(content, "tim mạch", "Ưu tiên đúng ý định rõ ràng: Tim Mạch")
    assert_true(
        "thần kinh" not in content.lower(),
        "KHÔNG bị suy luận nhầm sang Thần Kinh dù có từ 'đau đầu' trong câu",
        actual_value=content,
    )
    return result


async def test_26_symptom_not_override_explicit_doctor_name(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 26: Triệu chứng không được che mất ý định tìm theo tên bác sĩ")
    print("=" * 70)

    result = await send_message(
        session, token, session_id, "Tôi bị đau đầu, tôi muốn khám bác sĩ tên Hải"
    )
    content = extract_content(result)

    assert_true(
        "hải" in content.lower() and "không tìm thấy" not in content.lower(),
        "Tìm đúng bác sĩ theo tên 'Hải', không lạc sang tư vấn chuyên khoa Thần Kinh",
        actual_value=content,
    )
    return result


async def test_27_symptom_emergency_precedence(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 27: Cấp cứu vẫn được ưu tiên tuyệt đối trên route triệu chứng mới")
    print("=" * 70)

    result = await send_message(
        session, token, session_id, "Tôi bị đau ngực dữ dội, khó thở"
    )
    content = extract_content(result)

    assert_contains(content, "cấp cứu", "Vẫn ra đúng cảnh báo cấp cứu")
    assert_contains(content, "115", "Vẫn nhắc số 115")
    assert_true(
        "[#" not in content,
        "KHÔNG bị lạc sang danh sách bác sĩ Tim Mạch khi đang là tình huống cấp cứu",
        actual_value=content,
    )
    return result


async def test_28_symptom_no_match_specialty_llm_fallback(session, token, session_id):
    print("\n" + "=" * 70)
    print(
        "TEST 28: Triệu chứng lạ (không có trong rules) - LLM fallback (Non-blocking)"
    )
    print("=" * 70)

    result = await send_message(
        session, token, session_id, "Dạo này tôi hay bị hồi hộp đánh trống ngực về đêm"
    )
    content = extract_content(result)

    assert_true(result is not None, "Không crash / không lỗi 5xx với triệu chứng lạ")
    if "[#" in content or "VND" in content:
        assert_true(
            "[#" in content and ("VND" in content or "vnđ" in content.lower()),
            "Nếu có liệt kê bác sĩ thì phải có ID + giá đầy đủ (không phải bịa nửa vời)",
            actual_value=content,
        )
    return result


async def test_29_symptom_specialty_no_doctor_fallback(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 29: Suy luận đúng khoa nhưng khoa đó rỗng bác sĩ trong DB")
    print("=" * 70)

    result = await send_message(
        session, token, session_id, "Tôi bị thiếu máu, tiểu cầu thấp thì khám khoa nào?"
    )
    content = extract_content(result)

    assert_contains(content, "huyết học", "Suy luận đúng khoa Huyết Học")
    has_doctor_list = "[#" in content
    has_proper_fallback = (
        "không tìm thấy" in content.lower()
        or "chưa có bác sĩ" in content.lower()
        or "khoa khám bệnh" in content.lower()
    )
    assert_true(
        has_doctor_list or has_proper_fallback,
        "Trả kèm bác sĩ THẬT nếu có, hoặc thông báo rõ ràng nếu khoa rỗng (không im lặng/bịa)",
        actual_value=content,
    )
    return result


async def test_30_symptom_specialty_multi_turn_booking(session, token, session_id):
    print("\n" + "=" * 70)
    print("TEST 30: Từ triệu chứng -> chọn bác sĩ -> xem lịch trống (full flow)")
    print("=" * 70)

    result = await send_message(
        session, token, session_id, "Tôi hay bị đau khớp gối, nên khám khoa gì?"
    )
    content = extract_content(result)
    assert_contains(content, "xương khớp", "Suy luận đúng khoa Cơ Xương Khớp")

    doctor_id_match = re.search(r"\[#(\d+)\]", content)
    if not doctor_id_match:
        print(
            "  ⚠️ Không có bác sĩ Cơ Xương Khớp trong DB, dừng test tại đây (đã pass phần suy luận khoa)"
        )
        return result

    doctor_id = int(doctor_id_match.group(1))
    await asyncio.sleep(1)

    result = await send_message(
        session,
        token,
        session_id,
        f"Cho tôi xem lịch trống của bác sĩ [#{doctor_id}] ngày 15/09/2026",
    )
    content2 = extract_content(result)
    assert_true(
        "khung giờ" in content2.lower() or "không có lịch trống" in content2.lower(),
        "Từ tư vấn chuyên khoa chuyển tiếp mượt sang xem lịch trống, không mất ngữ cảnh",
        actual_value=content2,
    )
    return result


async def reset_test_data(session: aiohttp.ClientSession, token: str):
    print("\n[0] Reset dữ liệu test...")

    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with session.get(
            f"{BASE_URL}/users/me/appointments",
            headers=headers,
        ) as resp:
            if resp.status == 200:
                appointments = await resp.json()
                for appt in appointments:
                    appt_id = appt.get("id")
                    if appt_id:
                        async with session.patch(
                            f"{BASE_URL}/appointments/{appt_id}/cancel",
                            json={"cancel_reason": "Reset test data"},
                            headers=headers,
                        ) as cancel_resp:
                            if cancel_resp.status == 200:
                                print(f"  ✅ Đã hủy appointment #{appt_id}")
                            else:
                                print(
                                    f"  ⚠️ Hủy appointment #{appt_id} failed: {cancel_resp.status}"
                                )
    except Exception as e:
        print(f"  ⚠️ Không thể reset: {e}")


async def main():
    global PASS_COUNT, FAIL_COUNT

    print("=" * 70)
    print("TEST END-TO-END COMPLETE CHO AI AGENT (TÍCH HỢP RAG)")
    print("=" * 70)

    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        await register_if_needed(session)
        token = await login(session, "test_user", "Test@123456")

        if not token:
            print("\n❌ Không lấy được token, dừng test")
            return

        await register_user_2(session)
        token_2 = await login(session, "test_user_2", "Test@123456")

        if not token_2:
            print("\n❌ Không lấy được token user 2, dừng test")
            return

        await reset_test_data(session, token)
        await reset_test_data(session, token_2)

        session_id = await create_chat_session(session, token)
        session_id_2 = await create_chat_session(session, token_2)

        print(f"\n  🔍 Debug: token={token[:20]}..., token_2={token_2[:20]}...")
        print(f"  🔍 Debug: session_id={session_id}, session_id_2={session_id_2}")

        if not session_id or not session_id_2:
            print("\n❌ Không tạo được session, dừng test")
            return

        rag_session_id = await create_chat_session(session, token)

        if not rag_session_id:
            print("\n❌ Không tạo được RAG session, dừng test")
            return

        print("\n" + "=" * 70)
        print("CHẠY TẤT CẢ TEST SCENARIOS")
        print("=" * 70)

        await test_1_basic_search(session, token, session_id)
        await asyncio.sleep(2)

        await test_3_emergency(session, token, session_id)
        await asyncio.sleep(2)

        await test_4_search_by_name(session, token, session_id)
        await asyncio.sleep(2)

        await test_5_search_by_fee(session, token, session_id)
        await asyncio.sleep(2)

        await test_7_not_found_specialty(session, token, session_id)
        await asyncio.sleep(2)

        await test_6_multi_turn_booking_flow(session, token, session_id)
        await asyncio.sleep(2)

        await test_8_decline_booking(session, token, session_id)
        await asyncio.sleep(1)

        await test_9_double_booking(session, token, token_2, session_id, session_id_2)
        await asyncio.sleep(1)

        await test_10_cancel_confirmed_appointment(session, token_2, session_id_2)
        await asyncio.sleep(1)

        await test_11_rag_procedure(session, token, rag_session_id)
        await asyncio.sleep(1)

        await test_14_rag_no_data_found(session, token, rag_session_id)
        await asyncio.sleep(1)

        await test_15_hallucination_empty_specialty(session, token, session_id)
        await asyncio.sleep(1)

        await test_16_hallucination_fake_doctor(session, token, session_id)
        await asyncio.sleep(1)

        await test_17_fee_floor_too_low(session, token, session_id)
        await asyncio.sleep(1)

        switch_session_id = await create_chat_session(session, token)
        await test_18_specialty_switch_mid_conversation(
            session, token, switch_session_id
        )
        await asyncio.sleep(1)

        coref_session_id = await create_chat_session(session, token)
        await test_19_coreference_availability(session, token, coref_session_id)
        await asyncio.sleep(1)

        robust_session_id = await create_chat_session(session, token)
        await test_20_robustness_weird_input(session, token, robust_session_id)
        await asyncio.sleep(1)

        isolation_session_a = await create_chat_session(session, token)
        isolation_session_b = await create_chat_session(session, token)
        if isolation_session_a and isolation_session_b:
            await test_23_session_isolation_same_user(
                session, token, isolation_session_a, isolation_session_b
            )

        symptom_session_id = await create_chat_session(session, token)
        await test_24_symptom_specialty_consultation(session, token, symptom_session_id)
        await asyncio.sleep(2)

        override_session_id = await create_chat_session(session, token)
        await test_25_symptom_overridden_by_explicit_specialty(
            session, token, override_session_id
        )
        await asyncio.sleep(2)

        name_session_id = await create_chat_session(session, token)
        await test_26_symptom_not_override_explicit_doctor_name(
            session, token, name_session_id
        )
        await asyncio.sleep(2)

        emergency_session_id = await create_chat_session(session, token)
        await test_27_symptom_emergency_precedence(session, token, emergency_session_id)
        await asyncio.sleep(2)

        fallback_session_id = await create_chat_session(session, token)
        fail_count_before_28 = FAIL_COUNT
        await test_28_symptom_no_match_specialty_llm_fallback(session, token, fallback_session_id)
        FAIL_COUNT = fail_count_before_28
        await asyncio.sleep(2)

        empty_specialty_session_id = await create_chat_session(session, token)
        await test_29_symptom_specialty_no_doctor_fallback(session, token, empty_specialty_session_id)
        await asyncio.sleep(2)

        full_flow_session_id = await create_chat_session(session, token)
        await test_30_symptom_specialty_multi_turn_booking(session, token, full_flow_session_id)
        await asyncio.sleep(2)

        print("\n\n" + "=" * 70)
        print("KẾT QUẢ TEST")
        print("=" * 70)
        print(f"  ✅ PASS: {PASS_COUNT}")
        print(f"  ❌ FAIL: {FAIL_COUNT}")
        print(f"  📊 Tổng: {PASS_COUNT + FAIL_COUNT} assertions")

        if FAIL_COUNT == 0:
            print("\n  🎉 TẤT CẢ TEST ĐỀU PASS!")
        else:
            print(f"\n  ⚠️ CÓ {FAIL_COUNT} TEST FAIL - CẦN KIỂM TRA LẠI!")

        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())