from datetime import datetime
import os
from typing import List


def generate_html_report(analyzer, results: List, filename: str):
    """Generate a comprehensive HTML report of the genome analysis"""
    
    stats = analyzer.get_summary_stats()
    significant = analyzer.get_significant_snps(min_magnitude=2.0)
    medical = analyzer.get_medical_snps()
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Genome Analysis Report - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            display: block;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        
        .snp-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .snp-table th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        
        .snp-table td {{
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .snp-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .rsid {{
            font-family: 'Courier New', monospace;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .genotype {{
            font-family: 'Courier New', monospace;
            background: #e8f4fd;
            padding: 2px 6px;
            border-radius: 4px;
            color: #0066cc;
        }}
        
        .magnitude {{
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }}
        
        .mag-low {{ background: #d4edda; color: #155724; }}
        .mag-medium {{ background: #fff3cd; color: #856404; }}
        .mag-high {{ background: #f8d7da; color: #721c24; }}
        
        .repute-good {{ color: #28a745; font-weight: bold; }}
        .repute-bad {{ color: #dc3545; font-weight: bold; }}
        .repute-neutral {{ color: #6c757d; }}
        
        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
        
        .bar-chart {{
            display: flex;
            align-items: flex-end;
            height: 200px;
            gap: 10px;
            margin-top: 20px;
        }}
        
        .bar {{
            flex: 1;
            background: linear-gradient(to top, #667eea, #764ba2);
            border-radius: 5px 5px 0 0;
            position: relative;
            min-height: 20px;
            transition: opacity 0.3s ease;
        }}
        
        .bar:hover {{
            opacity: 0.8;
        }}
        
        .bar-label {{
            position: absolute;
            bottom: -25px;
            left: 0;
            right: 0;
            text-align: center;
            font-size: 0.9em;
            color: #666;
        }}
        
        .bar-value {{
            position: absolute;
            top: -25px;
            left: 0;
            right: 0;
            text-align: center;
            font-weight: bold;
            color: #667eea;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }}
        
        .footer p {{
            margin-bottom: 10px;
        }}
        
        .no-data {{
            text-align: center;
            padding: 40px;
            color: #999;
            font-style: italic;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
                border-radius: 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧬 Genome Analysis Report</h1>
            <div class="subtitle">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>
            <div class="subtitle">Powered by Offline SNPedia 2025 Database</div>
        </div>
        
        <div class="content">
            <!-- Summary Statistics -->
            <div class="section">
                <h2 class="section-title">📊 Analysis Summary</h2>
                <div class="summary-grid">
                    <div class="stat-card">
                        <span class="stat-number">{stats['total_analyzed']:,}</span>
                        <span class="stat-label">Total SNPs Analyzed</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number">{stats['with_snpedia_data']:,}</span>
                        <span class="stat-label">With SNPedia Data</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number">{stats['significant']:,}</span>
                        <span class="stat-label">Significant SNPs</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number">{stats['good_repute']:,}</span>
                        <span class="stat-label">Good Repute</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number">{stats['bad_repute']:,}</span>
                        <span class="stat-label">Bad Repute</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number">{stats['with_interpretation']:,}</span>
                        <span class="stat-label">With Interpretation</span>
                    </div>
                </div>
            </div>
            
            <!-- Magnitude Distribution -->
            <div class="section">
                <h2 class="section-title">📈 Magnitude Distribution</h2>
                <div class="chart-container">
                    <div class="bar-chart">
"""
    
    # Add magnitude distribution bars
    max_count = max(stats['magnitude_distribution'].values()) if stats['magnitude_distribution'] else 1
    for range_key, count in stats['magnitude_distribution'].items():
        height_percent = (count / max_count * 100) if max_count > 0 else 0
        html_content += f"""
                        <div class="bar" style="height: {height_percent}%;">
                            <span class="bar-value">{count}</span>
                            <span class="bar-label">{range_key}</span>
                        </div>
"""
    
    html_content += """
                    </div>
                </div>
            </div>
            
            <!-- Significant SNPs -->
            <div class="section">
                <h2 class="section-title">⚠️ Significant SNPs (Magnitude ≥ 2.0)</h2>
"""
    
    if significant:
        html_content += """
                <table class="snp-table">
                    <thead>
                        <tr>
                            <th>RSID</th>
                            <th>Genotype</th>
                            <th>Magnitude</th>
                            <th>Repute</th>
                            <th>Summary</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        for snp in significant[:50]:  # Limit to top 50
            mag_class = 'mag-low' if snp.magnitude < 2 else 'mag-medium' if snp.magnitude < 3 else 'mag-high'
            repute_class = 'repute-good' if snp.repute and 'good' in snp.repute.lower() else 'repute-bad' if snp.repute and 'bad' in snp.repute.lower() else 'repute-neutral'
            
            html_content += f"""
                        <tr>
                            <td><span class="rsid">{snp.rsid}</span></td>
                            <td><span class="genotype">{snp.user_genotype}</span></td>
                            <td><span class="magnitude {mag_class}">{snp.magnitude:.1f}</span></td>
                            <td><span class="{repute_class}">{snp.repute or '-'}</span></td>
                            <td>{snp.summary or snp.interpretation or '-'}</td>
                        </tr>
"""
        html_content += """
                    </tbody>
                </table>
"""
    else:
        html_content += '<div class="no-data">No significant SNPs found with magnitude ≥ 2.0</div>'
    
    html_content += """
            </div>
            
            <!-- Medical SNPs -->
            <div class="section">
                <h2 class="section-title">🏥 Medical SNPs</h2>
"""
    
    if medical:
        html_content += """
                <table class="snp-table">
                    <thead>
                        <tr>
                            <th>RSID</th>
                            <th>Genotype</th>
                            <th>Repute</th>
                            <th>Summary</th>
                            <th>Your Interpretation</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        for snp in medical[:50]:  # Limit to top 50
            repute_class = 'repute-good' if snp.repute and 'good' in snp.repute.lower() else 'repute-bad' if snp.repute and 'bad' in snp.repute.lower() else 'repute-neutral'
            
            html_content += f"""
                        <tr>
                            <td><span class="rsid">{snp.rsid}</span></td>
                            <td><span class="genotype">{snp.user_genotype}</span></td>
                            <td><span class="{repute_class}">{snp.repute or '-'}</span></td>
                            <td>{snp.summary or '-'}</td>
                            <td>{snp.interpretation or '-'}</td>
                        </tr>
"""
        html_content += """
                    </tbody>
                </table>
"""
    else:
        html_content += '<div class="no-data">No medical SNPs with reputation data found</div>'
    
    html_content += """
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Disclaimer:</strong> This report is for educational and research purposes only.</p>
            <p>It should not be used for medical diagnosis or treatment decisions.</p>
            <p>Please consult with qualified healthcare professionals for medical interpretation.</p>
            <hr style="margin: 20px 0; border: none; border-top: 1px solid #e0e0e0;">
            <p>Generated by Offline Genome Analyzer</p>
            <p>SNPedia data from July 2025 snapshot (CC-BY-NC-SA 3.0)</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Write the HTML file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    return filename