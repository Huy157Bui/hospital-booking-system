# File: app/tool_test_v3.py
import asyncio
import json
import aiohttp
import time
from typing import Any

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:3b"

# ============ TOOLS SCHEMA (V3) ============
# 1. Giữ max_fee trong search_doctors (model cần chỗ biểu đạt)
# 2. Thêm book_appointment để test đúng intent "đặt lịch"
# 3. Không có list_specialties trong test này (loại bỏ tool gây nhiễu)
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_doctors",
            "description": "Tìm bác sĩ theo chuyên khoa, giá khám. Dùng khi người dùng muốn tìm bác sĩ, hỏi giá khám, hoặc muốn biết bác sĩ theo chuyên khoa",
            "parameters": {
                "type": "object",
                "properties": {
                    "specialty_name": {
                        "type": "string",
                        "description": "Tên chuyên khoa (ví dụ: Tim Mạch, Mắt, Da Liễu, Nhi Khoa)",
                    },
                    "max_fee": {
                        "type": "number",
                        "description": "Giá khám tối đa (VNĐ). Ví dụ: 500000 cho 500k",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Kiểm tra lịch trống của bác sĩ theo ngày. Dùng khi người dùng hỏi về lịch khám, lịch trống, ngày giờ khám cụ thể của bác sĩ",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_name": {
                        "type": "string",
                        "description": "Tên bác sĩ (nếu người dùng đề cập)",
                    },
                    "specialty_name": {
                        "type": "string",
                        "description": "Tên chuyên khoa (nếu người dùng muốn khám theo chuyên khoa)",
                    },
                    "date": {
                        "type": "string",
                        "description": "Ngày khám (YYYY-MM-DD) nếu người dùng đề cập",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Đặt lịch khám. Dùng khi người dùng muốn đặt lịch khám cụ thể",
            "parameters": {
                "type": "object",
                "properties": {
                    "slot_id": {
                        "type": "integer",
                        "description": "ID khung giờ (nếu đã biết)",
                    },
                    "specialty_name": {
                        "type": "string",
                        "description": "Tên chuyên khoa muốn đặt lịch",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Lý do khám",
                    },
                },
            },
        },
    },
]

# ============ TEST CASES V3 - Ground truth đã được sửa ============
# Mỗi case: (câu hỏi, expected_tool, expected_specialty, description)
test_cases = [
    # === NHÓM 1: Tìm bác sĩ (search_doctors) ===
    (
        "Tôi muốn tìm bác sĩ tim mạch giá dưới 500k",
        "search_doctors",
        "Tim Mạch",
        "Tìm bác sĩ theo chuyên khoa + giá",
    ),
    (
        "Bác sĩ nào khám mắt giỏi?",
        "search_doctors",
        "Mắt",
        "Tìm bác sĩ theo chuyên khoa",
    ),
    (
        "Chi phí khám da liễu bao nhiêu?",
        "search_doctors",
        "Da Liễu",
        "Hỏi giá theo chuyên khoa",
    ),
    (
        "Bác sĩ nào giỏi về xương khớp?",
        "search_doctors",
        "Cơ Xương Khớp",
        "Tìm bác sĩ theo chuyên khoa",
    ),
    (
        "Giá khám tổng quát là bao nhiêu?",
        "search_doctors",
        None,
        "Hỏi giá khám tổng quát",
    ),
    (
        "Bác sĩ tim mạch nào nhận BHYT?",
        "search_doctors",
        "Tim Mạch",
        "Tìm bác sĩ + BHYT",
    ),
    (
        "Khám phụ khoa giá bao nhiêu?",
        "search_doctors",
        "Phụ Sản",
        "Hỏi giá theo chuyên khoa",
    ),
    (
        "Tôi cần tìm bác sĩ nội tiết",
        "search_doctors",
        "Nội Tiết",
        "Tìm bác sĩ chuyên khoa",
    ),
    ("Bác sĩ da liễu nào giỏi nhất?", "search_doctors", "Da Liễu", "Tìm bác sĩ giỏi"),
    (
        "Có phòng khám tai mũi họng nào gần đây không?",
        "search_doctors",
        "Tai Mũi Họng",
        "Tìm phòng khám theo chuyên khoa",
    ),
    # === NHÓM 2: Kiểm tra lịch (check_availability) ===
    (
        "Ngày mai bác sĩ Nguyễn Văn A có lịch trống không?",
        "check_availability",
        None,
        "Kiểm tra lịch bác sĩ cụ thể",
    ),
    (
        "Lịch khám của bác sĩ Trần Thị B tuần sau?",
        "check_availability",
        None,
        "Hỏi lịch bác sĩ cụ thể",
    ),
    (
        "Ngày 20/1 có lịch trống của bác sĩ nào không?",
        "check_availability",
        None,
        "Hỏi lịch trống chung",
    ),
    (
        "Có bác sĩ nhi khoa nào làm việc thứ 7 không?",
        "check_availability",
        "Nhi Khoa",
        "Hỏi lịch theo chuyên khoa",
    ),
    # === NHÓM 3: Đặt lịch (book_appointment) ===
    (
        "Đặt lịch khám nội khoa lúc 8h sáng mai",
        "book_appointment",
        "Nội Khoa",
        "Đặt lịch khám",
    ),
    (
        "Đặt lịch khám tim mạch cho mẹ tôi",
        "book_appointment",
        "Tim Mạch",
        "Đặt lịch cho người thân",
    ),
    (
        "Đặt lịch khám mắt cho con tôi 5 tuổi",
        "book_appointment",
        "Mắt",
        "Đặt lịch cho trẻ em",
    ),
    ("Đặt lịch khám hô hấp gấp", "book_appointment", "Hô Hấp", "Đặt lịch gấp"),
    (
        "Tôi muốn khám thần kinh vào chiều nay",
        "book_appointment",
        "Thần Kinh",
        "Đặt lịch khám chiều nay",
    ),
    # === NHÓM 4: Triệu chứng → Tư vấn (KHÔNG cần tool) ===
    (
        "Tôi bị đau đầu nên khám khoa nào?",
        None,
        "Thần Kinh",
        "Triệu chứng → gợi ý chuyên khoa (trả lời text)",
    ),
]


# ============ CHẤM ĐIỂM V3 ============
def evaluate_tool_call(
    user_message: str,
    actual_tool: str | None,
    actual_args: dict | None,
    expected_tool: str | None,
    expected_specialty: str | None,
) -> tuple[str, dict]:
    """
    Chấm điểm:
    - CORRECT: Đúng tool + đúng specialty (hoặc đúng khi không cần tool)
    - PARTIAL: Đúng tool nhưng sai/thiếu specialty
    - WRONG: Sai tool hoặc không gọi khi cần
    """
    # Case không cần tool (expected_tool = None)
    if expected_tool is None:
        if actual_tool is None:
            return "CORRECT", {
                "reason": "Correct: no tool needed",
                "note": f"Should suggest specialty: {expected_specialty}",
            }
        else:
            # Model gọi tool khi không cần - nhưng có thể chấp nhận search_doctors
            if actual_tool == "search_doctors":
                return "PARTIAL", {
                    "reason": "Called search_doctors instead of just suggesting specialty",
                    "note": "Acceptable but not optimal",
                }
            return "WRONG", {
                "reason": f"Called {actual_tool} when no tool needed",
            }

    # Case cần tool
    if actual_tool is None:
        return "WRONG", {
            "reason": f"No tool called (expected {expected_tool})",
        }

    if actual_tool != expected_tool:
        return "WRONG", {
            "reason": f"Wrong tool: expected {expected_tool}, got {actual_tool}",
        }

    # Đúng tool, kiểm tra specialty nếu cần
    if expected_specialty:
        actual_specialty = (actual_args or {}).get("specialty_name", "")
        if not actual_specialty:
            return "PARTIAL", {
                "reason": f"Missing specialty_name (expected: {expected_specialty})",
            }

        # So sánh fuzzy
        expected_norm = expected_specialty.lower().replace(" ", "").replace("-", "")
        actual_norm = actual_specialty.lower().replace(" ", "").replace("-", "")

        if (
            expected_norm == actual_norm
            or expected_norm in actual_norm
            or actual_norm in expected_norm
        ):
            return "CORRECT", {
                "reason": f"Correct tool and specialty: {actual_specialty}",
            }
        else:
            return "PARTIAL", {
                "reason": f"Wrong specialty: expected {expected_specialty}, got {actual_specialty}",
            }

    return "CORRECT", {
        "reason": f"Correct tool: {actual_tool}",
    }


async def test_tool_calling_v3():
    correct_count = 0
    partial_count = 0
    wrong_count = 0
    results = []
    latencies = []

    async with aiohttp.ClientSession() as session:
        for i, (test_case, expected_tool, expected_specialty, description) in enumerate(
            test_cases, 1
        ):
            try:
                start_time = time.time()

                payload = {
                    "model": MODEL,
                    "messages": [{"role": "user", "content": test_case}],
                    "tools": TOOLS_SCHEMA,
                    "stream": False,
                    "temperature": 0.1,
                }

                async with session.post(
                    f"{OLLAMA_URL}/api/chat", json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")

                    result = await response.json()
                    latency = time.time() - start_time
                    latencies.append(latency)

                # Lấy tool calls
                tool_calls = result.get("message", {}).get("tool_calls", [])

                if tool_calls:
                    tool_call = tool_calls[0]
                    actual_tool = tool_call.get("function", {}).get("name", "")
                    actual_args = tool_call.get("function", {}).get("arguments", {})

                    if isinstance(actual_args, str):
                        try:
                            actual_args = json.loads(actual_args)
                        except:
                            actual_args = {"raw": actual_args}
                else:
                    actual_tool = None
                    actual_args = None

                # Chấm điểm
                score, detail = evaluate_tool_call(
                    test_case,
                    actual_tool,
                    actual_args,
                    expected_tool,
                    expected_specialty,
                )

                if score == "CORRECT":
                    correct_count += 1
                    icon = "✅"
                elif score == "PARTIAL":
                    partial_count += 1
                    icon = "⚠️"
                else:
                    wrong_count += 1
                    icon = "❌"

                print(f"[{i}/{len(test_cases)}] {icon} ({latency:.2f}s) {test_case}")
                print(
                    f"  Expected: {expected_tool or 'NO_TOOL'}"
                    + (f" / {expected_specialty}" if expected_specialty else "")
                )
                print(
                    f"  Actual:   {actual_tool or 'NO_TOOL'}"
                    + (
                        f" / {actual_args.get('specialty_name', '') if actual_args else ''}"
                        if actual_args
                        else ""
                    )
                )
                print(f"  Score: {score} - {detail['reason']}")
                print()

                results.append(
                    {
                        "test_case": test_case,
                        "description": description,
                        "expected_tool": expected_tool,
                        "expected_specialty": expected_specialty,
                        "actual_tool": actual_tool,
                        "actual_args": actual_args,
                        "score": score,
                        "detail": detail,
                        "latency": latency,
                    }
                )

            except Exception as e:
                wrong_count += 1
                print(f"[{i}/{len(test_cases)}] ❌ {test_case}")
                print(f"  Error: {str(e)}")
                print()
                results.append(
                    {
                        "test_case": test_case,
                        "description": description,
                        "expected_tool": expected_tool,
                        "expected_specialty": expected_specialty,
                        "actual_tool": None,
                        "actual_args": None,
                        "score": "ERROR",
                        "detail": {"reason": str(e)},
                        "latency": 0,
                    }
                )

    # Tổng kết
    total = len(test_cases)
    correct_rate = (correct_count / total) * 100
    partial_rate = (partial_count / total) * 100
    wrong_rate = (wrong_count / total) * 100
    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    print("\n" + "=" * 70)
    print("KẾT QUẢ TEST TOOL-CALLING V3 (Ground truth đã chuẩn hóa)")
    print("=" * 70)
    print(f"Model: {MODEL}")
    print(f"Tổng số test cases: {total}")
    print(f"✅ CORRECT: {correct_count}/{total} ({correct_rate:.1f}%)")
    print(f"⚠️  PARTIAL: {partial_count}/{total} ({partial_rate:.1f}%)")
    print(f"❌ WRONG:   {wrong_count}/{total} ({wrong_rate:.1f}%)")
    print(f"Average latency: {avg_latency:.2f}s")
    print("=" * 70)

    # Phân tích theo nhóm
    print("\n=== PHÂN TÍCH THEO NHÓM ===")
    groups = {
        "search_doctors": [],
        "check_availability": [],
        "book_appointment": [],
        "no_tool": [],
    }

    for r in results:
        expected = r["expected_tool"] or "no_tool"
        if expected in groups:
            groups[expected].append(r)

    for group_name, group_results in groups.items():
        if group_results:
            correct = sum(1 for r in group_results if r["score"] == "CORRECT")
            total_group = len(group_results)
            print(
                f"{group_name}: {correct}/{total_group} correct ({correct / total_group * 100:.0f}%)"
            )

    # Lưu kết quả
    output = {
        "model": MODEL,
        "total_cases": total,
        "correct_count": correct_count,
        "partial_count": partial_count,
        "wrong_count": wrong_count,
        "correct_rate": correct_rate,
        "partial_rate": partial_rate,
        "wrong_rate": wrong_rate,
        "average_latency": avg_latency,
        "results": results,
    }

    with open("tool_test_v3_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nĐã lưu kết quả chi tiết vào tool_test_v3_results.json")


if __name__ == "__main__":
    asyncio.run(test_tool_calling_v3())