import time
import psutil
import multiprocessing as mp
import threading
from parallel_analyzer import ParallelGenomeAnalyzer


def monitor_cpu_usage(duration=60, interval=1):
    """Monitor CPU usage during analysis"""
    print(f"Monitoring CPU usage for {duration} seconds...")
    print("Time\tCPU%\tCores")
    print("-" * 30)
    
    start_time = time.time()
    max_cpu = 0
    
    while time.time() - start_time < duration:
        # Get overall CPU usage
        cpu_percent = psutil.cpu_percent(interval=interval)
        
        # Get per-core usage
        per_core = psutil.cpu_percent(interval=0, percpu=True)
        active_cores = sum(1 for usage in per_core if usage > 10)
        
        elapsed = time.time() - start_time
        print(f"{elapsed:4.0f}s\t{cpu_percent:5.1f}%\t{active_cores:2d}/{len(per_core)}")
        
        max_cpu = max(max_cpu, cpu_percent)
        
        if elapsed > 10 and cpu_percent < 20:
            print("⚠️  Low CPU usage detected - analysis may not be using all cores")
            break
            
    print(f"\nMax CPU usage observed: {max_cpu:.1f}%")
    print(f"Expected for full utilization: ~{len(per_core) * 90}% ({len(per_core)} cores)")
    
    if max_cpu > len(per_core) * 50:
        print("✅ Good parallel utilization detected!")
    else:
        print("❌ Poor parallel utilization - only using some cores")


def test_parallel_performance():
    """Test parallel analyzer with CPU monitoring"""
    print("=" * 60)
    print("PARALLEL GENOME ANALYZER CPU UTILIZATION TEST")
    print("=" * 60)
    
    cpu_count = mp.cpu_count()
    print(f"System specs:")
    print(f"  CPU cores: {cpu_count}")
    print(f"  RAM: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    print(f"  Available RAM: {psutil.virtual_memory().available / (1024**3):.1f} GB")
    
    # Initialize analyzer
    print(f"\nInitializing parallel analyzer with {cpu_count} processes...")
    analyzer = ParallelGenomeAnalyzer(num_processes=cpu_count)
    
    # Load genome file
    genome_file = "C:/Users/i_am_/Desktop/41240811505150.txt"
    print(f"Loading genome file: {genome_file}")
    
    try:
        genome_stats = analyzer.load_genome(genome_file)
        print(f"✅ Loaded {genome_stats['total_snps']:,} SNPs")
    except Exception as e:
        print(f"❌ Error loading genome: {e}")
        return
    
    # Test with different SNP counts to measure scaling
    test_sizes = [1000, 5000, 10000]
    
    for test_size in test_sizes:
        print(f"\n{'='*50}")
        print(f"TESTING WITH {test_size:,} SNPs")
        print(f"{'='*50}")
        
        # Start CPU monitoring in background
        stop_monitoring = threading.Event()
        monitor_thread = threading.Thread(
            target=lambda: monitor_cpu_during_test(stop_monitoring, test_size)
        )
        monitor_thread.start()
        
        # Run analysis
        print(f"Starting parallel analysis of {test_size:,} SNPs...")
        start_time = time.time()
        
        try:
            results = analyzer.analyze_all_parallel(
                magnitude_threshold=0.0,
                limit=test_size,
                batch_size=min(500, test_size // cpu_count)
            )
            
            end_time = time.time()
            analysis_time = end_time - start_time
            
            # Stop monitoring
            stop_monitoring.set()
            monitor_thread.join()
            
            # Calculate performance metrics
            rate = test_size / analysis_time if analysis_time > 0 else 0
            
            print(f"\n📊 RESULTS FOR {test_size:,} SNPs:")
            print(f"  Analysis time: {analysis_time:.2f} seconds")
            print(f"  Processing rate: {rate:.0f} SNPs/second")
            print(f"  Results found: {len(results):,}")
            print(f"  Theoretical max rate: ~{rate * cpu_count:.0f} SNPs/sec if perfectly parallel")
            
            # Estimate full genome time
            full_genome_time = (genome_stats['total_snps'] * analysis_time) / test_size / 60
            print(f"  Estimated full genome time: {full_genome_time:.1f} minutes")
            
        except Exception as e:
            stop_monitoring.set()
            monitor_thread.join()
            print(f"❌ Error during analysis: {e}")
            
        time.sleep(2)  # Brief pause between tests
    
    print(f"\n{'='*60}")
    print("CPU UTILIZATION TEST COMPLETE")
    print("If you saw high CPU usage (>1000%) during analysis,")
    print("then all cores are being utilized effectively!")
    print(f"{'='*60}")


def monitor_cpu_during_test(stop_event, test_size):
    """Monitor CPU usage during a specific test"""
    print(f"  🔍 Monitoring CPU usage during {test_size:,} SNP analysis...")
    
    max_cpu = 0
    max_cores_active = 0
    samples = 0
    
    while not stop_event.is_set():
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            per_core = psutil.cpu_percent(interval=0, percpu=True)
            active_cores = sum(1 for usage in per_core if usage > 20)
            
            max_cpu = max(max_cpu, cpu_percent)
            max_cores_active = max(max_cores_active, active_cores)
            samples += 1
            
            if samples % 4 == 0:  # Print every 2 seconds
                print(f"    CPU: {cpu_percent:5.1f}% | Active cores: {active_cores:2d}/{len(per_core)}")
                
        except:
            break
            
    print(f"  📈 Peak CPU usage: {max_cpu:.1f}%")
    print(f"  📈 Max active cores: {max_cores_active}/{len(per_core)}")
    
    if max_cpu > 800:  # 800% means ~8+ cores active
        print("  ✅ Excellent parallel utilization!")
    elif max_cpu > 400:  # 400% means ~4+ cores active  
        print("  ✅ Good parallel utilization!")
    elif max_cpu > 200:  # 200% means ~2+ cores active
        print("  ⚠️  Moderate parallel utilization")
    else:
        print("  ❌ Poor parallel utilization - mostly single-threaded")


if __name__ == "__main__":
    test_parallel_performance()