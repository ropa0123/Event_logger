"""
Modern GUI for Schedule Event Logging System
Uses customtkinter for modern Material Design-like appearance

Installation:
    pip install customtkinter pillow plyer

Usage:
    python modern_gui.py
"""

import os
import json
import csv
import threading
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import tkinter as tk
from tkinter import messagebox, ttk

try:
    import customtkinter as ctk
    from plyer import notification
    HAS_PLYER = True
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call(["pip", "install", "customtkinter", "pillow", "plyer"])
    import customtkinter as ctk
    from plyer import notification
    HAS_PLYER = True

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class User:
    def __init__(self, users_file: str = "users.json"):
        self.users_file = users_file
        self.users = self._load_users()
        self.current_user = None
        if not self.users:
            self._create_default_users()

    def _load_users(self) -> Dict:
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_users(self):
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def _create_default_users(self):
        self.users = {
            "admin": {"password": self._hash_password("admin123"), "role": "admin", "name": "Administrator"},
            "user": {"password": self._hash_password("user123"), "role": "user", "name": "Regular User"}
        }
        self._save_users()

    def authenticate(self, username: str, password: str) -> bool:
        if username in self.users:
            if self.users[username]['password'] == self._hash_password(password):
                self.current_user = username
                return True
        return False

    def get_role(self, username: str) -> Optional[str]:
        return self.users.get(username, {}).get('role')

    def is_admin(self, username: str) -> bool:
        return self.get_role(username) == 'admin'

    def add_user(self, username: str, password: str, role: str, name: str) -> bool:
        if username in self.users:
            return False
        self.users[username] = {"password": self._hash_password(password), "role": role, "name": name}
        self._save_users()
        return True

    def list_users(self):
        return self.users

    def get_name(self, username: str) -> str:
        return self.users.get(username, {}).get('name', username)

