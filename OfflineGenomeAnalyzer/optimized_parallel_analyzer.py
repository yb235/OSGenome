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

from snpedia_reader import SNPediaReader, SNPInfo
from genome_reader import GenomeReader, GenomeData
from offline_analyzer import AnalysisResult


def preload_snpedia_data(db_path):
    """Preload all SNPedia data into memory for faster access"""
    print("Preloading SNPedia database into memory...")
    start_time = time.time()
    
    snpedia_cache = {}
    
    with SNPediaReader(db_path) as reader:
        # Get all RSIDs
        all_rsids = reader.get_all_rsids()
        print(f"Found {len(all_rsids):,} SNPs in database")
        
        # Load in chunks to show progress
        chunk_size = 10000
        for i in range(0, len(all_rsids), chunk_size):
            chunk = all_rsids[i:i + chunk_size]
            for rsid in chunk:
                snp_info = reader.get_snp_info(rsid)
                if snp_info:
                    snpedia_cache[rsid] = snp_info
            
            if (i // chunk_size + 1) % 5 == 0:
                progress = (i + chunk_size) / len(all_rsids) * 100
                print(f"  Loaded {i + chunk_size:,}/{len(all_rsids):,} SNPs ({progress:.1f}%)")
    
    load_time = time.time() - start_time
    print(f"Preloaded {len(snpedia_cache):,} SNPs in {load_time:.2f} seconds")
    return snpedia_cache


def analyze_snp_batch_optimized(args):
    """
    Optimized worker function - operates on cached data instead of database
    """
    snpedia_cache, genome_snps_chunk, rsid_batch = args
    
    results = []
    processed_count = 0
    
    try:
        for rsid in rsid_batch:
            if rsid not in genome_snps_chunk:
                continue
                
            genome_snp = genome_snps_chunk[rsid]
            processed_count += 1
            
            # Get SNPedia information from cache (much faster than DB lookup)
            snp_info = snpedia_cache.get(rsid)
            if not snp_info:
                # No SNPedia data available
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
                
            # Find interpretation for user's genotype
            interpretation = None
            if genome_snp.genotype in snp_info.genotypes:
                interpretation = snp_info.genotypes[genome_snp.genotype]
            elif genome_snp.genotype[::-1] in snp_info.genotypes:  # Try reversed
                interpretation = snp_info.genotypes[genome_snp.genotype[::-1]]
                
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
        print(f"Error in optimized worker process: {e}")
        return []
        
    return results


class OptimizedParallelAnalyzer:
    """Highly optimized parallel genome analyzer that maximizes CPU utilization"""
    
    def __init__(self, db_path: str = "../SNPedia2025/SNPedia2025.db", 
                 num_processes: Optional[int] = None,
                 aggressive_mode: bool = True):
        self.db_path = db_path
        self.num_processes = num_processes or mp.cpu_count()
        self.aggressive_mode = aggressive_mode
        self.genome_reader = GenomeReader()
        self.results: List[AnalysisResult] = []
        self.snpedia_cache = None
        
        if aggressive_mode:
            # Use more processes than CPU cores for I/O bound work
            self.num_processes = min(self.num_processes * 2, 64)
            
        print(f"Initialized optimized analyzer with {self.num_processes} processes (aggressive: {aggressive_mode})")
        
    def load_genome(self, filepath: str) -> Dict:
        """Load a personal genome file"""
        print(f"Loading genome file: {filepath}")
        start_time = time.time()
        self.genome_reader.read_23andme_file(filepath)
        load_time = time.time() - start_time
        stats = self.genome_reader.get_stats()
        print(f"Loaded {stats['total_snps']:,} SNPs in {load_time:.2f} seconds")
        return stats
        
    def preload_snpedia(self):
        """Preload SNPedia data into memory"""
        if self.snpedia_cache is None:
            self.snpedia_cache = preload_snpedia_data(self.db_path)
        return self.snpedia_cache
        
    def analyze_all_optimized(self, magnitude_threshold: float = 0.0, 
                            limit: Optional[int] = None,
                            batch_size: Optional[int] = None,
                            progress_callback: Optional[Callable] = None) -> List[AnalysisResult]:
        """
        Highly optimized parallel analysis that maximizes CPU utilization
        """
        self.results.clear()
        
        # Preload SNPedia data if not already loaded
        if self.snpedia_cache is None:
            print("First run - preloading SNPedia database...")
            self.preload_snpedia()
        
        # Get RSIDs to analyze
        all_rsids = list(self.genome_reader.genome_data.keys())
        if limit:
            all_rsids = all_rsids[:limit]
            
        total_snps = len(all_rsids)
        print(f"Starting optimized analysis of {total_snps:,} SNPs using {self.num_processes} processes")
        
        # Calculate optimal batch size based on CPU count and data size
        if batch_size is None:
            # Smaller batches = better load distribution = higher CPU utilization
            batch_size = max(50, total_snps // (self.num_processes * 4))
            
        print(f"Using batch size: {batch_size} SNPs per batch")
        
        # Convert genome data to dict for serialization
        genome_snps = {
            rsid: snp for rsid, snp in self.genome_reader.genome_data.items()
            if rsid in all_rsids
        }
        
        # Create many small batches for better load balancing
        batches = []
        for i in range(0, len(all_rsids), batch_size):
            batch_rsids = all_rsids[i:i + batch_size]
            batch_genome_snps = {rsid: genome_snps[rsid] for rsid in batch_rsids if rsid in genome_snps}
            batches.append((self.snpedia_cache, batch_genome_snps, batch_rsids))
            
        print(f"Created {len(batches)} batches of ~{batch_size} SNPs each")
        print(f"This should maximize CPU utilization across all {self.num_processes} cores")
        
        # Process batches with maximum parallelization
        start_time = time.time()
        completed_batches = 0
        
        try:
            # Use ProcessPoolExecutor with custom settings for maximum CPU usage
            with ProcessPoolExecutor(
                max_workers=self.num_processes,
                mp_context=mp.get_context('spawn')  # Ensure clean process creation
            ) as executor:
                
                # Submit all batches immediately to keep all cores busy
                future_to_batch = {}
                for i, batch in enumerate(batches):
                    future = executor.submit(analyze_snp_batch_optimized, batch)
                    future_to_batch[future] = i
                
                print(f"Submitted {len(batches)} batches to {self.num_processes} worker processes")
                print("All CPU cores should now be at high utilization...")
                
                # Collect results as they complete
                for future in as_completed(future_to_batch):
                    batch_idx = future_to_batch[future]
                    try:
                        batch_results = future.result()
                        
                        # Apply magnitude filter
                        filtered_results = []
                        for result in batch_results:
                            if result.magnitude is None or result.magnitude >= magnitude_threshold:
                                filtered_results.append(result)
                                
                        self.results.extend(filtered_results)
                        completed_batches += 1
                        
                        # Progress update
                        progress = (completed_batches / len(batches)) * 100
                        elapsed = time.time() - start_time
                        snps_processed = completed_batches * batch_size
                        
                        if snps_processed > 0 and elapsed > 0:
                            rate = snps_processed / elapsed
                            eta = (total_snps - snps_processed) / rate if rate > 0 else 0
                            
                            status = f"Completed {completed_batches}/{len(batches)} batches ({progress:.1f}%) | "
                            status += f"Found: {len(self.results):,} results | "
                            status += f"Rate: {rate:.0f} SNPs/sec | ETA: {eta:.0f}s"
                            
                            print(status)
                            if progress_callback:
                                progress_callback(status)
                                
                        # Show progress every 10% or every 100 batches
                        if completed_batches % max(1, len(batches) // 10) == 0 or completed_batches % 100 == 0:
                            cpu_utilization = f"Batch {completed_batches}/{len(batches)} complete"
                            print(f"  {cpu_utilization}")
                                
                    except Exception as e:
                        print(f"Error processing batch {batch_idx}: {e}")
                        
        except Exception as e:
            print(f"Error in optimized parallel processing: {e}")
            return self.results
            
        # Sort by magnitude (highest first)
        self.results.sort(key=lambda x: x.magnitude if x.magnitude else 0, reverse=True)
        
        total_time = time.time() - start_time
        rate = total_snps / total_time if total_time > 0 else 0
        
        print(f"\n{'='*60}")
        print("OPTIMIZED PARALLEL ANALYSIS COMPLETE!")
        print(f"{'='*60}")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Processing rate: {rate:.0f} SNPs/second")
        print(f"Results found: {len(self.results):,}")
        print(f"Theoretical speedup: {self.num_processes}x")
        print(f"Actual speedup estimate: ~{rate / 50:.1f}x vs sequential")
        print(f"CPU cores utilized: {self.num_processes}")
        
        return self.results
        
    def get_significant_snps(self, min_magnitude: float = 2.0) -> List[AnalysisResult]:
        """Get SNPs with significant magnitude"""
        return [r for r in self.results if r.magnitude and r.magnitude >= min_magnitude]
        
    def get_medical_snps(self) -> List[AnalysisResult]:
        """Get SNPs with medical relevance"""
        return [r for r in self.results if r.repute]
        
    def export_results(self, filepath: str, format: str = 'json'):
        """Export analysis results to file"""
        if format == 'json':
            with open(filepath, 'w') as f:
                json.dump(
                    [r.to_dict() for r in self.results],
                    f,
                    indent=2,
                    default=str
                )
        elif format == 'tsv':
            with open(filepath, 'w') as f:
                f.write("RSID\tGenotype\tChromosome\tPosition\tMagnitude\tRepute\tSummary\tInterpretation\tReferences\n")
                for r in self.results:
                    refs = ';'.join(r.references) if r.references else ''
                    f.write(f"{r.rsid}\t{r.user_genotype}\t{r.chromosome}\t{r.position}\t")
                    f.write(f"{r.magnitude or ''}\t{r.repute or ''}\t{r.summary or ''}\t")
                    f.write(f"{r.interpretation or ''}\t{refs}\n")
                    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics"""
        stats = {
            'total_analyzed': len(self.results),
            'with_snpedia_data': sum(1 for r in self.results if r.summary != "No SNPedia information available"),
            'with_magnitude': sum(1 for r in self.results if r.magnitude is not None),
            'significant': sum(1 for r in self.results if r.magnitude and r.magnitude >= 2.0),
            'good_repute': sum(1 for r in self.results if r.repute and 'good' in r.repute.lower()),
            'bad_repute': sum(1 for r in self.results if r.repute and 'bad' in r.repute.lower()),
            'with_interpretation': sum(1 for r in self.results if r.interpretation)
        }
        
        # Magnitude distribution
        mag_dist = {'0-1': 0, '1-2': 0, '2-3': 0, '3-4': 0, '4+': 0}
        for r in self.results:
            if r.magnitude is not None:
                if r.magnitude < 1:
                    mag_dist['0-1'] += 1
                elif r.magnitude < 2:
                    mag_dist['1-2'] += 1
                elif r.magnitude < 3:
                    mag_dist['2-3'] += 1
                elif r.magnitude < 4:
                    mag_dist['3-4'] += 1
                else:
                    mag_dist['4+'] += 1
        stats['magnitude_distribution'] = mag_dist
        
        return stats


def main():
    """Test the optimized analyzer"""
    print("=" * 60)
    print("OPTIMIZED HIGH-CPU UTILIZATION GENOME ANALYZER")
    print("=" * 60)
    
    cpu_count = mp.cpu_count()
    print(f"System has {cpu_count} CPU cores")
    
    # Initialize optimized analyzer
    analyzer = OptimizedParallelAnalyzer(aggressive_mode=True)
    
    # Test with actual genome file
    genome_file = "C:/Users/i_am_/Desktop/41240811505150.txt"
    if os.path.exists(genome_file):
        print(f"Loading genome file: {genome_file}")
        genome_stats = analyzer.load_genome(genome_file)
        
        print(f"\nStarting optimized analysis...")
        print("This should utilize all CPU cores at high percentage!")
        
        # Test with 10K SNPs first
        results = analyzer.analyze_all_optimized(
            magnitude_threshold=0.0,
            limit=10000,
            batch_size=100  # Small batches for maximum parallelization
        )
        
        stats = analyzer.get_summary_stats()
        print(f"Analyzed {stats['total_analyzed']} SNPs")
        print(f"Found {stats['significant']} significant SNPs")
        
    else:
        print(f"Genome file not found: {genome_file}")


if __name__ == "__main__":
    main()