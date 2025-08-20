import os
import json
import multiprocessing as mp
from typing import Dict, List, Optional, Callable
from dataclasses import asdict
from datetime import datetime
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import math

from snpedia_reader import SNPediaReader
from genome_reader import GenomeReader
from offline_analyzer import AnalysisResult


def worker_process(args):
    """Simple worker that processes a chunk of RSIDs"""
    db_path, rsid_chunk, genome_data_chunk = args
    
    results = []
    
    try:
        # Each worker gets its own database connection
        with SNPediaReader(db_path) as snpedia_reader:
            for rsid in rsid_chunk:
                if rsid not in genome_data_chunk:
                    continue
                    
                genome_snp = genome_data_chunk[rsid]
                snp_info = snpedia_reader.get_snp_info(rsid)
                
                if not snp_info:
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
                else:
                    # Find interpretation
                    interpretation = None
                    if genome_snp.genotype in snp_info.genotypes:
                        interpretation = snp_info.genotypes[genome_snp.genotype]
                    elif genome_snp.genotype[::-1] in snp_info.genotypes:
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
        print(f"Worker error: {e}")
        return []
        
    return results


class SimpleParallelAnalyzer:
    """Clean, simple parallel analyzer"""
    
    def __init__(self, db_path: str = "../SNPedia2025/SNPedia2025.db", num_processes: Optional[int] = None):
        self.db_path = db_path
        self.num_processes = num_processes or mp.cpu_count()
        self.genome_reader = GenomeReader()
        self.results: List[AnalysisResult] = []
        
        print(f"Simple parallel analyzer with {self.num_processes} processes")
        
    def load_genome(self, filepath: str) -> Dict:
        """Load genome file"""
        print(f"Loading: {filepath}")
        start_time = time.time()
        self.genome_reader.read_23andme_file(filepath)
        stats = self.genome_reader.get_stats()
        load_time = time.time() - start_time
        print(f"Loaded {stats['total_snps']:,} SNPs in {load_time:.2f}s")
        return stats
        
    def analyze_parallel(self, magnitude_threshold: float = 0.0, 
                        limit: Optional[int] = None,
                        progress_callback: Optional[Callable] = None) -> List[AnalysisResult]:
        """Simple parallel analysis"""
        self.results.clear()
        
        # Get RSIDs to process
        all_rsids = list(self.genome_reader.genome_data.keys())
        if limit:
            all_rsids = all_rsids[:limit]
            
        total_snps = len(all_rsids)
        print(f"Analyzing {total_snps:,} SNPs with {self.num_processes} workers")
        
        # Split work evenly among processes
        chunk_size = math.ceil(total_snps / self.num_processes)
        chunks = []
        
        for i in range(0, total_snps, chunk_size):
            chunk_rsids = all_rsids[i:i + chunk_size]
            chunk_genome_data = {
                rsid: self.genome_reader.genome_data[rsid] 
                for rsid in chunk_rsids 
                if rsid in self.genome_reader.genome_data
            }
            chunks.append((self.db_path, chunk_rsids, chunk_genome_data))
            
        print(f"Created {len(chunks)} chunks of ~{chunk_size:,} SNPs each")
        
        # Process in parallel
        start_time = time.time()
        completed_chunks = 0
        
        with ProcessPoolExecutor(max_workers=self.num_processes) as executor:
            # Submit all chunks
            future_to_chunk = {executor.submit(worker_process, chunk): i for i, chunk in enumerate(chunks)}
            
            # Collect results
            for future in as_completed(future_to_chunk):
                chunk_idx = future_to_chunk[future]
                try:
                    chunk_results = future.result()
                    
                    # Apply magnitude filter
                    filtered_results = [
                        r for r in chunk_results 
                        if r.magnitude is None or r.magnitude >= magnitude_threshold
                    ]
                    
                    self.results.extend(filtered_results)
                    completed_chunks += 1
                    
                    # Progress
                    progress = (completed_chunks / len(chunks)) * 100
                    elapsed = time.time() - start_time
                    rate = len(self.results) / elapsed if elapsed > 0 else 0
                    
                    status = f"Chunk {completed_chunks}/{len(chunks)} ({progress:.1f}%) | Rate: {rate:.0f} SNPs/sec | Results: {len(self.results):,}"
                    print(status)
                    
                    if progress_callback:
                        progress_callback(status)
                        
                except Exception as e:
                    print(f"Error in chunk {chunk_idx}: {e}")
        
        # Sort by magnitude
        self.results.sort(key=lambda x: x.magnitude if x.magnitude else 0, reverse=True)
        
        total_time = time.time() - start_time
        rate = total_snps / total_time if total_time > 0 else 0
        
        print(f"\nCompleted in {total_time:.2f}s at {rate:.0f} SNPs/sec")
        print(f"Found {len(self.results):,} results")
        
        return self.results
        
    def get_significant_snps(self, min_magnitude: float = 2.0):
        return [r for r in self.results if r.magnitude and r.magnitude >= min_magnitude]
        
    def export_results(self, filepath: str, format: str = 'json'):
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
                    
    def get_summary_stats(self):
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
    """Test simple parallel analyzer"""
    print("Simple Parallel Analyzer Test")
    print("="*40)
    
    analyzer = SimpleParallelAnalyzer()
    
    genome_file = "C:/Users/i_am_/Desktop/41240811505150.txt"
    if os.path.exists(genome_file):
        genome_stats = analyzer.load_genome(genome_file)
        
        # Test with 10K SNPs
        print("\nTesting with 10,000 SNPs...")
        results = analyzer.analyze_parallel(limit=10000)
        
        stats = analyzer.get_summary_stats()
        print(f"Results: {len(results):,}")
        print(f"Significant: {stats['significant']}")
        
        # Export
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analyzer.export_results(f"simple_test_{timestamp}.json")
        
    else:
        print("Genome file not found")


if __name__ == "__main__":
    main()