# Offline Genome Analyzer

A completely offline genome analysis tool that uses the pre-downloaded SNPedia 2025 database to analyze personal genetic data without any internet connection required.

## Features

- **🔥 High-Performance Parallel Processing**: Uses ALL CPU cores for maximum speed
- **100% Offline**: All analysis is performed locally using the SNPedia2025.db database
- **Privacy-First**: Your genetic data never leaves your computer
- **23andMe Compatible**: Reads standard 23andMe genome files (.txt or .txt.gz)
- **Comprehensive Analysis**: Analyzes over 111,000 SNPs from SNPedia
- **Multiple Speed Options**: Single-core, multi-core, and maximum performance modes
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

### 🔥 High-Performance GUI (Recommended)

**Maximum Speed - Uses ALL CPU Cores:**
```bash
python final_gui.py
```

1. Click "Browse..." to select your genome file
2. Choose analysis mode:
   - **🔥 Test (10K SNPs)** - Quick test (recommended first run)
   - **⚡ Medium (100K SNPs)** - Moderate analysis
   - **🚀 Full Analysis (All 22M+ SNPs)** - Complete genome analysis
3. Click "🔥 START ANALYSIS" 
4. ⚠️ **Warning**: Full analysis will use ALL CPU cores and heat up your computer!

**Simple Parallel Processing:**
```bash
python parallel_gui_analyzer.py
```

**Single-Core (Original):**
```bash
python gui_analyzer.py
```

### Command Line Modes

**High-Performance Parallel:**
```bash
python simple_parallel_analyzer.py "C:\path\to\your\genome_file.txt"
```

**Original Single-Core:**
```bash
python offline_analyzer.py "C:\path\to\your\genome_file.txt"
```

### Programmatic Usage

**High-Performance Parallel:**
```python
from simple_parallel_analyzer import SimpleParallelAnalyzer

# Initialize high-performance analyzer (uses all CPU cores)
analyzer = SimpleParallelAnalyzer()

# Load genome file
genome_stats = analyzer.load_genome("your_genome_file.txt")
print(f"Loaded {genome_stats['total_snps']} SNPs")

# Analyze with parallel processing
results = analyzer.analyze_parallel(magnitude_threshold=0.0)

# Get significant SNPs
significant = analyzer.get_significant_snps(min_magnitude=2.0)
for snp in significant[:10]:
    print(f"{snp.rsid}: {snp.user_genotype} - {snp.summary}")

# Export results
analyzer.export_results("results.json", format='json')
analyzer.export_results("results.tsv", format='tsv')
```

**Original Single-Core:**
```python
from offline_analyzer import OfflineGenomeAnalyzer

# Initialize single-core analyzer
analyzer = OfflineGenomeAnalyzer()

# Load and analyze (slower but uses less CPU)
genome_stats = analyzer.load_genome("your_genome_file.txt")
results = analyzer.analyze_all(magnitude_threshold=0.0)

# Export and cleanup
analyzer.export_results("results.json", format='json')
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

## Performance Comparison

| Version | Speed | CPU Usage | Best For |
|---------|-------|-----------|----------|
| **🔥 final_gui.py** | **Fastest** | **ALL cores (will heat laptop!)** | **Large genomes, max speed** |
| parallel_gui_analyzer.py | Very Fast | Multi-core | Balanced performance |
| gui_analyzer.py | Moderate | Single-core | Light usage, older computers |
| simple_parallel_analyzer.py | **Fastest CLI** | **ALL cores** | **Command line power users** |
| offline_analyzer.py | Moderate | Single-core | Basic analysis |

### Speed Estimates (22.4M SNP genome):
- **🔥 High-Performance**: ~10-30 minutes (ALL CPU cores)
- Parallel: ~45-90 minutes (multi-core)
- Single-core: ~4-8 hours (one core)

## Comparison with Original OSGenome

| Feature | Original OSGenome | New Offline Analyzer |
|---------|------------------|------------------|
| Internet Required | Yes (web scraping) | No (offline DB) |
| Speed | Slow (API calls) | **🔥 Fast (parallel local DB)** |
| SNP Coverage | Limited by crawl | 111,727 SNPs |
| Privacy | Good | Excellent |
| CPU Usage | Low | **🔥 Configurable (1 to ALL cores)** |
| Updates | Real-time | Static snapshot |

## Troubleshooting

1. **"Database not found"**: Ensure SNPedia2025.db is in ../SNPedia2025/
2. **GUI doesn't start**: Install tkinter: `pip install tk`
3. **🔥 Laptop overheating**: This is normal with high-performance mode! Use Test mode first, ensure good ventilation
4. **CPU cores not all used**: Try smaller batch sizes or use final_gui.py instead
5. **Memory issues**: Use the limit parameter to process in batches, or reduce number of CPU cores
6. **No results**: Check your genome file format matches 23andMe standard
7. **Analysis too slow**: Use final_gui.py or simple_parallel_analyzer.py for maximum speed

### Performance Tips

- **Start with Test mode** (10K SNPs) to verify everything works
- **Monitor CPU temperature** during full analysis
- **Use all available RAM** - close other applications during analysis
- **For maximum speed**: Use final_gui.py with all CPU cores enabled

## Support

For issues or questions, please refer to the main OSGenome repository.