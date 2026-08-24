import json
import logging
from pathlib import Path
import requests
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = BASE_DIR / "dataset" / "bachmai" / "raw"
OUTPUT_JSON = OUTPUT_DIR / "bachmai_don_vi_sach.json"
OUTPUT_EXCEL = OUTPUT_DIR / "bachmai_don_vi_sach.xlsx"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s"
)

API_URL = "https://apicms.bachmai.gov.vn/api/Departments/list?language=vi"
PAYLOAD = {"maxResultCount": 100, "skipCount": 0}

# Danh sách từ khóa khẩu hiệu / quảng cáo không phải Khoa/Phòng
JUNK_KEYWORDS = [
    "hiệu quả điều trị",
    "tra cứu kết quả",
    "tuyến cao nhất",
    "hoàn chỉnh hạng đặc biệt",
    "cơ sở đào tạo",
    "dịch vụ cao cấp",
    "chuyên gia đầu ngành",
    "đặt lịch hẹn",
    "hỏi đáp cùng",
    "trang thiết bị hiện đại",
    "kỹ thuật tiên tiến",
]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logging.info("🚀 Đang gọi API lấy danh sách đơn vị Bệnh viện Bạch Mai...")

    try:
        res = requests.post(API_URL, json=PAYLOAD, timeout=15)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        logging.error(f"Lỗi gọi API: {e}")
        return

    if isinstance(data, list):
        raw_items = data
    elif isinstance(data, dict):
        raw_items = (
            data.get("items")
            or data.get("result", {}).get("items")
            or data.get("data")
            or []
        )
    else:
        raw_items = []

    clean_units = []
    stt = 1

    for item in raw_items:
        if not isinstance(item, dict):
            continue

        name = str(
            item.get("name")
            or item.get("Name")
            or item.get("title")
            or item.get("Title")
            or ""
        ).strip()
        slug = str(item.get("slug") or item.get("Slug") or "").strip()
        unit_id = str(item.get("id") or item.get("Id") or item.get("ID") or "").strip()

        if not name:
            continue

        # Lọc bỏ các khẩu hiệu quảng cáo
        if any(junk in name.lower() for junk in JUNK_KEYWORDS):
            continue

        if slug and unit_id:
            detail_url = f"https://bachmai.gov.vn/don-vi/{slug}/{unit_id}"
        elif slug:
            detail_url = f"https://bachmai.gov.vn/don-vi/{slug}"
        else:
            detail_url = ""

        clean_units.append(
            {
                "STT": stt,
                "Tên đơn vị": name,
                "Slug": slug,
                "ID": unit_id,
                "Link chi tiết": detail_url,
                "Địa chỉ": item.get("address") or item.get("Address"),
                "Số điện thoại": item.get("phoneNumber")
                or item.get("PhoneNumber")
                or item.get("phone"),
            }
        )
        stt += 1

    logging.info(f"✅ Đã lọc thành công {len(clean_units)} Khoa/Phòng/Viện sạch chuẩn.")

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(clean_units, f, ensure_ascii=False, indent=2)

    pd.DataFrame(clean_units).to_excel(OUTPUT_EXCEL, index=False)
    logging.info(f"🎉 Đã cập nhật file sạch tại: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()