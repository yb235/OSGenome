"""
Comprehensive Validation Suite for Hybrid Genome Analyzer
Ensures accuracy and consistency across all compute units
"""

import os
import json
import hashlib
import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import concurrent.futures
import threading

from hybrid_accelerated_analyzer import HybridAcceleratedAnalyzer, ComputeConfig
from simple_parallel_analyzer import SimpleParallelAnalyzer
from offline_analyzer import AnalysisResult


@dataclass
class ValidationResult:
    """Result of validation test"""
    test_name: str
    passed: bool
    accuracy_score: float
    error_count: int
    error_rate: float
    discrepancies: List[Dict]
    message: str
    timestamp: str


class ReferenceValidator:
    """Validates results against reference implementation"""
    
    def __init__(self, reference_analyzer_class=SimpleParallelAnalyzer):
        self.reference_analyzer_class = reference_analyzer_class
        self.tolerance = 1e-6  # Floating point comparison tolerance
        
    def generate_reference_results(self, genome_file: str, db_path: str, 
                                 test_snps: int = 1000) -> List[AnalysisResult]:
        """Generate reference results using baseline analyzer"""
        print(f"Generating reference results with {test_snps:,} SNPs...")
        
        reference_analyzer = self.reference_analyzer_class(db_path)
        reference_analyzer.load_genome(genome_file)
        
        # Use deterministic subset for reproducible results
        results = reference_analyzer.analyze_parallel(limit=test_snps)
        
        print(f"Generated {len(results):,} reference results")
        return results
        
    def validate_results(self, test_results: List[AnalysisResult], 
                        reference_results: List[AnalysisResult],
                        test_name: str) -> ValidationResult:
        """Validate test results against reference"""
        print(f"Validating {test_name}...")
        
        # Create lookup dictionaries
        ref_dict = {r.rsid: r for r in reference_results}
        test_dict = {r.rsid: r for r in test_results}
        
        discrepancies = []
        exact_matches = 0
        total_compared = 0
        
        # Compare all RSIDs present in both sets
        common_rsids = set(ref_dict.keys()) & set(test_dict.keys())
        
        for rsid in common_rsids:
            ref_result = ref_dict[rsid]
            test_result = test_dict[rsid]
            total_compared += 1
            
            # Check for discrepancies
            discrepancy = self._compare_results(ref_result, test_result, rsid)
            if discrepancy:
                discrepancies.append(discrepancy)
            else:
                exact_matches += 1
                
        # Check for missing RSIDs
        missing_in_test = set(ref_dict.keys()) - set(test_dict.keys())
        extra_in_test = set(test_dict.keys()) - set(ref_dict.keys())
        
        if missing_in_test:
            discrepancies.append({
                'type': 'missing_rsids',
                'count': len(missing_in_test),
                'examples': list(missing_in_test)[:5]
            })
            
        if extra_in_test:
            discrepancies.append({
                'type': 'extra_rsids',
                'count': len(extra_in_test),
                'examples': list(extra_in_test)[:5]
            })
        
        # Calculate metrics
        accuracy_score = exact_matches / total_compared if total_compared > 0 else 0.0
        error_count = len(discrepancies)
        error_rate = error_count / max(total_compared, 1)
        
        # Determine if test passed
        passed = (accuracy_score >= 0.99 and  # 99% accuracy threshold
                 len(missing_in_test) == 0 and
                 len(extra_in_test) == 0)
        
        message = f"Compared {total_compared:,} results, {exact_matches:,} exact matches"
        if not passed:
            message += f", {error_count} discrepancies found"
            
        return ValidationResult(
            test_name=test_name,
            passed=passed,
            accuracy_score=accuracy_score,
            error_count=error_count,
            error_rate=error_rate,
            discrepancies=discrepancies[:10],  # Limit to first 10 for readability
            message=message,
            timestamp=datetime.now().isoformat()
        )
        
    def _compare_results(self, ref: AnalysisResult, test: AnalysisResult, 
                        rsid: str) -> Optional[Dict]:
        """Compare two analysis results"""
        discrepancy = None
        
        # Check genotype
        if ref.user_genotype != test.user_genotype:
            discrepancy = {
                'rsid': rsid,
                'type': 'genotype_mismatch',
                'reference': ref.user_genotype,
                'test': test.user_genotype
            }
            
        # Check magnitude (with tolerance for floating point)
        elif not self._float_equal(ref.magnitude, test.magnitude):
            discrepancy = {
                'rsid': rsid,
                'type': 'magnitude_mismatch',
                'reference': ref.magnitude,
                'test': test.magnitude
            }
            
        # Check repute
        elif ref.repute != test.repute:
            discrepancy = {
                'rsid': rsid,
                'type': 'repute_mismatch',
                'reference': ref.repute,
                'test': test.repute
            }
            
        # Check summary
        elif ref.summary != test.summary:
            discrepancy = {
                'rsid': rsid,
                'type': 'summary_mismatch',
                'reference': ref.summary[:100],  # Truncate for readability
                'test': test.summary[:100]
            }
            
        # Check interpretation
        elif ref.interpretation != test.interpretation:
            discrepancy = {
                'rsid': rsid,
                'type': 'interpretation_mismatch',
                'reference': ref.interpretation,
                'test': test.interpretation
            }
            
        return discrepancy
        
    def _float_equal(self, a: Optional[float], b: Optional[float]) -> bool:
        """Compare floating point numbers with tolerance"""
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        return abs(a - b) < self.tolerance


