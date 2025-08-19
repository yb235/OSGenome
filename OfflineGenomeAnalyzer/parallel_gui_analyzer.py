import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import json
import multiprocessing as mp
from datetime import datetime

from parallel_analyzer import ParallelGenomeAnalyzer


class ParallelGenomeAnalyzerGUI:
    """GUI for Parallel Offline Genome Analyzer - Much Faster!"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Parallel Offline Genome Analyzer - SNPedia 2025 (FAST!)")
        self.root.geometry("1000x800")
        
        self.analyzer = None
        self.genome_file = None
        self.results = []
        self.cpu_count = mp.cpu_count()
        
        self.setup_ui()
        self.load_last_session()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title with CPU info
        title = ttk.Label(main_frame, text=f"Parallel Offline Genome Analyzer ({self.cpu_count} CPU Cores)", 
                         font=('Arial', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Performance info
        perf_info = ttk.Label(main_frame, 
                             text=f"🚀 Uses all {self.cpu_count} CPU cores for maximum speed! Expected speedup: ~{self.cpu_count}x",
                             font=('Arial', 10), foreground='green')
        perf_info.grid(row=1, column=0, columnspan=3, pady=5)
        
        # File selection section
        ttk.Label(main_frame, text="Genome File:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.file_label = ttk.Label(main_frame, text="No file selected", 
                                   relief=tk.SUNKEN, anchor=tk.W)
        self.file_label.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Browse...", 
                  command=self.select_file).grid(row=2, column=2, padx=5)
        
        # Analysis options
        options_frame = ttk.LabelFrame(main_frame, text="Analysis Options", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(options_frame, text="Minimum Magnitude:").grid(row=0, column=0, sticky=tk.W)
        self.magnitude_var = tk.DoubleVar(value=0.0)
        magnitude_spin = ttk.Spinbox(options_frame, from_=0, to=10, increment=0.5,
                                    textvariable=self.magnitude_var, width=10)
        magnitude_spin.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(options_frame, text="Limit Results:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.limit_var = tk.IntVar(value=0)
        limit_spin = ttk.Spinbox(options_frame, from_=0, to=10000000, increment=10000,
                                textvariable=self.limit_var, width=10)
        limit_spin.grid(row=0, column=3, sticky=tk.W, padx=5)
        ttk.Label(options_frame, text="(0 = analyze all)").grid(row=0, column=4, sticky=tk.W)
        
        # Parallel processing options
        ttk.Label(options_frame, text="CPU Cores:").grid(row=1, column=0, sticky=tk.W)
        self.cores_var = tk.IntVar(value=self.cpu_count)
        cores_spin = ttk.Spinbox(options_frame, from_=1, to=self.cpu_count,
                                textvariable=self.cores_var, width=10)
        cores_spin.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(options_frame, text="Batch Size:").grid(row=1, column=2, sticky=tk.W, padx=(20, 0))
        self.batch_var = tk.IntVar(value=1000)
        batch_spin = ttk.Spinbox(options_frame, from_=100, to=10000, increment=500,
                                textvariable=self.batch_var, width=10)
        batch_spin.grid(row=1, column=3, sticky=tk.W, padx=5)
        ttk.Label(options_frame, text="(SNPs per batch)").grid(row=1, column=4, sticky=tk.W)
        
        # Quick analysis presets
        presets_frame = ttk.LabelFrame(main_frame, text="Quick Analysis Presets", padding="10")
        presets_frame.grid(row=4, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Button(presets_frame, text="🔥 Fast Test (10K SNPs)", 
                  command=lambda: self.set_preset(10000, 2.0)).grid(row=0, column=0, padx=5)
        ttk.Button(presets_frame, text="⚡ Medium (100K SNPs)", 
                  command=lambda: self.set_preset(100000, 1.0)).grid(row=0, column=1, padx=5)
        ttk.Button(presets_frame, text="🚀 Full Analysis (All SNPs)", 
                  command=lambda: self.set_preset(0, 0.0)).grid(row=0, column=2, padx=5)
        ttk.Button(presets_frame, text="🎯 Significant Only", 
                  command=lambda: self.set_preset(0, 2.0)).grid(row=0, column=3, padx=5)
        
        # Analysis button
        self.analyze_btn = ttk.Button(main_frame, text="🚀 Start Parallel Analysis", 
                                     command=self.start_analysis, state=tk.DISABLED)
        self.analyze_btn.grid(row=5, column=0, columnspan=3, pady=10)
        
        # Progress section
        self.progress_label = ttk.Label(main_frame, text="")
        self.progress_label.grid(row=6, column=0, columnspan=3)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Performance metrics
        self.perf_label = ttk.Label(main_frame, text="", font=('Arial', 9), foreground='blue')
        self.perf_label.grid(row=8, column=0, columnspan=3)
        
        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="Analysis Results", padding="10")
        results_frame.grid(row=9, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(9, weight=1)
        
        # Results text area
        self.results_text = scrolledtext.ScrolledText(results_frame, height=15, width=80)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Export buttons
        export_frame = ttk.Frame(main_frame)
        export_frame.grid(row=10, column=0, columnspan=3, pady=10)
        
        self.export_json_btn = ttk.Button(export_frame, text="Export JSON", 
                                         command=lambda: self.export_results('json'),
                                         state=tk.DISABLED)
        self.export_json_btn.grid(row=0, column=0, padx=5)
        
        self.export_tsv_btn = ttk.Button(export_frame, text="Export TSV (Excel)", 
                                        command=lambda: self.export_results('tsv'),
                                        state=tk.DISABLED)
        self.export_tsv_btn.grid(row=0, column=1, padx=5)
        
        self.export_html_btn = ttk.Button(export_frame, text="Generate HTML Report", 
                                         command=self.generate_html_report,
                                         state=tk.DISABLED)
        self.export_html_btn.grid(row=0, column=2, padx=5)
        
        # Status bar
        self.status_label = ttk.Label(main_frame, text=f"Ready - {self.cpu_count} CPU cores available", 
                                     relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=11, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
    def set_preset(self, limit, magnitude):
        """Set quick analysis presets"""
        self.limit_var.set(limit)
        self.magnitude_var.set(magnitude)
        
    def select_file(self):
        """Select genome file"""
        filename = filedialog.askopenfilename(
            title="Select Genome File",
            filetypes=[
                ("Text files", "*.txt"),
                ("Compressed files", "*.gz"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            self.genome_file = filename
            self.file_label.config(text=os.path.basename(filename))
            self.analyze_btn.config(text=f"🚀 Start Parallel Analysis ({self.cores_var.get()} cores)")
            self.analyze_btn.config(state=tk.NORMAL)
            self.save_session()
            self.status_label.config(text=f"File selected: {os.path.basename(filename)}")
            
    def start_analysis(self):
        """Start the analysis in a separate thread"""
        if not self.genome_file:
            messagebox.showerror("Error", "Please select a genome file first")
            return
            
        # Disable buttons during analysis
        self.analyze_btn.config(state=tk.DISABLED)
        self.export_json_btn.config(state=tk.DISABLED)
        self.export_tsv_btn.config(state=tk.DISABLED)
        self.export_html_btn.config(state=tk.DISABLED)
        
        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        self.progress_bar.config(value=0)
        
        # Start progress bar
        self.progress_label.config(text="Initializing parallel analysis...")
        
        # Run analysis in separate thread
        thread = threading.Thread(target=self.run_analysis)
        thread.daemon = True
        thread.start()
        
    def run_analysis(self):
        """Run the actual parallel analysis"""
        try:
            # Initialize parallel analyzer
            num_processes = self.cores_var.get()
            self.analyzer = ParallelGenomeAnalyzer(num_processes=num_processes)
            
            # Load genome
            self.root.after(0, self.update_progress, "Loading genome file...", 0)
            genome_stats = self.analyzer.load_genome(self.genome_file)
            
            total_snps = genome_stats['total_snps']
            limit = self.limit_var.get() if self.limit_var.get() > 0 else None
            analyze_count = limit if limit else total_snps
            
            self.root.after(0, self.update_progress, 
                          f"Loaded {total_snps:,} SNPs. Starting parallel analysis of {analyze_count:,} SNPs...", 10)
            
            # Progress callback function
            def progress_callback(status):
                # Extract progress percentage from status if possible
                try:
                    if "%" in status:
                        percent_str = status.split("(")[1].split("%")[0]
                        percent = float(percent_str)
                        self.root.after(0, self.update_progress, status, 10 + (percent * 0.8))
                    else:
                        self.root.after(0, self.update_progress, status, None)
                except:
                    self.root.after(0, self.update_progress, status, None)
            
            # Run parallel analysis
            magnitude = self.magnitude_var.get()
            batch_size = self.batch_var.get()
            
            self.results = self.analyzer.analyze_all_parallel(
                magnitude_threshold=magnitude,
                limit=limit,
                batch_size=batch_size,
                progress_callback=progress_callback
            )
            
            # Get statistics
            stats = self.analyzer.get_summary_stats()
            
            # Update UI with results
            self.root.after(0, self.display_results, stats)
            
        except Exception as e:
            self.root.after(0, self.show_error, str(e))
        finally:
            self.root.after(0, self.analysis_complete)
            
    def update_progress(self, message, percent=None):
        """Update progress label and bar"""
        self.progress_label.config(text=message)
        if percent is not None:
            self.progress_bar.config(value=percent)
        self.status_label.config(text=message)
        
        # Extract performance metrics if available
        if "Rate:" in message and "SNPs/sec" in message:
            self.perf_label.config(text=message.split("Rate:")[1].split("-")[0].strip())
        
    def display_results(self, stats):
        """Display analysis results"""
        self.results_text.delete(1.0, tk.END)
        
        # Performance summary
        self.results_text.insert(tk.END, "🚀 PARALLEL ANALYSIS COMPLETE\n", 'title')
        self.results_text.insert(tk.END, "=" * 60 + "\n\n")
        
        # Summary statistics
        self.results_text.insert(tk.END, "📊 ANALYSIS SUMMARY\n", 'title')
        self.results_text.insert(tk.END, "=" * 40 + "\n\n")
        
        self.results_text.insert(tk.END, f"Total SNPs analyzed: {stats['total_analyzed']:,}\n")
        self.results_text.insert(tk.END, f"SNPs with SNPedia data: {stats['with_snpedia_data']:,}\n")
        self.results_text.insert(tk.END, f"SNPs with magnitude: {stats['with_magnitude']:,}\n")
        self.results_text.insert(tk.END, f"Significant SNPs (mag >= 2): {stats['significant']:,}\n")
        self.results_text.insert(tk.END, f"Good repute: {stats['good_repute']:,}\n")
        self.results_text.insert(tk.END, f"Bad repute: {stats['bad_repute']:,}\n")
        self.results_text.insert(tk.END, f"With interpretation: {stats['with_interpretation']:,}\n\n")
        
        # Magnitude distribution
        self.results_text.insert(tk.END, "📈 Magnitude Distribution:\n", 'subtitle')
        for range_key, count in stats['magnitude_distribution'].items():
            self.results_text.insert(tk.END, f"  {range_key}: {count:,}\n")
        
        # Top significant SNPs
        significant = self.analyzer.get_significant_snps(min_magnitude=2.0)
        if significant:
            self.results_text.insert(tk.END, "\n⚠️  TOP SIGNIFICANT SNPs (Magnitude >= 2.0)\n", 'title')
            self.results_text.insert(tk.END, "=" * 50 + "\n\n")
            
            for i, result in enumerate(significant[:20], 1):
                self.results_text.insert(tk.END, f"{i}. {result.rsid} ", 'rsid')
                self.results_text.insert(tk.END, f"({result.user_genotype})\n")
                
                if result.magnitude:
                    self.results_text.insert(tk.END, f"   🔥 Magnitude: {result.magnitude}\n")
                if result.repute:
                    color = 'good' if 'good' in result.repute.lower() else 'bad' if 'bad' in result.repute.lower() else None
                    self.results_text.insert(tk.END, f"   📋 Repute: ")
                    self.results_text.insert(tk.END, f"{result.repute}\n", color)
                if result.summary:
                    self.results_text.insert(tk.END, f"   📝 Summary: {result.summary}\n")
                if result.interpretation:
                    self.results_text.insert(tk.END, f"   🧬 Your genotype: {result.interpretation}\n")
                self.results_text.insert(tk.END, "\n")
                
        # Medical SNPs
        medical = self.analyzer.get_medical_snps()
        if medical:
            self.results_text.insert(tk.END, f"\n🏥 MEDICAL SNPs ({len(medical):,} found)\n", 'title')
            self.results_text.insert(tk.END, "=" * 30 + "\n\n")
            
            for i, result in enumerate(medical[:10], 1):
                self.results_text.insert(tk.END, f"{i}. {result.rsid} ", 'rsid')
                self.results_text.insert(tk.END, f"({result.user_genotype}) - ")
                color = 'good' if result.repute and 'good' in result.repute.lower() else 'bad' if result.repute and 'bad' in result.repute.lower() else None
                self.results_text.insert(tk.END, f"{result.repute}\n", color)
                if result.summary:
                    self.results_text.insert(tk.END, f"   {result.summary}\n")
                self.results_text.insert(tk.END, "\n")
                
        # Configure text tags for formatting
        self.results_text.tag_config('title', font=('Arial', 12, 'bold'))
        self.results_text.tag_config('subtitle', font=('Arial', 10, 'bold'))
        self.results_text.tag_config('rsid', font=('Courier', 10, 'bold'), foreground='blue')
        self.results_text.tag_config('good', foreground='green')
        self.results_text.tag_config('bad', foreground='red')
        
    def analysis_complete(self):
        """Called when analysis is complete"""
        self.progress_bar.config(value=100)
        self.progress_label.config(text="🎉 Parallel analysis complete!")
        self.analyze_btn.config(state=tk.NORMAL)
        self.export_json_btn.config(state=tk.NORMAL)
        self.export_tsv_btn.config(state=tk.NORMAL)
        self.export_html_btn.config(state=tk.NORMAL)
        self.status_label.config(text=f"✅ Analysis complete! {len(self.results):,} results found using {self.cores_var.get()} CPU cores")
        
    def show_error(self, error_message):
        """Show error message"""
        messagebox.showerror("Analysis Error", error_message)
        self.progress_bar.config(value=0)
        self.progress_label.config(text="❌ Error occurred")
        self.analyze_btn.config(state=tk.NORMAL)
        
    def export_results(self, format):
        """Export results to file"""
        if not self.results:
            messagebox.showwarning("No Results", "No analysis results to export")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == 'json':
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                initialname=f"parallel_analysis_{timestamp}.json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
        else:  # tsv
            filename = filedialog.asksaveasfilename(
                defaultextension=".tsv",
                initialname=f"parallel_analysis_{timestamp}.tsv",
                filetypes=[("Tab-separated files", "*.tsv"), ("All files", "*.*")]
            )
            
        if filename:
            try:
                self.analyzer.export_results(filename, format=format)
                messagebox.showinfo("Export Complete", f"Results exported to:\n{filename}")
                self.status_label.config(text=f"📁 Exported to {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))
                
    def generate_html_report(self):
        """Generate HTML report"""
        if not self.results:
            messagebox.showwarning("No Results", "No analysis results to generate report")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = filedialog.asksaveasfilename(
            defaultextension=".html",
            initialname=f"parallel_genome_report_{timestamp}.html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                from html_report_generator import generate_html_report
                generate_html_report(self.analyzer, self.results, filename)
                messagebox.showinfo("Report Generated", f"HTML report generated:\n{filename}")
                self.status_label.config(text=f"📄 Report generated: {os.path.basename(filename)}")
                
                # Ask if user wants to open the report
                if messagebox.askyesno("Open Report", "Do you want to open the report in your browser?"):
                    import webbrowser
                    webbrowser.open(f"file://{os.path.abspath(filename)}")
            except Exception as e:
                messagebox.showerror("Report Error", str(e))
                
    def save_session(self):
        """Save session data"""
        session_file = "session.json"
        session_data = {
            'last_genome_file': self.genome_file,
            'last_magnitude': self.magnitude_var.get(),
            'last_limit': self.limit_var.get(),
            'last_cores': self.cores_var.get(),
            'last_batch': self.batch_var.get()
        }
        try:
            with open(session_file, 'w') as f:
                json.dump(session_data, f)
        except:
            pass
            
    def load_last_session(self):
        """Load last session data"""
        session_file = "session.json"
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    if 'last_genome_file' in session_data:
                        last_file = session_data['last_genome_file']
                        if os.path.exists(last_file):
                            self.genome_file = last_file
                            self.file_label.config(text=os.path.basename(last_file))
                            self.analyze_btn.config(state=tk.NORMAL)
                    
                    # Restore settings
                    if 'last_magnitude' in session_data:
                        self.magnitude_var.set(session_data['last_magnitude'])
                    if 'last_limit' in session_data:
                        self.limit_var.set(session_data['last_limit'])
                    if 'last_cores' in session_data:
                        self.cores_var.set(session_data['last_cores'])
                    if 'last_batch' in session_data:
                        self.batch_var.set(session_data['last_batch'])
            except:
                pass


def main():
    # Check if multiprocessing is properly configured
    mp.set_start_method('spawn', force=True)
    
    root = tk.Tk()
    app = ParallelGenomeAnalyzerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()