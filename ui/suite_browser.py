import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import json
import threading

class SuiteBrowser(ctk.CTkFrame):
    def __init__(self, parent, db, runner, on_back=None):
        super().__init__(parent, fg_color="transparent")
        
        self.db = db
        self.runner = runner  # To execute scenarios
        self.parent = parent
        self.on_back = on_back
        
        # Seçili Suite
        self.current_suite_id = None
        self.current_suite_name = ""
        self.current_suite_scenarios = [] # List of scenario IDs
        
        # Düzen
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Left Panel (Suites List)
        self.left_panel = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nswe")
        
        if self.on_back:
            btn_back = ctk.CTkButton(self.left_panel, text="⬅ Ana Menü", fg_color="#0D3B7A", width=80, height=24, command=self.on_back)
            btn_back.pack(pady=(10, 5), padx=10, anchor="w")

        lbl_left = ctk.CTkLabel(self.left_panel, text="Kayıtlı Suitler", font=("Arial", 16, "bold"))
        lbl_left.pack(pady=10)
        
        btn_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        btn_new = ctk.CTkButton(btn_frame, text="✚ Yeni", width=60, command=self.create_suite, fg_color="#27AE60", hover_color="#2ECC71")
        btn_new.pack(side="left", padx=2)
        
        btn_import = ctk.CTkButton(btn_frame, text="📥 İçe Aktar", width=80, command=self.import_suite, fg_color="#F39C12", hover_color="#E67E22")
        btn_import.pack(side="left", padx=2)
        
        self.suite_listbox = tk.Listbox(self.left_panel, bg="#1E1E1E", fg="white", font=("Arial", 12), selectbackground="#3498DB")
        self.suite_listbox.pack(expand=True, fill="both", padx=10, pady=5)
        self.suite_listbox.bind("<<ListboxSelect>>", self.on_suite_select)
        
        # Right Panel (Suite Details)
        self.right_panel = ctk.CTkFrame(self, corner_radius=0)
        self.right_panel.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)
        
        self.lbl_suite_title = ctk.CTkLabel(self.right_panel, text="Bir Suit Seçin", font=("Arial", 18, "bold"))
        self.lbl_suite_title.pack(pady=10)
        
        hdr_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=5)
        
        self.btn_run = ctk.CTkButton(hdr_frame, text="▶ Süiti Çalıştır", command=self.run_suite, fg_color="green", state="disabled")
        self.btn_run.pack(side="left", padx=5)
        
        self.btn_stats = ctk.CTkButton(hdr_frame, text="📊 İstatistikler", command=self.show_statistics, state="disabled")
        self.btn_stats.pack(side="left", padx=5)
        
        self.btn_add_scenario = ctk.CTkButton(hdr_frame, text="➕ Senaryo Ekle", command=self.add_scenario_to_suite, state="disabled")
        self.btn_add_scenario.pack(side="left", padx=5)
        
        self.btn_export = ctk.CTkButton(hdr_frame, text="📤 Dışa Aktar", command=self.export_suite, state="disabled")
        self.btn_export.pack(side="right", padx=5)
        
        self.btn_del = ctk.CTkButton(hdr_frame, text="🗑️ Sil", width=60, command=self.delete_suite, fg_color="red", state="disabled")
        self.btn_del.pack(side="right", padx=5)
        
        self.scenario_list_frame = ctk.CTkScrollableFrame(self.right_panel, label_text="Ekli Senaryolar (Yukarıdan aşağıya sırayla çalışır)")
        self.scenario_list_frame.pack(expand=True, fill="both", pady=10)
        
        self.refresh_suites()
        
    def refresh_suites(self):
        self.suite_listbox.delete(0, tk.END)
        self.suites = self.db.list_suites() # [(id, name, date), ...]
        for s in self.suites:
            # s[1] is name
            self.suite_listbox.insert(tk.END, f"{s[1]}")
            
    def on_suite_select(self, event):
        sel = self.suite_listbox.curselection()
        if not sel: return
        
        idx = sel[0]
        s_id = self.suites[idx][0]
        self.load_suite(s_id)
        
    def load_suite(self, s_id):
        suite_data = self.db.load_suite_by_id(s_id)
        if not suite_data: return
        
        self.current_suite_id = suite_data["id"]
        self.current_suite_name = suite_data["name"]
        
        # The payload should be a list of scenario IDs or dicts {"id": X, "name": Y}
        # Let's assume list of scenario IDs dicts: [{"id": 1, "name": "Login"}, ...]
        payload = suite_data.get("payload", [])
        if isinstance(payload, list):
            self.current_suite_scenarios = payload
        else:
            self.current_suite_scenarios = []
            
        self.lbl_suite_title.configure(text=f"Suit: {self.current_suite_name}")
        self.btn_run.configure(state="normal")
        self.btn_stats.configure(state="normal")
        self.btn_add_scenario.configure(state="normal")
        self.btn_export.configure(state="normal")
        self.btn_del.configure(state="normal")
        
        self.render_scenario_list()
        
    def render_scenario_list(self):
        for w in self.scenario_list_frame.winfo_children():
            w.destroy()
            
        for i, sc in enumerate(self.current_suite_scenarios):
            frame = ctk.CTkFrame(self.scenario_list_frame, height=40)
            frame.pack(pady=2, fill="x")
            
            lbl = ctk.CTkLabel(frame, text=f"{sc.get('name', 'Bilinmiyor')}", anchor="w", font=("Arial", 13, "bold"))
            lbl.pack(side="left", padx=10, fill="x", expand=True)
            
            # Index Entry for ordering
            idx_entry = ctk.CTkEntry(frame, width=40, font=("Arial", 12))
            idx_entry.insert(0, str(i + 1))
            idx_entry.pack(side="left", padx=5)
            
            btn_move = ctk.CTkButton(frame, text="Taşı", width=40, command=lambda idx=i, ent=idx_entry: self.move_sc_to(idx, ent.get()))
            btn_move.pack(side="left", padx=2)
            
            btn_rm = ctk.CTkButton(frame, text="X", width=30, fg_color="red", command=lambda idx=i: self.remove_sc(idx))
            btn_rm.pack(side="right", padx=5)
            
    def move_sc_to(self, old_idx, new_idx_str):
        try:
            new_idx = int(new_idx_str) - 1
        except:
            messagebox.showwarning("Uyarı", "Geçerli bir sıra numarası girin.", parent=self.winfo_toplevel())
            return
            
        if new_idx < 0: new_idx = 0
        if new_idx >= len(self.current_suite_scenarios): new_idx = len(self.current_suite_scenarios) - 1
        
        if old_idx != new_idx:
            item = self.current_suite_scenarios.pop(old_idx)
            self.current_suite_scenarios.insert(new_idx, item)
            self.save_current_suite()
            self.render_scenario_list()

    def remove_sc(self, idx):
        self.current_suite_scenarios.pop(idx)
        self.save_current_suite()
        self.render_scenario_list()
        
    def show_statistics(self):
        """Seçili süitin çalışma geçmişini gösterir."""
        if not self.current_suite_id: return
        
        history = self.db.get_suite_history(self.current_suite_id)
        
        top = ctk.CTkToplevel(self.winfo_toplevel())
        top.title(f"İstatistikler: {self.current_suite_name}")
        top.geometry("650x400")
        top.transient(self.winfo_toplevel())
        top.grab_set()
        
        if not history:
            ctk.CTkLabel(top, text="Henüz bu süit için çalışma geçmişi bulunmuyor.", font=("Arial", 14)).pack(pady=20)
            return
            
        scroll = ctk.CTkScrollableFrame(top)
        scroll.pack(expand=True, fill="both", padx=10, pady=10)
        
        headers = ["Başlangıç", "Bitiş", "Süre", "Toplam", "Başarılı", "Başarısız"]
        hdr_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=2)
        
        # Adjust column weights
        for i in range(6):
            hdr_frame.columnconfigure(i, weight=1)
            
        for i, h in enumerate(headers):
            ctk.CTkLabel(hdr_frame, text=h, font=("Arial", 13, "bold")).grid(row=0, column=i, padx=5, sticky="ew")
            
        from datetime import datetime
            
        for record in history:
            row_frame = ctk.CTkFrame(scroll)
            row_frame.pack(fill="x", pady=2)
            for i in range(6):
                row_frame.columnconfigure(i, weight=1)
                
            # Hesapla Süre (Duration)
            dur_str = "-"
            if record[1] and record[2]:
                try:
                    s_dt = datetime.strptime(record[1], '%Y-%m-%d %H:%M:%S')
                    e_dt = datetime.strptime(record[2], '%Y-%m-%d %H:%M:%S')
                    sec = (e_dt - s_dt).total_seconds()
                    mins = int(sec // 60)
                    secs = int(sec % 60)
                    dur_str = f"{mins}d {secs}s" if mins > 0 else f"{secs}s"
                except:
                    pass

            # record: 0:id, 1:start, 2:end, 3:total, 4:success, 5:fail
            vals = [
                record[1].split()[1] if record[1] else "-",  # Sadece saati göster veya isteğe bağlı tam tarih
                record[2].split()[1] if record[2] else "-",
                dur_str,
                str(record[3]),
                str(record[4]),
                str(record[5])
            ]
            
            for col_idx, val in enumerate(vals):
                color = None
                if col_idx == 4 and record[4] > 0: color = "#2ecc71" # Green
                elif col_idx == 5 and record[5] > 0: color = "#e74c3c" # Red
                
                ctk.CTkLabel(row_frame, text=val, text_color=color).grid(row=0, column=col_idx, padx=5, sticky="ew")
        
    def save_current_suite(self):
        if self.current_suite_id:
            self.db.save_suite(self.current_suite_name, self.current_suite_scenarios, self.current_suite_id)
            
    def create_suite(self):
        name = simpledialog.askstring("Yeni Suit", "Test Suit Adı:", parent=self.winfo_toplevel())
        if name:
            s_id = self.db.save_suite(name, [])
            self.refresh_suites()
            self.load_suite(s_id)
            
    def delete_suite(self):
        if self.current_suite_id:
            if messagebox.askyesno("Onay", f"'{self.current_suite_name}' tamamen silinecek. Onaylıyor musunuz?", parent=self.winfo_toplevel()):
                self.db.delete_suite(self.current_suite_id)
                self.current_suite_id = None
                self.current_suite_scenarios = []
                self.lbl_suite_title.configure(text="Bir Suit Seçin")
                self.btn_run.configure(state="disabled")
                self.btn_add_scenario.configure(state="disabled")
                self.btn_export.configure(state="disabled")
                self.btn_del.configure(state="disabled")
                self.render_scenario_list()
                self.refresh_suites()

    def add_scenario_to_suite(self):
        """Mevcut senaryolardan seçip suite'e ekler."""
        all_scenarios = self.db.list_scenarios()
        if not all_scenarios:
            messagebox.showinfo("Bilgi", "Veritabanında hiç senaryo bulunamadı.", parent=self.winfo_toplevel())
            return
            
        # Basit bir Toplevel ile seçtir
        top = ctk.CTkToplevel(self)
        top.title("Senaryo Ekle")
        top.geometry("400x400")
        top.transient(self)
        top.grab_set()
        
        lb = tk.Listbox(top, bg="#2b2b2b", fg="white", font=("Arial", 12))
        lb.pack(expand=True, fill="both", padx=10, pady=10)
        
        for sc in all_scenarios:
            lb.insert(tk.END, f"{sc[0]} - {sc[1]}") # ID - Name
            
        def on_add():
            sel = lb.curselection()
            if not sel: return
            idx = sel[0]
            sc_id = all_scenarios[idx][0]
            sc_name = all_scenarios[idx][1]
            
            self.current_suite_scenarios.append({"id": sc_id, "name": sc_name})
            self.save_current_suite()
            self.render_scenario_list()
            top.destroy()
            
        btn_ok = ctk.CTkButton(top, text="Ekle", command=on_add)
        btn_ok.pack(pady=10)
        
    def export_suite(self):
        """Süiti ve içindeki senaryoları JSON'a dışa aktarır (v168.0: Asset Encoding)."""
        if not self.current_suite_id: return
        
        # Gather all full scenario payloads
        export_data = {
            "suite_name": self.current_suite_name,
            "scenarios": [],
            "_embedded_assets": {}
        }
        
        # Asset Repository
        import base64
        import os
        all_assets = self.db.list_assets() # (id, name, created, data)
        asset_map = {name: data for _, name, _, data in all_assets if data}
        used_asset_names = set()

        for sc in self.current_suite_scenarios:
            sc_id = sc["id"]
            # load scenario from DB completely
            result = self.db._get_connection().cursor().execute("SELECT payload FROM scenarios WHERE id=?", (sc_id,)).fetchone()
            if result:
                full_payload = json.loads(result[0])
                export_data["scenarios"].append(full_payload)
                
                # Resim Taraması 
                for action_dict in full_payload.get("actions", []):
                    params = action_dict.get("params", {})
                    a_type = action_dict.get("type", "")
                    
                    # 1) Normal Tıklama ve Görsel Doğrulama (Assert_Exists, Click, Click Offset)
                    target = params.get("target")
                    if target and isinstance(target, str):
                        asset_name = os.path.basename(target)
                        if asset_name in asset_map:
                            used_asset_names.add(asset_name)

                    # 2) Popup Kontrolcüleri Taraması
                    if a_type == "POPUP_CHECK":
                        triggers = params.get("triggers", [])
                        for trig in triggers:
                            if trig.get("type") == "image":
                                pm_name = trig.get("value")
                                if pm_name and pm_name in asset_map:
                                    used_asset_names.add(pm_name)
                                    
        # Embed Found Assets Base64 strings
        for name in used_asset_names:
            export_data["_embedded_assets"][name] = base64.b64encode(asset_map[name]).decode('utf-8')
                
        if not export_data["scenarios"]:
            messagebox.showwarning("Uyarı", "Süit içerisinde dışa aktarılacak senaryo bulunamadı veya silinmiş.")
            return
            
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")], initialfile=f"{self.current_suite_name}.json")
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    # check if the dictionary compiles properly
                    json.dumps(export_data) 
                    json.dump(export_data, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("Başarılı", "Süit ve içerdiği senaryolar (görsel bağımlılıklarıyla beraber) dışa aktarıldı.")
            except Exception as e:
                messagebox.showerror("Hata", f"Dışa aktarılamadı: {e}")

    def import_suite(self):
        """JSON dosyasından Süiti, senaryoları ve Asset'leri içe aktarır (v168.0)."""
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not filepath: return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            suite_name = data.get("suite_name", "İçe Aktarılan Suit")
            scenarios = data.get("scenarios", [])
            embedded_assets = data.get("_embedded_assets", {})
            
            if not scenarios:
                messagebox.showwarning("Uyarı", "Geçersiz veya boş süit dosyası.")
                return
                
            # 1) Resimleri ve Varlıkları Kurtar (Asset Deserialization)
            import base64
            import os
            from core.config import ASSETS_DIR
            
            try: os.makedirs(ASSETS_DIR, exist_ok=True)
            except: pass
            
            for name, b64_data in embedded_assets.items():
                try:
                    binary = base64.b64decode(b64_data)
                    tmp_path = os.path.join(ASSETS_DIR, f"imported_{name}")
                    if not os.path.splitext(tmp_path)[1]:
                         tmp_path += ".png"
                         
                    with open(tmp_path, 'wb') as f_out:
                         f_out.write(binary)
                    
                    self.db.save_asset(name, tmp_path)
                except Exception as e:
                    self.logger.warning(f"Süit Asset import hatası ({name}): {e}")
                    
            # 2) Süiti Yarat
            s_id = self.db.save_suite(suite_name, [])
            
            suite_scenarios = []
            from core.scenario import Scenario
            
            for sc_dict in scenarios:
                # v168.0: Dosya yolunu temizle (Sanitization)
                for action_dict in sc_dict.get("actions", []):
                    params = action_dict.get("params", {})
                    target = params.get("target")
                    if target and isinstance(target, str):
                        if os.path.sep in target or "/" in target:
                            clean_name = os.path.basename(target)
                            params["target"] = clean_name
                            desc = action_dict.get("description", "")
                            if desc and target in desc:
                                action_dict["description"] = desc.replace(target, clean_name)

                # Yeni ID ile kaydet (Force new insert for scenario and its parameters)
                sc = Scenario.from_dict(sc_dict)
                sc.id = None 
                new_sc_id = self.db.save_scenario(sc)
                if new_sc_id:
                    suite_scenarios.append({"id": new_sc_id, "name": sc.name})
                    
            # Update Suite with new IDs
            self.db.save_suite(suite_name, suite_scenarios, s_id)
            
            self.refresh_suites()
            self.load_suite(s_id)
            messagebox.showinfo("Başarılı", f"Süit başarıyla içe aktarıldı ({len(suite_scenarios)} senaryo).")
            
        except Exception as e:
            messagebox.showerror("Hata", f"İçe aktarılamadı: {e}")

    def run_suite(self):
        if not self.current_suite_scenarios: return
        
        # Minimize the window while running so it doesn't block vision
        if self.parent:
            self.parent.iconify()
            self.parent.overlay.show() # Display the red border overlay
            
        def suite_thread():
            try:
                import time
                from datetime import datetime
                
                start_time = datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S')
                success_count = 0
                fail_count = 0
                total_scenarios = len(self.current_suite_scenarios)
                
                for i, sc in enumerate(self.current_suite_scenarios):
                    sc_id = sc["id"]
                    sc_obj = self.db.load_scenario_by_id(sc_id)
                    if sc_obj:
                        msg = f"SÜİT: {self.current_suite_name} ({i+1}/{total_scenarios}) - {sc_obj.name}"
                        print(msg)
                        
                        # Runner thread-based çalıştığı için bitmesini beklemeliyiz
                        evt = threading.Event()
                        scenario_success = {"status": False}
                        
                        def _on_finish(success, err):
                            scenario_success["status"] = success
                            evt.set()
                            
                        self.runner.run_scenario(sc_obj, on_finish=_on_finish)
                        evt.wait() # Senaryonun bitmesini bekle
                        
                        if scenario_success["status"]:
                            success_count += 1
                        else:
                            fail_count += 1
                    else:
                        print(f"Senaryo bulunamadı (ID: {sc_id})")
                        fail_count += 1
                    
                    time.sleep(1) # Gap between scenarios
                    
                end_time = datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S')
                
                # Veritabanına kaydet
                self.db.save_suite_history(self.current_suite_id, start_time, end_time, total_scenarios, success_count, fail_count)
                    
                print(f"Test Süiti Tamamlandı! ({success_count} Başarılı, {fail_count} Başarısız)")
                
                # Geri Getir ve Overlay Kapat (Main Thread)
                def restore():
                    if self.parent:
                        self.parent.overlay.hide()
                        self.parent.deiconify()
                    
                    # Show completion message securely on UI thread
                    messagebox.showinfo("Suite Bitti", f"Test Süiti Tamamlandı!\nBaşarılı: {success_count}\nBaşarısız: {fail_count}")

                self.after(2000, restore)
            except Exception as e:
                import traceback
                print(f"SUITE THREAD ERROR: {e}")
                print(traceback.format_exc())
                
                def restore_error():
                    if self.parent:
                        self.parent.overlay.hide()
                        self.parent.deiconify()
                    messagebox.showerror("Suite Hatası", f"Süit çalıştırılırken kritik bir hata oluştu:\n{e}")
                self.after(100, restore_error)

        threading.Thread(target=suite_thread, daemon=True).start()
