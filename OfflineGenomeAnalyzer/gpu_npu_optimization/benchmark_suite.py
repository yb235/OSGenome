"""
Comprehensive Benchmarking Suite for Hybrid Genome Analyzer
Tests performance, accuracy, and resource utilization
"""

import os
import time
import json
import psutil
import threading
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# GPU monitoring
try:
    import pynvml
    GPU_MONITORING = True
    pynvml.nvmlInit()
except ImportError:
    GPU_MONITORING = False

from hybrid_accelerated_analyzer import HybridAcceleratedAnalyzer, ComputeConfig
from simple_parallel_analyzer import SimpleParallelAnalyzer
from optimized_parallel_analyzer import OptimizedParallelAnalyzer
from max_cpu_analyzer import MaxCPUAnalyzer


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run"""
    analyzer_name: str
    total_snps: int
    processing_time: float
    snps_per_second: float
    results_found: int
    significant_snps: int
    cpu_usage_avg: float
    cpu_usage_max: float
    memory_usage_mb: float
    gpu_usage_avg: Optional[float] = None
    gpu_memory_mb: Optional[float] = None
    accuracy_score: Optional[float] = None
    error_rate: Optional[float] = None


@dataclass
class ResourceUsage:
    """System resource usage during analysis"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    gpu_percent: Optional[float] = None
    gpu_memory_mb: Optional[float] = None


class ResourceMonitor:
    """Real-time system resource monitoring"""
    
    def __init__(self):
        self.monitoring = False
        self.usage_data: List[ResourceUsage] = []
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start resource monitoring"""
        self.monitoring = True
        self.usage_data.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
            
    def _monitor_loop(self):
        """Monitor system resources every 0.5 seconds"""
        while self.monitoring:
            cpu_percent = psutil.cpu_percent(interval=None)
            memory_mb = psutil.virtual_memory().used / (1024**2)
            
            gpu_percent = None
            gpu_memory_mb = None
            
            if GPU_MONITORING:
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    gpu_info = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_percent = gpu_info.gpu
                    
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    gpu_memory_mb = mem_info.used / (1024**2)
                except:
                    pass
            
            usage = ResourceUsage(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                gpu_percent=gpu_percent,
                gpu_memory_mb=gpu_memory_mb
            )
            
            self.usage_data.append(usage)
            time.sleep(0.5)
            
    def get_stats(self) -> Dict:
        """Get resource usage statistics"""
        if not self.usage_data:
            return {}
            
        cpu_values = [u.cpu_percent for u in self.usage_data]
        memory_values = [u.memory_mb for u in self.usage_data]
        
        stats = {
            'cpu_avg': np.mean(cpu_values),
            'cpu_max': np.max(cpu_values),
            'cpu_min': np.min(cpu_values),
            'memory_avg_mb': np.mean(memory_values),
            'memory_max_mb': np.max(memory_values),
            'sample_count': len(self.usage_data)
        }
        
        if GPU_MONITORING and any(u.gpu_percent is not None for u in self.usage_data):
            gpu_values = [u.gpu_percent for u in self.usage_data if u.gpu_percent is not None]
            gpu_memory_values = [u.gpu_memory_mb for u in self.usage_data if u.gpu_memory_mb is not None]
            
            if gpu_values:
                stats.update({
                    'gpu_avg': np.mean(gpu_values),
                    'gpu_max': np.max(gpu_values),
                    'gpu_memory_avg_mb': np.mean(gpu_memory_values) if gpu_memory_values else 0
                })
        
        return stats


class InterferenceDetector:
    """Detect interference between compute units"""
    
    def __init__(self):
        self.baseline_performance = {}
        
    def measure_baseline(self, analyzer, test_data: List[str]) -> Dict:
        """Measure baseline performance for each compute unit"""
        results = {}
        
        # Test GPU only
        if hasattr(analyzer, 'config'):
            original_config = analyzer.config
            
            # GPU only test
            gpu_config = ComputeConfig(use_gpu=True, use_npu=False, use_cpu=False)
            analyzer.config = gpu_config
            start_time = time.time()
            analyzer.analyze_hybrid(limit=1000)
            gpu_time = time.time() - start_time
            results['gpu_only'] = 1000 / gpu_time if gpu_time > 0 else 0
            
            # NPU only test
            npu_config = ComputeConfig(use_gpu=False, use_npu=True, use_cpu=False)
            analyzer.config = npu_config
            start_time = time.time()
            analyzer.analyze_hybrid(limit=1000)
            npu_time = time.time() - start_time
            results['npu_only'] = 1000 / npu_time if npu_time > 0 else 0
            
            # CPU only test
            cpu_config = ComputeConfig(use_gpu=False, use_npu=False, use_cpu=True)
            analyzer.config = cpu_config
            start_time = time.time()
            analyzer.analyze_hybrid(limit=1000)
            cpu_time = time.time() - start_time
            results['cpu_only'] = 1000 / cpu_time if cpu_time > 0 else 0
            
            # Restore original config
            analyzer.config = original_config
            
        self.baseline_performance = results
        return results
        
    def detect_interference(self, hybrid_performance: float) -> Dict:
        """Detect if there's interference between compute units"""
        if not self.baseline_performance:
            return {'interference_detected': False, 'message': 'No baseline measurements'}
        
        # Theoretical maximum is sum of individual performances
        theoretical_max = sum(self.baseline_performance.values())
        efficiency = hybrid_performance / theoretical_max if theoretical_max > 0 else 0
        
        interference_detected = efficiency < 0.8  # Less than 80% efficiency indicates interference
        
        return {
            'interference_detected': interference_detected,
            'efficiency_ratio': efficiency,
            'theoretical_max_snps_per_sec': theoretical_max,
            'actual_snps_per_sec': hybrid_performance,
            'performance_loss_percent': (1 - efficiency) * 100,
            'baseline_performance': self.baseline_performance
        }


