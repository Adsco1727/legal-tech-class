@echo off
cd /d c:\Users\Gary\Documents\GitHub\legal-tech-class
.\.venv\Scripts\python.exe -m pytest dpo_system/tests/test_csf_ingest.py dpo_system/tests/test_ooma_dialer.py
