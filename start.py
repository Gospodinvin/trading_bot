#!/usr/bin/env python3
import os
import sys
import subprocess

def main():
    # Получаем порт
    port = os.environ.get('PORT', '8000')
    print(f"Starting server on port {port}")
    
    # Запускаем Gunicorn
    cmd = [
        sys.executable, "-m", "gunicorn",
        "app.main:app",
        "--workers", "2",
        "--worker-class", "uvicorn.workers.UvicornWorker",
        "--bind", f"0.0.0.0:{port}"
    ]
    
    # Запускаем команду
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
