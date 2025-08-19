#!/usr/bin/env python3
"""
Simple test to verify the integration is working
"""

import sys
import os
sys.path.append('./OfflineGenomeAnalyzer')

from offline_analyzer import OfflineGenomeAnalyzer
from api_server import calculate_yolo_metrics, get_top_findings

def test_analyzer():
    """Test the genome analyzer directly"""
    print("=== Testing Offline Genome Analyzer ===")
    
    # Check if sample file exists
    sample_file = "OfflineGenomeAnalyzer/sample_genome.txt"
    if not os.path.exists(sample_file):
        print(f"Sample file not found: {sample_file}")
        return False
    
    try:
        # Initialize analyzer
        print("1. Initializing analyzer...")
        analyzer = OfflineGenomeAnalyzer(db_path="SNPedia2025/SNPedia2025.db")
        
        # Load genome
        print("2. Loading genome file...")
        genome_stats = analyzer.load_genome(sample_file)
        print(f"   Loaded {genome_stats['total_snps']} SNPs")
        
        # Analyze first 50 SNPs for testing
        print("3. Analyzing SNPs (limited to 50 for testing)...")
        results = analyzer.analyze_all(magnitude_threshold=0.0, limit=50)
        print(f"   Analyzed {len(results)} SNPs")
        
        # Calculate YOLO metrics
        print("4. Calculating YOLO metrics...")
        yolo_metrics = calculate_yolo_metrics(results)
        print("   YOLO Metrics:")
        print(f"     Risk Ape Index: {yolo_metrics['riskApeIndex']}%")
        print(f"     Diamond Hands DNA: {yolo_metrics['diamondHandsDNA']}%")
        print(f"     Panic Sell Propensity: {yolo_metrics['panicSellPropensity']}%")
        print(f"     Total SNPs Analyzed: {yolo_metrics['totalSnpsAnalyzed']}")
        print(f"     Significant Findings: {yolo_metrics['significantFindings']}")
        
        # Get top findings
        print("5. Getting top findings...")
        top_findings = get_top_findings(results, limit=5)
        print(f"   Found {len(top_findings)} significant findings")
        
        if top_findings:
            print("   Top finding:")
            finding = top_findings[0]
            print(f"     RSID: {finding['rsid']}")
            print(f"     Genotype: {finding['genotype']}")
            print(f"     Magnitude: {finding['magnitude']}")
            print(f"     Summary: {finding['summary'][:100] if finding['summary'] else 'None'}...")
        
        # Clean up
        analyzer.close()
        
        print("\n[SUCCESS] Integration test successful! The backend analysis is working correctly.")
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_analyzer()