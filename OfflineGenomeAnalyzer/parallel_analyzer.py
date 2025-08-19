import os
import json
import multiprocessing as mp
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import sqlite3
import threading
import queue

from snpedia_reader import SNPediaReader, SNPInfo
from genome_reader import GenomeReader, GenomeData
from offline_analyzer import AnalysisResult


def analyze_snp_batch(args):
    """
    Worker function to analyze a batch of SNPs in parallel
    This runs in a separate process
    """
    db_path, genome_snps, rsid_batch = args
    
    results = []
    
    # Each worker process gets its own database connection
    try:
        with SNPediaReader(db_path) as snpedia_reader:
            for rsid in rsid_batch:
                if rsid not in genome_snps:
                    continue
                    
                genome_snp = genome_snps[rsid]
                
                # Get SNPedia information
                snp_info = snpedia_reader.get_snp_info(rsid)
                if not snp_info:
                    # Even without SNPedia data, we can return basic info
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
        print(f"Error in worker process: {e}")
        return []
        
    return results


class ParallelGenomeAnalyzer:
    """Parallel version of the offline genome analyzer using multiprocessing"""
    
    def __init__(self, db_path: str = "../SNPedia2025/SNPedia2025.db", num_processes: Optional[int] = None):
        self.db_path = db_path
        self.num_processes = num_processes or mp.cpu_count()
        self.genome_reader = GenomeReader()
        self.results: List[AnalysisResult] = []
        
        print(f"Initialized parallel analyzer with {self.num_processes} processes")
        
    def load_genome(self, filepath: str) -> Dict:
        """Load a personal genome file"""
        print(f"Loading genome file: {filepath}")
        start_time = time.time()
        self.genome_reader.read_23andme_file(filepath)
        load_time = time.time() - start_time
        stats = self.genome_reader.get_stats()
        print(f"Loaded {stats['total_snps']:,} SNPs in {load_time:.2f} seconds")
        return stats
        
    def analyze_all_parallel(self, magnitude_threshold: float = 0.0, 
                           limit: Optional[int] = None,
                           batch_size: int = 1000,
                           progress_callback: Optional[Callable] = None) -> List[AnalysisResult]:
        """
        Analyze all SNPs in parallel using multiple processes
        
        Args:
            magnitude_threshold: Only include SNPs with magnitude >= this value
            limit: Maximum number of SNPs to analyze
            batch_size: Number of SNPs per batch (affects memory usage)
            progress_callback: Function to call with progress updates
        """
        self.results.clear()
        
        # Get list of RSIDs to analyze
        all_rsids = list(self.genome_reader.genome_data.keys())
        if limit:
            all_rsids = all_rsids[:limit]
            
        total_snps = len(all_rsids)
        print(f"Starting parallel analysis of {total_snps:,} SNPs using {self.num_processes} processes")
        
        # Convert genome data to dict for serialization
        genome_snps = {
            rsid: snp for rsid, snp in self.genome_reader.genome_data.items()
            if rsid in all_rsids
        }
        
        # Split RSIDs into batches for parallel processing
        batches = []
        for i in range(0, len(all_rsids), batch_size):
            batch = all_rsids[i:i + batch_size]
            batches.append((self.db_path, genome_snps, batch))
            
        print(f"Created {len(batches)} batches of ~{batch_size} SNPs each")
        
        # Process batches in parallel
        start_time = time.time()
        completed_batches = 0
        
        try:
            with ProcessPoolExecutor(max_workers=self.num_processes) as executor:
                # Submit all batches
                future_to_batch = {executor.submit(analyze_snp_batch, batch): i 
                                 for i, batch in enumerate(batches)}
                
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
                        if snps_processed > 0:
                            rate = snps_processed / elapsed
                            eta = (total_snps - snps_processed) / rate if rate > 0 else 0
                            
                            status = f"Processed {completed_batches}/{len(batches)} batches ({progress:.1f}%) - "
                            status += f"{len(self.results):,} results found - "
                            status += f"Rate: {rate:.0f} SNPs/sec - ETA: {eta:.0f}s"
                            
                            print(status)
                            if progress_callback:
                                progress_callback(status)
                                
                    except Exception as e:
                        print(f"Error processing batch {batch_idx}: {e}")
                        
        except Exception as e:
            print(f"Error in parallel processing: {e}")
            return self.results
            
        # Sort by magnitude (highest first)
        self.results.sort(key=lambda x: x.magnitude if x.magnitude else 0, reverse=True)
        
        total_time = time.time() - start_time
        rate = total_snps / total_time if total_time > 0 else 0
        
        print(f"\nParallel analysis complete!")
        print(f"  Total time: {total_time:.2f} seconds")
        print(f"  Processing rate: {rate:.0f} SNPs/second")
        print(f"  Results found: {len(self.results):,}")
        print(f"  Speedup estimate: ~{self.num_processes}x faster than sequential")
        
        return self.results
        
    def get_significant_snps(self, min_magnitude: float = 2.0) -> List[AnalysisResult]:
        """Get SNPs with significant magnitude"""
        return [r for r in self.results if r.magnitude and r.magnitude >= min_magnitude]
        
    def get_medical_snps(self) -> List[AnalysisResult]:
        """Get SNPs with medical relevance (have 'repute' field)"""
        return [r for r in self.results if r.repute]
        
    def search_by_keyword(self, keyword: str) -> List[AnalysisResult]:
        """Search results by keyword in summary or interpretation"""
        keyword = keyword.lower()
        return [
            r for r in self.results
            if (r.summary and keyword in r.summary.lower()) or
               (r.interpretation and keyword in r.interpretation.lower())
        ]
        
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
                # Header
                f.write("RSID\tGenotype\tChromosome\tPosition\tMagnitude\tRepute\tSummary\tInterpretation\tReferences\n")
                # Data
                for r in self.results:
                    refs = ';'.join(r.references) if r.references else ''
                    f.write(f"{r.rsid}\t{r.user_genotype}\t{r.chromosome}\t{r.position}\t")
                    f.write(f"{r.magnitude or ''}\t{r.repute or ''}\t{r.summary or ''}\t")
                    f.write(f"{r.interpretation or ''}\t{refs}\n")
                    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics of the analysis"""
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
    """Example usage and testing"""
    print("=" * 60)
    print("Parallel Offline Genome Analyzer")
    print("=" * 60)
    
    # Show CPU info
    cpu_count = mp.cpu_count()
    print(f"Detected {cpu_count} CPU cores")
    
    # Initialize parallel analyzer
    analyzer = ParallelGenomeAnalyzer()
    
    # Look for genome file
    genome_files = [
        "C:/Users/i_am_/Desktop/41240811505150.txt",
        "../genome_John_Doe_v5_Full_20240101010101.txt",
        "../genome.txt",
        "../23andme.txt",
        "sample_genome.txt"
    ]
    
    genome_file = None
    for file in genome_files:
        if os.path.exists(file):
            genome_file = file
            break
            
    if not genome_file:
        print("\nNo genome file found. Please provide a 23andMe format file.")
        print("Example usage:")
        print("  python parallel_analyzer.py your_genome_file.txt")
        return
        
    print(f"\nLoading genome file: {genome_file}")
    genome_stats = analyzer.load_genome(genome_file)
    
    print(f"\nStarting parallel analysis...")
    print("(This should be much faster than the sequential version!)")
    
    # Analyze with parallel processing
    # For testing, analyze first 10000 SNPs
    results = analyzer.analyze_all_parallel(
        magnitude_threshold=0.0, 
        limit=10000,  # Remove this for full analysis
        batch_size=500
    )
    
    print(f"\nAnalyzed {len(results)} SNPs")
    
    # Get summary statistics
    stats = analyzer.get_summary_stats()
    print("\nAnalysis Summary:")
    print(f"  Total analyzed: {stats['total_analyzed']}")
    print(f"  With SNPedia data: {stats['with_snpedia_data']}")
    print(f"  With magnitude: {stats['with_magnitude']}")
    print(f"  Significant (mag >= 2): {stats['significant']}")
    print(f"  Good repute: {stats['good_repute']}")
    print(f"  Bad repute: {stats['bad_repute']}")
    
    # Show top significant SNPs
    significant = analyzer.get_significant_snps(min_magnitude=2.0)
    if significant:
        print(f"\nTop Significant SNPs (magnitude >= 2.0):")
        for i, result in enumerate(significant[:10], 1):
            print(f"\n{i}. {result.rsid} ({result.user_genotype})")
            print(f"   Magnitude: {result.magnitude}")
            print(f"   Repute: {result.repute}")
            print(f"   Summary: {result.summary}")
            if result.interpretation:
                print(f"   Your genotype: {result.interpretation}")
                
    # Export results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"parallel_analysis_{timestamp}.json"
    analyzer.export_results(output_file, format='json')
    print(f"\nResults exported to: {output_file}")
    
    print(f"\nParallel analysis complete! Used {cpu_count} CPU cores for maximum speed.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Use command line argument as genome file
        genome_file = sys.argv[1]
        if os.path.exists(genome_file):
            analyzer = ParallelGenomeAnalyzer()
            print(f"Loading genome file: {genome_file}")
            genome_stats = analyzer.load_genome(genome_file)
            
            print(f"\nStarting full parallel analysis of {genome_stats['total_snps']:,} SNPs...")
            print("This will use all available CPU cores for maximum speed!")
            
            results = analyzer.analyze_all_parallel(magnitude_threshold=0.0)
            
            stats = analyzer.get_summary_stats()
            print(f"\nAnalyzed {stats['total_analyzed']} SNPs")
            print(f"Found {stats['significant']} significant SNPs (magnitude >= 2.0)")
            
            # Export results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"full_parallel_analysis_{timestamp}.json"
            analyzer.export_results(output_file, format='json')
            print(f"Results exported to: {output_file}")
            
        else:
            print(f"Error: File not found: {genome_file}")
    else:
        main()