class ConsistencyValidator:
    """Validates consistency across multiple runs"""
    
    def __init__(self):
        self.hash_algorithm = hashlib.sha256
        
    def validate_determinism(self, analyzer_class, config: ComputeConfig,
                           genome_file: str, db_path: str, 
                           runs: int = 3, test_snps: int = 1000) -> ValidationResult:
        """Validate that analyzer produces deterministic results"""
        print(f"Testing determinism with {runs} runs...")
        
        run_results = []
        run_hashes = []
        
        for run_idx in range(runs):
            print(f"  Run {run_idx + 1}/{runs}")
            
            analyzer = analyzer_class(db_path, config=config)
            analyzer.load_genome(genome_file)
            results = analyzer.analyze_hybrid(limit=test_snps)
            
            # Sort results by RSID for consistent comparison
            results.sort(key=lambda x: x.rsid)
            run_results.append(results)
            
            # Generate hash of results
            result_hash = self._hash_results(results)
            run_hashes.append(result_hash)
            
        # Check if all hashes are identical
        unique_hashes = set(run_hashes)
        is_deterministic = len(unique_hashes) == 1
        
        discrepancies = []
        if not is_deterministic:
            discrepancies.append({
                'type': 'non_deterministic',
                'unique_hashes': len(unique_hashes),
                'hash_samples': list(unique_hashes)[:3]
            })
            
            # Find specific differences
            base_results = run_results[0]
            for run_idx, results in enumerate(run_results[1:], 1):
                differences = self._find_result_differences(base_results, results)
                if differences:
                    discrepancies.append({
                        'type': 'run_difference',
                        'run': run_idx,
                        'differences': differences[:5]
                    })
        
        return ValidationResult(
            test_name=f"Determinism Test ({runs} runs)",
            passed=is_deterministic,
            accuracy_score=1.0 if is_deterministic else 0.0,
            error_count=len(discrepancies),
            error_rate=0.0 if is_deterministic else 1.0,
            discrepancies=discrepancies,
            message=f"Deterministic: {is_deterministic}, {len(unique_hashes)} unique result sets",
            timestamp=datetime.now().isoformat()
        )
        
    def _hash_results(self, results: List[AnalysisResult]) -> str:
        """Generate hash of results for comparison"""
        # Create a deterministic string representation
        result_strings = []
        for result in results:
            result_str = f"{result.rsid}|{result.user_genotype}|{result.magnitude}|{result.repute}|{result.summary}"
            result_strings.append(result_str)
            
        combined_string = "\n".join(result_strings)
        return self.hash_algorithm(combined_string.encode()).hexdigest()
        
    def _find_result_differences(self, results1: List[AnalysisResult], 
                               results2: List[AnalysisResult]) -> List[Dict]:
        """Find differences between two result sets"""
        dict1 = {r.rsid: r for r in results1}
        dict2 = {r.rsid: r for r in results2}
        
        differences = []
        
        # Check common RSIDs
        common_rsids = set(dict1.keys()) & set(dict2.keys())
        for rsid in common_rsids:
            r1, r2 = dict1[rsid], dict2[rsid]
            if (r1.user_genotype != r2.user_genotype or
                r1.magnitude != r2.magnitude or
                r1.repute != r2.repute):
                differences.append({
                    'rsid': rsid,
                    'field_differences': [
                        f for f in ['genotype', 'magnitude', 'repute']
                        if getattr(r1, f) != getattr(r2, f)
                    ]
                })
                
        return differences


