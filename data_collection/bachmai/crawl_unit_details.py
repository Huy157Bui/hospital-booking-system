import json
import logging
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
INPUT_JSON = BASE_DIR / "dataset" / "bachmai" / "raw" / "bachmai_don_vi_sach.json"
OUTPUT_DIR = BASE_DIR / "dataset" / "bachmai" / "processed"
OUTPUT_JSON = OUTPUT_DIR / "bachmai_units_detail.json"
OUTPUT_EXCEL = OUTPUT_DIR / "bachmai_units_detail.xlsx"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def parse_bachmai_unit_html(html_content: str, url: str) -> dict:
    soup = BeautifulSoup(html_content, "html.parser")

    result = {
        "url": url,
        "address": "",
        "phone": "",
        "website": "",
        "leadership": [],
        "content_detail_text": "",
        "status": "success",
        "error": None,
    }

    try:
        intro_section = soup.find("section", id="gioi-thieu")
        if intro_section:
            info_box = intro_section.find("div", class_="department-content-box")
            if info_box:
                for p in info_box.find_all("p"):
                    text = p.get_text(strip=True)
                    if "Địa điểm trụ sở chính:" in text:
                        result["address"] = text.replace(
                            "Địa điểm trụ sở chính:", ""
                        ).strip()
                    elif "Điện thoại:" in text:
                        result["phone"] = text.replace("Điện thoại:", "").strip()
                    elif "Website:" in text:
                        a_tag = p.find("a")
                        result["website"] = (
                            a_tag["href"]
                            if a_tag
                            else text.replace("Website:", "").strip()
                        )

        leadership_section = soup.find("section", id="ban-lanh-dao")
        if leadership_section:
            slides = leadership_section.find_all("div", class_="swiper-slide")
            for slide in slides:
                a_tag = slide.find("a", class_="items")
                if a_tag:
                    href = a_tag.get("href", "")
                    doctor_id = href.split("/")[-1] if href else ""

                    title_div = a_tag.find("div", class_="title")
                    desc_div = a_tag.find("div", class_="desc")

                    result["leadership"].append(
                        {
                            "doctor_id": doctor_id,
                            "position": title_div.get_text(strip=True)
                            if title_div
                            else "",
                            "name": desc_div.get_text(strip=True) if desc_div else "",
                        }
                    )

        content_editor = soup.find("div", class_="content-editor")
        if content_editor:
            result["content_detail_text"] = content_editor.get_text(
                separator="\n", strip=True
            )

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def main():
    if not INPUT_JSON.exists():
        logging.error(f"Không tìm thấy file: {INPUT_JSON}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        units = json.load(f)

    logging.info(f"Bắt đầu cào thông tin chi tiết cho {len(units)} đơn vị...")
    detailed_units = []

    for index, unit in enumerate(units, start=1):
        unit_name = unit.get("Tên đơn vị", "N/A")
        detail_url = unit.get("Link chi tiết")

        logging.info(f"[{index}/{len(units)}] Đang cào: {unit_name}")

        if detail_url and detail_url.startswith("http"):
            try:
                res = requests.get(detail_url, headers=HEADERS, timeout=15)
                if res.status_code == 200:
                    parsed_data = parse_bachmai_unit_html(res.text, detail_url)
                else:
                    parsed_data = {
                        "status": "failed",
                        "error": f"HTTP {res.status_code}",
                    }
            except Exception as e:
                parsed_data = {"status": "failed", "error": str(e)}
        else:
            parsed_data = {"status": "invalid_url", "error": "Invalid URL"}

        merged_record = {**unit, "Chi tiết": parsed_data}
        detailed_units.append(merged_record)
        time.sleep(1.0)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(detailed_units, f, ensure_ascii=False, indent=2)
    logging.info(f"✅ Đã lưu JSON tại: {OUTPUT_JSON}")

    excel_list = []
    for u in detailed_units:
        dt = u.get("Chi tiết", {})
        excel_list.append(
            {
                "STT": u.get("STT"),
                "Tên đơn vị": u.get("Tên đơn vị"),
                "ID": u.get("ID"),
                "Link chi tiết": u.get("Link chi tiết"),
                "Địa chỉ": dt.get("address", ""),
                "Điện thoại": dt.get("phone", ""),
                "Website": dt.get("website", ""),
                "Ban lãnh đạo": ", ".join(
                    [f"{l['position']}: {l['name']}" for l in dt.get("leadership", [])]
                ),
                "Nội dung chi tiết (Text)": dt.get("content_detail_text", ""),
                "Trạng thái cào": dt.get("status", ""),
            }
        )
    pd.DataFrame(excel_list).to_excel(OUTPUT_EXCEL, index=False)
    logging.info(f"✅ Đã lưu Excel tại: {OUTPUT_EXCEL}")

if __name__ == "__main__":
    main()