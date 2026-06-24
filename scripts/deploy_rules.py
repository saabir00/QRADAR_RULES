#!/usr/bin/env python3
"""
QRadar Rule Deploy Script — Custom JSON to QRadar Analytics API
GitHub Actions CI/CD Pipeline

Hər rules/*.json faylını oxuyur, AQL daxilindən WHERE şərtini kəsir 
və QRadar-ın Analytics API-sinə (Rule Engine) POST/PUT edir.
Bununla da qaydalar birbaşa "Offenses -> Rules" bölməsinə əlavə olunur.
"""

import os
import re
import json
import glob
import sys
import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# QRadar mühit dəyişənləri
QRADAR_HOST  = os.environ.get('QRADAR_HOST', '').rstrip('/')
QRADAR_TOKEN = os.environ.get('QRADAR_SEC_TOKEN') or os.environ.get('QRADAR_TOKEN', '')

if not QRADAR_HOST or not QRADAR_TOKEN:
    print("XƏTA: QRADAR_HOST və ya QRADAR_SEC_TOKEN tapılmadı!")
    sys.exit(1)

HEADERS = {
    'SEC'     : QRADAR_TOKEN,
    'Accept'  : 'application/json',
    'Content-Type': 'application/json',
    'Version' : '19.0', # Analytics Rules API üçün uyğun versiya
}

# ── JSON Tərcüməçi (Converter) ────────────────────────────────────
def transform_to_qradar_payload(custom_json):
    """Xüsusi JSON strukturunu QRadar Rule payload-una çevirir."""
    aql_query = custom_json.get("aql", "")
    
    where_match = re.search(r'WHERE\s+(.*?)(?:\s+ORDER\s+BY|\s+LAST\s+|\s*$)', aql_query, re.IGNORECASE)
    aql_condition = where_match.group(1).strip() if where_match else ""

    if not aql_condition:
        print(f"   XƏTA: '{custom_json.get('id')}' üçün AQL 'WHERE' şərti tapılmadı.")
        return None

    qradar_meta = custom_json.get("qradar", {})
    credibility = qradar_meta.get("credibility", 8)
    relevance = qradar_meta.get("relevance", 8)

    # DİQQƏT: Aşağıdakı mötərizə və vergüllərin tam olduğuna əmin olun
    qradar_payload = {
        "name": qradar_meta.get("rule_name", custom_json.get("title", "Unnamed SOC Rule")),
        "identifier": custom_json.get("id", ""),
        "enabled": True,
        "type": "EVENT",
        "responses": {
            "offense": {
                "enabled": qradar_meta.get("response_action") == "create_offense",
                "severity": credibility,
                "credibility": credibility,
                "relevance": relevance
            }
        },
        "tests": [
            {
                "uid": "1",
                "type": "AQLFilterTest",
                "aql": aql_condition
            }
        ]
    }
    
    return qradar_payload
