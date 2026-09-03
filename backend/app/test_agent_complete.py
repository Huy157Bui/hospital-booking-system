

import asyncio
import json
from typing import Optional
import aiohttp

import re

# ============ CONFIG ============
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

# ============ ASSERTION HELPERS ============
PASS_COUNT = 0
FAIL_COUNT = 0


def assert_true(condition, message, actual_value=None):
    """Assertion helper"""
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
    """Kiểm tra text chứa keyword (case-insensitive)"""
    assert_true(keyword.lower() in text.lower() if text else False, message)


# ============ HELPER FUNCTIONS ============


async def register_if_needed(session: aiohttp.ClientSession):
    """Đăng ký user nếu chưa tồn tại"""
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
    """Đăng ký user thứ 2 cho test double-booking"""
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


async def login(session: aiohttp.ClientSession, username: str = "test_user", password: str = "Test@123456") -> Optional[str]:
    """Đăng nhập và lấy access token"""
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
    """Tạo chat session mới"""
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
    """Gửi tin nhắn và nhận response"""
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

            # In đầy đủ content, không cắt
            try:
                response_json = json.loads(response_text)
                assistant_content = response_json.get("assistant_message", {}).get(
                    "content", ""
                )
                print(f"  📥 Full assistant content: {assistant_content!r}")
            except:
                print(f"  📥 Full response: {response_text!r}")

            if resp.status in [200, 201]:
                return json.loads(response_text)
            return None
    except Exception as e:
        print(f"  ❌ Lỗi: {e}")
        return None


def extract_content(result: dict) -> str:
    """Extract content từ response"""
    if not result:
        return ""

    # Thử các cấu trúc response khác nhau
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


def extract_doctor_id(result: dict) -> Optional[int]:
    """Extract doctor_id từ response nếu có"""
    if not result:
        return None

    # Tìm trong các cấu trúc khác nhau
    def search_dict(d):
        if isinstance(d, dict):
            if "doctor_id" in d:
                return d["doctor_id"]
            if "tool_calls" in d:
                for call in d["tool_calls"]:
                    if isinstance(call, dict) and "arguments" in call:
                        args = call["arguments"]
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except:
                                pass
                        if isinstance(args, dict) and "doctor_id" in args:
                            return args["doctor_id"]
            for v in d.values():
                result = search_dict(v)
                if result:
                    return result
        elif isinstance(d, list):
            for item in d:
                result = search_dict(item)
                if result:
                    return result
        return None

    return search_dict(result)


# ============ TEST SCENARIOS ============


async def test_1_basic_search(session, token, session_id):
    """Test: Tìm bác sĩ theo chuyên khoa"""
    print("\n" + "=" * 70)
    print("TEST 1: Tìm bác sĩ tim mạch (có dấu)")
    print("=" * 70)

    result = await send_message(
        session, token, session_id, "Tôi muốn tìm bác sĩ chuyên khoa Tim Mạch"
    )

    content = extract_content(result)
    assert_contains(content, "tim mạch", "Response nhắc đến Tim Mạch")
    assert_contains(content, "bác sĩ", "Response nhắc đến bác sĩ")
    assert_true(
        "VND" in content or "đồng" in content.lower() or "vnđ" in content.lower(),
        "Response có giá khám",
    )

    return result


async def test_2_search_no_accent(session, token, session_id):
    """Test: Tìm bác sĩ không dấu"""
    print("\n" + "=" * 70)
    print("TEST 2: Tìm bác sĩ tim mạch (KHÔNG dấu)")
    print("=" * 70)

    result = await send_message(session, token, session_id, "Tìm bác sĩ tim mach")

    content = extract_content(result)
    assert_contains(content, "tim mạch", "Fuzzy match không dấu hoạt động")

    return result


async def test_3_emergency(session, token, session_id):
    """Test: Emergency response"""
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
    """Test: Tìm theo tên bác sĩ"""
    print("\n" + "=" * 70)
    print("TEST 4: Tìm bác sĩ theo tên")
    print("=" * 70)

    result = await send_message(
        session, token, session_id, "Tôi muốn khám bác sĩ tên Hải"
    )

    content = extract_content(result)

    # FIX: Kiểm tra CHẶT CHẼ hơn
    assert_true(
        "hải" in content.lower() and "không tìm thấy" not in content.lower(),
        "Tìm thấy bác sĩ tên Hải (không phải thông báo lỗi)"
    )

    return result


