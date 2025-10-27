"""
API Settings Page - Secure credential management
"""
import tkinter as tk
from tkinter import messagebox
import json
import os
import webbrowser


class APISettingsPage:
    """API Settings page for managing credentials"""
    
    def __init__(self, parent, colors):
        """
        Initialize API Settings page
        
        Args:
            parent: Parent tkinter widget
            colors: Dictionary of color scheme
        """
        self.parent = parent
        self.colors = colors
        self.config_file = "config/api_config.json"
        
        # Entry widgets for editing
        self.account_entry = None
        self.key_entry = None
        
        # Edit mode tracking
        self.edit_mode = False
        
    def create_page(self):
        """Create the API settings page"""
        # Main container
        main_frame = tk.Frame(self.parent, bg=self.colors['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = tk.Frame(main_frame, bg=self.colors['bg_panel'], relief=tk.SOLID, borderwidth=1)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(title_frame, text="═══ API SETTINGS ═══", bg=self.colors['bg_panel'], 
                fg=self.colors['white'], font=('Courier', 14, 'bold')).pack(pady=15)
        
        # Grid container - 2 columns layout
        grid_container = tk.Frame(main_frame, bg=self.colors['bg_dark'])
        grid_container.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # Configure grid weights for responsive layout
        grid_container.grid_columnconfigure(0, weight=1)
        grid_container.grid_columnconfigure(1, weight=1)
        grid_container.grid_rowconfigure(0, weight=1)
        grid_container.grid_rowconfigure(1, weight=1)
        
        # Left column - top: Info section
        info_container = tk.Frame(grid_container, bg=self.colors['bg_dark'])
        info_container.grid(row=0, column=0, sticky='nsew', padx=(0, 5), pady=(0, 5))
        self._create_info_section(info_container)
        
        # Right column - top: Credentials section
        creds_container = tk.Frame(grid_container, bg=self.colors['bg_dark'])
        creds_container.grid(row=0, column=1, sticky='nsew', padx=(5, 0), pady=(0, 5))
        self._create_credentials_section(creds_container)
        
        # Bottom row - spanning both columns: External Links section
        links_container = tk.Frame(grid_container, bg=self.colors['bg_dark'])
        links_container.grid(row=1, column=0, columnspan=2, sticky='nsew', pady=(5, 0))
        self._create_external_links_section(links_container)
    
    def _create_info_section(self, parent):
        """Create information section"""
        info_frame = tk.Frame(parent, bg=self.colors['bg_panel'], relief=tk.SOLID, borderwidth=1)
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(info_frame, text="ℹ️  SETUP INSTRUCTIONS", bg=self.colors['bg_panel'], 
                fg=self.colors['blue'], font=('Courier', 11, 'bold')).pack(pady=(15, 10), anchor='w', padx=15)
        
        instructions = [
            "1. Create your Hyperliquid trading account using the link below",
            "2. Set up your API credentials (wallet address + secret key)",
            "3. Enter your credentials below and click 'Save Changes'",
            "4. Your credentials are stored locally in config/api_config.json",
            "",
            "⚠️  SECURITY NOTICE:",
            "• Never share your secret key with anyone",
            "• Keep your config file secure and backed up",
            "• Use the referral code BONUS500 for 4% discount"
        ]
        
        for instruction in instructions:
            color = self.colors['yellow'] if instruction.startswith('⚠️') else self.colors['gray']
            tk.Label(info_frame, text=instruction, bg=self.colors['bg_panel'], 
                    fg=color, font=('Courier', 9), anchor='w').pack(pady=2, padx=20, anchor='w')
        
        tk.Label(info_frame, text="", bg=self.colors['bg_panel']).pack(pady=5)
    
    def _create_credentials_section(self, parent):
        """Create credentials management section"""
        creds_frame = tk.Frame(parent, bg=self.colors['bg_panel'], relief=tk.SOLID, borderwidth=1)
        creds_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(creds_frame, text="🔐 API CREDENTIALS", bg=self.colors['bg_panel'], 
                fg=self.colors['green'], font=('Courier', 11, 'bold')).pack(pady=(15, 10), anchor='w', padx=15)
        
        # Load current credentials
        config = self._load_config()
        account = config.get('account_address', '')
        secret_key = config.get('secret_key', '')
        
        # Account Address
        account_frame = tk.Frame(creds_frame, bg=self.colors['bg_panel'])
        account_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(account_frame, text="Account Address:", bg=self.colors['bg_panel'], 
                fg=self.colors['white'], font=('Courier', 10, 'bold'), width=20, anchor='w').pack(side=tk.LEFT, padx=(0, 10))
        
        self.account_entry = tk.Entry(account_frame, bg=self.colors['bg_dark'], fg=self.colors['white'],
                                      font=('Courier', 10), insertbackground=self.colors['white'],
                                      relief=tk.SOLID, borderwidth=1)
        self.account_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.account_entry.insert(0, account if account else "0x...")
        self.account_entry.config(state='readonly')
        
        # Secret Key (masked)
        key_frame = tk.Frame(creds_frame, bg=self.colors['bg_panel'])
        key_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(key_frame, text="Secret Key:", bg=self.colors['bg_panel'], 
                fg=self.colors['white'], font=('Courier', 10, 'bold'), width=20, anchor='w').pack(side=tk.LEFT, padx=(0, 10))
        
        self.key_entry = tk.Entry(key_frame, bg=self.colors['bg_dark'], fg=self.colors['white'],
                                  font=('Courier', 10), insertbackground=self.colors['white'],
                                  relief=tk.SOLID, borderwidth=1, show='*')
        self.key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.key_entry.insert(0, secret_key if secret_key else "0x...")
        self.key_entry.config(state='readonly')
        
        # Buttons frame
        buttons_frame = tk.Frame(creds_frame, bg=self.colors['bg_panel'])
        buttons_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # Edit/Cancel button
        self.edit_btn = tk.Button(buttons_frame, text="✏️  EDIT CREDENTIALS", 
                                  bg=self.colors['blue'], fg=self.colors['bg_dark'],
                                  font=('Courier', 10, 'bold'), cursor="hand2",
                                  relief=tk.RAISED, borderwidth=2, padx=20, pady=8,
                                  command=self._toggle_edit_mode)
        self.edit_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Save button (initially hidden)
        self.save_btn = tk.Button(buttons_frame, text="💾 SAVE CHANGES", 
                                  bg=self.colors['green'], fg=self.colors['bg_dark'],
                                  font=('Courier', 10, 'bold'), cursor="hand2",
                                  relief=tk.RAISED, borderwidth=2, padx=20, pady=8,
                                  command=self._save_credentials)
        # Don't pack initially
        
        # Status label
        self.status_label = tk.Label(creds_frame, text="", bg=self.colors['bg_panel'], 
                                    fg=self.colors['gray'], font=('Courier', 9))
        self.status_label.pack(pady=(0, 10))
    
    def _create_external_links_section(self, parent):
        """Create external links section"""
        links_frame = tk.Frame(parent, bg=self.colors['bg_panel'], relief=tk.SOLID, borderwidth=1)
        links_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(links_frame, text="🔗 QUICK LINKS", bg=self.colors['bg_panel'], 
                fg=self.colors['yellow'], font=('Courier', 11, 'bold')).pack(pady=(15, 10), anchor='w', padx=15)
        
        # Link 1: Create Account
        link1_frame = tk.Frame(links_frame, bg=self.colors['bg_dark'], relief=tk.SOLID, borderwidth=1)
        link1_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(link1_frame, text="📝 Create Your Free Trading Account", 
                bg=self.colors['bg_dark'], fg=self.colors['white'], 
                font=('Courier', 10, 'bold')).pack(pady=(10, 5), padx=10, anchor='w')
        
        tk.Label(link1_frame, text="Use referral code: BONUS500 for 4% discount", 
                bg=self.colors['bg_dark'], fg=self.colors['green'], 
                font=('Courier', 9)).pack(pady=(0, 5), padx=10, anchor='w')
        
        link1_btn = tk.Button(link1_frame, text="🌐 Open Hyperliquid Registration", 
                             bg=self.colors['green'], fg=self.colors['bg_dark'],
                             font=('Courier', 9, 'bold'), cursor="hand2",
                             relief=tk.RAISED, borderwidth=2, padx=15, pady=5,
                             command=lambda: self._open_url("https://app.hyperliquid.xyz/join/BONUS500"))
        link1_btn.pack(pady=(0, 10), padx=10, anchor='w')
        
        # Link 2: Create API
        link2_frame = tk.Frame(links_frame, bg=self.colors['bg_dark'], relief=tk.SOLID, borderwidth=1)
        link2_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(link2_frame, text="🔑 Create Your Trading Bot Wallet / API Credentials", 
                bg=self.colors['bg_dark'], fg=self.colors['white'], 
                font=('Courier', 10, 'bold')).pack(pady=(10, 5), padx=10, anchor='w')
        
        tk.Label(link2_frame, text="Generate your API wallet and secret key", 
                bg=self.colors['bg_dark'], fg=self.colors['gray'], 
                font=('Courier', 9)).pack(pady=(0, 5), padx=10, anchor='w')
        
        link2_btn = tk.Button(link2_frame, text="🌐 Open API Management", 
                             bg=self.colors['blue'], fg=self.colors['bg_dark'],
                             font=('Courier', 9, 'bold'), cursor="hand2",
                             relief=tk.RAISED, borderwidth=2, padx=15, pady=5,
                             command=lambda: self._open_url("https://app.hyperliquid.xyz/API"))
        link2_btn.pack(pady=(0, 10), padx=10, anchor='w')
        
        tk.Label(links_frame, text="", bg=self.colors['bg_panel']).pack(pady=5)
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
        return {}
    
    def _save_config(self, config):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def _toggle_edit_mode(self):
        """Toggle between view and edit mode"""
        if not self.edit_mode:
            # Enter edit mode
            self.edit_mode = True
            self.account_entry.config(state='normal')
            self.key_entry.config(state='normal', show='')
            self.edit_btn.config(text="❌ CANCEL", bg=self.colors['red'])
            self.save_btn.pack(side=tk.LEFT, padx=(0, 10))
            self.status_label.config(text="✏️  Edit mode enabled - modify credentials and click Save", 
                                   fg=self.colors['yellow'])
        else:
            # Exit edit mode (cancel)
            self.edit_mode = False
            
            # Reload original values
            config = self._load_config()
            account = config.get('account_address', '')
            secret_key = config.get('secret_key', '')
            
            self.account_entry.config(state='normal')
            self.key_entry.config(state='normal', show='*')
            
            self.account_entry.delete(0, tk.END)
            self.account_entry.insert(0, account if account else "0x...")
            
            self.key_entry.delete(0, tk.END)
            self.key_entry.insert(0, secret_key if secret_key else "0x...")
            
            self.account_entry.config(state='readonly')
            self.key_entry.config(state='readonly')
            
            self.edit_btn.config(text="✏️  EDIT CREDENTIALS", bg=self.colors['blue'])
            self.save_btn.pack_forget()
            self.status_label.config(text="", fg=self.colors['gray'])
    
    def _save_credentials(self):
        """Save the edited credentials"""
        account = self.account_entry.get().strip()
        secret_key = self.key_entry.get().strip()
        
        # Validation
        if not account or not account.startswith('0x'):
            messagebox.showerror("Invalid Input", "Account address must start with '0x'")
            return
        
        if not secret_key or not secret_key.startswith('0x'):
            messagebox.showerror("Invalid Input", "Secret key must start with '0x'")
            return
        
        # Load current config
        config = self._load_config()
        
        # Update credentials
        config['account_address'] = account
        config['secret_key'] = secret_key
        
        # Save to file
        if self._save_config(config):
            self.status_label.config(text="✅ Credentials saved successfully! Restart the bot to apply changes.", 
                                   fg=self.colors['green'])
            
            # Exit edit mode
            self.edit_mode = False
            self.account_entry.config(state='readonly')
            self.key_entry.config(state='readonly', show='*')
            self.edit_btn.config(text="✏️  EDIT CREDENTIALS", bg=self.colors['blue'])
            self.save_btn.pack_forget()
            
            messagebox.showinfo("Success", "API credentials saved successfully!\n\nPlease restart the trading bot for changes to take effect.")
        else:
            self.status_label.config(text="❌ Error saving credentials", fg=self.colors['red'])
            messagebox.showerror("Error", "Failed to save credentials. Check file permissions.")
    
    def _open_url(self, url):
        """Open URL in default browser"""
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Error opening URL: {e}")
            messagebox.showerror("Error", f"Failed to open URL: {url}")
