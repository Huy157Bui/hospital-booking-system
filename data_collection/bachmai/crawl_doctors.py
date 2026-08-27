import os
import json
import time
import logging
from pathlib import Path
import requests
import pandas as pd
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s"
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = BASE_DIR / "dataset" / "bachmai" / "raw"
JSON_OUTPUT_PATH = OUTPUT_DIR / "bachmai_bac_si.json"
EXCEL_OUTPUT_PATH = OUTPUT_DIR / "bachmai_bac_si.xlsx"

BASE_URL = "https://apicms.bachmai.gov.vn/api/Doctors"
DOMAIN_IMAGE_BASE = "https://apicms.bachmai.gov.vn"


def safe_str(val):
    if val is None:
        return ""
    return str(val).strip()


def clean_html(html_content):
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def fetch_all_doctors():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": "https://bachmai.gov.vn/",
    }

    doctors_list = []
    skip_count = 0
    max_result_count = 100
    total_count = None

    logging.info("🚀 Bắt đầu quá trình thu thập danh sách Bác sĩ Bệnh viện Bạch Mai...")

    while True:
        params = {
            "language": "vi",
            "skipCount": skip_count,
            "maxResultCount": max_result_count,
            "notIsDoctor": "false",
        }

        try:
            response = requests.get(
                BASE_URL, headers=headers, params=params, timeout=15
            )
            response.raise_for_status()
            data = response.json()

            result = data.get("result", {})
            if total_count is None:
                total_count = result.get("totalCount", 0)
                logging.info(
                    f"📊 Tổng số Bác sĩ phát hiện trên hệ thống: {total_count}"
                )

            items = result.get("items", [])
            if not items:
                break

            for item in items:
                avatar_obj = item.get("avatar") or {}
                avatar_relative_url = avatar_obj.get("url", "")
                avatar_full_url = (
                    f"{DOMAIN_IMAGE_BASE}{avatar_relative_url}"
                    if avatar_relative_url
                    else ""
                )

                train_raw = item.get("train", "")
                strengths_raw = item.get("strengths", "")

                doctor_data = {
                    "doctor_id": safe_str(item.get("id")),
                    "full_name": safe_str(item.get("fullName")),
                    "position": safe_str(item.get("position")),
                    "title": safe_str(item.get("title")),
                    "degree": safe_str(item.get("degree")),
                    "department_id": safe_str(item.get("departmentId")),
                    "avatar_url": avatar_full_url,
                    "train_html": train_raw,
                    "train_text": clean_html(train_raw),
                    "strengths_html": strengths_raw,
                    "strengths_text": clean_html(strengths_raw),
                    "is_lanh_dao": item.get("isLanhDao", False),
                    "is_expert": item.get("isExpert", False),
                    "order": item.get("order", 0),
                }
                doctors_list.append(doctor_data)

            logging.info(
                f"✅ Đã tải: {len(doctors_list)} / {total_count} bác sĩ..."
            )

            skip_count += max_result_count
            if len(doctors_list) >= total_count:
                break

            time.sleep(0.3)

        except Exception as e:
            logging.error(
                f"❌ Lỗi trong quá trình cào dữ liệu tại skipCount={skip_count}: {e}"
            )
            break

    logging.info(f"🎉 Hoàn thành thu thập thành công {len(doctors_list)} Bác sĩ!")
    return doctors_list


def save_dataset(doctors):
    if not doctors:
        logging.warning("⚠️ Không có dữ liệu để lưu!")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(JSON_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(doctors, f, ensure_ascii=False, indent=4)
    logging.info(f"💾 Đã lưu file JSON chuẩn tại: {JSON_OUTPUT_PATH}")

    df = pd.DataFrame(doctors)
    df_excel = df.drop(
        columns=["train_html", "strengths_html"], errors="ignore"
    )
    df_excel.to_excel(EXCEL_OUTPUT_PATH, index=False)
    logging.info(f"💾 Đã lưu file Excel chuẩn tại: {EXCEL_OUTPUT_PATH}")


if __name__ == "__main__":
    doctors_data = fetch_all_doctors()
    save_dataset(doctors_data)