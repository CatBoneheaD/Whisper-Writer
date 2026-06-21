import os
import requests

MODEL_DIR = os.path.join(os.environ["USERPROFILE"], ".cache", "huggingface", "hub",
                         "models--Systran--faster-whisper-large-v3", "snapshots", "main")
os.makedirs(MODEL_DIR, exist_ok=True)

FILES = {
    "model.bin": "https://huggingface.co/Systran/faster-whisper-large-v3/resolve/main/model.bin",
    "config.json": "https://huggingface.co/Systran/faster-whisper-large-v3/resolve/main/config.json",
    "tokenizer.json": "https://huggingface.co/Systran/faster-whisper-large-v3/resolve/main/tokenizer.json",
    "vocabulary.json": "https://huggingface.co/Systran/faster-whisper-large-v3/resolve/main/vocabulary.json",
    "preprocessor_config.json": "https://huggingface.co/Systran/faster-whisper-large-v3/resolve/main/preprocessor_config.json",
}

def download(filename, url):
    path = os.path.join(MODEL_DIR, filename)
    existing = os.path.getsize(path) if os.path.exists(path) else 0
    headers = {"Range": f"bytes={existing}-"} if existing else {}

    print(f"\n{'Докачиваю' if existing else 'Качаю'}: {filename} (уже есть: {existing // 1024 // 1024} МБ)")
    r = requests.get(url, headers=headers, stream=True, timeout=30)

    if r.status_code == 416:
        print(f"  Уже скачан полностью, пропускаю.")
        return
    if r.status_code not in (200, 206):
        print(f"  Ошибка: HTTP {r.status_code}")
        return

    total = int(r.headers.get("content-length", 0)) + existing
    downloaded = existing

    with open(path, "ab" if existing else "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                pct = downloaded / total * 100 if total else 0
                mb = downloaded // 1024 // 1024
                print(f"\r  {mb} МБ / {total // 1024 // 1024} МБ ({pct:.1f}%)", end="", flush=True)
    print(f"\n  Готово: {filename}")

for name, url in FILES.items():
    download(name, url)

print("\n\nВсе файлы скачаны! Модель готова к использованию.")
print(f"Путь: {MODEL_DIR}")
input("Нажми Enter для выхода...")
