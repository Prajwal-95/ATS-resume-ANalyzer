"""
Download required NLP models.
Run this once after installing dependencies:
    python scripts/download_models.py
"""

import subprocess
import sys


def main():
    print("Downloading spaCy English model...")
    subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)
    print("spaCy model downloaded.")


if __name__ == "__main__":
    main()