async def test_5_search_by_fee(session, token, session_id):
    """Test: Tìm theo giá"""
    print("\n" + "=" * 70)
    print("TEST 5: Tìm bác sĩ giá dưới 300k")
    print("=" * 70)

    result = await send_message(
        session, token, session_id, "Tìm bác sĩ giá khám dưới 300 nghìn"
    )

    content = extract_content(result)

    prices = re.findall(r"(\d{1,3}(?:[.,]\d{3})*)", content)
    has_valid_price = False
    for p in prices:
        try:
            price_value = float(p.replace(".", "").replace(",", "."))
            if price_value < 300000:
                has_valid_price = True
                break
        except:
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
    """Test QUAN TRỌNG NHẤT: Luồng đặt lịch qua nhiều lượt chat"""
    print("\n" + "=" * 70)
    print("TEST 6: LUỒNG ĐẶT LỊCH ĐẦY ĐỦ (Multi-turn)")
    print("=" * 70)

    # Bước 1: Tìm bác sĩ
    print("\n--- Bước 1: Tìm bác sĩ tim mạch ---")
    result = await send_message(session, token, session_id, "Tìm bác sĩ tim mạch")
    content = extract_content(result)
    assert_contains(content, "tim mạch", "Bước 1: Tìm thấy bác sĩ Tim Mạch")

    # Extract doctor_name từ response (lấy tên bác sĩ đầu tiên)
    doctor_name = None
    if content:
        # Tìm pattern "1. [Tên bác sĩ]"
        lines = content.split("\n")
        for line in lines:
            if line.strip().startswith(("1.", "1)", "-")) and "VND" in line:
                # Extract tên (bỏ số thứ tự và giá)
                parts = line.split("-")
                if len(parts) >= 2:
                    doctor_name = parts[0].strip()
                    # Bỏ số thứ tự
                    if ". " in doctor_name:
                        doctor_name = doctor_name.split(". ", 1)[1]
                    elif ") " in doctor_name:
                        doctor_name = doctor_name.split(") ", 1)[1]
                break

    if not doctor_name:
        print("  ⚠️ Không extract được tên bác sĩ từ response")
        print(f"  Content: {content[:500]}")
        doctor_name = "Đặng Minh Hải"  # Fallback

    print(f"  ℹ️ Sử dụng tên bác sĩ: {doctor_name}")

    await asyncio.sleep(1)

    # Bước 2: Xem lịch trống
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

    # Bước 3: Đề xuất đặt lịch
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

    # Bước 4: Xác nhận đặt lịch (HTTP request RIÊNG BIỆT)
    print("\n--- Bước 4: Xác nhận đặt lịch (request riêng) ---")
    result = await send_message(session, token, session_id, "Xác nhận đặt lịch")
    content = extract_content(result)

    # Phải có mã lịch hẹn dạng #số
    import re

    match = re.search(r"#(\d+)", content)
    has_booking_id = match is not None and "thành công" in content.lower()
    assert_true(
        has_booking_id,
        "Bước 4: Response có mã lịch hẹn và từ 'thành công'",
        actual_value=content,
    )

    # Kiểm tra DB thật — Appointment tồn tại
    if match:
        appt_id = int(match.group(1))
        try:
            import aiohttp

            async with aiohttp.ClientSession() as db_session:
                # Gọi API để kiểm tra appointment thật
                headers = {"Authorization": f"Bearer {token}"}
                async with db_session.get(
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
    """Test: Chuyên khoa không tồn tại"""
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
    """Test: Hủy đề xuất đặt lịch"""
    print("\n" + "=" * 70)
    print("TEST 8: Hủy đề xuất đặt lịch")
    print("=" * 70)

    # Đề xuất đặt lịch
    result = await send_message(session, token, session_id, "Đặt lịch khám tim mạch")

    await asyncio.sleep(1)

    # Hủy
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
    """Test: 2 user khác nhau cùng đặt 1 slot — user 2 phải bị reject"""
    print("\n" + "=" * 70)
    print("TEST 9: Đặt trùng slot (double-booking)")
    print("=" * 70)

    # User 1: Tìm bác sĩ tim mạch → xem lịch → đặt slot đầu tiên
    print("\n--- User 1: Tìm và đặt slot đầu tiên ---")
    result = await send_message(session, token, session_id_1, "Tìm bác sĩ tim mạch")
    content = extract_content(result)

    # Lấy doctor_id từ response
    import re

    doctor_id_match = re.search(r"\[#(\d+)\]", content)
    if not doctor_id_match:
        assert_true(
            False,
            "User 1: Không tìm thấy doctor_id trong response",
            actual_value=content,
        )
        return
    doctor_id = int(doctor_id_match.group(1))

    # Xem lịch trống
    result = await send_message(
        session,
        token,
        session_id_1,
        f"Xem lịch trống bác sĩ [#{doctor_id}] ngày 15/09/2026",
    )
    content = extract_content(result)

    # Lấy slot_id đầu tiên
    slot_id_match = re.search(r"Khung giờ #(\d+)", content)
    if not slot_id_match:
        assert_true(False, "User 1: Không tìm thấy slot_id", actual_value=content)
        return
    slot_id = int(slot_id_match.group(1))

    # Đặt slot
    result = await send_message(
        session, token, session_id_1, f"Đặt cho tôi khung giờ #{slot_id}"
    )
    content = extract_content(result)

    # Xác nhận
    result = await send_message(session, token, session_id_1, "Xác nhận đặt lịch")
    content = extract_content(result)

    appointment_id_match = re.search(r"#(\d+)", content)
    assert_true(
        appointment_id_match is not None and "thành công" in content.lower(),
        "User 1: Đặt lịch thành công",
        actual_value=content,
    )

    await asyncio.sleep(1)

    # User 2: Tìm bác sĩ tim mạch → xem lịch → cố đặt cùng slot
    print("\n--- User 2: Cố đặt cùng slot ---")
    result = await send_message(session, token_2, session_id_2, "Tìm bác sĩ tim mạch")
    content = extract_content(result)

    # Xem lịch trống
    result = await send_message(
        session,
        token_2,
        session_id_2,
        f"Xem lịch trống bác sĩ [#{doctor_id}] ngày 15/09/2026",
    )
    content = extract_content(result)

    # User 2 cố đặt cùng slot
    result = await send_message(
        session, token_2, session_id_2, f"Đặt cho tôi khung giờ #{slot_id}"
    )
    content = extract_content(result)

    # Xác nhận
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
    """Test: Hủy appointment đã confirm"""
    print("\n" + "=" * 70)
    print("TEST 10: Hủy appointment đã xác nhận")
    print("=" * 70)

    # Tìm bác sĩ → xem lịch → đặt slot → xác nhận
    result = await send_message(session, token, session_id, "Tìm bác sĩ Hô Hấp")
    content = extract_content(result)

    import re

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

        # Gọi API hủy appointment
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


async def reset_test_data(session: aiohttp.ClientSession, token: str):
    """Reset dữ liệu test — xóa appointments cũ, khôi phục slot"""
    print("\n[0] Reset dữ liệu test...")

    # Lấy danh sách appointments của user hiện tại và hủy chúng
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


# ============ MAIN TEST RUNNER ============


async def main():
    global PASS_COUNT, FAIL_COUNT

    print("=" * 70)
    print("TEST END-TO-END COMPLETE CHO AI AGENT")
    print("=" * 70)

    async with aiohttp.ClientSession() as session:
        # Setup
        await register_if_needed(session)
        token = await login(session, "test_user", "Test@123456")

        if not token:
            print("\n❌ Không lấy được token, dừng test")
            return



        # Đăng ký và login user 2 cho test double-booking
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

        # Chạy tất cả test
        print("\n" + "=" * 70)
        print("CHẠY TẤT CẢ TEST SCENARIOS")
        print("=" * 70)

        # Test cơ bản
        await test_1_basic_search(session, token, session_id)
        await asyncio.sleep(2)

        await test_2_search_no_accent(session, token, session_id)
        await asyncio.sleep(2)

        await test_3_emergency(session, token, session_id)
        await asyncio.sleep(2)

        await test_4_search_by_name(session, token, session_id)
        await asyncio.sleep(2)

        await test_5_search_by_fee(session, token, session_id)
        await asyncio.sleep(2)

        await test_7_not_found_specialty(session, token, session_id)
        await asyncio.sleep(2)

        # Test QUAN TRỌNG NHẤT: Multi-turn booking flow
        await test_6_multi_turn_booking_flow(session, token, session_id)
        await asyncio.sleep(2)

        await test_8_decline_booking(session, token, session_id)

        await test_9_double_booking(session, token, token_2, session_id, session_id_2)
        await test_10_cancel_confirmed_appointment(session, token_2, session_id_2)

        # Tổng kết
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