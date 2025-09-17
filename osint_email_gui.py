#!/usr/bin/env python3
"""
Advanced Email OSINT Tool - GUI Interface
Author: Security Researcher
Date: September 2025
Description: Graphical user interface for the email OSINT tool
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import json
import os
from datetime import datetime
import webbrowser

from osint_email import OSINTEmailTool
from utils.email_validator import EmailValidator


class OSINTEmailGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Email OSINT Tool v1.0 - September 2025")
        self.root.geometry("1000x700")
        self.root.configure(bg='#2b2b2b')
        
        # Initialize components
        self.osint_tool = None
        self.email_validator = EmailValidator()
        self.current_results = None
        self.search_thread = None
        
        # Style configuration
        self.setup_styles()
        
        # Create GUI components
        self.create_widgets()
        
        # Initialize tool
        self.initialize_tool()
        
    def setup_styles(self):
        """Setup custom styles for the GUI"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#ffffff', background='#2b2b2b')
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'), foreground='#4CAF50', background='#2b2b2b')
        style.configure('Custom.TButton', font=('Arial', 10, 'bold'))
        style.configure('Status.TLabel', font=('Arial', 9), foreground='#FFA726', background='#2b2b2b')
        
    def create_widgets(self):
        """Create and arrange GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="🔍 Advanced Email OSINT Tool", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Search Configuration", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Email input
        email_frame = ttk.Frame(input_frame)
        email_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(email_frame, text="Email Address:", style='Header.TLabel').pack(anchor=tk.W)
        self.email_entry = ttk.Entry(email_frame, font=('Arial', 11), width=50)
        self.email_entry.pack(fill=tk.X, pady=(5, 0))
        self.email_entry.bind('<KeyRelease>', self.validate_email_input)
        
        # Email validation status
        self.email_status_label = ttk.Label(email_frame, text="", style='Status.TLabel')
        self.email_status_label.pack(anchor=tk.W, pady=(2, 0))
        
        # Platform selection
        platform_frame = ttk.Frame(input_frame)
        platform_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(platform_frame, text="Platforms to Search:", style='Header.TLabel').pack(anchor=tk.W)
        
        platform_checkboxes_frame = ttk.Frame(platform_frame)
        platform_checkboxes_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.platform_vars = {
            'marketplaces': tk.BooleanVar(value=True),
            'discussions': tk.BooleanVar(value=True),
            'google': tk.BooleanVar(value=True)
        }
        
        for platform, var in self.platform_vars.items():
            ttk.Checkbutton(platform_checkboxes_frame, text=platform.title(), 
                           variable=var).pack(side=tk.LEFT, padx=(0, 20))
        
        # Advanced options
        advanced_frame = ttk.LabelFrame(input_frame, text="Advanced Options", padding=5)
        advanced_frame.pack(fill=tk.X, pady=(10, 0))
        
        options_frame = ttk.Frame(advanced_frame)
        options_frame.pack(fill=tk.X)
        
        # Workers
        ttk.Label(options_frame, text="Concurrent Workers:").pack(side=tk.LEFT)
        self.workers_var = tk.StringVar(value="5")
        workers_spinbox = ttk.Spinbox(options_frame, from_=1, to=20, width=5, textvariable=self.workers_var)
        workers_spinbox.pack(side=tk.LEFT, padx=(5, 20))
        
        # Output format
        ttk.Label(options_frame, text="Output Format:").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="json")
        format_combo = ttk.Combobox(options_frame, textvariable=self.format_var, 
                                   values=['json', 'csv', 'xml', 'txt', 'html', 'xlsx'], 
                                   state="readonly", width=10)
        format_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.search_button = ttk.Button(control_frame, text="🔍 Start Search", 
                                       command=self.start_search, style='Custom.TButton')
        self.search_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="⏹ Stop Search", 
                                     command=self.stop_search, style='Custom.TButton', 
                                     state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_button = ttk.Button(control_frame, text="💾 Save Results", 
                                     command=self.save_results, style='Custom.TButton',
                                     state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(control_frame, text="🗑 Clear", 
                                      command=self.clear_results, style='Custom.TButton')
        self.clear_button.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(10, 0))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to search", style='Status.TLabel')
        self.status_label.pack(pady=(5, 10))
        
        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="Search Results", padding=5)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Results notebook
        self.results_notebook = ttk.Notebook(results_frame)
        self.results_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Summary tab
        self.summary_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.summary_frame, text="Summary")
        
        self.summary_text = scrolledtext.ScrolledText(self.summary_frame, wrap=tk.WORD, 
                                                     height=15, font=('Consolas', 10))
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Detailed results tab
        self.details_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.details_frame, text="Detailed Results")
        
        # Treeview for detailed results
        columns = ('Platform', 'Type', 'Status', 'Matches', 'URL')
        self.results_tree = ttk.Treeview(self.details_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        for col in columns:
            self.results_tree.heading(col, text=col)
            if col == 'Platform':
                self.results_tree.column(col, width=150)
            elif col == 'Type':
                self.results_tree.column(col, width=100)
            elif col == 'Status':
                self.results_tree.column(col, width=100)
            elif col == 'Matches':
                self.results_tree.column(col, width=80)
            elif col == 'URL':
                self.results_tree.column(col, width=200)
        
        # Scrollbar for treeview
        tree_scrollbar = ttk.Scrollbar(self.details_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Bind double-click on tree
        self.results_tree.bind('<Double-1>', self.on_tree_double_click)
        
        # Raw data tab
        self.raw_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.raw_frame, text="Raw Data")
        
        self.raw_text = scrolledtext.ScrolledText(self.raw_frame, wrap=tk.WORD, 
                                                 height=15, font=('Consolas', 9))
        self.raw_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def initialize_tool(self):
        """Initialize the OSINT tool"""
        try:
            self.osint_tool = OSINTEmailTool()
            self.update_status("Tool initialized successfully")
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize OSINT tool:\n{str(e)}")
            self.update_status(f"Initialization failed: {str(e)}")
            
    def validate_email_input(self, event=None):
        """Validate email input in real-time"""
        email = self.email_entry.get().strip()
        
        if not email:
            self.email_status_label.config(text="")
            return
            
        if self.email_validator.is_valid_email(email):
            self.email_status_label.config(text="✅ Valid email format", foreground='#4CAF50')
        else:
            self.email_status_label.config(text="❌ Invalid email format", foreground='#F44336')
            
    def start_search(self):
        """Start the email search process"""
        email = self.email_entry.get().strip()
        
        if not email:
            messagebox.showwarning("Input Error", "Please enter an email address")
            return
            
        if not self.email_validator.is_valid_email(email):
            messagebox.showerror("Invalid Email", "Please enter a valid email address")
            return
            
        # Get selected platforms
        selected_platforms = [platform for platform, var in self.platform_vars.items() if var.get()]
        
        if not selected_platforms:
            messagebox.showwarning("Platform Selection", "Please select at least one platform to search")
            return
            
        # Update UI state
        self.search_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.DISABLED)
        
        # Clear previous results
        self.clear_results()
        
        # Start progress bar
        self.progress.start(10)
        self.update_status(f"Searching for {email}...")
        
        # Start search in separate thread
        workers = int(self.workers_var.get())
        self.search_thread = threading.Thread(
            target=self.perform_search,
            args=(email, selected_platforms, workers)
        )
        self.search_thread.daemon = True
        self.search_thread.start()
        
    def perform_search(self, email, platforms, workers):
        """Perform the actual search (runs in separate thread)"""
        try:
            self.current_results = self.osint_tool.search_email(
                email=email,
                platforms=platforms,
                max_workers=workers
            )
            
            # Update UI from main thread
            self.root.after(0, self.search_completed)
            
        except Exception as e:
            # Update UI from main thread
            self.root.after(0, lambda: self.search_failed(str(e)))
            
    def search_completed(self):
        """Handle search completion"""
        self.progress.stop()
        
        # Update UI state
        self.search_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.NORMAL)
        
        # Display results
        self.display_results()
        
        # Update status
        if self.current_results:
            summary = self.current_results.get('summary', {})
            hits = summary.get('platforms_with_hits', 0)
            total = summary.get('total_platforms_searched', 0)
            self.update_status(f"Search completed: {hits}/{total} platforms returned results")
        else:
            self.update_status("Search completed with no results")
            
    def search_failed(self, error_message):
        """Handle search failure"""
        self.progress.stop()
        
        # Update UI state
        self.search_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # Show error
        messagebox.showerror("Search Error", f"Search failed:\n{error_message}")
        self.update_status(f"Search failed: {error_message}")
        
    def stop_search(self):
        """Stop the current search"""
        if self.search_thread and self.search_thread.is_alive():
            # Note: This is a simple implementation. In production, you'd want
            # proper thread cancellation mechanisms
            self.update_status("Stop requested (search may continue briefly)...")
            
        self.progress.stop()
        self.search_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
    def display_results(self):
        """Display search results in the GUI"""
        if not self.current_results:
            return
            
        # Display summary
        self.display_summary()
        
        # Display detailed results
        self.display_detailed_results()
        
        # Display raw data
        self.display_raw_data()
        
    def display_summary(self):
        """Display summary results"""
        self.summary_text.delete(1.0, tk.END)
        
        if not self.current_results:
            return
            
        email = self.current_results.get('email', 'Unknown')
        timestamp = self.current_results.get('timestamp', 'Unknown')
        summary = self.current_results.get('summary', {})
        
        summary_text = f"""EMAIL OSINT SEARCH SUMMARY
{'='*50}

