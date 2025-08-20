import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import json
import multiprocessing as mp
from datetime import datetime

from simple_parallel_analyzer import SimpleParallelAnalyzer


class FinalGenomeAnalyzerGUI:
    """Final GUI using the working simple parallel analyzer"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"🔥 High-Performance Genome Analyzer ({mp.cpu_count()} CPU Cores)")
        self.root.geometry("1000x700")
        
        self.analyzer = None
        self.genome_file = None
        self.results = []
        self.cpu_count = mp.cpu_count()
        
        self.setup_ui()
        self.load_last_session()
        
    def setup_ui(self):
        """Setup UI"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title = ttk.Label(main_frame, text=f"🔥 High-Performance Genome Analyzer", 
                         font=('Arial', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Warning label
        warning = ttk.Label(main_frame, 
                           text=f"⚠️ WARNING: Uses ALL {self.cpu_count} CPU cores - will heat up your laptop!",
                           font=('Arial', 10), foreground='red')
        warning.grid(row=1, column=0, columnspan=3, pady=5)
        
        # File selection
        ttk.Label(main_frame, text="Genome File:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.file_label = ttk.Label(main_frame, text="No file selected", 
                                   relief=tk.SUNKEN, anchor=tk.W)
        self.file_label.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(main_frame, text="Browse...", 
                  command=self.select_file).grid(row=2, column=2, padx=5, pady=5)
        
        # Analysis options
        options_frame = ttk.LabelFrame(main_frame, text="Analysis Options", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(options_frame, text="Minimum Magnitude:").grid(row=0, column=0, sticky=tk.W)
        self.magnitude_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(options_frame, from_=0, to=10, increment=0.5,
                   textvariable=self.magnitude_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(options_frame, text="Limit SNPs:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.limit_var = tk.IntVar(value=0)
        ttk.Spinbox(options_frame, from_=0, to=1000000, increment=10000,
                   textvariable=self.limit_var, width=10).grid(row=0, column=3, sticky=tk.W, padx=5)
        ttk.Label(options_frame, text="(0 = all SNPs)").grid(row=0, column=4, sticky=tk.W)
        
        # Quick presets
        presets_frame = ttk.LabelFrame(main_frame, text="🚀 Quick Start", padding="10")
        presets_frame.grid(row=4, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Button(presets_frame, text="🔥 Test (10K SNPs)", 
                  command=lambda: self.set_preset(10000, 2.0)).grid(row=0, column=0, padx=5)
        ttk.Button(presets_frame, text="⚡ Medium (100K SNPs)", 
                  command=lambda: self.set_preset(100000, 1.0)).grid(row=0, column=1, padx=5)
        ttk.Button(presets_frame, text="🚀 Full Analysis (All 22M SNPs)", 
                  command=lambda: self.set_preset(0, 0.0)).grid(row=0, column=2, padx=5)
        
        # Analysis button
        self.analyze_btn = ttk.Button(main_frame, text=f"🔥 START ANALYSIS ({self.cpu_count} cores)", 
                                     command=self.start_analysis, state=tk.DISABLED)
        self.analyze_btn.grid(row=5, column=0, columnspan=3, pady=15)
        
        # Progress
        self.progress_label = ttk.Label(main_frame, text="")
        self.progress_label.grid(row=6, column=0, columnspan=3)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Results
        results_frame = ttk.LabelFrame(main_frame, text="Analysis Results", padding="10")
        results_frame.grid(row=8, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(8, weight=1)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, height=12, width=80)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Export buttons
        export_frame = ttk.Frame(main_frame)
        export_frame.grid(row=9, column=0, columnspan=3, pady=10)
        
        self.export_json_btn = ttk.Button(export_frame, text="Export JSON", 
                                         command=lambda: self.export_results('json'),
                                         state=tk.DISABLED)
        self.export_json_btn.grid(row=0, column=0, padx=5)
        
        self.export_tsv_btn = ttk.Button(export_frame, text="Export TSV", 
                                        command=lambda: self.export_results('tsv'),
                                        state=tk.DISABLED)
        self.export_tsv_btn.grid(row=0, column=1, padx=5)
        
        # Status
        self.status_label = ttk.Label(main_frame, text=f"Ready - {self.cpu_count} CPU cores available", 
                                     relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
    def set_preset(self, limit, magnitude):
        """Set analysis presets"""
        self.limit_var.set(limit)
        self.magnitude_var.set(magnitude)
        
    def select_file(self):
        """Select genome file"""
        filename = filedialog.askopenfilename(
            title="Select Genome File",
            filetypes=[("Text files", "*.txt"), ("Compressed files", "*.gz"), ("All files", "*.*")]
        )
        
        if filename:
            self.genome_file = filename
            self.file_label.config(text=os.path.basename(filename))
            self.analyze_btn.config(state=tk.NORMAL)
            self.save_session()
            self.status_label.config(text=f"File selected: {os.path.basename(filename)}")
            
    def start_analysis(self):
        """Start analysis"""
        if not self.genome_file:
            messagebox.showerror("Error", "Please select a genome file first")
            return
            
        # Warning for full analysis
        limit = self.limit_var.get()
        if limit == 0:
            result = messagebox.askyesno(
                "Full Analysis Warning", 
                f"This will analyze ALL 22+ million SNPs using all {self.cpu_count} CPU cores.\n\n"
                "Your laptop will get very hot and the analysis may take 30+ minutes.\n\n"
                "Continue with full analysis?"
            )
            if not result:
                return
        
        # Disable buttons
        self.analyze_btn.config(state=tk.DISABLED)
        self.export_json_btn.config(state=tk.DISABLED)
        self.export_tsv_btn.config(state=tk.DISABLED)
        
        # Clear results
        self.results_text.delete(1.0, tk.END)
        self.progress_bar.config(value=0)
        
        # Start analysis thread
        thread = threading.Thread(target=self.run_analysis)
        thread.daemon = True
        thread.start()
        
    def run_analysis(self):
        """Run the analysis"""
        try:
            # Initialize analyzer
            self.analyzer = SimpleParallelAnalyzer()
            
            # Load genome
            self.root.after(0, self.update_progress, "Loading genome file...", 5)
            genome_stats = self.analyzer.load_genome(self.genome_file)
            
            total_snps = genome_stats['total_snps']
            limit = self.limit_var.get() if self.limit_var.get() > 0 else None
            analyze_count = limit if limit else total_snps
            
            self.root.after(0, self.update_progress, 
                          f"Loaded {total_snps:,} SNPs. Starting analysis of {analyze_count:,} SNPs...", 10)
            
            # Progress callback
            def progress_callback(status):
                self.root.after(0, self.update_progress, status, None)
            
            # Run analysis
            magnitude = self.magnitude_var.get()
            
            self.results = self.analyzer.analyze_parallel(
                magnitude_threshold=magnitude,
                limit=limit,
                progress_callback=progress_callback
            )
            
            # Get statistics
            stats = self.analyzer.get_summary_stats()
            
            # Update UI
            self.root.after(0, self.display_results, stats)
            
        except Exception as e:
            self.root.after(0, self.show_error, str(e))
        finally:
            self.root.after(0, self.analysis_complete)
            
    def update_progress(self, message, percent=None):
        """Update progress"""
        self.progress_label.config(text=message)
        if percent is not None:
            self.progress_bar.config(value=percent)
        self.status_label.config(text=message)
        
    def display_results(self, stats):
        """Display results"""
        self.results_text.delete(1.0, tk.END)
        
        self.results_text.insert(tk.END, "🔥 HIGH-PERFORMANCE ANALYSIS COMPLETE!\n", 'title')
        self.results_text.insert(tk.END, "=" * 60 + "\n\n")
        
        self.results_text.insert(tk.END, f"Total SNPs analyzed: {stats['total_analyzed']:,}\n")
        self.results_text.insert(tk.END, f"SNPs with SNPedia data: {stats['with_snpedia_data']:,}\n")
        self.results_text.insert(tk.END, f"Significant SNPs (mag >= 2): {stats['significant']:,}\n")
        self.results_text.insert(tk.END, f"Good repute: {stats['good_repute']:,}\n")
        self.results_text.insert(tk.END, f"Bad repute: {stats['bad_repute']:,}\n\n")
        
        # Show top significant SNPs
        significant = self.analyzer.get_significant_snps(min_magnitude=2.0)
        if significant:
            self.results_text.insert(tk.END, "🌟 TOP SIGNIFICANT SNPs:\n", 'title')
            self.results_text.insert(tk.END, "=" * 40 + "\n\n")
            
            for i, result in enumerate(significant[:15], 1):
                self.results_text.insert(tk.END, f"{i}. {result.rsid} ", 'rsid')
                self.results_text.insert(tk.END, f"({result.user_genotype})\n")
                
                if result.magnitude:
                    self.results_text.insert(tk.END, f"   Magnitude: {result.magnitude}\n")
                if result.repute:
                    color = 'good' if 'good' in result.repute.lower() else 'bad' if 'bad' in result.repute.lower() else None
                    self.results_text.insert(tk.END, f"   Repute: {result.repute}\n", color)
                if result.summary:
                    self.results_text.insert(tk.END, f"   Summary: {result.summary}\n")
                self.results_text.insert(tk.END, "\n")
                
        # Configure tags
        self.results_text.tag_config('title', font=('Arial', 12, 'bold'))
        self.results_text.tag_config('rsid', font=('Courier', 10, 'bold'), foreground='blue')
        self.results_text.tag_config('good', foreground='green')
        self.results_text.tag_config('bad', foreground='red')
        
    def analysis_complete(self):
        """Analysis complete"""
        self.progress_bar.config(value=100)
        self.progress_label.config(text="🎉 Analysis complete!")
        self.analyze_btn.config(state=tk.NORMAL)
        self.export_json_btn.config(state=tk.NORMAL)
        self.export_tsv_btn.config(state=tk.NORMAL)
        self.status_label.config(text=f"✅ Complete! {len(self.results):,} results found")
        
    def show_error(self, error_message):
        """Show error"""
        messagebox.showerror("Analysis Error", error_message)
        self.progress_bar.config(value=0)
        self.progress_label.config(text="❌ Error occurred")
        self.analyze_btn.config(state=tk.NORMAL)
        
    def export_results(self, format):
        """Export results"""
        if not self.results:
            messagebox.showwarning("No Results", "No analysis results to export")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == 'json':
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                initialname=f"genome_analysis_{timestamp}.json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
        else:
            filename = filedialog.asksaveasfilename(
                defaultextension=".tsv",
                initialname=f"genome_analysis_{timestamp}.tsv",
                filetypes=[("Tab-separated files", "*.tsv"), ("All files", "*.*")]
            )
            
        if filename:
            try:
                self.analyzer.export_results(filename, format=format)
                messagebox.showinfo("Export Complete", f"Results exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))
                
    def save_session(self):
        """Save session"""
        try:
            with open("session.json", 'w') as f:
                json.dump({'last_genome_file': self.genome_file}, f)
        except:
            pass
            
    def load_last_session(self):
        """Load last session"""
        try:
            if os.path.exists("session.json"):
                with open("session.json", 'r') as f:
                    session_data = json.load(f)
                    if 'last_genome_file' in session_data:
                        last_file = session_data['last_genome_file']
                        if os.path.exists(last_file):
                            self.genome_file = last_file
                            self.file_label.config(text=os.path.basename(last_file))
                            self.analyze_btn.config(state=tk.NORMAL)
        except:
            pass


def main():
    root = tk.Tk()
    app = FinalGenomeAnalyzerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()