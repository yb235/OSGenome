import sqlite3
import os
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class SNPInfo:
    """Data class for SNP information"""
    rsid: str
    genotypes: Dict[str, str]
    magnitude: Optional[float]
    summary: Optional[str]
    repute: Optional[str]
    references: List[str]
    raw_content: str


class SNPediaReader:
    """Reads SNP information from the offline SNPedia2025 database"""
    
    def __init__(self, db_path: str = "../SNPedia2025/SNPedia2025.db"):
        """Initialize the SNPedia reader with database path"""
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            
    def get_snp_raw(self, rsid: str) -> Optional[str]:
        """Get raw wiki content for a specific SNP"""
        rsid = rsid.upper()
        if not rsid.startswith('RS') and not rsid.startswith('I'):
            rsid = 'RS' + rsid
            
        self.cursor.execute("SELECT content FROM snps WHERE UPPER(rsid) = ?", (rsid,))
        result = self.cursor.fetchone()
        return result[0] if result else None
        
    def parse_snp_content(self, content: str) -> Dict:
        """Parse wiki markup content to extract relevant information"""
        info = {
            'genotypes': {},
            'magnitude': None,
            'summary': None,
            'repute': None,
            'references': []
        }
        
        # Extract genotype information (e.g., {{Rsnum|Rs53576|A|A}})
        genotype_pattern = r'\{\{Rsnum\|([^|]+)\|([^|]+)\|([^|}]+)(?:\|([^}]+))?\}\}'
        genotype_matches = re.findall(genotype_pattern, content)
        for match in genotype_matches:
            if len(match) >= 3:
                genotype = match[1] + match[2]
                info['genotypes'][genotype] = match[3] if len(match) > 3 else ''
        
        # Extract magnitude
        magnitude_pattern = r'[Mm]agnitude\s*=\s*([\d.]+)'
        magnitude_match = re.search(magnitude_pattern, content)
        if magnitude_match:
            try:
                info['magnitude'] = float(magnitude_match.group(1))
            except ValueError:
                pass
                
        # Extract repute
        repute_pattern = r'[Rr]epute\s*=\s*([^|\n]+)'
        repute_match = re.search(repute_pattern, content)
        if repute_match:
            info['repute'] = repute_match.group(1).strip()
            
        # Extract summary
        summary_pattern = r'[Ss]ummary\s*=\s*([^|\n]+)'
        summary_match = re.search(summary_pattern, content)
        if summary_match:
            info['summary'] = summary_match.group(1).strip()
            
        # Extract PMID references
        pmid_pattern = r'PMID[:\s]*(\d+)'
        info['references'] = re.findall(pmid_pattern, content)
        
        return info
        
    def get_snp_info(self, rsid: str) -> Optional[SNPInfo]:
        """Get parsed SNP information"""
        raw_content = self.get_snp_raw(rsid)
        if not raw_content:
            return None
            
        parsed = self.parse_snp_content(raw_content)
        return SNPInfo(
            rsid=rsid.upper(),
            genotypes=parsed['genotypes'],
            magnitude=parsed['magnitude'],
            summary=parsed['summary'],
            repute=parsed['repute'],
            references=parsed['references'],
            raw_content=raw_content
        )
        
    def search_snps(self, pattern: str, limit: int = 100) -> List[str]:
        """Search for SNPs matching a pattern"""
        query = "SELECT rsid FROM snps WHERE rsid LIKE ? LIMIT ?"
        self.cursor.execute(query, (f"%{pattern}%", limit))
        return [row[0] for row in self.cursor.fetchall()]
        
    def get_all_rsids(self) -> List[str]:
        """Get all RSIDs in the database"""
        self.cursor.execute("SELECT rsid FROM snps")
        return [row[0] for row in self.cursor.fetchall()]
        
    def get_stats(self) -> Dict:
        """Get database statistics"""
        stats = {}
        
        # Total count
        self.cursor.execute("SELECT COUNT(*) FROM snps")
        stats['total_snps'] = self.cursor.fetchone()[0]
        
        # RS vs I SNPs
        self.cursor.execute("SELECT COUNT(*) FROM snps WHERE rsid LIKE 'RS%'")
        stats['rs_snps'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM snps WHERE rsid LIKE 'I%'")
        stats['i_snps'] = self.cursor.fetchone()[0]
        
        stats['other_snps'] = stats['total_snps'] - stats['rs_snps'] - stats['i_snps']
        
        return stats


if __name__ == "__main__":
    # Example usage
    with SNPediaReader() as reader:
        # Get database stats
        stats = reader.get_stats()
        print(f"Database contains {stats['total_snps']} SNPs")
        print(f"  RS SNPs: {stats['rs_snps']}")
        print(f"  I SNPs: {stats['i_snps']}")
        print(f"  Other: {stats['other_snps']}")
        
        # Example: Get information about a specific SNP
        test_rsid = "Rs53576"
        snp_info = reader.get_snp_info(test_rsid)
        if snp_info:
            print(f"\nInformation for {test_rsid}:")
            print(f"  Magnitude: {snp_info.magnitude}")
            print(f"  Repute: {snp_info.repute}")
            print(f"  Summary: {snp_info.summary}")
            print(f"  Genotypes found: {list(snp_info.genotypes.keys())}")