"""
Alert system for multi-channel notifications.
"""

import json
from typing import List
from datetime import datetime
import sys
sys.path.append('..')

from schemas import ConsolidatedAlert


class AlertSystem:
    """
    Multi-channel alert system.
    
    Supports:
    - Console output
    - File logging
    - Webhook (optional)
    - Email (optional)
    """
    
    def __init__(self, config: dict):
        """
        Initialize alert system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.enable_console = config.get("enable_console", True)
        self.enable_file = config.get("enable_file", True)
        self.enable_webhook = config.get("enable_webhook", False)
        self.enable_email = config.get("enable_email", False)
        
        self.log_file = config.get("log_file", "alerts.log")
        
        # Initialize file logging
        if self.enable_file:
            self._init_file_logging()
    
    def _init_file_logging(self):
        """Initialize file logging"""
        try:
            with open(self.log_file, 'a') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"Alert System Initialized: {datetime.now().isoformat()}\n")
                f.write(f"{'='*80}\n\n")
            print(f"✓ Alert logging to: {self.log_file}")
        except Exception as e:
            print(f"Warning: Could not initialize file logging: {e}")
            self.enable_file = False
    
    def send_alerts(self, alerts: List[ConsolidatedAlert]):
        """
        Send alerts through configured channels.
        
        Args:
            alerts: List of ConsolidatedAlert objects
        """
        for alert in alerts:
            if self.enable_console:
                self._send_console(alert)
            
            if self.enable_file:
                self._send_file(alert)
            
            if self.enable_webhook:
                self._send_webhook(alert)
            
            if self.enable_email:
                self._send_email(alert)
    
    def _send_console(self, alert: ConsolidatedAlert):
        """Print alert to console"""
        # Color codes for terminal
        color_map = {
            "CRITICAL": "\033[91m",  # Red
            "HIGH": "\033[93m",      # Yellow
            "MEDIUM": "\033[94m",    # Blue
            "LOW": "\033[92m",       # Green
            "INFO": "\033[97m",      # White
        }
        reset = "\033[0m"
        
        color = color_map.get(alert.level, reset)
        timestamp = datetime.fromtimestamp(alert.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"{color}[{alert.level}] {timestamp} - {alert.message}{reset}")
    
    def _send_file(self, alert: ConsolidatedAlert):
        """Log alert to file"""
        try:
            with open(self.log_file, 'a') as f:
                timestamp = datetime.fromtimestamp(alert.timestamp).isoformat()
                f.write(f"[{timestamp}] [{alert.level}] {alert.message}\n")
                f.write(f"  Alert ID: {alert.alert_id}\n")
                f.write(f"  Events: {len(alert.events)}\n")
                for event in alert.events:
                    f.write(f"    - {event.agent_name}: {event.event_type} (conf: {event.confidence:.2f})\n")
                f.write("\n")
        except Exception as e:
            print(f"Error logging to file: {e}")
    
    def _send_webhook(self, alert: ConsolidatedAlert):
        """Send alert via webhook"""
        # Placeholder for webhook implementation
        webhook_url = self.config.get("webhook_url")
        if not webhook_url:
            return
        
        try:
            import requests
            payload = alert.to_dict()
            response = requests.post(webhook_url, json=payload, timeout=5)
            if response.status_code != 200:
                print(f"Webhook error: {response.status_code}")
        except Exception as e:
            print(f"Error sending webhook: {e}")
    
    def _send_email(self, alert: ConsolidatedAlert):
        """Send alert via email"""
        # Placeholder for email implementation
        email_config = self.config.get("email_config", {})
        
        if not email_config.get("smtp_server"):
            return
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            msg = MIMEText(f"{alert.message}\n\nAlert ID: {alert.alert_id}")
            msg['Subject'] = f"[{alert.level}] Patient Monitoring Alert"
            msg['From'] = email_config.get("sender")
            msg['To'] = ", ".join(email_config.get("recipients", []))
            
            with smtplib.SMTP(email_config.get("smtp_server"), email_config.get("smtp_port", 587)) as server:
                server.starttls()
                server.login(email_config.get("sender"), email_config.get("password"))
                server.send_message(msg)
        except Exception as e:
            print(f"Error sending email: {e}")
