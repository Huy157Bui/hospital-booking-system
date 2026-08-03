import uuid

def generate_record_number() -> str:
    return f"MR-{uuid.uuid4().hex[:10].upper()}"

def generate_reference_number() -> str:
    return f"REF-{uuid.uuid4().hex[:8].upper()}"