class AccuracyValidator:
    """Validate accuracy of parallel/accelerated results"""
    
    def compare_results(self, reference_results: List, test_results: List) -> Dict:
        """Compare test results against reference implementation"""
        if len(reference_results) != len(test_results):
            return {
                'accuracy_score': 0.0,
                'error_rate': 1.0,
                'message': f'Result count mismatch: {len(reference_results)} vs {len(test_results)}'
            }
        
        # Create lookup dictionaries
        ref_dict = {r.rsid: r for r in reference_results}
        test_dict = {r.rsid: r for r in test_results}
        
        total_compared = 0
        matches = 0
        magnitude_errors = []
        
        for rsid in ref_dict:
            if rsid in test_dict:
                ref_result = ref_dict[rsid]
                test_result = test_dict[rsid]
                
                total_compared += 1
                
                # Check exact match on key fields
                if (ref_result.user_genotype == test_result.user_genotype and
                    ref_result.magnitude == test_result.magnitude and
                    ref_result.repute == test_result.repute and
                    ref_result.summary == test_result.summary):
                    matches += 1
                else:
                    # Track magnitude differences for analysis
                    if ref_result.magnitude != test_result.magnitude:
                        magnitude_errors.append({
                            'rsid': rsid,
                            'ref_magnitude': ref_result.magnitude,
                            'test_magnitude': test_result.magnitude
                        })
        
        accuracy_score = matches / total_compared if total_compared > 0 else 0.0
        error_rate = 1.0 - accuracy_score
        
        return {
            'accuracy_score': accuracy_score,
            'error_rate': error_rate,
            'total_compared': total_compared,
            'exact_matches': matches,
            'magnitude_errors': len(magnitude_errors),
            'magnitude_error_details': magnitude_errors[:10]  # First 10 errors for debugging
        }


