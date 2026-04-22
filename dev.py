"""
Локальний запуск лабораторної №3 без Vercel.

Використання:
    python dev.py            # http://localhost:8000
    python dev.py 5000       # на іншому порту

MongoDB не обов'язковий — без MONGODB_URI працює in-memory резерв.
Щоб увімкнути MongoDB:
    setx MONGODB_URI "mongodb+srv://..."   (PowerShell, на постійно)
    set MONGODB_URI=mongodb+srv://...      (cmd, на сесію)
"""

import sys
from http.server import HTTPServer

# Windows-консоль за замовчуванням cp1252, перемикаємо на UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from api.index import handler


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    httpd = HTTPServer(("127.0.0.1", port), handler)
    print(f"Lab 3 dev server: http://127.0.0.1:{port}")
    print("Ctrl+C to stop.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        print("\nStopped.")


if __name__ == "__main__":
    main()
