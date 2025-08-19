#!/usr/bin/env python3
"""
Test script for the Genetic YOLO API
"""

import requests
import json
import time
import os

API_BASE = "http://localhost:5000/api"
SAMPLE_FILE = "OfflineGenomeAnalyzer/sample_genome.txt"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            return True
    except Exception as e:
        print(f"Health check failed: {e}")
    return False

def test_upload():
    """Test file upload"""
    if not os.path.exists(SAMPLE_FILE):
        print(f"Sample file not found: {SAMPLE_FILE}")
        return None
    
    try:
        with open(SAMPLE_FILE, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{API_BASE}/upload", files=files, timeout=30)
            
        print(f"Upload: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Upload response: {data}")
            return data.get('session_id')
        else:
            print(f"Upload error: {response.text}")
    except Exception as e:
        print(f"Upload failed: {e}")
    return None

def test_analysis(session_id):
    """Test genome analysis"""
    try:
        payload = {
            'magnitude_threshold': 0.0,
            'limit': 100  # Limit for testing
        }
        response = requests.post(
            f"{API_BASE}/analyze/{session_id}", 
            json=payload, 
            timeout=60
        )
        
        print(f"Analysis: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Analysis completed!")
            print(f"  Total SNPs analyzed: {data['yolo_metrics']['totalSnpsAnalyzed']}")
            print(f"  Significant findings: {data['yolo_metrics']['significantFindings']}")
            print(f"  Risk Ape Index: {data['yolo_metrics']['riskApeIndex']}%")
            print(f"  Diamond Hands DNA: {data['yolo_metrics']['diamondHandsDNA']}%")
            return True
        else:
            print(f"Analysis error: {response.text}")
    except Exception as e:
        print(f"Analysis failed: {e}")
    return False

def main():
    print("=== Genetic YOLO API Test ===")
    
    # Test health
    print("\n1. Testing health endpoint...")
    if not test_health():
        print("Health check failed! Make sure the server is running.")
        return
    
    # Test upload
    print("\n2. Testing file upload...")
    session_id = test_upload()
    if not session_id:
        print("Upload failed!")
        return
    
    # Test analysis
    print(f"\n3. Testing analysis for session {session_id}...")
    if test_analysis(session_id):
        print("\n✅ All tests passed! The integration is working correctly.")
    else:
        print("\n❌ Analysis test failed.")

if __name__ == "__main__":
    main()