class StressValidator:
    """Validates performance under stress conditions"""
    
    def __init__(self):
        self.stress_configurations = [
            {"name": "High Memory", "snp_count": 50000, "batch_size": 10000},
            {"name": "High Concurrency", "snp_count": 20000, "batch_size": 500},
            {"name": "Mixed Load", "snp_count": 30000, "batch_size": 2000}
        ]
        
    def validate_stress_conditions(self, analyzer_class, config: ComputeConfig,
                                 genome_file: str, db_path: str) -> List[ValidationResult]:
        """Run stress tests"""
        results = []
        
        for stress_config in self.stress_configurations:
            print(f"Running stress test: {stress_config['name']}")
            
            try:
                analyzer = analyzer_class(db_path, config=config)
                analyzer.load_genome(genome_file)
                
                start_time = datetime.now()
                test_results = analyzer.analyze_hybrid(
                    limit=stress_config['snp_count']
                )
                end_time = datetime.now()
                
                processing_time = (end_time - start_time).total_seconds()
                rate = len(test_results) / processing_time if processing_time > 0 else 0
                
                # Consider test passed if it completes without errors
                # and maintains reasonable performance
                passed = (len(test_results) > 0 and 
                         processing_time < stress_config['snp_count'] / 100)  # At least 100 SNPs/sec
                
                validation_result = ValidationResult(
                    test_name=f"Stress Test: {stress_config['name']}",
                    passed=passed,
                    accuracy_score=1.0 if passed else 0.0,
                    error_count=0 if passed else 1,
                    error_rate=0.0 if passed else 1.0,
                    discrepancies=[],
                    message=f"Processed {len(test_results):,} SNPs in {processing_time:.2f}s ({rate:.0f} SNPs/sec)",
                    timestamp=datetime.now().isoformat()
                )
                
            except Exception as e:
                validation_result = ValidationResult(
                    test_name=f"Stress Test: {stress_config['name']}",
                    passed=False,
                    accuracy_score=0.0,
                    error_count=1,
                    error_rate=1.0,
                    discrepancies=[{'type': 'exception', 'message': str(e)}],
                    message=f"Test failed with exception: {str(e)[:100]}",
                    timestamp=datetime.now().isoformat()
                )
                
            results.append(validation_result)
            
        return results