class BenchmarkSuite:
    """Comprehensive benchmarking suite"""
    
    def __init__(self, genome_file: str, db_path: str = "../SNPedia2025/SNPedia2025.db"):
        self.genome_file = genome_file
        self.db_path = db_path
        self.results: List[BenchmarkResult] = []
        self.monitor = ResourceMonitor()
        self.interference_detector = InterferenceDetector()
        self.accuracy_validator = AccuracyValidator()
        
    def run_benchmark(self, analyzer_class, analyzer_name: str, 
                     test_snps: int = 10000, **kwargs) -> BenchmarkResult:
        """Run a single benchmark"""
        print(f"\n{'='*50}")
        print(f"Benchmarking: {analyzer_name}")
        print(f"SNPs to analyze: {test_snps:,}")
        print(f"{'='*50}")
        
        # Initialize analyzer
        if analyzer_class == HybridAcceleratedAnalyzer:
            analyzer = analyzer_class(self.db_path, **kwargs)
        else:
            analyzer = analyzer_class(self.db_path)
        
        # Load genome
        analyzer.load_genome(self.genome_file)
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        # Run analysis
        start_time = time.time()
        results = analyzer.analyze_parallel(limit=test_snps) if hasattr(analyzer, 'analyze_parallel') else \
                 analyzer.analyze_all_optimized(limit=test_snps) if hasattr(analyzer, 'analyze_all_optimized') else \
                 analyzer.analyze_max_cpu(limit=test_snps) if hasattr(analyzer, 'analyze_max_cpu') else \
                 analyzer.analyze_hybrid(limit=test_snps)
        
        processing_time = time.time() - start_time
        
        # Stop monitoring
        self.monitor.stop_monitoring()
        
        # Get resource stats
        resource_stats = self.monitor.get_stats()
        
        # Calculate metrics
        snps_per_second = test_snps / processing_time if processing_time > 0 else 0
        significant_snps = len([r for r in results if r.magnitude and r.magnitude >= 2.0])
        
        # Create benchmark result
        benchmark_result = BenchmarkResult(
            analyzer_name=analyzer_name,
            total_snps=test_snps,
            processing_time=processing_time,
            snps_per_second=snps_per_second,
            results_found=len(results),
            significant_snps=significant_snps,
            cpu_usage_avg=resource_stats.get('cpu_avg', 0),
            cpu_usage_max=resource_stats.get('cpu_max', 0),
            memory_usage_mb=resource_stats.get('memory_avg_mb', 0),
            gpu_usage_avg=resource_stats.get('gpu_avg'),
            gpu_memory_mb=resource_stats.get('gpu_memory_avg_mb')
        )
        
        # Print results
        print(f"Processing time: {processing_time:.2f}s")
        print(f"Rate: {snps_per_second:.0f} SNPs/second")
        print(f"Results found: {len(results):,}")
        print(f"Significant SNPs: {significant_snps:,}")
        print(f"CPU usage: {resource_stats.get('cpu_avg', 0):.1f}% avg, {resource_stats.get('cpu_max', 0):.1f}% max")
        if resource_stats.get('gpu_avg'):
            print(f"GPU usage: {resource_stats.get('gpu_avg', 0):.1f}% avg")
        
        self.results.append(benchmark_result)
        return benchmark_result
        
    def run_full_benchmark_suite(self):
        """Run complete benchmark suite with all analyzers"""
        print("STARTING COMPREHENSIVE BENCHMARK SUITE")
        print("="*60)
        
        test_snps = 10000
        
        # 1. Simple Parallel Analyzer (baseline)
        self.run_benchmark(SimpleParallelAnalyzer, "Simple Parallel", test_snps)
        
        # 2. Optimized Parallel Analyzer
        self.run_benchmark(OptimizedParallelAnalyzer, "Optimized Parallel", test_snps)
        
        # 3. Max CPU Analyzer
        self.run_benchmark(MaxCPUAnalyzer, "Max CPU", test_snps)
        
        # 4. Hybrid Accelerated Analyzer (CPU only)
        cpu_config = ComputeConfig(use_gpu=False, use_npu=False, use_cpu=True)
        self.run_benchmark(HybridAcceleratedAnalyzer, "Hybrid (CPU only)", test_snps, config=cpu_config)
        
        # 5. Hybrid Accelerated Analyzer (GPU + CPU)
        gpu_config = ComputeConfig(use_gpu=True, use_npu=False, use_cpu=True)
        self.run_benchmark(HybridAcceleratedAnalyzer, "Hybrid (GPU + CPU)", test_snps, config=gpu_config)
        
        # 6. Hybrid Accelerated Analyzer (NPU + CPU)
        npu_config = ComputeConfig(use_gpu=False, use_npu=True, use_cpu=True)
        self.run_benchmark(HybridAcceleratedAnalyzer, "Hybrid (NPU + CPU)", test_snps, config=npu_config)
        
        # 7. Hybrid Accelerated Analyzer (All units)
        full_config = ComputeConfig(use_gpu=True, use_npu=True, use_cpu=True)
        hybrid_result = self.run_benchmark(HybridAcceleratedAnalyzer, "Hybrid (GPU + NPU + CPU)", test_snps, config=full_config)
        
        # Test for interference
        analyzer = HybridAcceleratedAnalyzer(self.db_path, config=full_config)
        analyzer.load_genome(self.genome_file)
        baseline = self.interference_detector.measure_baseline(analyzer, [])
        interference_analysis = self.interference_detector.detect_interference(hybrid_result.snps_per_second)
        
        print(f"\n{'='*60}")
        print("INTERFERENCE ANALYSIS")
        print(f"{'='*60}")
        print(f"Interference detected: {interference_analysis['interference_detected']}")
        print(f"Efficiency ratio: {interference_analysis['efficiency_ratio']:.3f}")
        print(f"Performance loss: {interference_analysis['performance_loss_percent']:.1f}%")
        
        # Generate report
        self.generate_report()
        
    def generate_report(self):
        """Generate comprehensive benchmark report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"OfflineGenomeAnalyzer/gpu_npu_optimization/benchmark_report_{timestamp}.json"
        
        # Prepare report data
        report = {
            'timestamp': timestamp,
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_gb': psutil.virtual_memory().total / (1024**3),
                'platform': os.name
            },
            'benchmark_results': [asdict(result) for result in self.results],
            'performance_ranking': sorted(
                [(r.analyzer_name, r.snps_per_second) for r in self.results],
                key=lambda x: x[1], reverse=True
            )
        }
        
        # Save report
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{'='*60}")
        print("BENCHMARK SUMMARY")
        print(f"{'='*60}")
        print("Performance Ranking (SNPs/second):")
        for i, (name, rate) in enumerate(report['performance_ranking'], 1):
            print(f"{i:2d}. {name:25s}: {rate:8.0f} SNPs/sec")
        
        print(f"\nDetailed report saved to: {report_file}")
        
        # Create visualization if matplotlib is available
        try:
            self.create_visualization(timestamp)
        except ImportError:
            print("Matplotlib not available for visualization")
            
    def create_visualization(self, timestamp: str):
        """Create performance visualization"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        names = [r.analyzer_name for r in self.results]
        rates = [r.snps_per_second for r in self.results]
        cpu_usage = [r.cpu_usage_avg for r in self.results]
        memory_usage = [r.memory_usage_mb for r in self.results]
        
        # Performance comparison
        ax1.bar(names, rates)
        ax1.set_title('Processing Rate Comparison')
        ax1.set_ylabel('SNPs/second')
        ax1.tick_params(axis='x', rotation=45)
        
        # CPU usage
        ax2.bar(names, cpu_usage)
        ax2.set_title('CPU Usage Comparison')
        ax2.set_ylabel('CPU Usage (%)')
        ax2.tick_params(axis='x', rotation=45)
        
        # Memory usage
        ax3.bar(names, memory_usage)
        ax3.set_title('Memory Usage Comparison')
        ax3.set_ylabel('Memory (MB)')
        ax3.tick_params(axis='x', rotation=45)
        
        # Performance vs CPU efficiency
        efficiency = [r.snps_per_second / r.cpu_usage_avg if r.cpu_usage_avg > 0 else 0 for r in self.results]
        ax4.scatter(cpu_usage, rates, s=100)
        for i, name in enumerate(names):
            ax4.annotate(name, (cpu_usage[i], rates[i]), xytext=(5, 5), textcoords='offset points')
        ax4.set_xlabel('CPU Usage (%)')
        ax4.set_ylabel('SNPs/second')
        ax4.set_title('Performance vs CPU Usage')
        
        plt.tight_layout()
        plot_file = f"OfflineGenomeAnalyzer/gpu_npu_optimization/benchmark_plot_{timestamp}.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"Visualization saved to: {plot_file}")


def main():
    """Run the complete benchmark suite"""
    genome_file = "C:/Users/i_am_/Desktop/41240811505150.txt"
    
    if not os.path.exists(genome_file):
        print(f"Genome file not found: {genome_file}")
        return
    
    # Initialize benchmark suite
    suite = BenchmarkSuite(genome_file)
    
    # Run complete benchmark
    suite.run_full_benchmark_suite()
    
    print("\nBenchmark suite completed!")


if __name__ == "__main__":
    main()