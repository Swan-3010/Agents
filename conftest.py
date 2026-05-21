"""conftest.py — добавляет корень проекта в sys.path для pytest."""
import sys
from pathlib import Path

# Корень репозитория (папка где лежит этот файл)
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
