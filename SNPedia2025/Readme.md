# SNPedia Complete Database Mirror
*A comprehensive collection of genetic variant information from SNPedia*

## Overview
This database contains a complete mirror of SNPedia's genetic variant entries, totaling 111,727 SNPs (Single Nucleotide Polymorphisms) and related genetic variants. SNPedia is a wiki-based bioinformatics resource that catalogs the functional consequences of human genetic variation, serving as a valuable reference for personal genomics, medical genetics, and genetic genealogy.

## Database Contents
- **Total Entries**: 111,727
  - Rs SNPs (Reference SNP cluster IDs): 108,873 (97.4%)
  - I-SNPs (23andMe internal identifiers): 2,851 (2.6%)  
  - Other variants: 3 (0.0%)
    - MYH6 c.2161 / MYH6_c.2161 (gene mutation, duplicate entries)
    - OMIM604611.0004 (OMIM database reference)

## Source & Attribution
**All content in this database is from SNPedia (www.snpedia.com)**

SNPedia is owned and operated by MyHeritage (acquired September 2019). The original wiki was created by geneticist Greg Lennon and programmer Mike Cariaso.

## License
**This database is distributed under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License**

License URL: https://creativecommons.org/licenses/by-nc-sa/3.0/

This means:
- ✅ **Attribution** — You must give appropriate credit to SNPedia
- ❌ **NonCommercial** — You may NOT use this for commercial purposes  
- 🔄 **ShareAlike** — If you remix, transform, or build upon this material, you must distribute your contributions under the same license

## Important Legal Notice
By using this database, you agree to:
1. Provide attribution to SNPedia in any use or derivative work
2. Use this data for personal, educational, or non-commercial research only
3. Share any modifications or derivatives under the same CC-BY-NC-SA 3.0 license
4. Review and comply with SNPedia's Terms of Use: https://www.snpedia.com/index.php/Terms_of_Use

## Collection Method
This database was created using a custom Python scraper that:
- Respected SNPedia's robots.txt with 3-second delays between requests
- Used the official MediaWiki API endpoint (https://bots.snpedia.com/api.php)
- Retrieved all pages from Category:Is_a_snp
- Preserved original wiki markup content
- Included automatic resume capability and error logging

**Scraping Period**: July 12-17, 2025  
**Scraper Source**: https://github.com/jaykobdetar/SNPedia-Scraper

## Database Schema
```sql
CREATE TABLE snps (
    rsid TEXT PRIMARY KEY,      -- SNP identifier (e.g., Rs7412, I3000001)
    content TEXT,               -- Original wiki markup content from SNPedia
    scraped_at TIMESTAMP,       -- When this entry was retrieved
    attribution TEXT            -- License and source attribution
);
```

Each entry includes full attribution in the format:
`Source: SNPedia (www.snpedia.com) | License: CC-BY-NC-SA 3.0 (https://creativecommons.org/licenses/by-nc-sa/3.0/) | Original: https://www.snpedia.com/index.php/[rsid]`

## Intended Use
This database is intended for:
- Personal genomics analysis (similar to Promethease)
- Academic and educational research
- Non-commercial genetic genealogy
- Open-source bioinformatics tool development

## Accessing Original Pages
To view the original SNPedia page for any entry:
- Visit: `https://www.snpedia.com/index.php/[rsid]`
- Example: https://www.snpedia.com/index.php/Rs53576

## Updates & Currency
This is a static snapshot from July 2025. SNPedia is actively maintained and updated. For the most current information, please visit the original SNPedia website.

## Technical Notes
- Character encoding: UTF-8
- Some entries contain special characters in wiki markup
- Content includes MediaWiki templates and formatting
- Average content size: 984 characters per entry
- Content size range: 27 to 57,167 characters


## Disclaimer
This database is provided "as is" for research and educational purposes. Neither the distributor nor SNPedia provides medical advice. Genetic information should be interpreted by qualified healthcare professionals.

## Contact
- **SNPedia**: info@snpedia.com
- **This Mirror**: simyc4982@gmail.com
- **Scraper Issues**: https://github.com/jaykobdetar/SNPedia-Scraper/issues

---
*Remember: Knowledge about genetic variants is constantly evolving. Always verify important findings with current sources and consult healthcare professionals for medical interpretation.*