Target Email: {email}
Search Time: {timestamp}

STATISTICS
----------
• Total Platforms Searched: {summary.get('total_platforms_searched', 0)}
• Platforms with Hits: {summary.get('platforms_with_hits', 0)}
• Platforms with Errors: {summary.get('platforms_with_errors', 0)}
• Success Rate: {summary.get('hit_rate_percentage', 0):.2f}%

PLATFORM BREAKDOWN
------------------
"""
        
        for platform_type, platform_results in self.current_results.get('results', {}).items():
            hits = sum(1 for r in platform_results if r.get('status') == 'found')
            potential = sum(1 for r in platform_results if r.get('status') == 'potential_match')
            total = len(platform_results)
            
            summary_text += f"{platform_type.title()}: {hits} hits, {potential} potential matches ({total} platforms)\n"
            
        # Add matches details
        summary_text += "\nDETAILED FINDINGS\n" + "-"*20 + "\n"
        
        for platform_type, platform_results in self.current_results.get('results', {}).items():
            for result in platform_results:
                if result.get('status') in ['found', 'potential_match']:
                    summary_text += f"\n✅ {result.get('platform', 'Unknown')} ({platform_type})\n"
                    summary_text += f"   Status: {result.get('status', 'Unknown')}\n"
                    summary_text += f"   URL: {result.get('url', 'Unknown')}\n"
                    
                    if result.get('matches'):
                        summary_text += f"   Matches: {len(result['matches'])}\n"
                        for match in result['matches'][:2]:  # Show first 2 matches
                            if isinstance(match, dict):
                                for key, value in match.items():
                                    if key in ['title', 'snippet', 'context']:
                                        summary_text += f"   {key.title()}: {str(value)[:100]}...\n"
                                        
        self.summary_text.insert(tk.END, summary_text)
        
    def display_detailed_results(self):
        """Display detailed results in treeview"""
        # Clear existing data
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
        if not self.current_results:
            return
            
        # Populate treeview
        for platform_type, platform_results in self.current_results.get('results', {}).items():
            for result in platform_results:
                status = result.get('status', 'Unknown')
                matches_count = len(result.get('matches', []))
                
                # Status with emoji
                status_display = {
                    'found': '✅ Found',
                    'not_found': '❌ Not Found',
                    'error': '⚠️ Error',
                    'potential_match': '🔍 Potential'
                }.get(status, status)
                
                item = self.results_tree.insert('', tk.END, values=(
                    result.get('platform', 'Unknown'),
                    platform_type.title(),
                    status_display,
                    matches_count if matches_count > 0 else '-',
                    result.get('url', 'Unknown')
                ))
                
                # Add tag for status coloring
                if status == 'found':
                    self.results_tree.set(item, 'Status', '✅ Found')
                elif status == 'potential_match':
                    self.results_tree.set(item, 'Status', '🔍 Potential')
                elif status == 'error':
                    self.results_tree.set(item, 'Status', '⚠️ Error')
                    
    def display_raw_data(self):
        """Display raw JSON data"""
        self.raw_text.delete(1.0, tk.END)
        
        if self.current_results:
            raw_json = json.dumps(self.current_results, indent=2, ensure_ascii=False, default=str)
            self.raw_text.insert(tk.END, raw_json)
            
    def on_tree_double_click(self, event):
        """Handle double-click on treeview item"""
        item = self.results_tree.selection()[0] if self.results_tree.selection() else None
        if not item:
            return
            
        values = self.results_tree.item(item, 'values')
        if values and len(values) > 4:
            url = values[4]  # URL column
            if url and url != 'Unknown':
                # Open URL in browser
                try:
                    webbrowser.open(f"https://{url}")
                except Exception as e:
                    messagebox.showerror("Browser Error", f"Failed to open URL:\n{str(e)}")
                    
    def save_results(self):
        """Save search results to file"""
        if not self.current_results:
            messagebox.showwarning("No Results", "No results to save")
            return
            
        # Get save location
        format_type = self.format_var.get()
        filetypes = {
            'json': [('JSON files', '*.json')],
            'csv': [('CSV files', '*.csv')],
            'xml': [('XML files', '*.xml')],
            'txt': [('Text files', '*.txt')],
            'html': [('HTML files', '*.html')],
            'xlsx': [('Excel files', '*.xlsx')]
        }
        
        filename = filedialog.asksaveasfilename(
            defaultextension=f".{format_type}",
            filetypes=filetypes.get(format_type, [('All files', '*.*')]),
            title="Save Search Results"
        )
        
        if not filename:
            return
            
        try:
            # Use the formatter to save results
            saved_file = self.osint_tool.formatter.save_results(
                results=self.current_results,
                filename=filename.rsplit('.', 1)[0],  # Remove extension
                format_type=format_type
            )
            
            messagebox.showinfo("Save Successful", f"Results saved to:\n{saved_file}")
            self.update_status(f"Results saved to {saved_file}")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save results:\n{str(e)}")
            
    def clear_results(self):
        """Clear all results displays"""
        self.summary_text.delete(1.0, tk.END)
        self.raw_text.delete(1.0, tk.END)
        
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
        self.current_results = None
        self.save_button.config(state=tk.DISABLED)
        
    def update_status(self, message):
        """Update status label"""
        self.status_label.config(text=message)
        self.root.update_idletasks()


def main():
    """Main function to run the GUI"""
    root = tk.Tk()
    app = OSINTEmailGUI(root)
    
    # Handle window closing
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # Run the GUI
    root.mainloop()


if __name__ == "__main__":
    main()