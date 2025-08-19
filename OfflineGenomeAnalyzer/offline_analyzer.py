import os
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import re

from snpedia_reader import SNPediaReader, SNPInfo
from genome_reader import GenomeReader, GenomeData


@dataclass
class AnalysisResult:
    """Result of analyzing a single SNP"""
    rsid: str
    user_genotype: str
    chromosome: str
    position: int
    magnitude: Optional[float]
    repute: Optional[str]
    summary: Optional[str]
    interpretation: Optional[str]
    references: List[str]
    
    def to_dict(self):
        return asdict(self)


class OfflineGenomeAnalyzer:
    """Main class for offline genome analysis using pre-downloaded SNPedia data"""
    
    def __init__(self, db_path: str = "../SNPedia2025/SNPedia2025.db"):
        self.snpedia_reader = SNPediaReader(db_path)
        self.genome_reader = GenomeReader()
        self.results: List[AnalysisResult] = []
        
    def load_genome(self, filepath: str) -> Dict:
        """Load a personal genome file"""
        self.genome_reader.read_23andme_file(filepath)
        return self.genome_reader.get_stats()
        
    def analyze_snp(self, rsid: str) -> Optional[AnalysisResult]:
        """Analyze a single SNP"""
        # Get user's genotype
        genome_snp = self.genome_reader.get_snp(rsid)
        if not genome_snp:
            return None
            
        # Get SNPedia information
        snp_info = self.snpedia_reader.get_snp_info(rsid)
        if not snp_info:
            # Even without SNPedia data, we can return basic info
            return AnalysisResult(
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
            
        # Find interpretation for user's genotype
        interpretation = None
        if genome_snp.genotype in snp_info.genotypes:
            interpretation = snp_info.genotypes[genome_snp.genotype]
        elif genome_snp.genotype[::-1] in snp_info.genotypes:  # Try reversed
            interpretation = snp_info.genotypes[genome_snp.genotype[::-1]]
            
        return AnalysisResult(
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
        
    def analyze_all(self, magnitude_threshold: float = 0.0, 
                   limit: Optional[int] = None) -> List[AnalysisResult]:
        """
        Analyze all SNPs in the loaded genome
        
        Args:
            magnitude_threshold: Only include SNPs with magnitude >= this value
            limit: Maximum number of SNPs to analyze (for testing)
        """
        self.results.clear()
        analyzed = 0
        
        for rsid in self.genome_reader.genome_data:
            if limit and analyzed >= limit:
                break
                
            result = self.analyze_snp(rsid)
            if result:
                # Apply magnitude filter
                if result.magnitude is None or result.magnitude >= magnitude_threshold:
                    self.results.append(result)
                    analyzed += 1
                    
                    # Progress indicator for large analyses
                    if analyzed % 1000 == 0:
                        print(f"  Analyzed {analyzed} SNPs...")
                        
        # Sort by magnitude (highest first)
        self.results.sort(key=lambda x: x.magnitude if x.magnitude else 0, reverse=True)
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
        
    def close(self):
        """Close database connections"""
        self.snpedia_reader.close()


def main():
    """Example usage and testing"""
    print("=" * 60)
    print("Offline Genome Analyzer")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = OfflineGenomeAnalyzer()
    
    # Look for example genome file
    genome_files = [
        "../genome_John_Doe_v5_Full_20240101010101.txt",
        "../genome.txt",
        "../23andme.txt",
        "../example_genome.txt"
    ]
    
    genome_file = None
    for file in genome_files:
        if os.path.exists(file):
            genome_file = file
            break
            
    if not genome_file:
        print("\nNo genome file found. Please provide a 23andMe format file.")
        print("Example usage:")
        print("  python offline_analyzer.py your_genome_file.txt")
        return
        
    print(f"\nLoading genome file: {genome_file}")
    genome_stats = analyzer.load_genome(genome_file)
    print(f"Loaded {genome_stats['total_snps']} SNPs")
    
    print("\nAnalyzing genome against SNPedia database...")
    print("(This may take a few minutes for full analysis)")
    
    # Analyze first 100 SNPs as example (remove limit for full analysis)
    results = analyzer.analyze_all(magnitude_threshold=0.0, limit=100)
    
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
    output_file = "analysis_results.json"
    analyzer.export_results(output_file, format='json')
    print(f"\nResults exported to: {output_file}")
    
    # Export TSV for Excel
    tsv_file = "analysis_results.tsv"
    analyzer.export_results(tsv_file, format='tsv')
    print(f"TSV file exported to: {tsv_file} (can be opened in Excel)")
    
    analyzer.close()
    print("\nAnalysis complete!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Use command line argument as genome file
        genome_file = sys.argv[1]
        if os.path.exists(genome_file):
            analyzer = OfflineGenomeAnalyzer()
            print(f"Loading genome file: {genome_file}")
            genome_stats = analyzer.load_genome(genome_file)
            print(f"Loaded {genome_stats['total_snps']} SNPs")
            
            print("\nAnalyzing genome... (this may take several minutes)")
            results = analyzer.analyze_all(magnitude_threshold=0.0)
            
            stats = analyzer.get_summary_stats()
            print(f"\nAnalyzed {stats['total_analyzed']} SNPs")
            print(f"Found {stats['significant']} significant SNPs (magnitude >= 2.0)")
            
            # Export results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"analysis_{timestamp}.json"
            analyzer.export_results(output_file, format='json')
            print(f"Results exported to: {output_file}")
            
            analyzer.close()
        else:
            print(f"Error: File not found: {genome_file}")
    else:
        main()