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
    'SEC'         : QRADAR_TOKEN,
    'Accept'      : 'application/json',
    'Content-Type': 'application/json',
    'Version'     : '19.0', # Analytics Rules API üçün uyğun versiya
}

# ── 1. Bağlantı və Token Testi ────────────────────────────────────
def test_qradar_connection():
    """QRadar API ilə bağlantını və Token-in etibarlılığını yoxlayır."""
    print("🔍 QRadar API bağlantısı və Token yoxlanılır...")
    
    # Çox yüngül bir sorğu göndəririk (sadəcə 1 qaydanı gətirməsini istəyirik)
    test_url = f"{QRADAR_HOST}/api/analytics/rules?Range=items=0-0"
    
    try:
        response = requests.get(test_url, headers=HEADERS, verify=False, timeout=15)
        
        if response.status_code in [200, 206]:
            print("   ✅ BAĞLANTI UĞURLUDUR: Token etibarlıdır və API ilə əlaqə quruldu!\n")
            return True
        elif response.status_code in [401, 403]:
            print(f"   ❌ XƏTA (HTTP {response.status_code}): Token səhvdir və ya yetki çatmır!")
            return False
