#!/usr/bin/env python3
"""
QRadar Rule Deploy Script — Custom JSON to QRadar Analytics API
GitHub Actions CI/CD Pipeline
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
    'SEC'         : QRADAR_TOKEN,
    'Accept'      : 'application/json',
    'Content-Type': 'application/json',
    'Version'     : '19.0', 
}

# ── 1. Bağlantı və Token Testi ────────────────────────────────────
def test_qradar_connection():
    print("🔍 QRadar API bağlantısı və Token yoxlanılır...")
    test_url = f"{QRADAR_HOST}/api/analytics/rules?Range=items=0-0"
    
    try:
        response = requests.get(test_url, headers=HEADERS, verify=False, timeout=15)
        
        if response.status_code in [200, 206]:
            print("   ✅ BAĞLANTI UĞURLUDUR: Token etibarlıdır və API ilə əlaqə quruldu!\n")
            return True
        elif response.status_code in [401, 403]:
            print(f"   ❌ XƏTA (HTTP {response.status_code}): Token səhvdir və ya yetki çatmır!")
            return False
        else:
            print(f"   ⚠️ GÖZLƏNİLMƏZ CAVAB (HTTP {response.status_code}): {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ XƏTA: QRadar serverinə qoşularkən vaxt bitdi (Timeout).")
        return False
    except requests.exceptions.ConnectionError:
        print("   ❌ XƏTA: QRadar serverinə qoşulmaq mümkün olmadı.")
        return False
    except Exception as e:
        print(f"   ❌ XƏTA: Gözlənilməz problem baş verdi: {e}")
        return False


# ── 2. JSON Tərcüməçi (Converter) ─────────────────────────────────
def transform_to_qradar_payload(custom_json):
    aql_query = custom_json.get("aql", "")
    
    where_match = re.search(r'WHERE\s+(.*?)(?:\s+ORDER\s+BY|\s+LAST\s+|\s*$)', aql_query, re.IGNORECASE)
    aql_condition = where_match.group(1).strip() if where_match else ""

    if not aql_condition:
        print(f"   XƏTA: '{custom_json.get('id')}' üçün AQL 'WHERE' şərti tapılmadı.")
        return None

    qradar_
