# Offline Genome Analyzer

A completely offline genome analysis tool that uses the pre-downloaded SNPedia 2025 database to analyze personal genetic data without any internet connection required.

## Features

- **100% Offline**: All analysis is performed locally using the SNPedia2025.db database
- **Privacy-First**: Your genetic data never leaves your computer
- **23andMe Compatible**: Reads standard 23andMe genome files (.txt or .txt.gz)
- **Comprehensive Analysis**: Analyzes over 111,000 SNPs from SNPedia
- **Multiple Interfaces**: GUI, CLI, and programmatic API
- **Export Options**: JSON, TSV (Excel), and HTML reports

## Requirements

- Python 3.7+
- SQLite3 (included with Python)
- tkinter (for GUI, included with most Python installations)
- No external API calls or internet connection needed

## Installation

1. Ensure you have the SNPedia2025 database in the parent directory:
   ```
   OSGenome/
   ├── SNPedia2025/
   │   ├── SNPedia2025.db
   │   └── Readme.md
   └── OfflineGenomeAnalyzer/
       ├── snpedia_reader.py
       ├── genome_reader.py
       ├── offline_analyzer.py
       ├── gui_analyzer.py
       └── html_report_generator.py
   ```

2. No additional installation needed - all code uses Python standard library

## Usage

### GUI Mode (Recommended)

```bash
python gui_analyzer.py
```

1. Click "Browse..." to select your genome file
2. Adjust analysis options:
   - Minimum Magnitude: Filter results by significance (0 = show all)
   - Limit Results: Limit number of SNPs analyzed (0 = analyze all)
3. Click "Start Analysis"
4. Export results as JSON, TSV, or HTML report

### Command Line Mode

```bash
# Analyze with default settings
python offline_analyzer.py your_genome_file.txt

# Run example analysis (if no genome file provided)
python offline_analyzer.py
```

### Programmatic Usage

```python
from offline_analyzer import OfflineGenomeAnalyzer

# Initialize analyzer
analyzer = OfflineGenomeAnalyzer()

# Load genome file
genome_stats = analyzer.load_genome("your_genome_file.txt")
print(f"Loaded {genome_stats['total_snps']} SNPs")

# Analyze all SNPs
results = analyzer.analyze_all(magnitude_threshold=0.0)

# Get significant SNPs
significant = analyzer.get_significant_snps(min_magnitude=2.0)
for snp in significant[:10]:
    print(f"{snp.rsid}: {snp.user_genotype} - {snp.summary}")

# Export results
analyzer.export_results("results.json", format='json')
analyzer.export_results("results.tsv", format='tsv')

# Clean up
analyzer.close()
```

## Understanding Results

### Magnitude
- **0-1**: Common variations, usually harmless
- **1-2**: Interesting but not medically significant
- **2-3**: Worth noting, may have health implications
- **3-4**: Significant, discuss with healthcare provider
- **4+**: Highly significant, medical consultation recommended

### Repute
- **Good**: Generally beneficial or protective variant
- **Bad**: May increase risk for certain conditions
- **Neutral/None**: No clear positive or negative association

## Output Files

- **JSON**: Complete structured data for programmatic processing
- **TSV**: Tab-separated values for Excel/spreadsheet analysis
- **HTML**: Beautiful formatted report for viewing in browser

## Privacy & Security

- All processing happens locally on your computer
- No internet connection required after database download
- Your genetic data is never transmitted anywhere
- No tracking, analytics, or data collection

## Limitations

- Database snapshot from July 2025 (not real-time updated)
- Medical interpretations should be verified with healthcare professionals
- Some rare variants may not have SNPedia entries
- Research use only - not for clinical diagnosis

## License

The SNPedia data is licensed under CC-BY-NC-SA 3.0. This means:
- You must provide attribution to SNPedia
- Non-commercial use only
- Share-alike required for derivatives

## Comparison with Original OSGenome

| Feature | Original OSGenome | Offline Analyzer |
|---------|------------------|------------------|
| Internet Required | Yes (web scraping) | No (offline DB) |
| Speed | Slow (API calls) | Fast (local DB) |
| SNP Coverage | Limited by crawl | 111,727 SNPs |
| Privacy | Good | Excellent |
| Updates | Real-time | Static snapshot |

## Troubleshooting

1. **"Database not found"**: Ensure SNPedia2025.db is in ../SNPedia2025/
2. **GUI doesn't start**: Install tkinter: `pip install tk`
3. **Memory issues**: Use the limit parameter to process in batches
4. **No results**: Check your genome file format matches 23andMe standard

## Support

For issues or questions, please refer to the main OSGenome repository.