class ComprehensiveValidationSuite:
    """Master validation suite combining all validators"""
    
    def __init__(self, genome_file: str, db_path: str):
        self.genome_file = genome_file
        self.db_path = db_path
        
        self.reference_validator = ReferenceValidator()
        self.consistency_validator = ConsistencyValidator()
        self.stress_validator = StressValidator()
        
        self.validation_results: List[ValidationResult] = []
        
    def run_full_validation(self) -> bool:
        """Run comprehensive validation suite"""
        print("="*60)
        print("COMPREHENSIVE VALIDATION SUITE")
        print("="*60)
        
        all_passed = True
        
        # Test configurations
        test_configs = [
            ("CPU Only", ComputeConfig(use_gpu=False, use_npu=False, use_cpu=True)),
            ("GPU + CPU", ComputeConfig(use_gpu=True, use_npu=False, use_cpu=True)),
            ("NPU + CPU", ComputeConfig(use_gpu=False, use_npu=True, use_cpu=True)),
            ("Full Hybrid", ComputeConfig(use_gpu=True, use_npu=True, use_cpu=True))
        ]
        
        # Generate reference results once
        print("\n1. Generating Reference Results...")
        reference_results = self.reference_validator.generate_reference_results(
            self.genome_file, self.db_path, test_snps=5000
        )
        
        # Test each configuration
        for config_name, config in test_configs:
            print(f"\n2. Testing Configuration: {config_name}")
            
            # Accuracy validation
            try:
                analyzer = HybridAcceleratedAnalyzer(self.db_path, config=config)
                analyzer.load_genome(self.genome_file)
                test_results = analyzer.analyze_hybrid(limit=5000)
                
                accuracy_result = self.reference_validator.validate_results(
                    test_results, reference_results, f"Accuracy: {config_name}"
                )
                self.validation_results.append(accuracy_result)
                all_passed &= accuracy_result.passed
                
                print(f"  Accuracy: {'PASS' if accuracy_result.passed else 'FAIL'} "
                      f"({accuracy_result.accuracy_score:.3f})")
                
            except Exception as e:
                print(f"  Accuracy test failed: {e}")
                all_passed = False
                
            # Determinism validation
            try:
                determinism_result = self.consistency_validator.validate_determinism(
                    HybridAcceleratedAnalyzer, config, self.genome_file, self.db_path,
                    runs=3, test_snps=1000
                )
                self.validation_results.append(determinism_result)
                all_passed &= determinism_result.passed
                
                print(f"  Determinism: {'PASS' if determinism_result.passed else 'FAIL'}")
                
            except Exception as e:
                print(f"  Determinism test failed: {e}")
                all_passed = False
        
        # Stress testing (only on full hybrid)
        print(f"\n3. Stress Testing...")
        try:
            full_config = ComputeConfig(use_gpu=True, use_npu=True, use_cpu=True)
            stress_results = self.stress_validator.validate_stress_conditions(
                HybridAcceleratedAnalyzer, full_config, self.genome_file, self.db_path
            )
            
            for stress_result in stress_results:
                self.validation_results.append(stress_result)
                all_passed &= stress_result.passed
                print(f"  {stress_result.test_name}: {'PASS' if stress_result.passed else 'FAIL'}")
                
        except Exception as e:
            print(f"  Stress testing failed: {e}")
            all_passed = False
        
        # Generate report
        self._generate_validation_report()
        
        print(f"\n{'='*60}")
        print(f"VALIDATION SUMMARY: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
        print(f"{'='*60}")
        
        return all_passed
        
    def _generate_validation_report(self):
        """Generate comprehensive validation report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"OfflineGenomeAnalyzer/gpu_npu_optimization/validation_report_{timestamp}.json"
        
        # Summary statistics
        total_tests = len(self.validation_results)
        passed_tests = sum(1 for r in self.validation_results if r.passed)
        failed_tests = total_tests - passed_tests
        
        avg_accuracy = np.mean([r.accuracy_score for r in self.validation_results])
        
        report = {
            'timestamp': timestamp,
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'pass_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'average_accuracy': avg_accuracy
            },
            'detailed_results': [asdict(result) for result in self.validation_results],
            'failed_tests': [
                asdict(result) for result in self.validation_results 
                if not result.passed
            ]
        }
        
        # Save report
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\nValidation report saved to: {report_file}")
        print(f"Tests passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"Average accuracy: {avg_accuracy:.3f}")


def main():
    """Run the validation suite"""
    genome_file = "C:/Users/i_am_/Desktop/41240811505150.txt"
    db_path = "../SNPedia2025/SNPedia2025.db"
    
    if not os.path.exists(genome_file):
        print(f"Genome file not found: {genome_file}")
        return
        
    # Run comprehensive validation
    validation_suite = ComprehensiveValidationSuite(genome_file, db_path)
    all_passed = validation_suite.run_full_validation()
    
    print(f"\nValidation completed. All tests passed: {all_passed}")


if __name__ == "__main__":
    main()