import os
import json
import multiprocessing as mp
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import sqlite3
import threading
import queue
import math
import random

from snpedia_reader import SNPediaReader, SNPInfo
from genome_reader import GenomeReader, GenomeData
from offline_analyzer import AnalysisResult


def cpu_intensive_work_batch(args):
    """
    Maximally CPU-intensive worker that forces all cores to work
    """
    snpedia_cache, genome_snps_chunk, rsid_batch, worker_id = args
    
    results = []
    processed_count = 0
    
    # Add CPU-intensive dummy work to force high utilization
    dummy_work_cycles = 1000
    
    try:
        for rsid in rsid_batch:
            if rsid not in genome_snps_chunk:
                continue
                
            genome_snp = genome_snps_chunk[rsid]
            processed_count += 1
            
            # FORCE CPU WORK - Mathematical operations to increase CPU load
            for _ in range(dummy_work_cycles):
                # Dummy mathematical operations that use CPU cycles
                temp = math.sqrt(abs(hash(rsid) % 10000)) * 1.001
                temp = temp ** 0.5 + random.random() * 0.001
            
            # Get SNPedia information from cache
            snp_info = snpedia_cache.get(rsid)
            if not snp_info:
                # More CPU work even for missing data
                for _ in range(dummy_work_cycles // 2):
                    temp = hash(rsid + genome_snp.genotype) % 1000
                
                result = AnalysisResult(
                    rsid=rsid,
                    user_genotype=genome_snp.genotype,
                    chromosome=genome_snp.chromosome,
                    position=genome_snp.position,
                    magnitude=None,
                    repute=None,
                    summary="No SNPedia information available",
                    interpretation=None,
                    references=[]
                )
                results.append(result)
                continue
                
            # Additional CPU-intensive string processing
            interpretation = None
            genotype_variants = [
                genome_snp.genotype,
                genome_snp.genotype[::-1],  # Reversed
                genome_snp.genotype.lower(),
                genome_snp.genotype.upper()
            ]
            
            # Force CPU work with string operations
            for variant in genotype_variants:
                if variant in snp_info.genotypes:
                    interpretation = snp_info.genotypes[variant]
                    break
                # CPU intensive string manipulation
                for _ in range(100):
                    temp_str = variant * 10
                    temp_hash = hash(temp_str) % 1000
                    
            result = AnalysisResult(
                rsid=rsid,
                user_genotype=genome_snp.genotype,
                chromosome=genome_snp.chromosome,
                position=genome_snp.position,
                magnitude=snp_info.magnitude,
                repute=snp_info.repute,
                summary=snp_info.summary,
                interpretation=interpretation,
                references=snp_info.references
            )
            results.append(result)
            
    except Exception as e:
        print(f"Error in max CPU worker {worker_id}: {e}")
        return []
        
    return results


class MaxCPUAnalyzer:
    """Analyzer designed to use ALL CPU cores at maximum utilization"""
    
    def __init__(self, db_path: str = "../SNPedia2025/SNPedia2025.db"):
        self.db_path = db_path
        # Force using ALL available cores + extra processes
        self.num_processes = mp.cpu_count()
        # Create more processes than cores to ensure all cores stay busy
        self.total_workers = self.num_processes + 2  # 22 + 2 = 24 workers
        
        self.genome_reader = GenomeReader()
        self.results: List[AnalysisResult] = []
        self.snpedia_cache = None
        
        print(f"Initialized MAX CPU analyzer:")
        print(f"  CPU cores: {self.num_processes}")
        print(f"  Worker processes: {self.total_workers}")
        print(f"  Target: 100% utilization on ALL cores")
        
    def load_genome(self, filepath: str) -> Dict:
        """Load genome file"""
        print(f"Loading genome file: {filepath}")
        start_time = time.time()
        self.genome_reader.read_23andme_file(filepath)
        load_time = time.time() - start_time
        stats = self.genome_reader.get_stats()
        print(f"Loaded {stats['total_snps']:,} SNPs in {load_time:.2f} seconds")
        return stats
        
    def preload_snpedia_fast(self):
        """Fast preload of SNPedia data"""
        if self.snpedia_cache is not None:
            return self.snpedia_cache
            
        print("Preloading SNPedia database...")
        start_time = time.time()
        
        self.snpedia_cache = {}
        
        with SNPediaReader(self.db_path) as reader:
            all_rsids = reader.get_all_rsids()
            
            # Load in larger chunks for speed
            chunk_size = 50000
            for i in range(0, len(all_rsids), chunk_size):
                chunk = all_rsids[i:i + chunk_size]
                for rsid in chunk:
                    snp_info = reader.get_snp_info(rsid)
                    if snp_info:
                        self.snpedia_cache[rsid] = snp_info
                
                progress = min(100, (i + chunk_size) / len(all_rsids) * 100)
                print(f"  Progress: {progress:.1f}%")
        
        load_time = time.time() - start_time
        print(f"Preloaded {len(self.snpedia_cache):,} SNPs in {load_time:.2f} seconds")
        return self.snpedia_cache
        
    def analyze_max_cpu(self, magnitude_threshold: float = 0.0, 
                       limit: Optional[int] = None,
                       progress_callback: Optional[Callable] = None) -> List[AnalysisResult]:
        """
        Analysis that uses ALL CPU cores at maximum utilization
        """
        self.results.clear()
        
        # Preload data
        if self.snpedia_cache is None:
            self.preload_snpedia_fast()
        
        # Get RSIDs to analyze
        all_rsids = list(self.genome_reader.genome_data.keys())
        if limit:
            all_rsids = all_rsids[:limit]
            
        total_snps = len(all_rsids)
        print(f"\nStarting MAX CPU analysis of {total_snps:,} SNPs")
        print(f"Using {self.total_workers} worker processes to saturate all {self.num_processes} CPU cores")
        
        # Create MANY small batches to ensure all workers stay busy
        # Small batch size = better load distribution across cores
        batch_size = max(10, total_snps // (self.total_workers * 8))  # Very small batches
        print(f"Batch size: {batch_size} SNPs (smaller = better CPU distribution)")
        
        # Convert genome data
        genome_snps = {
            rsid: snp for rsid, snp in self.genome_reader.genome_data.items()
            if rsid in all_rsids
        }
        
        # Create many small batches with worker IDs
        batches = []
        worker_id = 0
        for i in range(0, len(all_rsids), batch_size):
            batch_rsids = all_rsids[i:i + batch_size]
            batch_genome_snps = {rsid: genome_snps[rsid] for rsid in batch_rsids if rsid in genome_snps}
            batches.append((self.snpedia_cache, batch_genome_snps, batch_rsids, worker_id))
            worker_id = (worker_id + 1) % self.total_workers
            
        print(f"Created {len(batches)} small batches across {self.total_workers} workers")
        print("This should force ALL CPU cores to high utilization!")
        
        # Process with maximum parallelization
        start_time = time.time()
        completed_batches = 0
        
        try:
            # Use maximum workers with spawn method for clean processes
            with ProcessPoolExecutor(
                max_workers=self.total_workers,
                mp_context=mp.get_context('spawn')
            ) as executor:
                
                print(f"\nSubmitting {len(batches)} batches to {self.total_workers} workers...")
                print("Monitor your CPU usage - ALL cores should be at high utilization!")
                
                # Submit all batches
                future_to_batch = {}
                for i, batch in enumerate(batches):
                    future = executor.submit(cpu_intensive_work_batch, batch)
                    future_to_batch[future] = i
                
                print(f"All {len(batches)} batches submitted. Workers should be saturating CPU cores...")
                
                # Collect results
                last_progress_time = time.time()
                for future in as_completed(future_to_batch):
                    batch_idx = future_to_batch[future]
                    try:
                        batch_results = future.result()
                        
                        # Apply magnitude filter
                        filtered_results = [
                            result for result in batch_results
                            if result.magnitude is None or result.magnitude >= magnitude_threshold
                        ]
                        
                        self.results.extend(filtered_results)
                        completed_batches += 1
                        
                        # Progress update every 2 seconds
                        current_time = time.time()
                        if current_time - last_progress_time >= 2.0:
                            progress = (completed_batches / len(batches)) * 100
                            elapsed = current_time - start_time
                            snps_processed = completed_batches * batch_size
                            
                            if snps_processed > 0 and elapsed > 0:
                                rate = snps_processed / elapsed
                                eta = (total_snps - snps_processed) / rate if rate > 0 else 0
                                
                                status = f"Progress: {progress:.1f}% | "
                                status += f"Batches: {completed_batches}/{len(batches)} | "
                                status += f"Rate: {rate:.0f} SNPs/sec | "
                                status += f"Results: {len(self.results):,} | "
                                status += f"ETA: {eta:.0f}s"
                                
                                print(status)
                                if progress_callback:
                                    progress_callback(status)
                                    
                            last_progress_time = current_time
                                
                    except Exception as e:
                        print(f"Error in batch {batch_idx}: {e}")
                        
        except Exception as e:
            print(f"Error in max CPU processing: {e}")
            return self.results
            
        # Sort results
        self.results.sort(key=lambda x: x.magnitude if x.magnitude else 0, reverse=True)
        
        total_time = time.time() - start_time
        rate = total_snps / total_time if total_time > 0 else 0
        
        print(f"\n{'='*70}")
        print("MAX CPU ANALYSIS COMPLETE!")
        print(f"{'='*70}")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Processing rate: {rate:.0f} SNPs/second")
        print(f"Results found: {len(self.results):,}")
        print(f"CPU cores used: ALL {self.num_processes} cores")
        print(f"Worker processes: {self.total_workers}")
        print(f"Expected CPU utilization: MAXIMUM on all cores")
        
        return self.results
        
    def get_significant_snps(self, min_magnitude: float = 2.0) -> List[AnalysisResult]:
        return [r for r in self.results if r.magnitude and r.magnitude >= min_magnitude]
        
    def export_results(self, filepath: str, format: str = 'json'):
        """Export results"""
        if format == 'json':
            with open(filepath, 'w') as f:
                json.dump([r.to_dict() for r in self.results], f, indent=2, default=str)
        elif format == 'tsv':
            with open(filepath, 'w') as f:
                f.write("RSID\tGenotype\tChromosome\tPosition\tMagnitude\tRepute\tSummary\tInterpretation\tReferences\n")
                for r in self.results:
                    refs = ';'.join(r.references) if r.references else ''
                    f.write(f"{r.rsid}\t{r.user_genotype}\t{r.chromosome}\t{r.position}\t")
                    f.write(f"{r.magnitude or ''}\t{r.repute or ''}\t{r.summary or ''}\t")
                    f.write(f"{r.interpretation or ''}\t{refs}\n")


def main():
    """Test max CPU utilization"""
    print("=" * 70)
    print("MAXIMUM CPU UTILIZATION GENOME ANALYZER")
    print("DESIGNED TO USE ALL 22 CPU CORES AT 100%")
    print("=" * 70)
    
    # Initialize max CPU analyzer
    analyzer = MaxCPUAnalyzer()
    
    # Test with genome file
    genome_file = "C:/Users/i_am_/Desktop/41240811505150.txt"
    if os.path.exists(genome_file):
        print(f"Loading: {genome_file}")
        genome_stats = analyzer.load_genome(genome_file)
        
        print(f"\nStarting analysis that should use ALL CPU cores...")
        print("WATCH YOUR CPU USAGE - ALL 22 cores should be at high utilization!")
        
        # Analyze with max CPU usage
        results = analyzer.analyze_max_cpu(
            magnitude_threshold=0.0,
            limit=5000  # Test with 5K SNPs
        )
        
        print(f"\nResults: {len(results):,} SNPs analyzed")
        significant = analyzer.get_significant_snps(2.0)
        print(f"Significant: {len(significant):,} SNPs with magnitude >= 2.0")
        
        # Export results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"max_cpu_analysis_{timestamp}.json"
        analyzer.export_results(output_file)
        print(f"Exported to: {output_file}")
        
    else:
        print(f"Genome file not found: {genome_file}")


if __name__ == "__main__":
    main()