class ScheduleLogger:
    def __init__(self, log_file: str = "schedule_log.json"):
        self.log_file = log_file
        self.events = self._load_events()
        self.alert_running = False
        self.alert_thread = None
        self.alert_callback = None

    def _load_events(self) -> List[Dict]:
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def _save_events(self):
        with open(self.log_file, 'w') as f:
            json.dump(self.events, f, indent=2)

    def _next_id(self):
        if not self.events:
            return 1
        return max(e['id'] for e in self.events) + 1

    def add_event(self, time_slot: str, client: str, delivery_type: str, resource: str,
                  assigned_to: str, signature: str = "", length: str = "",
                  notes: str = "", alert_minutes: int = 5) -> Dict:
        event = {
            "id": self._next_id(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time_slot": time_slot,
            "length": length,
            "client": client,
            "delivery_type": delivery_type,
            "resource": resource,
            "assigned_to": assigned_to,
            "signature": signature,
            "notes": notes,
            "status": "logged",
            "alert_minutes": alert_minutes,
            "alert_triggered": False
        }
        self.events.append(event)
        self._save_events()
        return event

    def view_events(self, date: Optional[str] = None, client: Optional[str] = None) -> List[Dict]:
        filtered = self.events
        if date:
            filtered = [e for e in filtered if e['date'] == date]
        if client:
            filtered = [e for e in filtered if client.lower() in e['client'].lower()]
        return sorted(filtered, key=lambda x: x.get('timestamp', ''), reverse=True)

    def update_event(self, event_id: int, **kwargs) -> bool:
        for event in self.events:
            if event['id'] == event_id:
                event.update(kwargs)
                event['last_modified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._save_events()
                return True
        return False

    def delete_event(self, event_id: int) -> bool:
        for i, event in enumerate(self.events):
            if event['id'] == event_id:
                self.events.pop(i)
                self._save_events()
                return True
        return False

    def export_to_csv(self, filename: str = "schedule_export.csv"):
        if not self.events:
            return False
        keys = self.events[0].keys()
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.events)
        return True

    def get_summary(self, date: Optional[str] = None) -> Dict:
        events = self.view_events(date=date)
        clients = {}
        delivery_types = {}
        for event in events:
            clients[event['client']] = clients.get(event['client'], 0) + 1
            delivery_types[event['delivery_type']] = delivery_types.get(event['delivery_type'], 0) + 1
        return {
            "total_events": len(events),
            "clients": clients,
            "delivery_types": delivery_types,
            "date_range": date or "all time"
        }

    def parse_time_slot(self, time_slot: str) -> Optional[datetime]:
        try:
            start_time = time_slot.split('-')[0].strip()
            today = datetime.now().date()
            event_time = datetime.strptime(f"{today} {start_time}", "%Y-%m-%d %H:%M")
            return event_time
        except Exception:
            return None

    def check_alerts(self):
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        for event in self.events:
            if event['date'] != today or event.get('alert_triggered'):
                continue
            event_time = self.parse_time_slot(event['time_slot'])
            if not event_time:
                continue
            alert_time = event_time - timedelta(minutes=event.get('alert_minutes', 5))
            if now >= alert_time and now < event_time:
                if HAS_PLYER:
                    try:
                        notification.notify(
                            title=f"Event Alert #{event['id']}",
                            message=f"{event['client']} - {event['time_slot']}",
                            timeout=10
                        )
                    except Exception:
                        pass
                if self.alert_callback:
                    self.alert_callback(event)
                event['alert_triggered'] = True
                self._save_events()

    def start_alert_monitor(self, callback=None):
        if self.alert_running:
            return False
        self.alert_callback = callback
        self.alert_running = True
        self.alert_thread = threading.Thread(target=self._alert_loop, daemon=True)
        self.alert_thread.start()
        return True

    def stop_alert_monitor(self):
        if not self.alert_running:
            return False
        self.alert_running = False
        self.alert_callback = None
        return True

    def _alert_loop(self):
        while self.alert_running:
            self.check_alerts()
            time.sleep(30)

    def reset_alerts_for_today(self):
        today = datetime.now().strftime("%Y-%m-%d")
        for event in self.events:
            if event['date'] == today:
                event['alert_triggered'] = False
        self._save_events()
        return True

class ModernGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Schedule Event Logging System")
        self.root.geometry("1200x700")
        
        self.user_mgmt = User()
        self.logger = ScheduleLogger()
        self.current_user = None
        
        self.main_container = None
        self.show_login()
        
    def show_login(self):
        self.clear_window()
        
        login_frame = ctk.CTkFrame(self.root)
        login_frame.pack(expand=True, fill="both", padx=50, pady=50)
        
        ctk.CTkLabel(
            login_frame,
            text="Schedule Event Logging System",
            font=("Arial", 32, "bold")
        ).pack(pady=(40, 10))
        
        ctk.CTkLabel(
            login_frame,
            text="Sign in to continue",
            font=("Arial", 16),
            text_color="gray"
        ).pack(pady=(0, 40))
        
        input_frame = ctk.CTkFrame(login_frame, fg_color="transparent")
        input_frame.pack(pady=20)
        
        ctk.CTkLabel(input_frame, text="Username", font=("Arial", 14)).pack(anchor="w", pady=(10, 5))
        username_entry = ctk.CTkEntry(input_frame, width=300, height=40, font=("Arial", 14))
        username_entry.pack(pady=(0, 15))
        
        ctk.CTkLabel(input_frame, text="Password", font=("Arial", 14)).pack(anchor="w", pady=(10, 5))
        password_entry = ctk.CTkEntry(input_frame, width=300, height=40, show="*", font=("Arial", 14))
        password_entry.pack(pady=(0, 20))
        
        error_label = ctk.CTkLabel(input_frame, text="", text_color="red", font=("Arial", 12))
        error_label.pack()
        
        def attempt_login():
            username = username_entry.get()
            password = password_entry.get()
            
            if self.user_mgmt.authenticate(username, password):
                self.current_user = username
                self.show_dashboard()
            else:
                error_label.configure(text="Invalid username or password")
        
        password_entry.bind("<Return>", lambda e: attempt_login())
        
        ctk.CTkButton(
            input_frame,
            text="Sign In",
            width=300,
            height=40,
            font=("Arial", 16, "bold"),
            command=attempt_login
        ).pack(pady=10)
        
        ctk.CTkLabel(
            login_frame,
            text="Default: admin/admin123 or user/user123",
            font=("Arial", 11),
            text_color="gray"
        ).pack(side="bottom", pady=20)
    
    def show_dashboard(self):
        self.clear_window()
        
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill="both", expand=True)
        
        header = ctk.CTkFrame(self.main_container, height=70, fg_color="#1f538d")
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="Schedule Event Logging",
            font=("Arial", 24, "bold"),
            text_color="white"
        ).pack(side="left", padx=20)
        
        user_info = ctk.CTkFrame(header, fg_color="transparent")
        user_info.pack(side="right", padx=20)
        
        ctk.CTkLabel(
            user_info,
            text=f"Welcome, {self.user_mgmt.get_name(self.current_user)}",
            font=("Arial", 14),
            text_color="white"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            user_info,
            text="Logout",
            width=80,
            height=32,
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self.logout
        ).pack(side="left")
        
        content = ctk.CTkFrame(self.main_container)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        sidebar = ctk.CTkFrame(content, width=200)
        sidebar.pack(side="left", fill="y", padx=(0, 20))
        sidebar.pack_propagate(False)
        
        ctk.CTkLabel(sidebar, text="MENU", font=("Arial", 14, "bold")).pack(pady=(20, 10))
        
        menu_buttons = [
            ("Dashboard", lambda: self.show_content_dashboard()),
            ("View Events", lambda: self.show_content_events()),
            ("Add Event", lambda: self.show_content_add_event()),
            ("Export CSV", self.export_csv),
        ]
        
        if self.user_mgmt.is_admin(self.current_user):
            menu_buttons.append(("Manage Users", lambda: self.show_content_users()))
        
        for text, command in menu_buttons:
            ctk.CTkButton(
                sidebar,
                text=text,
                width=180,
                height=40,
                font=("Arial", 13),
                fg_color="transparent",
                hover_color="#1f538d",
                anchor="w",
                command=command
            ).pack(pady=5, padx=10)
        
        self.content_area = ctk.CTkScrollableFrame(content)
        self.content_area.pack(side="left", fill="both", expand=True)
        
        self.logger.start_alert_monitor(callback=self.on_alert)
        self.show_content_dashboard()
    
    def on_alert(self, event):
        def show_alert():
            messagebox.showinfo(
                f"Event Alert #{event['id']}",
                f"Client: {event['client']}\nTime: {event['time_slot']}\nResource: {event['resource']}"
            )
        self.root.after(0, show_alert)
    
    def show_content_dashboard(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        ctk.CTkLabel(
            self.content_area,
            text="Dashboard",
            font=("Arial", 28, "bold")
        ).pack(anchor="w", pady=(0, 20))
        
        summary = self.logger.get_summary()
        
        stats_frame = ctk.CTkFrame(self.content_area)
        stats_frame.pack(fill="x", pady=10)
        
        stats = [
            ("Total Events", str(summary['total_events']), "#3b82f6"),
            ("Unique Clients", str(len(summary['clients'])), "#10b981"),
            ("Delivery Types", str(len(summary['delivery_types'])), "#f59e0b"),
        ]
        
        for i, (label, value, color) in enumerate(stats):
            stat_card = ctk.CTkFrame(stats_frame, fg_color=color, corner_radius=10)
            stat_card.pack(side="left", expand=True, fill="both", padx=5, pady=5)
            
            ctk.CTkLabel(
                stat_card,
                text=value,
                font=("Arial", 36, "bold"),
                text_color="white"
            ).pack(pady=(20, 0))
            
            ctk.CTkLabel(
                stat_card,
                text=label,
                font=("Arial", 14),
                text_color="white"
            ).pack(pady=(0, 20))
        
        recent_frame = ctk.CTkFrame(self.content_area)
        recent_frame.pack(fill="both", expand=True, pady=(20, 0))
        
        ctk.CTkLabel(
            recent_frame,
            text="Recent Events",
            font=("Arial", 20, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        recent_events = self.logger.view_events()[:5]
        
        for event in recent_events:
            event_card = ctk.CTkFrame(recent_frame, fg_color="#2b2b2b", corner_radius=8)
            event_card.pack(fill="x", padx=20, pady=5)
            
            info_frame = ctk.CTkFrame(event_card, fg_color="transparent")
            info_frame.pack(fill="x", padx=15, pady=10)
            
            ctk.CTkLabel(
                info_frame,
                text=f"#{event['id']} - {event['client']}",
                font=("Arial", 16, "bold")
            ).pack(side="left")
            
            ctk.CTkLabel(
                info_frame,
                text=event['time_slot'],
                font=("Arial", 14),
                text_color="gray"
            ).pack(side="right")
            
            ctk.CTkLabel(
                event_card,
                text=f"Type: {event['delivery_type']} | Resource: {event['resource']} | Assigned: {event['assigned_to']}",
                font=("Arial", 12),
                text_color="gray"
            ).pack(anchor="w", padx=15, pady=(0, 10))
    
    def show_content_events(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        ctk.CTkLabel(
            self.content_area,
            text="All Events",
            font=("Arial", 28, "bold")
        ).pack(anchor="w", pady=(0, 20))
        
        filter_frame = ctk.CTkFrame(self.content_area)
        filter_frame.pack(fill="x", pady=(0, 20))
        
        date_entry = ctk.CTkEntry(filter_frame, placeholder_text="Date (YYYY-MM-DD)", width=200)
        date_entry.pack(side="left", padx=5)
        
        client_entry = ctk.CTkEntry(filter_frame, placeholder_text="Client name", width=200)
        client_entry.pack(side="left", padx=5)
        
        def apply_filter():
            date_val = date_entry.get() if date_entry.get() else None
            client_val = client_entry.get() if client_entry.get() else None
            self.refresh_events_list(events_list_frame, date_val, client_val)
        
        ctk.CTkButton(filter_frame, text="Filter", command=apply_filter, width=100).pack(side="left", padx=5)
        ctk.CTkButton(
            filter_frame,
            text="Clear",
            command=lambda: [date_entry.delete(0, 'end'), client_entry.delete(0, 'end'), apply_filter()],
            width=100,
            fg_color="gray"
        ).pack(side="left", padx=5)
        
        events_list_frame = ctk.CTkFrame(self.content_area)
        events_list_frame.pack(fill="both", expand=True)
        
        self.refresh_events_list(events_list_frame)
    
    def refresh_events_list(self, container, date=None, client=None):
        for widget in container.winfo_children():
            widget.destroy()
        
        events = self.logger.view_events(date=date, client=client)
        
        if not events:
            ctk.CTkLabel(
                container,
                text="No events found",
                font=("Arial", 16),
                text_color="gray"
            ).pack(pady=40)
            return
        
        for event in events:
            event_card = ctk.CTkFrame(container, fg_color="#2b2b2b", corner_radius=8)
            event_card.pack(fill="x", pady=5)
            
            header_frame = ctk.CTkFrame(event_card, fg_color="transparent")
            header_frame.pack(fill="x", padx=15, pady=(10, 5))
            
            ctk.CTkLabel(
                header_frame,
                text=f"#{event['id']} - {event['client']}",
                font=("Arial", 16, "bold")
            ).pack(side="left")
            
            ctk.CTkLabel(
                header_frame,
                text=event['time_slot'],
                font=("Arial", 14),
                text_color="#3b82f6"
            ).pack(side="left", padx=20)
            
            btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            btn_frame.pack(side="right")
            
            ctk.CTkButton(
                btn_frame,
                text="Edit",
                width=60,
                height=28,
                font=("Arial", 12),
                command=lambda e=event: self.show_edit_event(e)
            ).pack(side="left", padx=2)
            
            ctk.CTkButton(
                btn_frame,
                text="Delete",
                width=60,
                height=28,
                font=("Arial", 12),
                fg_color="#ef4444",
                hover_color="#dc2626",
                command=lambda e=event: self.delete_event(e['id'])
            ).pack(side="left", padx=2)
            
            details_frame = ctk.CTkFrame(event_card, fg_color="transparent")
            details_frame.pack(fill="x", padx=15, pady=(0, 10))
            
            details_text = f"Type: {event['delivery_type']} | Resource: {event['resource']} | Assigned: {event['assigned_to']}"
            if event.get('notes'):
                details_text += f"\nNotes: {event['notes']}"
            
            ctk.CTkLabel(
                details_frame,
                text=details_text,
                font=("Arial", 12),
                text_color="gray",
                justify="left"
            ).pack(anchor="w")
    
    def show_content_add_event(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        ctk.CTkLabel(
            self.content_area,
            text="Add New Event",
            font=("Arial", 28, "bold")
        ).pack(anchor="w", pady=(0, 20))
        
        form_frame = ctk.CTkFrame(self.content_area)
        form_frame.pack(fill="both", expand=True)
        
        fields = {}
        
        field_defs = [
            ("Time Slot (HH:MM-HH:MM)", "time_slot", True),
            ("Client Name", "client", True),
            ("Delivery Type", "delivery_type", False),
            ("Resource/Program", "resource", False),
            ("Assigned To", "assigned_to", False),
            ("Alert Minutes Before", "alert_minutes", False, "5"),
        ]
        
        for i, field_def in enumerate(field_defs):
            label_text = field_def[0]
            field_name = field_def[1]
            required = field_def[2]
            default = field_def[3] if len(field_def) > 3 else ""
            
            ctk.CTkLabel(
                form_frame,
                text=label_text + (" *" if required else ""),
                font=("Arial", 14)
            ).pack(anchor="w", padx=20, pady=(15, 5))
            
            entry = ctk.CTkEntry(form_frame, height=40, font=("Arial", 13))
            entry.pack(fill="x", padx=20)
            if default:
                entry.insert(0, default)
            fields[field_name] = entry
        
        ctk.CTkLabel(
            form_frame,
            text="Notes",
            font=("Arial", 14)
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        notes_entry = ctk.CTkTextbox(form_frame, height=100, font=("Arial", 13))
        notes_entry.pack(fill="x", padx=20)
        fields['notes'] = notes_entry
        
        def save_event():
            try:
                alert_min = int(fields['alert_minutes'].get())
            except ValueError:
                alert_min = 5
            
            self.logger.add_event(
                time_slot=fields['time_slot'].get(),
                client=fields['client'].get(),
                delivery_type=fields['delivery_type'].get(),
                resource=fields['resource'].get(),
                assigned_to=fields['assigned_to'].get(),
                notes=notes_entry.get("1.0", "end-1c"),
                alert_minutes=alert_min
            )
            messagebox.showinfo("Success", "Event created successfully!")
            self.show_content_events()
        
        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="Create Event",
            width=150,
            height=40,
            font=("Arial", 14, "bold"),
            command=save_event
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=150,
            height=40,
            font=("Arial", 14),
            fg_color="gray",
            command=self.show_content_events
        ).pack(side="left", padx=5)
    
    def show_edit_event(self, event):
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        ctk.CTkLabel(
            self.content_area,
            text=f"Edit Event #{event['id']}",
            font=("Arial", 28, "bold")
        ).pack(anchor="w", pady=(0, 20))
        
        form_frame = ctk.CTkFrame(self.content_area)
        form_frame.pack(fill="both", expand=True)
        
        fields = {}
        
        field_defs = [
            ("Time Slot", "time_slot", event.get('time_slot', '')),
            ("Client Name", "client", event.get('client', '')),
            ("Delivery Type", "delivery_type", event.get('delivery_type', '')),
            ("Resource/Program", "resource", event.get('resource', '')),
            ("Assigned To", "assigned_to", event.get('assigned_to', '')),
            ("Alert Minutes", "alert_minutes", str(event.get('alert_minutes', 5))),
        ]
        
        for label_text, field_name, default_val in field_defs:
            ctk.CTkLabel(
                form_frame,
                text=label_text,
                font=("Arial", 14)
            ).pack(anchor="w", padx=20, pady=(15, 5))
            
            entry = ctk.CTkEntry(form_frame, height=40, font=("Arial", 13))
            entry.pack(fill="x", padx=20)
            entry.insert(0, default_val)
            fields[field_name] = entry
        
        ctk.CTkLabel(
            form_frame,
            text="Notes",
            font=("Arial", 14)
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        notes_entry = ctk.CTkTextbox(form_frame, height=100, font=("Arial", 13))
        notes_entry.pack(fill="x", padx=20)
        notes_entry.insert("1.0", event.get('notes', ''))
        
        def update_event():
            try:
                alert_min = int(fields['alert_minutes'].get())
            except ValueError:
                alert_min = 5
            
            self.logger.update_event(
                event['id'],
                time_slot=fields['time_slot'].get(),
                client=fields['client'].get(),
                delivery_type=fields['delivery_type'].get(),
                resource=fields['resource'].get(),
                assigned_to=fields['assigned_to'].get(),
                notes=notes_entry.get("1.0", "end-1c"),
                alert_minutes=alert_min
            )
            messagebox.showinfo("Success", "Event updated successfully!")
            self.show_content_events()
        
        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="Update Event",
            width=150,
            height=40,
            font=("Arial", 14, "bold"),
            command=update_event
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=150,
            height=40,
            font=("Arial", 14),
            fg_color="gray",
            command=self.show_content_events
        ).pack(side="left", padx=5)
    
    def delete_event(self, event_id):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this event?"):
            self.logger.delete_event(event_id)
            self.show_content_events()
    
    def show_content_users(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        ctk.CTkLabel(
            self.content_area,
            text="Manage Users",
            font=("Arial", 28, "bold")
        ).pack(anchor="w", pady=(0, 20))
        
        add_frame = ctk.CTkFrame(self.content_area)
        add_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(add_frame, text="Add New User", font=("Arial", 18, "bold")).pack(anchor="w", padx=20, pady=(15, 10))
        
        fields = {}
        for field_name, label_text in [("username", "Username"), ("name", "Full Name"), ("password", "Password")]:
            ctk.CTkLabel(add_frame, text=label_text, font=("Arial", 13)).pack(anchor="w", padx=20, pady=(10, 2))
            entry = ctk.CTkEntry(add_frame, height=35)
            entry.pack(fill="x", padx=20, pady=(0, 5))
            fields[field_name] = entry
        
        ctk.CTkLabel(add_frame, text="Role", font=("Arial", 13)).pack(anchor="w", padx=20, pady=(10, 2))
        role_var = ctk.StringVar(value="user")
        role_menu = ctk.CTkOptionMenu(add_frame, values=["user", "admin"], variable=role_var, height=35)
        role_menu.pack(fill="x", padx=20, pady=(0, 15))
        
        def add_user():
            username = fields['username'].get()
            name = fields['name'].get()
            password = fields['password'].get()
            role = role_var.get()
            
            if not username or not name or not password:
                messagebox.showerror("Error", "All fields are required")
                return
            
            if self.user_mgmt.add_user(username, password, role, name):
                messagebox.showinfo("Success", "User created successfully!")
                self.show_content_users()
            else:
                messagebox.showerror("Error", "Username already exists")
        
        ctk.CTkButton(
            add_frame,
            text="Create User",
            height=40,
            font=("Arial", 14, "bold"),
            command=add_user
        ).pack(padx=20, pady=(0, 15))
        
        users_frame = ctk.CTkFrame(self.content_area)
        users_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(users_frame, text="Existing Users", font=("Arial", 18, "bold")).pack(anchor="w", padx=20, pady=(15, 10))
        
        for username, details in self.user_mgmt.list_users().items():
            user_card = ctk.CTkFrame(users_frame, fg_color="#2b2b2b", corner_radius=8)
            user_card.pack(fill="x", padx=20, pady=5)
            
            info_frame = ctk.CTkFrame(user_card, fg_color="transparent")
            info_frame.pack(fill="x", padx=15, pady=10)
            
            ctk.CTkLabel(
                info_frame,
                text=f"{details['name']} (@{username})",
                font=("Arial", 15, "bold")
            ).pack(side="left")
            
            role_badge_color = "#3b82f6" if details['role'] == "admin" else "#6b7280"
            role_label = ctk.CTkLabel(
                info_frame,
                text=details['role'].upper(),
                font=("Arial", 11, "bold"),
                fg_color=role_badge_color,
                corner_radius=6,
                width=60,
                height=24
            )
            role_label.pack(side="right")
    
    def export_csv(self):
        filename = f"schedule_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        if self.logger.export_to_csv(filename):
            messagebox.showinfo("Success", f"Events exported to {filename}")
        else:
            messagebox.showwarning("Warning", "No events to export")
    
    def logout(self):
        self.logger.stop_alert_monitor()
        self.current_user = None
        self.show_login()
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ModernGUI()
    app.run()