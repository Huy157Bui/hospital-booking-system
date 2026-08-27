import json
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
INPUT_JSON = (
    BASE_DIR / "dataset" / "bachmai" / "processed" / "bachmai_units_detail.json"
)
OUTPUT_RAG_JSON = (
    BASE_DIR / "dataset" / "bachmai" / "processed" / "bachmai_rag_chunks.json"
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s"
)


def split_text_into_chunks(
    text: str, chunk_size: int = 700, overlap: int = 100
) -> list[str]:
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]

        if end < text_length:
            last_newline = chunk.rfind("\n")
            last_period = chunk.rfind(". ")
            cut_point = max(last_newline, last_period)
            if cut_point > chunk_size // 2:
                chunk = chunk[: cut_point + 1]
                end = start + cut_point + 1

        cleaned_chunk = chunk.strip()
        if cleaned_chunk:
            chunks.append(cleaned_chunk)

        start = end - overlap if (end - overlap) > start else end

    return chunks


def main():
    if not INPUT_JSON.exists():
        logging.error(
            f"Chưa có file {INPUT_JSON}. Vui lòng chạy crawl_unit_details.py trước!"
        )
        return

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        units = json.load(f)

    rag_chunks = []
    global_chunk_counter = 1

    for unit in units:
        unit_name = unit.get("Tên đơn vị", "")
        slug = unit.get("Slug", "")
        unit_id = unit.get("ID", "")
        detail_data = unit.get("Chi tiết", {})

        text_content = detail_data.get("content_detail_text", "")
        address = detail_data.get("address", "")
        phone = detail_data.get("phone", "")
        website = detail_data.get("website", "")
        leadership = detail_data.get("leadership", [])

        if not text_content and not address and not leadership:
            continue

        header_info = f"Đơn vị: {unit_name}\nĐịa chỉ: {address}\nĐiện thoại: {phone}\nWebsite: {website}\n"
        if leadership:
            header_info += (
                "Ban lãnh đạo:\n"
                + "\n".join([f"- {l['position']}: {l['name']}" for l in leadership])
                + "\n"
            )

        full_document = header_info + "\nNội dung chi tiết:\n" + text_content
        chunks = split_text_into_chunks(full_document, chunk_size=700, overlap=100)

        for index, chunk_text in enumerate(chunks, start=1):
            rag_chunks.append(
                {
                    "chunk_id": f"chunk_{slug}_{index}",
                    "global_id": global_chunk_counter,
                    "text_payload": chunk_text,
                    "metadata": {
                        "source": "bachmai.gov.vn",
                        "unit_id": unit_id,
                        "unit_name": unit_name,
                        "slug": slug,
                        "url": unit.get("Link chi tiết", ""),
                        "address": address,
                        "phone": phone,
                        "chunk_index": index,
                        "total_chunks": len(chunks),
                    },
                }
            )
            global_chunk_counter += 1

    with open(OUTPUT_RAG_JSON, "w", encoding="utf-8") as f:
        json.dump(rag_chunks, f, ensure_ascii=False, indent=2)

    logging.info(
        f"🎉 Đã tạo thành công {len(rag_chunks)} chunks chất lượng cho RAG tại: {OUTPUT_RAG_JSON}"
    )

if __name__ == "__main__":
    main()