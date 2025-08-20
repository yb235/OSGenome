import time
import psutil
import multiprocessing as mp
import threading
from parallel_analyzer import ParallelGenomeAnalyzer


def monitor_cpu_usage(duration=30):
    """Monitor CPU usage during analysis"""
    print(f"Monitoring CPU usage for {duration} seconds...")
    print("Time   CPU%   Active_Cores/Total")
    print("-" * 35)
    
    start_time = time.time()
    max_cpu = 0
    max_active = 0
    
    while time.time() - start_time < duration:
        cpu_percent = psutil.cpu_percent(interval=1)
        per_core = psutil.cpu_percent(interval=0, percpu=True)
        active_cores = sum(1 for usage in per_core if usage > 10)
        
        elapsed = time.time() - start_time
        print(f"{elapsed:4.0f}s  {cpu_percent:5.1f}%     {active_cores:2d}/{len(per_core)}")
        
        max_cpu = max(max_cpu, cpu_percent)
        max_active = max(max_active, active_cores)
        
    print(f"\nPeak CPU usage: {max_cpu:.1f}%")
    print(f"Max active cores: {max_active}/{len(per_core)}")
    return max_cpu, max_active


def test_cpu_utilization():
    """Test CPU utilization with parallel processing"""
    print("=" * 60)
    print("CPU UTILIZATION TEST - PARALLEL GENOME ANALYZER")
    print("=" * 60)
    
    cpu_count = mp.cpu_count()
    print(f"System has {cpu_count} CPU cores")
    print(f"Available RAM: {psutil.virtual_memory().available / (1024**3):.1f} GB")
    
    # Initialize analyzer
    analyzer = ParallelGenomeAnalyzer(num_processes=cpu_count)
    
    # Load genome
    print("\nLoading genome file...")
    start_time = time.time()
    genome_stats = analyzer.load_genome("C:/Users/i_am_/Desktop/41240811505150.txt")
    load_time = time.time() - start_time
    
    print(f"Loaded {genome_stats['total_snps']:,} SNPs in {load_time:.1f} seconds")
    
    # Test parallel processing with CPU monitoring
    test_snps = 5000
    print(f"\nTesting parallel analysis of {test_snps:,} SNPs...")
    print("This will show if all CPU cores are being utilized")
    
    # Start CPU monitoring in background thread
    stop_monitor = threading.Event()
    max_cpu = 0
    max_active = 0
    
    def cpu_monitor():
        nonlocal max_cpu, max_active
        while not stop_monitor.is_set():
            try:
                cpu = psutil.cpu_percent(interval=0.5)
                cores = psutil.cpu_percent(interval=0, percpu=True)
                active = sum(1 for usage in cores if usage > 15)
                
                max_cpu = max(max_cpu, cpu)
                max_active = max(max_active, active)
                
                print(f"  CPU: {cpu:5.1f}% | Active cores: {active:2d}/{len(cores)}")
            except:
                break
    
    # Start monitoring
    monitor_thread = threading.Thread(target=cpu_monitor)
    monitor_thread.start()
    
    # Run analysis
    print("Starting analysis...")
    analysis_start = time.time()
    
    results = analyzer.analyze_all_parallel(
        magnitude_threshold=0.0,
        limit=test_snps,
        batch_size=250
    )
    
    analysis_time = time.time() - analysis_start
    
    # Stop monitoring
    stop_monitor.set()
    monitor_thread.join()
    
    # Results
    print(f"\nAnalysis Results:")
    print(f"  Time taken: {analysis_time:.2f} seconds")
    print(f"  Processing rate: {test_snps/analysis_time:.0f} SNPs/second")
    print(f"  Results found: {len(results):,}")
    
    print(f"\nCPU Utilization Results:")
    print(f"  Peak CPU usage: {max_cpu:.1f}%")
    print(f"  Max active cores: {max_active}/{cpu_count}")
    print(f"  Utilization efficiency: {(max_active/cpu_count)*100:.1f}%")
    
    # Performance assessment
    if max_cpu > cpu_count * 70:  # If using >70% of theoretical max
        print("  Status: EXCELLENT - All cores highly utilized!")
    elif max_cpu > cpu_count * 40:
        print("  Status: GOOD - Most cores being used")
    elif max_cpu > cpu_count * 20:
        print("  Status: MODERATE - Some cores being used")
    else:
        print("  Status: POOR - Limited parallel utilization")
    
    # Estimate full genome processing time
    full_time_minutes = (genome_stats['total_snps'] * analysis_time) / test_snps / 60
    print(f"\nEstimated full genome processing time: {full_time_minutes:.1f} minutes")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    if max_active >= cpu_count * 0.8:
        print("SUCCESS: Parallel processing is working well!")
    else:
        print("WARNING: May not be using all available cores efficiently")
    print("=" * 60)


if __name__ == "__main__":
    test_cpu_utilization()