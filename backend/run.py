import subprocess
import sys
import os
import time

def main():
    backend_dir = os.path.dirname(os.path.abspath(__file__))

    print("\n🔥 BƯỚC 1: SEED DỮ LIỆU")
    subprocess.run([sys.executable, "app/seed.py"], cwd=backend_dir)

    print("\n🔥 BƯỚC 2: KHỞI ĐỘNG UVICORN")
    uvicorn_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8000"],
        cwd=backend_dir,
    )
    print("⏳ Đang chờ server khởi động...")
    time.sleep(5)

    print("\n🔥 BƯỚC 3: CHẠY TEST")
    subprocess.run([sys.executable, "app/test_chat_agent_integration.py"], cwd=backend_dir)

    print("\n🛑 Đang dừng uvicorn...")
    uvicorn_process.terminate()
    try:
        uvicorn_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        uvicorn_process.kill()
        uvicorn_process.wait()
    print("✅ Đã dừng uvicorn")

if __name__ == "__main__":
    main()