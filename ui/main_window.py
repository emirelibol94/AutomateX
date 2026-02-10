import customtkinter as ctk
import threading
import logging
from tkinter import filedialog, messagebox, simpledialog

from core.scenario import Scenario, Action
from core.runner import AutomationRunner
from drivers.desktop_driver import DesktopDriver
from ui.snip_tool import SnipTool
from ui.overlay import ExecutionOverlay
from ui.inspector_overlay import InspectorOverlay # v80
from ui.recorder import Recorder
from core.database import DatabaseManager
import json
import os
import datetime
from core.config import APP_VERSION

ctk.set_appearance_mode("Light") # Kurumsal Tema (v38)
ctk.set_default_color_theme("blue")

class VariableDefinitionDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_save, initial_variables=None):
        super().__init__(parent)
        self.title("Senaryo Değişkenleri")
        self.geometry("500x400")
        self.on_save = on_save
        self.parent = parent
        
        # Modal yap
        self.transient(parent)
        self.grab_set()
        
        # Başlık for v167.17
        ctk.CTkLabel(self, text="Küresel Değişkenler", font=("Arial", 16, "bold")).pack(pady=10)
        ctk.CTkLabel(self, text="Senaryo genelinde kullanılacak değerleri tanımlayın.", text_color="gray").pack(pady=(0, 10))
        
        # Scrollable Frame for Rows
        self.scroll_frame = ctk.CTkScrollableFrame(self, height=250)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.rows = []
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(btn_frame, text="+ Değişken Ekle", command=self.add_row, fg_color="#27AE60").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Kaydet", command=self.save, fg_color="#2980B9").pack(side="right", padx=5)
        
        # Load existing variables (v167.17)
        if initial_variables:
            for name, value in initial_variables.items():
                vtype = "int" if isinstance(value, int) else "str"
                self.add_row(name, vtype, str(value))
        else:
            self.add_row()

    def add_row(self, name="", vtype="str", value=""):
        row_frame = ctk.CTkFrame(self.scroll_frame)
        row_frame.pack(fill="x", pady=2)
        
        # Name
        ctk.CTkLabel(row_frame, text="Ad:").pack(side="left", padx=2)
        ent_name = ctk.CTkEntry(row_frame, width=120, placeholder_text="orn_sayi")
        ent_name.insert(0, name)
        ent_name.pack(side="left", padx=2)
        
        # Type
        type_var = ctk.StringVar(value=vtype)
        cmb_type = ctk.CTkComboBox(row_frame, values=["str", "int"], variable=type_var, width=70)
        cmb_type.pack(side="left", padx=2)
        
        # Value
        ctk.CTkLabel(row_frame, text="Değer:").pack(side="left", padx=2)
        ent_val = ctk.CTkEntry(row_frame, width=120, placeholder_text="Değer")
        ent_val.insert(0, value)
        ent_val.pack(side="left", padx=2)
        
        # Delete
        btn_del = ctk.CTkButton(row_frame, text="X", width=30, fg_color="#C0392B", command=lambda: self.delete_row(row_frame))
        btn_del.pack(side="right", padx=2)
        
        self.rows.append({
            "frame": row_frame,
            "ent_name": ent_name,
            "type_var": type_var,
            "ent_val": ent_val
        })

    def delete_row(self, frame):
        frame.destroy()
        # Listeden de sil
        self.rows = [r for r in self.rows if r["frame"].winfo_exists()]

    def save(self):
        variables = {}
        for r in self.rows:
            if not r["frame"].winfo_exists(): continue
            
            name = r["ent_name"].get().strip()
            vtype = r["type_var"].get()
            val_str = r["ent_val"].get()
            
            if not name: continue
            
            # Value conversion
            value = val_str
            if vtype == "int":
                try: value = int(val_str)
                except: 
                    messagebox.showerror("Hata", f"'{name}' için geçersiz sayısal değer: {val_str}")
                    return

            variables[name] = value
            
        # Boş olsa bile kaydet (silme desteği)
        self.on_save(variables)
        self.destroy()

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        # self.title(f"Desktop Otomasyon - {APP_VERSION}") # v65: Başlık dinamik olarak güncelleniyor
        self.geometry("1000x700")

        # Çekirdek Bileşenler
        self.db = DatabaseManager()
        self.driver = DesktopDriver(db=self.db) # v63: DB'yi sürücüye ilet
        self.runner = AutomationRunner(self.driver, db=self.db)
        self.overlay = ExecutionOverlay()
        
        self.current_scenario_id = None
        self.recorder = None
        self.drag_index = None # Sürükle & Bırak için
        self.current_scenario = Scenario(name="Yeni Senaryo", description="")
        
        # v64: Tekil Pencereler (Singleton)
        self.asset_browser_win = None
        self.scenario_browser_win = None

        # Düzen Kurulumu
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # v65: İki Ana Görünüm
        self.welcome_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.editor_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        # Editör Izgarasını Yapılandır (Dahili)
        self.editor_frame.grid_columnconfigure(1, weight=1)
        self.editor_frame.grid_rowconfigure(0, weight=1)

        # Görünümleri Başlat
        self._init_welcome_screen()
        self._setup_editor_panels()
        
        # Karşılama Ekranında Başla
        self.show_welcome()
        
        # Loglamayı Kur (Bir Kere)
        self._setup_logging()

    def _init_welcome_screen(self):
        """v65: Karşılama Ekranı"""
        self.welcome_frame.grid_columnconfigure(0, weight=1)
        self.welcome_frame.grid_rowconfigure(0, weight=1)
        self.welcome_frame.grid_rowconfigure(1, weight=0) # Telif Hakkı (Copyright)
        
        center_frame = ctk.CTkFrame(self.welcome_frame, fg_color="transparent")
        center_frame.grid(row=0, column=0)
        
        lbl_title = ctk.CTkLabel(center_frame, text="AutomateX", font=("Arial", 32, "bold"))
        lbl_title.pack(pady=(0, 40))
        
        btn_new = ctk.CTkButton(center_frame, text="📄 Yeni Senaryo", font=("Arial", 16), width=200, height=50, command=self.start_new_scenario)
        btn_new.pack(pady=10)
        
        btn_load = ctk.CTkButton(center_frame, text="📂 Senaryo Yükle", font=("Arial", 16), width=200, height=50, command=self.show_scenarios_welcome)
        btn_load.pack(pady=10)

        lbl_ver = ctk.CTkLabel(self.welcome_frame, text=f"Sürüm: {APP_VERSION}", text_color="gray")
        lbl_ver.grid(row=1, column=0, pady=20)

    def _setup_editor_panels(self):
        """Editör panellerini editor_frame içine kurar."""
        self._setup_left_panel()
        self._setup_main_panel()
        self._setup_right_panel()

    def show_welcome(self):
        self.editor_frame.grid_forget()
        self.welcome_frame.grid(row=0, column=0, sticky="nsew")
        self.title("AutomateX - Hoşgeldiniz")

    def show_editor(self):
        self.welcome_frame.grid_forget()
        self.editor_frame.grid(row=0, column=0, sticky="nsew")
        self.title(f"AutomateX - {self.current_scenario.name}")

    def start_new_scenario(self):
        # v70: Kesin Senaryo Bağlamı - İsim iste ve hemen kaydet
        name = simpledialog.askstring("Yeni Senaryo", "Senaryo Adı:")
        if not name or not name.strip():
            return # İptal edildi
            
        self.current_scenario = Scenario(name=name.strip(), description="")
        
        # İlk kaydı oluştur (ID almak için)
        scenario_id = self.db.save_scenario(self.current_scenario)
        if scenario_id:
            self.current_scenario_id = scenario_id # Eski takip yöntemi (başka yerde kullanılıyorsa)
            
        self.refresh_step_list()
        self.show_editor()

    def show_scenarios_welcome(self):
        # Karşılama ekranından yükleme yapınca direkt editöre geçecek geri çağırım (callback)
        if self.scenario_browser_win and self.scenario_browser_win.winfo_exists():
            self.scenario_browser_win.focus_force()
            self.scenario_browser_win.lift()
            return
        
        def on_load(scenario):
            self.current_scenario = scenario
            self.refresh_step_list()
            messagebox.showinfo("Yüklendi", f"'{scenario.name}' senaryosu yüklendi.")
            self.show_editor()

        self.scenario_browser_win = DatabaseBrowser(self, self.db, on_load)
        self.scenario_browser_win.grab_set()

    def go_back_to_welcome(self):
        # v160.2: Auto-save devrede olduğu için onay sormadan dönüyoruz
        # Kullanıcı isteği: "zaten artık auto save yapabiliyoruz"
        if self.current_scenario.id:
             self.db.save_scenario(self.current_scenario)
             
        self.show_welcome()


    def _setup_left_panel(self):
        """Aksiyon Ekleme Paneli"""
        # Mavisi Kenar Çubuğu (Scrollable yapıldı v52)
        # GÜNCELLEME (v54): Genişlik 260px yapıldı (Check State yazısı sığsın diye)
        # v65: Ebeveyn self.editor_frame olarak değiştirildi
        self.sidebar_frame = ctk.CTkScrollableFrame(self.editor_frame, width=260, corner_radius=0, fg_color="#194E91")
        self.sidebar_frame.grid(row=0, column=0, sticky="nswe")
        
        # v65: Geri Dön Butonu
        btn_back = ctk.CTkButton(self.sidebar_frame, text="⬅ Ana Menü", fg_color="#0D3B7A", width=80, height=24, command=self.go_back_to_welcome)
        btn_back.pack(pady=(10, 5), padx=10, anchor="w")
        
        self.lbl_toolbox = ctk.CTkLabel(self.sidebar_frame, text="Aksiyonlar", font=("Arial", 16, "bold"), text_color="white")
        self.lbl_toolbox.pack(pady=10, padx=10)

        # Akıllı Aksiyonlar (Smart Actions)
        self.lbl_smart = ctk.CTkLabel(self.sidebar_frame, text="Smart Recorder", text_color="white")
        self.lbl_smart.pack(pady=(10, 0))
        
        self.btn_smart_rec = ctk.CTkButton(self.sidebar_frame, text="🔴 Kaydı Başlat", command=self.toggle_smart_recording, fg_color="#E91E63", hover_color="#C2185B")
        self.btn_smart_rec.pack(pady=5, padx=10, fill="x")

        # Temel Aksiyonlar (v85.2 Refactor)
        self.lbl_basic = ctk.CTkLabel(self.sidebar_frame, text="Temel Aksiyonlar", text_color="white")
        self.lbl_basic.pack(pady=(15, 0))

        actions = [
            ("🖱️ Sol Tıkla (Selector)", lambda: self.start_inspector("left")),
            ("🖱️ Sağ Tıkla (Selector)", lambda: self.start_inspector("right")),
            ("🖱️ Çift Tıkla (Selector)", lambda: self.start_inspector("double")),
            ("🖱️ Sol Tıkla (Görsel)", self.add_click_action),
            ("🖱️ Sağ Tıkla (Görsel)", self.add_right_click_action),
            ("🖱️ Çift Tıkla (Görsel)", self.add_double_click_action),
            ("✍️ Type", self.add_type_action),
            ("⌨️ Tuş Bas", self.add_key_press_action),
            ("↕️ Kaydır (Scroll)", self.add_scroll_action),
            ("⏳ Wait", self.add_wait_action),
            ("🚀 Launch App", self.add_launch_action),
            ("🌍 Siteye Git", self.add_open_browser_action),
        ]

        for text, cmd in actions:
            # Selector için özel renk, ayırt edilmesi için
            fcolor = "#673AB7" if "Selector" in text else "#555555"
            hcolor = "#512DA8" if "Selector" in text else "#333333"
            
            btn = ctk.CTkButton(self.sidebar_frame, text=text, command=cmd, fg_color=fcolor, hover_color=hcolor)
            btn.pack(pady=3, padx=10, fill="x")

        self.lbl_repo = ctk.CTkLabel(self.sidebar_frame, text="Depo (Repository)", text_color="white")
        self.lbl_repo.pack(pady=(15, 0))

        self.btn_assets = ctk.CTkButton(self.sidebar_frame, text="📦 Görsel Öğeler", command=self.show_asset_browser, fg_color="#555555", hover_color="#333333")
        self.btn_assets.pack(pady=5, padx=10, fill="x")

        self.btn_selectors = ctk.CTkButton(self.sidebar_frame, text="🎯 Seçiciler (Selectors)", command=self.show_selector_browser, fg_color="#555555", hover_color="#333333")
        self.btn_selectors.pack(pady=5, padx=10, fill="x")

        # v162.0: Hızlı Kütüphane Kaydı (Move here for visibility)
        self.btn_quick_save = ctk.CTkButton(self.sidebar_frame, text="⚡ Hızlı Kayıt (Kütüphane)", command=self.open_quick_save_dialog, fg_color="#2ECC71", hover_color="#27AE60", text_color="white")
        self.btn_quick_save.pack(pady=(10, 5), padx=10, fill="x")

        # GÜNCELLEME (v54): Doğrulama ve Kontrol Alanı Geri Geldi
        self.lbl_val = ctk.CTkLabel(self.sidebar_frame, text="Doğrulama & Kontrol", text_color="white")
        self.lbl_val.pack(pady=(15, 0))

        # Popup İşleyici (v160.6 Fixed)
        self.btn_popup = ctk.CTkButton(self.sidebar_frame, text="🛡️ Popup Yakala", command=self.add_popup_step, fg_color="#FF5722", hover_color="#E64A19")
        self.btn_popup.pack(pady=5, padx=10, fill="x")

        # v167.16: Değişken Tanımla
        self.btn_vars = ctk.CTkButton(self.sidebar_frame, text="🔢 Değişken Tanımla", command=self.add_variable_action, fg_color="#8E44AD", hover_color="#9B59B6")
        self.btn_vars.pack(pady=5, padx=10, fill="x")
        
        # v167.24: Veri Okuma
        self.btn_get_text = ctk.CTkButton(self.sidebar_frame, text="📥 Veri Oku (Get Text)", command=self.add_get_text_action, fg_color="#16A085", hover_color="#1ABC9C")
        self.btn_get_text.pack(pady=5, padx=10, fill="x")

        # Durum Kontrolü (Smart Wait)
        self.btn_check_state = ctk.CTkButton(self.sidebar_frame, text="👁️ Görseli Bekle (Check)", command=self.add_assert_action, fg_color="#FF9800", hover_color="#F57C00", text_color="black")
        self.btn_check_state.pack(pady=5, padx=10, fill="x")
        
        # v167.24: Veri Kontrolü
        self.btn_check_text = ctk.CTkButton(self.sidebar_frame, text="✅ Veri Kontrolü (Check Text)", command=self.add_check_text_action, fg_color="#C0392B", hover_color="#E74C3C")
        self.btn_check_text.pack(pady=5, padx=10, fill="x")

        # v162.0: Hızlı Kütüphane Kaydı (Depo Bölümüne Taşındı)
        # self.btn_quick_save... (Moved up)

        # Eski Doğrulama (Validate Window/Element) - v71.2: Kaldırıldı

    def _setup_main_panel(self):
        """Senaryo Adımları Listesi"""
        # v65: Ebeveyn self.editor_frame olarak değiştirildi
        self.main_frame = ctk.CTkFrame(self.editor_frame, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)
        
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=5)
        
        self.lbl_scenario = ctk.CTkLabel(header_frame, text="Senaryo Adımları", font=("Arial", 16, "bold"))
        self.lbl_scenario.pack(side="left", padx=10)
        
        self.btn_clear_all = ctk.CTkButton(header_frame, text="🗑️ Temizle", width=80, fg_color="red", command=self.clear_all_steps)
        self.btn_clear_all.pack(side="right", padx=10)

        self.scrollable_steps = ctk.CTkScrollableFrame(self.main_frame, label_text="Adım Listesi")
        self.scrollable_steps.pack(expand=True, fill="both", padx=10, pady=5)

    def _setup_right_panel(self):
        """Kontrol ve Log Paneli"""
        # v65: Ebeveyn self.editor_frame olarak değiştirildi
        self.right_frame = ctk.CTkFrame(self.editor_frame, width=250, corner_radius=0)
        self.right_frame.grid(row=0, column=2, sticky="nswe")

        self.lbl_controls = ctk.CTkLabel(self.right_frame, text="Kontrol Paneli", font=("Arial", 16, "bold"))
        self.lbl_controls.pack(pady=10)

        self.btn_run = ctk.CTkButton(self.right_frame, text="▶️ Çalıştır", command=self.run_scenario, fg_color="#D90085", hover_color="#C2185B")
        self.btn_run.pack(pady=10, padx=10, fill="x")

        self.btn_stop = ctk.CTkButton(self.right_frame, text="⛔ Durdur", command=self.stop_scenario, fg_color="#D90085", hover_color="#C2185B")
        self.btn_stop.pack(pady=10, padx=10, fill="x")
        
        self.btn_save = ctk.CTkButton(self.right_frame, text="💾 Kaydet", command=self.save_to_db, fg_color="#194E91", hover_color="#0D47A1")
        self.btn_save.pack(pady=5, padx=10, fill="x")

        self.btn_load = ctk.CTkButton(self.right_frame, text="📂 Senaryolar", command=self.show_scenarios, fg_color="#194E91", hover_color="#0D47A1")
        self.btn_load.pack(pady=5, padx=10, fill="x")

        # Dışa/İçe Aktar (Export/Import) (v63)
        self.btn_export = ctk.CTkButton(self.right_frame, text="📦 Dışa Aktar (Export)", command=self.export_scenario, fg_color="#2CC985", hover_color="#27AE60", text_color="black")
        self.btn_export.pack(pady=(15, 5), padx=10, fill="x")
        
        self.btn_import = ctk.CTkButton(self.right_frame, text="📥 İçe Aktar (Import)", command=self.import_scenario, fg_color="#FF9800", hover_color="#F57C00", text_color="black")
        self.btn_import.pack(pady=5, padx=10, fill="x")

        
        self.textbox_log = ctk.CTkTextbox(self.right_frame, state="disabled") # v71.3: Salt-okunur (Read-only)
        self.textbox_log.pack(expand=True, fill="both", padx=10, pady=10)


    def _setup_logging(self):
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.widget = text_widget

            def emit(self, record):
                msg = self.format(record)
                # Thread-safe UI update
                self.widget.after(0, lambda m=msg: self._safe_append(m))
            
            def _safe_append(self, msg):
                self.widget.configure(state="normal") # v71.3: Yazmak için kilidi aç
                self.widget.insert("end", msg + "\n")
                self.widget.see("end")
                self.widget.configure(state="disabled") # v71.3: Tekrar kilitle

        # Global log konfigürasyonu main.py içinde yapılır (DEBUG seviyesi)
        # UI'da sadece INFO ve üzerini istiyoruz
        handler = TextHandler(self.textbox_log)
        handler.setLevel(logging.INFO) # v74: UI loglarını filtrele
        
        # Sadece bizim loglarımızı daha temiz göster
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)


    def refresh_step_list(self):
        for widget in self.scrollable_steps.winfo_children():
            widget.destroy()

        for idx, action in enumerate(self.current_scenario.actions):
            frame = ctk.CTkFrame(self.scrollable_steps, height=40)
            frame.pack(pady=2, padx=5, fill="x")
            
            # Sürükle & Bırak Bağlamaları
            bind_cmd = lambda e, i=idx: self.on_drag_start(e, i)
            motion_cmd = self.on_drag_motion
            drop_cmd = lambda e, i=idx: self.on_drop(e, i)

            frame.bind("<Button-1>", bind_cmd)
            frame.bind("<B1-Motion>", motion_cmd)
            frame.bind("<ButtonRelease-1>", drop_cmd)
            
            # Adım Bilgisi
            # v68: Hızlı Sıralama (Adıma Git / Jump to Step)
            ent_idx = ctk.CTkEntry(frame, width=35, height=24, font=("Arial", 12))
            ent_idx.insert(0, str(idx + 1))
            ent_idx.pack(side="left", padx=(5, 2))
            ent_idx.bind("<Return>", lambda e, i=idx, ent=ent_idx: self.change_step_order(i, ent.get()))
            ent_idx.bind("<FocusOut>", lambda e, i=idx, ent=ent_idx: self.change_step_order(i, ent.get(), silent=True)) # Opsiyonel: Focus çıkınca da kaydetsin mi? Belki tehlikeli olabilir, sadece Enter daha iyi.

            # Adım Bilgisi (Sıra numarası olmadan)
            lbl_text = f"{action.type}"
            button_type = action.params.get("button", "left")
            if button_type == "double":
                btn_label = "(Çift)"
            elif button_type == "right":
                btn_label = "(Sağ)"
            else:
                btn_label = "(Sol)"

            if action.type == "CLICK":
                lbl_text += f" {btn_label}"
                # GÜNCELLEME (v39): Dosya adı yerine kullanıcının verdiği ismi (description) göster
                if action.description:
                    lbl_text += f" - {action.description}"
                elif action.params.get("by_image"):
                    lbl_text += f" (Img: {os.path.basename(action.params['target'])})"
            elif action.type == "CLICK_TEXT":
                lbl_text += f" {btn_label} ('{action.params.get('text')}')"
            elif action.type == "TYPE":
                lbl_text += f" ('{action.params['text']}')"
            else:
                lbl_text += f" - {action.description}"
                
            lbl = ctk.CTkLabel(frame, text=lbl_text, anchor="w")
            lbl.pack(side="left", padx=5, expand=True, fill="x")
            
            # Label'a da bind ekle (event'in frame'den geçmesi için)
            lbl.bind("<Button-1>", bind_cmd)
            lbl.bind("<B1-Motion>", motion_cmd)
            lbl.bind("<ButtonRelease-1>", drop_cmd)
            
            # Kontrol Butonları (Yukarı/Aşağı/Sil)
            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.pack(side="right", padx=5)

            # v68.1: Yukarı/Aşağı butonları kaldırıldı (Işınlanma özelliği geldiği için)
            # btn_up = ctk.CTkButton...
            # btn_down = ctk.CTkButton...
            
            # Çalıştır Butonu (Buradan Başlat - Debug) (v160.3)
            btn_run_here = ctk.CTkButton(btn_frame, text="▶", width=30, fg_color="#2CC985", hover_color="#229966", command=lambda i=idx: self.run_scenario_from_step(i))
            btn_run_here.pack(side="left", padx=2)
            # Tooltip eklenebilir ama şimdilik ikon yeterli.

            # Düzenle Butonu (v46) - Geri Getirildi (v64 gerileme düzeltmesi)
            btn_edit = ctk.CTkButton(btn_frame, text="✏️", width=30, fg_color="blue", command=lambda i=idx: self.edit_step(i))
            btn_edit.pack(side="left", padx=2)

            # Resim Değiştir Butonu (Repo) (v64)
            if action.params.get("by_image") or action.type in ["CLICK", "ASSERT_EXISTS", "SCROLL_UNTIL"]:
                btn_img_change = ctk.CTkButton(btn_frame, text="🖼️", width=30, fg_color="purple", command=lambda i=idx: self.change_step_image(i))
                btn_img_change.pack(side="left", padx=2)

            btn_del = ctk.CTkButton(btn_frame, text="❌", width=30, fg_color="darkred", command=lambda i=idx: self.delete_step(i))
            btn_del.pack(side="left", padx=2)


    def edit_step(self, index):
        if not (0 <= index < len(self.current_scenario.actions)): return
        
        action = self.current_scenario.actions[index]
        
        # v160.6: Pop-up için özel editör
        if action.type == "POPUP_CHECK":
            self._edit_popup_step(index)
            return

        if action.type == "OPEN_URL":
            current_url = action.params.get("url", "")
            new_url = simpledialog.askstring("Düzenle", "Yeni URL Girin:", initialvalue=current_url)
            if new_url:
                if not new_url.startswith("http"):
                    new_url = "https://" + new_url
                action.params["url"] = new_url
                action.description = f"Open URL: {new_url}"
                self.refresh_step_list()
        
        elif action.type == "TYPE":
            current_text = action.params.get("text", "")
            new_text = simpledialog.askstring("Düzenle", "Yazılacak Metni Düzenle:", initialvalue=current_text)
            if new_text is not None:
                action.params["text"] = new_text
                action.description = f"Type '{new_text}'"
                self.refresh_step_list()

        elif action.type == "WAIT":
            current_sec = action.params.get("seconds", "1")
            new_sec = simpledialog.askstring("Düzenle", "Bekleme Süresi (sn):", initialvalue=str(current_sec))
            if new_sec:
                action.params["seconds"] = new_sec
                action.description = f"Wait {new_sec}s"
                self.refresh_step_list()

        elif action.type == "ASSERT_EXISTS":
            current = action.params.get("timeout", 10)
            new_val = simpledialog.askstring("Düzenle", "Bekleme Süresi (Maksimum sn):", initialvalue=str(current))
            if new_val:
                try:
                    to = int(new_val)
                    action.params["timeout"] = to
                    
                    # Description güncelle
                    # "Wait for: xxx (10s)" formatını koruyalım
                    base_desc = action.description.split('(')[0].strip()
                    action.description = f"{base_desc} ({to}s)"
                    
                    self.refresh_step_list()
                except: pass

        elif action.type == "CLICK":
            if not action.params.get("by_image"):
                 messagebox.showinfo("Bilgi", "Sadece görsel ile yapılan tıklamalar için gelişmiş ayarlar yapılabilir.")
                 return

            # Gelişmiş Ayarlar Menüsü (v63)
            dialog = ctk.CTkToplevel(self)
            dialog.title("Tıklama Ayarları")
            dialog.geometry("300x500")
            dialog.grab_set()
            
            # v72: Dinamik Güvenlik (Dynamic Confidence) Mantığı
            current_conf = action.params.get("confidence")
            is_dynamic = current_conf is None
            
            def toggle_dynamic():
                if dyn_var.get():
                    conf_entry.configure(state="disabled", fg_color="gray")
                else:
                    conf_entry.configure(state="normal", fg_color=["#F9F9FA", "#343638"]) # Varsayılan renkler
            
            dyn_var = ctk.BooleanVar(value=is_dynamic)
            chk_dyn = ctk.CTkCheckBox(dialog, text="Dinamik Güvenlik (Önerilen)", variable=dyn_var, command=toggle_dynamic)
            chk_dyn.pack(pady=15)

            ctk.CTkLabel(dialog, text="Hassasiyet (0.1-1.0):").pack(pady=5)
            # Eğer dinamikse, varsayılan 0.85 göster (ama devre dışı olacak)
            disp_val = str(current_conf) if current_conf is not None else "0.85"
            conf_var = ctk.StringVar(value=disp_val)
            conf_entry = ctk.CTkEntry(dialog, textvariable=conf_var)
            conf_entry.pack(pady=5)
            
            if is_dynamic:
                conf_entry.configure(state="disabled", fg_color="gray")
            
            ctk.CTkLabel(dialog, text="Eşleşme Sırası (Match Index):").pack(pady=5)
            idx_var = ctk.StringVar(value=str(action.match_index))
            ctk.CTkEntry(dialog, textvariable=idx_var).pack(pady=5)
            
            ctk.CTkLabel(dialog, text="Ofset (X, Y):").pack(pady=5)
            off_var = ctk.StringVar(value=f"{action.offset[0]}, {action.offset[1]}")
            ctk.CTkEntry(dialog, textvariable=off_var).pack(pady=5)
            
            def save_settings():
                try:
                    if dyn_var.get():
                        action.params["confidence"] = None # Dinamik
                    else:
                        action.params["confidence"] = float(conf_var.get())

                    action.match_index = int(idx_var.get())
                    ox, oy = map(float, off_var.get().split(','))
                    action.offset = (ox, oy)
                    
                    self.refresh_step_list()
                    
                    # Ayar değişikliğini otomatik kaydet
                    if self.current_scenario.id:
                        self.db.save_scenario(self.current_scenario)
                        
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Hata", f"Geçersiz değer: {e}")
            
            ctk.CTkButton(dialog, text="Kaydet", command=save_settings).pack(pady=20)
        
        elif action.type == "CLICK_SELECTOR":
            # v80.1: JSON ile Selector Düzenleme
            import json
            current_sel = action.params.get("selector", {})
            current_name = action.params.get("selector_name", "Element")
            
            # Ham JSON düzenlemek için büyük metin alanı içeren bir diyalog göster
            dialog = ctk.CTkToplevel(self)
            dialog.title(f"Düzenle: {current_name}")
            dialog.geometry("500x500")
            dialog.grab_set()
            
            ctk.CTkLabel(dialog, text="Selector JSON (Gelişmiş Düzenleme):", font=("Arial", 12, "bold")).pack(pady=5)
            
            txt_json = ctk.CTkTextbox(dialog, width=450, height=350, font=("Consolas", 10))
            txt_json.pack(pady=5, padx=10)
            
            # Ön doldurma
            try:
                txt_json.insert("1.0", json.dumps(current_sel, indent=4))
            except:
                txt_json.insert("1.0", str(current_sel))
                
            def save_selector_json():
                try:
                    new_json_str = txt_json.get("1.0", "end").strip()
                    new_sel = json.loads(new_json_str)
                    
                    action.params["selector"] = new_sel
                    # İndeks değiştiyse açıklamayı da güncelle
                    # Ama açıklama genellikle "Tıkla: İsim" şeklindedir
                    
                    self.refresh_step_list()
                    if self.current_scenario.id:
                        self.db.save_scenario(self.current_scenario)
                        
                    dialog.destroy()
                    messagebox.showinfo("Başarılı", "Selector güncellendi!")
                except Exception as e:
                    messagebox.showerror("Hata", f"Geçersiz JSON: {e}")

            ctk.CTkButton(dialog, text="Kaydet", command=save_selector_json).pack(pady=10)
            
            # İndeks için Yardımcı
            def fast_add_index():
                 try:
                    js = json.loads(txt_json.get("1.0", "end").strip())
                    cur_idx = js.get("foundIndex", 1)
                    new = simpledialog.askinteger("Hızlı Index", "Index Numarası:", initialvalue=cur_idx)
                    if new:
                        js["foundIndex"] = new
                        txt_json.delete("1.0", "end")
                        txt_json.insert("1.0", json.dumps(js, indent=4))
                 except: pass
            
            ctk.CTkButton(dialog, text="🔢 Hızlı Index Değiştir", fg_color="gray", command=fast_add_index).pack(pady=5)

        else:
            messagebox.showinfo("Bilgi", "Bu adım türü için düzenleme desteği henüz eklenmedi.")


    def _edit_popup_step(self, index):
        """v160.9: Pop-up Adımı Düzenleme Penceresi - Görsel ve Detay Destekli"""
        action = self.current_scenario.actions[index]
        triggers = action.params.get("triggers", [])

        dialog = ctk.CTkToplevel(self)
        dialog.title("Pop-up / Engel Yakalayıcı")
        dialog.geometry("600x600")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Takip Edilecek Hedefler", font=("Arial", 16, "bold")).pack(pady=(15, 5))
        ctk.CTkLabel(dialog, text="Bu hedeflerden herhangi biri görünürse tıklanır ve döngü durur.\nGörünmezse hata vermeden devam edilir.", font=("Arial", 10), text_color="gray").pack(pady=(0, 10))

        # Liste
        scroll_frame = ctk.CTkScrollableFrame(dialog, width=550, height=350)
        scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.pop_image_refs = [] # Önizleme resimleri için referans tutucu

        def refresh_list():
            for widget in scroll_frame.winfo_children():
                widget.destroy()
            self.pop_image_refs.clear()
            
            for i, trig in enumerate(triggers):
                f = ctk.CTkFrame(scroll_frame)
                f.pack(fill="x", pady=5, padx=5)
                
                t_type = trig.get("type")
                t_value = trig.get("value")
                
                # DB'den detayları çek (Önizleme için)
                preview_data = None
                details = ""
                
                if t_type == "selector":
                    sel = self.db.get_selector_by_name(t_value)
                    if sel:
                        preview_data = sel[4] # image_data
                        details = sel[2] # content (JSON)
                        if len(details) > 50: details = details[:47] + "..."
                elif t_type == "image":
                    asset = self.db.get_asset_by_name(t_value)
                    if asset:
                        preview_data = asset[2] # blob data
                
                # Görsel Önizleme
                if preview_data:
                    try:
                        import io
                        from PIL import Image, ImageTk
                        pil_img = Image.open(io.BytesIO(preview_data))
                        pil_img.thumbnail((60, 60))
                        tk_img = ImageTk.PhotoImage(pil_img)
                        self.pop_image_refs.append(tk_img)
                        
                        img_lbl = ctk.CTkLabel(f, image=tk_img, text="")
                        img_lbl.pack(side="left", padx=5)
                    except:
                        pass
                
                # Metin Bilgisi
                info_frame = ctk.CTkFrame(f, fg_color="transparent")
                info_frame.pack(side="left", padx=10, fill="y", expand=True)
                
                type_icon = "🎯" if t_type == "selector" else "🖼️"
                ctk.CTkLabel(info_frame, text=f"{type_icon} {t_value}", font=("Arial", 12, "bold"), anchor="w").pack(fill="x")
                if details:
                    ctk.CTkLabel(info_frame, text=details, font=("Arial", 9), text_color="gray", anchor="w").pack(fill="x")
                
                ctk.CTkButton(f, text="Sil", width=50, fg_color="#C0392B", hover_color="#922B21", command=lambda idx=i: remove_trigger(idx)).pack(side="right", padx=10)

        def remove_trigger(idx):
            triggers.pop(idx)
            refresh_list()
            save_changes()

        def save_changes():
            action.params["triggers"] = triggers
            self.refresh_step_list()
            if self.current_scenario.id:
                self.db.save_scenario(self.current_scenario)

        refresh_list()
        
        # Ekleme Butonları
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=15)

        def add_selector():
            def on_select(selector_data):
                # selector_data: (id, name, content, type, image_data)
                name = selector_data[1]
                triggers.append({"type": "selector", "value": name, "action": "click"})
                refresh_list()
                save_changes()
                if hasattr(self, 'pop_selector_browser'):
                    self.pop_selector_browser.destroy()
            
            # v160.9: SelectorBrowser'ı dialog'un üzerinde aç
            self.pop_selector_browser = SelectorBrowser(dialog, self.db, on_select, mode="pick")
            self.pop_selector_browser.grab_set()

        def add_image():
            def on_selected(path, name):
                # AssetBrowser pick modunda name döndürür
                triggers.append({"type": "image", "value": name, "action": "click"})
                refresh_list()
                save_changes()
                if hasattr(self, 'pop_asset_browser'):
                    self.pop_asset_browser.destroy()
            
            # v160.9: AssetBrowser'ı dialog'un üzerinde aç
            self.pop_asset_browser = AssetBrowser(dialog, self.db, on_selected, mode="pick")
            self.pop_asset_browser.grab_set()

        ctk.CTkButton(btn_frame, text="🎯 Selector Kütüphanesi", command=add_selector, font=("Arial", 12)).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🖼️ Görsel Kütüphanesi", command=add_image, font=("Arial", 12)).pack(side="left", padx=10)

    def delete_step(self, index):
        if 0 <= index < len(self.current_scenario.actions):
            self.current_scenario.actions.pop(index)
            self.refresh_step_list()
            # v70: Değişiklikte otomatik kaydet
            if self.current_scenario.id:
                self.db.save_scenario(self.current_scenario)

    def change_step_order(self, current_index, new_index_str, silent=False):
        """v68: Adımı belirtilen sıraya taşır (1-based index)."""
        try:
            # Sadece Enter tuşu (silent=False) ile işlem yapıldığında logla veya hata ver
            new_index = int(new_index_str) - 1 # 1-based to 0-based
            if new_index < 0: new_index = 0
            if new_index >= len(self.current_scenario.actions): new_index = len(self.current_scenario.actions) - 1
            
            if new_index == current_index:
                return # Değişiklik yok

            # Taşıma işlemi
            action = self.current_scenario.actions.pop(current_index)
            self.current_scenario.actions.insert(new_index, action)
            
            self.refresh_step_list()
            
            # v70: Auto-save on modification
            if self.current_scenario.id:
                self.db.save_scenario(self.current_scenario)
            
            # Odaklanma (Opsiyonel: Taşınan satırın Entry'sine odaklanılabilir ama şimdilik liste yenileniyor)
            
        except ValueError:
            if not silent:
                messagebox.showerror("Hata", "Lütfen geçerli bir sayı girin.")
        except Exception as e:
            if not silent:
                print(f"Sıralama hatası: {e}")

    def move_step_up(self, index):
        if index > 0:
            self.current_scenario.actions[index], self.current_scenario.actions[index-1] = self.current_scenario.actions[index-1], self.current_scenario.actions[index]
            self.refresh_step_list()

    def move_step_down(self, index):
        if index < len(self.current_scenario.actions) - 1:
            self.current_scenario.actions[index], self.current_scenario.actions[index+1] = self.current_scenario.actions[index+1], self.current_scenario.actions[index]
            self.refresh_step_list()
            
    def clear_all_steps(self):
        if not self.current_scenario.actions: return

        if messagebox.askyesno("Onay", "Tüm adımları silmek istediğinize emin misiniz?"):
            self.current_scenario.actions = []
            self.refresh_step_list()
            
            # v76: Auto-save on clear
            if self.current_scenario.id:
                if not self.db.save_scenario(self.current_scenario):
                    messagebox.showerror("Hata", "Silme işlemi kaydedilemedi!")

    def on_drag_start(self, event, index):
        self.drag_index = index
        self.scrollable_steps.configure(cursor="hand2")
        # Görsel geri bildirim: Seçili olanı belirginleştir
        for i, child in enumerate(self.scrollable_steps.winfo_children()):
            if i == index:
                child.configure(fg_color="#3B3B3B") # Hafif gri/reaktif renk

    def on_drag_motion(self, event):
        pass

    def on_drop(self, event, index):
        self.scrollable_steps.configure(cursor="")
        if self.drag_index is not None:
            source_idx = self.drag_index
            target_idx = None
            
            x, y = self.winfo_pointerxy()
            for i, child in enumerate(self.scrollable_steps.winfo_children()):
                if isinstance(child, ctk.CTkFrame):
                    # Rengi eski haline getir
                    child.configure(fg_color=["#3B3B3B", "#2B2B2B"]) # CTK default
                    
                    x1 = child.winfo_rootx()
                    y1 = child.winfo_rooty()
                    x2 = x1 + child.winfo_width()
                    y2 = y1 + child.winfo_height()
                    
                    if x1 <= x <= x2 and y1 <= y <= y2:
                        target_idx = i

            if target_idx is not None and source_idx != target_idx:
                action = self.current_scenario.actions.pop(source_idx)
                self.current_scenario.actions.insert(target_idx, action)
                self.refresh_step_list()
            else:
                self.refresh_step_list() # Rengi sıfırlamak için
        
        self.drag_index = None

    # --- Smart Recorder Methods ---
    def toggle_smart_recording(self):
        if self.recorder and self.recorder.is_recording:
            self.recorder.stop()
        else:
            # Başlat
            self.iconify() # Arayüzü gizle
            self.recorder = Recorder(
                on_action_recorded=self.on_action_recorded_callback,
                on_stop=self.on_recorder_stop,
                exclude_window=self
            )
            self.recorder.start()
            self.btn_smart_rec.configure(text="⏹ Kaydı Bitir (ESC)")

    def on_action_recorded_callback(self, action_type, params):
        # Thread güvenliği için after kullanıyoruz
        self.after(0, lambda: self._add_recorded_action(action_type, params))

    def _add_recorded_action(self, action_type, params):
        description = f"Auto: {action_type}"
        if action_type == "CLICK":
            description = f"Click Image: {os.path.basename(params['target'])}"
            # Otomatik kaydı da kütüphaneye ekle
            asset_name = f"auto_{datetime.datetime.now().strftime('%H%M%S')}_{os.path.basename(params['target'])}"
            self.db.save_asset(asset_name, params['target'])
            
            # v66: Dosyayı SİL ve hedefi sadece İSİM yap
            try:
                os.remove(params['target'])
            except: pass
            params['target'] = asset_name
            
        action = Action(type=action_type, params=params, description=description)
        self.current_scenario.add_action(action)
        self.refresh_step_list()
        
        # v70: Otomatik kaydet
        if self.current_scenario.id:
            self.db.save_scenario(self.current_scenario)

    def on_recorder_stop(self):
        self.after(0, self._on_recorder_stop_ui)

    def _on_recorder_stop_ui(self):
        self.deiconify() # Arayüzü geri getir
        self.btn_smart_rec.configure(text="📸 Kaydı Başlat")
        messagebox.showinfo("Kayıt Tamamlandı", "Otomatik kayıt sonlandırıldı.")

    def smart_record_click(self):

        self.start_snip_tool(self._on_record_click_complete)
        
    def smart_record_assert(self):
        self.start_snip_tool(self._on_record_assert_complete)
        
    def start_snip_tool(self, callback):
        # UI'ı küçült ki ekran rahat görünsün
        self.iconify()
        # Snip aracı bittiğinde UI geri gelsin
        def wrapped_callback(filepath, offset=(0, 0)):
            self.deiconify()
            # v64 Fix: SnipTool destroy edildikten sonra biraz bekle ki modal dialog arkada kalmasın
            if filepath:
                self.after(200, lambda: callback(filepath, offset))
        
        SnipTool(self, wrapped_callback).start_selection()
        
    def _on_record_click_complete(self, filepath, offset=(0, 0)):
        action = Action(type="CLICK", 
                        params={"target": filepath, "by_image": True}, 
                        description=f"Click Image: {os.path.basename(filepath)}",
                        offset=offset)
        self.current_scenario.add_action(action)
        self.refresh_step_list()
        
    def _on_record_assert_complete(self, filepath, offset=(0, 0)):
        action = Action(type="ASSERT_EXISTS", 
                        params={"target": filepath}, 
                        description=f"Assert Image: {os.path.basename(filepath)}",
                        offset=offset)
        self.current_scenario.add_action(action)
        self.refresh_step_list()

    
    # --- Aksiyon Ekleme Fonksiyonları ---
    def add_click_action(self):
        # Koordinat sormayı tamamen kaldırdık, direkt SnipTool başlatıyoruz
        self.start_snip_tool(self._on_manual_click_snip_complete)

    def _on_manual_click_snip_complete(self, filepath, offset=(0, 0)):
        # Görseli kütüphaneye de kaydedelim
        name = simpledialog.askstring("Kütüphaneye Kaydet", f"Görsel için bir isim verin (Offset: {offset}):")
        
        if name is None: return 
            
        if not name.strip():
            name = f"manual_click_{os.path.basename(filepath)}"
        
        # DB'ye kaydet (v63: Binary de kaydediliyor)
        self.db.save_asset(name, filepath)
        
        # v66: Dosyayı SİL
        try:
             os.remove(filepath)
        except: pass
        
        action = Action(type="CLICK", 
                        params={"target": name, "by_image": True}, 
                        description=f"Click: {name}",
                        offset=offset)
        self.current_scenario.add_action(action)
        self.refresh_step_list()
        
        # v70.3: Manuel otomatik kaydet
        if self.current_scenario.id:
            self.db.save_scenario(self.current_scenario)

    def add_right_click_action(self):
        # GÜNCELLEME (v41): Dosya seçme yerine Snip Tool ile seçim (Sol tık gibi)
        self.start_snip_tool(self._on_manual_right_click_snip_complete)

    def _on_manual_right_click_snip_complete(self, filepath, offset=(0, 0)):
        # Görseli kütüphaneye kaydet
        name = simpledialog.askstring("Kütüphaneye Kaydet", f"Sağ Tıklanacak Görselin Adı (Offset: {offset}):")
        
        if name is None: return

        if not name.strip():
            name = f"manual_right_click_{os.path.basename(filepath)}"
        
        # DB'ye kaydet
        self.db.save_asset(name, filepath)

        # v66: Dosyayı SİL
        try:
             os.remove(filepath)
        except: pass
        
        # Action ekle (button="right")
        action = Action(type="CLICK", 
                        params={"target": name, "by_image": True, "button": "right"}, 
                        description=f"Right Click: {name}",
                        offset=offset)
        self.current_scenario.add_action(action)
        self.refresh_step_list()

        # v70.3: Manuel otomatik kaydet
        if self.current_scenario.id:
            self.db.save_scenario(self.current_scenario)

    def add_double_click_action(self):
        # GÜNCELLEME (v49): Çift Tıklama
        self.start_snip_tool(self._on_manual_double_click_snip_complete)

    def _on_manual_double_click_snip_complete(self, filepath, offset=(0, 0)):
        name = simpledialog.askstring("Kütüphaneye Kaydet", f"Çift Tıklanacak Görselin Adı (Offset: {offset}):")
        
        if name is None: return
            
        if not name.strip():
            name = f"manual_double_click_{os.path.basename(filepath)}"
            
        self.db.save_asset(name, filepath)

        # v66: Dosyayı SİL
        try:
             os.remove(filepath)
        except: pass
        
        # Action ekle (button="double")
        action = Action(type="CLICK", 
                        params={"target": name, "by_image": True, "button": "double"}, 
                        description=f"Double Click: {name}",
                        offset=offset)
        self.current_scenario.add_action(action)
        self.refresh_step_list()
        
        # v70.3: Manuel otomatik kaydet
        if self.current_scenario.id:
            self.db.save_scenario(self.current_scenario)

    def add_type_action(self):
        # v155: Basitleştirilmiş Yazma Aksiyonu - Varsayılan olarak Hızlı (0.01s)
        dialog = ctk.CTkInputDialog(text="Yazılacak metin:", title="Metin Yaz (Type)")
        text = dialog.get_input()
        if text:
            action = Action(type="TYPE", params={"text": text, "interval": 0.01}, description=f"Type (Hızlı): '{text}'")
            self.current_scenario.add_action(action)
            self.refresh_step_list()
            # v70.2: Auto-save
            if self.current_scenario.id:
                self.db.save_scenario(self.current_scenario)

    def add_key_press_action(self):
        # Özel tuş seçimi için diyalog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Tuş Seç")
        dialog.geometry("300x200")
        dialog.grab_set()
        
        lbl = ctk.CTkLabel(dialog, text="Basılacak özel tuşu seçin:")
        lbl.pack(pady=10)
        
        keys = ["enter", "tab", "esc", "backspace", "delete", "space", "home", "end", "pgup", "pgdn", "up", "down", "left", "right", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"]
        
        combo = ctk.CTkComboBox(dialog, values=keys)
        combo.pack(pady=10)
        combo.set("enter")
        
        def add():
            key = combo.get()
            action = Action(type="PRESS_KEY", params={"key": key}, description=f"Press Key: {key}")
            self.current_scenario.add_action(action)
            self.refresh_step_list()
            # v70.2: Auto-save
            if self.current_scenario.id:
                self.db.save_scenario(self.current_scenario)
            dialog.destroy()
            
        btn = ctk.CTkButton(dialog, text="Ekle", command=add)
        btn.pack(pady=10)

    def add_scroll_action(self):
        # v55: Gelişmiş Scroll Penceresi
        dialog = ctk.CTkToplevel(self)
        dialog.title("Gelişmiş Kaydırma (Scroll)")
        dialog.geometry("450x650") 
        dialog.grab_set()
        
        # Tab View
        tabview = ctk.CTkTabview(dialog)
        tabview.pack(expand=True, fill="both", padx=10, pady=10)
        
        tab_manual = tabview.add("Manuel Kaydırma")
        tab_smart = tabview.add("Görsel (Smart)")
        tab_selector = tabview.add("Seçici (Smart)")
        
        # --- TAB 1: MANUEL ---
        lbl_dir = ctk.CTkLabel(tab_manual, text="Kaydırma Yönü:", font=("Arial", 12, "bold"))
        lbl_dir.pack(pady=5)
        
        dir_var = ctk.StringVar(value="down")
        rb_down = ctk.CTkRadioButton(tab_manual, text="⬇️ Aşağı (Down)", variable=dir_var, value="down")
        rb_down.pack(pady=5)
        rb_up = ctk.CTkRadioButton(tab_manual, text="⬆️ Yukarı (Up)", variable=dir_var, value="up")
        rb_up.pack(pady=5)
        
        lbl_amt = ctk.CTkLabel(tab_manual, text="Miktar (Birim):", font=("Arial", 12, "bold"))
        lbl_amt.pack(pady=(15, 5))
        
        # Slider & Entry
        amount_var = ctk.IntVar(value=500)
        
        def update_entry(val):
            amount_var.set(int(val))
            
        def update_slider(*args):
             try: slider.set(amount_var.get())
             except: pass

        slider = ctk.CTkSlider(tab_manual, from_=100, to=5000, number_of_steps=49, command=update_entry)
        slider.set(500)
        slider.pack(fill="x", padx=20, pady=5)
        
        ent_amount = ctk.CTkEntry(tab_manual, textvariable=amount_var)
        ent_amount.pack(pady=5)
        ent_amount.bind("<KeyRelease>", lambda e: slider.set(amount_var.get() if amount_var.get() else 100))
        
        lbl_hint = ctk.CTkLabel(tab_manual, text="(Bilgi: 100 birim ≈ 1 Fare Tekerleği Tıkı)", text_color="gray", font=("Arial", 10))
        lbl_hint.pack(pady=5)
        
        def add_manual():
            direction = dir_var.get()
            amt = amount_var.get()
            final_amt = -amt if direction == "down" else amt
            
            action = Action(type="SCROLL", params={"amount": final_amt}, description=f"Scroll {direction.upper()} {amt}")
            self.current_scenario.add_action(action)
            self.refresh_step_list()
            # v70.2: Auto-save
            if self.current_scenario.id:
                self.db.save_scenario(self.current_scenario)
            dialog.destroy()
            
        btn_add_manual = ctk.CTkButton(tab_manual, text="Ekle", command=add_manual, fg_color="#194E91")
        btn_add_manual.pack(pady=20, fill="x", padx=20)
        
        # --- TAB 2: SMART ---
        lbl_smart_info = ctk.CTkLabel(tab_smart, text="Hedef görseli bulana kadar kaydırır.", text_color="gray")
        lbl_smart_info.pack(pady=5)
        
        self.smart_scroll_target = None
        self.lbl_target_status = ctk.CTkLabel(tab_smart, text="Görsel Seçilmedi ❌", text_color="red")
        self.lbl_target_status.pack(pady=5)
        
        def pick_image():
            # Dialogu gizle, snip tool aç -> callback -> dialogu geri getir
            dialog.withdraw()
            def on_snip(filepath, offset=(0,0)): # offset parametresini ekledik
                dialog.deiconify()
                if filepath:
                    self.smart_scroll_target = filepath
                    self.lbl_target_status.configure(text=f"Seçildi: {os.path.basename(filepath)} ✅", text_color="green")
            
            self.start_snip_tool(on_snip)
            
        def pick_from_repo():
            def on_asset(asset_path, asset_name):
                # asset_path is the 'name' in v66
                self.smart_scroll_target = asset_name
                self.lbl_target_status.configure(text=f"Kütüphane: {asset_name} ✅", text_color="green")
            
            browser = AssetBrowser(dialog, self.db, on_asset, mode="pick")
            browser.grab_set()

        btn_pick_new = ctk.CTkButton(tab_smart, text="📸 Yeni Görsel Yakala", command=pick_image, fg_color="#E91E63")
        btn_pick_new.pack(pady=5)
        
        btn_pick_repo = ctk.CTkButton(tab_smart, text="📦 Kütüphaneden Seç", command=pick_from_repo, fg_color="#3498DB")
        btn_pick_repo.pack(pady=5)
        
        lbl_smart_dir = ctk.CTkLabel(tab_smart, text="Arama Yönü:", font=("Arial", 12, "bold"))
        lbl_smart_dir.pack(pady=5)
        
        smart_dir_var = ctk.StringVar(value="down")
        rb_s_down = ctk.CTkRadioButton(tab_smart, text="⬇️ Aşağı Doğru Ara", variable=smart_dir_var, value="down")
        rb_s_down.pack(pady=5)
        rb_s_up = ctk.CTkRadioButton(tab_smart, text="⬆️ Yukarı Doğru Ara", variable=smart_dir_var, value="up")
        rb_s_up.pack(pady=5)
        
        lbl_max = ctk.CTkLabel(tab_smart, text="Maksimum Adım:", font=("Arial", 12, "bold"))
        lbl_max.pack(pady=(10, 5))
        
        max_var = ctk.StringVar(value="10")
        ent_max = ctk.CTkEntry(tab_smart, textvariable=max_var)
        ent_max.pack(pady=5)
        
        # v55.1: Adım Miktarı (Step Size) - Görseli atlamayı önlemek için
        lbl_step = ctk.CTkLabel(tab_smart, text="Adım Miktarı (Scroll Step):", font=("Arial", 12, "bold"))
        lbl_step.pack(pady=(10, 5))
        
        step_var = ctk.StringVar(value="300") # Default reduced from 500 to 300
        ent_step = ctk.CTkEntry(tab_smart, textvariable=step_var)
        ent_step.pack(pady=5)
        
        def add_smart():
            if not self.smart_scroll_target:
                messagebox.showerror("Hata", "Lütfen önce hedef görsel seçin.")
                return
            
            direction = smart_dir_var.get()
            try: max_steps = int(max_var.get())
            except: max_steps = 10
            
            try: step_val = int(step_var.get())
            except: step_val = 300
            
            # Smart Scroll Action
            # Target is either a filepath (new snip) or a library name
            target_val = self.smart_scroll_target
            is_repo = "Kütüphane:" in self.lbl_target_status.cget("text")
            
            if not is_repo:
                # Kaydet asset
                name = f"smart_scroll_{os.path.basename(target_val)}"
                self.db.save_asset(name, target_val)
                target_val = name
            
            action = Action(type="SCROLL_UNTIL", 
                            params={
                                "target": target_val, 
                                "direction": direction, 
                                "max_steps": max_steps,
                                "step": step_val 
                            }, 
                            description=f"Scroll {direction.upper()} until found: {os.path.basename(target_val)}")
            self.current_scenario.add_action(action)
            self.refresh_step_list()
            # v70.2: Auto-save
            if self.current_scenario.id:
                self.db.save_scenario(self.current_scenario)
        btn_add_smart = ctk.CTkButton(tab_smart, text="Ekle", command=add_smart, fg_color="#194E91")
        btn_add_smart.pack(pady=20, fill="x", padx=20)

        # --- TAB 3: SEÇİCİ (SMART) ---
        lbl_sel_info = ctk.CTkLabel(tab_selector, text="Hedef elementi bulana kadar kaydırır.", text_color="gray")
        lbl_sel_info.pack(pady=5)
        self.smart_scroll_selector = None
        lbl_sel_status = ctk.CTkLabel(tab_selector, text="Seçici Seçilmedi ❌", text_color="red")
        lbl_sel_status.pack(pady=5)

        # v164.0: Embedded Selector List
        sel_list_frame = ctk.CTkScrollableFrame(tab_selector, height=250) # v165: Increased height
        sel_list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        def refresh_selector_list():
            for w in sel_list_frame.winfo_children(): w.destroy()
            selectors = self.db.list_selectors()
            for s_id, name, content, s_type, created, img_data in selectors:
                f = ctk.CTkFrame(sel_list_frame)
                f.pack(fill="x", pady=2)
                ctk.CTkLabel(f, text=name, anchor="w").pack(side="left", padx=5, expand=True, fill="x")
                ctk.CTkButton(f, text="Seç", width=50, fg_color="#27AE60",
                             command=lambda c=content, n=name: select_from_list(c, n)).pack(side="right", padx=2)

        def select_from_list(content, name):
            self.smart_scroll_selector = {"name": name, "content": content}
            lbl_sel_status.configure(text=f"Seçildi: {name} ✅", text_color="green")

        def pick_new_selector():
            # v165.0: Direct capture
            def on_captured(*args):
                # v166: Return Scroll Dialog
                dialog.deiconify()
                dialog.lift()
                dialog.focus_force()
                dialog.grab_set() # v167: Re-grab focus
                
                # selector extraction logic (reused from _on_spy_selected)
                selector = args[1] if len(args) == 4 else (args[0] if len(args) == 1 else None)
                if not selector: return
                
                default_name = selector.get("ControlName") or selector.get("AutomationId") or "Element"
                name = simpledialog.askstring("Hızlı Kayıt", "Seçici İsmi:", initialvalue=default_name)
                
                # v167: If user cancels name, we still return to dialog
                if not name: 
                    dialog.grab_set()
                    return

                image_data = args[3] if len(args) == 4 else None
                self.db.save_selector(name, selector, image_data=image_data)
                if image_data: self.db.save_asset(name, image_data)
                
                # Automatically select it
                select_from_list(selector, name)
                refresh_selector_list()
                # v167: Removed blocking success message for seamless flow
                # messagebox.showinfo("Başarılı", f"'{name}' yakalandı ve kütüphaneye eklendi.")

            dialog.grab_release() # v167: Release grab before hiding
            dialog.withdraw() # Hide dialog for capture
            self.iconify()
            self.update() # v167: Force UI update to hide window
            import time
            time.sleep(0.2) # Small delay to ensure visual clear
            InspectorOverlay(self, on_captured)

        # Buttons Center Frame
        btn_center_frame = ctk.CTkFrame(tab_selector, fg_color="transparent")
        btn_center_frame.pack(pady=5)

        ctk.CTkButton(btn_center_frame, text="🎯 Yeni Seçici Yakala", command=pick_new_selector, fg_color="#E67E22").pack(side="left", padx=5)
        ctk.CTkButton(btn_center_frame, text="🔄 Listeyi Yenile", command=refresh_selector_list, width=100).pack(side="left", padx=5)
        
        sel_dir_var = ctk.StringVar(value="down")
        rb_sel_down = ctk.CTkRadioButton(tab_selector, text="⬇️ Aşağı Doğru Ara", variable=sel_dir_var, value="down")
        rb_sel_down.pack(pady=2)
        rb_sel_up = ctk.CTkRadioButton(tab_selector, text="⬆️ Yukarı Doğru Ara", variable=sel_dir_var, value="up")
        rb_sel_up.pack(pady=2)
        
        # Horizontal Frame for Max/Step
        val_frame = ctk.CTkFrame(tab_selector, fg_color="transparent")
        val_frame.pack(pady=5)
        
        ctk.CTkLabel(val_frame, text="Maks Adım:").pack(side="left", padx=5)
        sel_max_steps_var = ctk.StringVar(value="10")
        ctk.CTkEntry(val_frame, textvariable=sel_max_steps_var, width=60).pack(side="left", padx=5)
        
        ctk.CTkLabel(val_frame, text="Adım Miktarı:").pack(side="left", padx=5)
        sel_step_size_var = ctk.StringVar(value="300")
        ctk.CTkEntry(val_frame, textvariable=sel_step_size_var, width=60).pack(side="left", padx=5)

        refresh_selector_list()

        def add_smart_selector():
            if not self.smart_scroll_selector:
                messagebox.showerror("Hata", "Lütfen önce kütüphaneden bir seçici seçin.")
                return
            
            direction = sel_dir_var.get()
            try: max_steps = int(sel_max_steps_var.get())
            except: max_steps = 10
            
            try: step_val = int(sel_step_size_var.get())
            except: step_val = 300
            
            action = Action(type="SCROLL_UNTIL", 
                            params={
                                "selector": self.smart_scroll_selector["content"], 
                                "selector_name": self.smart_scroll_selector["name"],
                                "direction": direction, 
                                "max_steps": max_steps,
                                "step": step_val,
                                "by_selector": True
                            }, 
                            description=f"Scroll {direction.upper()} until element: {self.smart_scroll_selector['name']}")
            self.current_scenario.add_action(action)
            self.refresh_step_list()
            # v70.2: Auto-save
            if self.current_scenario.id:
                self.db.save_scenario(self.current_scenario)
            dialog.destroy()

        btn_add_sel_smart = ctk.CTkButton(tab_selector, text="Ekle", command=add_smart_selector, fg_color="#194E91", height=40)
        btn_add_sel_smart.pack(pady=10, fill="x", padx=20)

    def add_popup_step(self):
        """v160.6: Pop-up Yakalama adımı ekler."""
        action = Action(
            type="POPUP_CHECK", 
            description="Pop-up Kontrolü", 
            params={"triggers": []}
        )
        self.current_scenario.add_action(action) # Changed from .actions.append to .add_action
        self.refresh_step_list()
        # Otomatik düzenlemeyi aç
        # self.edit_step(len(self.current_scenario.actions) - 1) # This line is commented out or not present in the original context, so I'll keep it as is from the user's snippet.

    def add_wait_action(self):
        dialog = ctk.CTkInputDialog(text="Süre (saniye):", title="Wait Action")
        seconds = dialog.get_input()
        if seconds:
            action = Action(type="WAIT", params={"seconds": seconds}, description=f"Wait {seconds}s")
            self.current_scenario.add_action(action)
            self.refresh_step_list()
            # v70.2: Auto-save
            if self.current_scenario.id:
                self.db.save_scenario(self.current_scenario)

    # v167.24: GET TEXT & CHECK TEXT UI
    def add_get_text_action(self):
        """Ekranda seçilen bir alandaki metni okuyup değişkene kaydetme."""
        # Selector List
        selectors = self.db.list_selectors()
        if not selectors:
            messagebox.showwarning("Uyarı", "Kayıtlı seçici bulunamadı! Önce 'Seçiciler' menüsünden bir alan tanımlayın.")
            return
            
        sel_names = [s[1] for s in selectors]
        
        # Variable List (from scenario settings)
        var_names = list(self.current_scenario.variables.keys()) if self.current_scenario.variables else []
        if not var_names:
            messagebox.showwarning("Uyarı", "Senaryoda tanımlı değişken yok! Önce 'Değişken Tanımla' menüsünden değişken oluşturun.")
            return
            
        # Dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Veri Okuma (Get Text)")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Hangi alandan okunacak?", font=("Arial", 12, "bold")).pack(pady=5)
        cmb_selector = ctk.CTkComboBox(dialog, values=sel_names)
        cmb_selector.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Hangi değişkene kaydedilecek?", font=("Arial", 12, "bold")).pack(pady=5)
        cmb_variable = ctk.CTkComboBox(dialog, values=var_names)
        cmb_variable.set(var_names[0])
        cmb_variable.pack(pady=5)
        
        def save():
            sel = cmb_selector.get()
            var = cmb_variable.get()
            
            if not sel or not var: return
            
            action = Action(
                type="GET_TEXT", 
                params={"selector": sel, "variable": var}, 
                description=f"Read Text: '{sel}' -> ${{{var}}}"
            )
            self.current_scenario.add_action(action)
            self.refresh_step_list()
            if self.current_scenario.id: self.db.save_scenario(self.current_scenario)
            dialog.destroy()
            
        ctk.CTkButton(dialog, text="Ekle", command=save, fg_color="#27AE60").pack(pady=20)

    def add_check_text_action(self):
        """Bir değişkenin değerini kontrol etme."""
        # Variable List
        var_names = list(self.current_scenario.variables.keys()) if self.current_scenario.variables else []
        if not var_names:
            messagebox.showwarning("Uyarı", "Senaryoda tanımlı değişken yok! Önce değişken tanımlayın.")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Veri Kontrolü (Check Text)")
        dialog.geometry("400x350")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Kontrol Edilecek Değişken:", font=("Arial", 12, "bold")).pack(pady=5)
        cmb_variable = ctk.CTkComboBox(dialog, values=var_names)
        cmb_variable.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Koşul:", font=("Arial", 12, "bold")).pack(pady=5)
        cmb_condition = ctk.CTkComboBox(dialog, values=["equals", "contains"], state="readonly")
        cmb_condition.set("equals")
        cmb_condition.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Beklenen Değer:", font=("Arial", 12, "bold")).pack(pady=5)
        ent_value = ctk.CTkEntry(dialog, placeholder_text="Örn: Başarılı")
        ent_value.pack(pady=5)
        
        def save():
            var = cmb_variable.get()
            cond = cmb_condition.get()
            val = ent_value.get()
            
            if not var or not val: return
            
            action = Action(
                type="CHECK_TEXT",
                params={"variable": var, "condition": cond, "value": val},
                description=f"Check: ${{{var}}} {cond} '{val}'"
            )
            self.current_scenario.add_action(action)
            self.refresh_step_list()
            if self.current_scenario.id: self.db.save_scenario(self.current_scenario)
            dialog.destroy()
            
        ctk.CTkButton(dialog, text="Ekle", command=save, fg_color="#E74C3C").pack(pady=20)

    # --- v162.0: Hızlı Kayıt Araçları (Restored v167.26) ---
    def open_quick_save_dialog(self):
        """Kütüphanelere hızlıca veri eklemek için bir diyalog açar."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Hızlı Kayıt Paneli")
        dialog.geometry("350x250")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Ne Kaydedilecek?", font=("Arial", 14, "bold")).pack(pady=20)
        
        btn_img = ctk.CTkButton(dialog, text="🖼️ Görsel Kaydet (Snip)", height=45, fg_color="#3498DB",
                               command=lambda: [dialog.destroy(), self.quick_save_image()])
        btn_img.pack(pady=10, padx=20, fill="x")

        btn_sel = ctk.CTkButton(dialog, text="🎯 Selector Kaydet (Spy)", height=45, fg_color="#9B59B6",
                               command=lambda: [dialog.destroy(), self.quick_save_selector()])
        btn_sel.pack(pady=10, padx=20, fill="x")

    def quick_save_image(self):
        """Sadece kütüphaneye kaydetmek üzere SnipTool başlatır."""
        self.start_snip_tool(self._on_quick_snip_complete)

    def _on_quick_snip_complete(self, filepath, offset=(0, 0)):
        """Görseli sadece DB'ye kaydeder, aksiyon eklemez."""
        name = simpledialog.askstring("Kütüphaneye Kaydet", "Görsel İsmi:")
        if not name or not name.strip():
            if os.path.exists(filepath): os.remove(filepath)
            return
            
        self.db.save_asset(name, filepath)
        try: os.remove(filepath) # Geçici dosyayı sil
        except: pass
        
        messagebox.showinfo("Başarılı", f"'{name}' görseli kütüphaneye kaydedildi.")

    def quick_save_selector(self):
        """Sadece kütüphaneye kaydetmek üzere InspectorOverlay başlatır."""
        self.iconify()
        InspectorOverlay(self, self._on_quick_spy_selected)

    def _on_quick_spy_selected(self, *args):
        """Selectorü sadece DB'ye kaydeder, aksiyon eklemez."""
        self.deiconify()
        
        selector = None
        image_data = None
        
        if len(args) == 4:
            _, selector, _, image_data = args
        elif len(args) == 1:
            selector = args[0]

        if not selector: return

        default_name = selector.get("ControlName") or selector.get("AutomationId") or "Element"
        name = simpledialog.askstring("Seçiciyi Kaydet", "Seçici İsmi:", initialvalue=default_name)
        
        if not name: return

        self.db.save_selector(name, selector, image_data=image_data)
        if image_data:
            self.db.save_asset(name, image_data)
        
        messagebox.showinfo("Başarılı", f"'{name}' seçicisi kütüphaneye kaydedildi.")
            
    def add_launch_action(self):
        file_path = filedialog.askopenfilename(title="Uygulama Seç", filetypes=[("Executables", "*.exe"), ("All Files", "*.*")])
        if file_path:
            action = Action(type="LAUNCH_APP", params={"path": file_path}, description=f"Open {os.path.basename(file_path)}")
            self.current_scenario.add_action(action)
            self.refresh_step_list()
            # v70.2: Auto-save
            if self.current_scenario.id:
                self.db.save_scenario(self.current_scenario)

    def add_open_browser_action(self):
        url = simpledialog.askstring("Siteye Git", "Açılacak URL adresi (Örn: google.com):", initialvalue="https://")
        if url:
             # Eğer kullanıcı http/https eklememişse biz ekleyelim
            if not url.startswith("http"):
                url = "https://" + url
            
            action = Action(type="OPEN_URL", params={"url": url}, description=f"Open URL: {url}")
            self.current_scenario.add_action(action)
            self.refresh_step_list()
            # v70.2: Auto-save
            if self.current_scenario.id:
                self.db.save_scenario(self.current_scenario)
            
    def add_assert_action(self):
        target = filedialog.askopenfilename(title="Aranacak Görseli Seç", filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if target:
            action = Action(type="ASSERT_EXISTS", params={"target": target}, description=f"Assert Exists: {os.path.basename(target)}")
            self.current_scenario.add_action(action)
            self.current_scenario.add_action(action)
            self.refresh_step_list()

    def add_variable_action(self):
        """v167.17: Değişken Tanımlama (Senaryo Ayarları)"""
        def on_vars_saved(variables_dict):
            # v167.17: Senaryoya değişkenleri kaydet
            self.current_scenario.variables = variables_dict
            
            if self.current_scenario.id:
                self.db.save_scenario(self.current_scenario)
            # v167.36: Removed success message boxes per user request

        VariableDefinitionDialog(self, on_vars_saved, initial_variables=self.current_scenario.variables)

    def add_popup_handler_action(self):
        """v67: Popup Giderici Ekleme - Snip -> DB -> Action"""
        messagebox.showinfo("Bilgi", "Kapatılacak Popup'ın butonunu (Tamam/Kapat/X) seçin.")
        self.start_snip_tool(self._on_popup_snip_complete)

    def _on_popup_snip_complete(self, filepath, offset=(0, 0)):
        name = simpledialog.askstring("Kütüphaneye Kaydet", f"Popup Görseli Adı (Offset: {offset}):")
        
        if name is None: return
        if not name.strip():
            name = f"popup_{os.path.basename(filepath)}"
            
        # DB'ye kaydet ve dosyayı sil
        self.db.save_asset(name, filepath)
        try: os.remove(filepath)
        except: pass
        
        # Action ekle
        action = Action(type="HANDLE_POPUP", 
                        params={"target": name}, 
                        description=f"Handle Popup: {name}")
        self.current_scenario.add_action(action)
        self.refresh_step_list()
        
        # v70.1: Auto-save
        if self.current_scenario.id:
            self.db.save_scenario(self.current_scenario)

    # --- Çalıştırma ve Kayıt ---
    def on_speed_change(self, value):
        self.runner.action_delay = float(value)
        self.lbl_speed.configure(text=f"İşlem Gecikmesi (sn): {value:.1f}")

    def run_scenario(self):
        """Senaryoyu baştan başlatır."""
        self._start_execution(start_index=0)

    def run_scenario_from_step(self, index):
        """Senaryoyu belirtilen adımdan başlatır (Debug)."""
        self._start_execution(start_index=index)

    def _start_execution(self, start_index=0):
        if not self.current_scenario.actions:
            messagebox.showwarning("Uyarı", "Senaryoda hiç adım yok!")
            return

        # Disable buttons
        self.btn_run.configure(state="disabled", text="⏳ Çalışıyor...", fg_color="gray")
        if hasattr(self, 'btn_smart_rec'):
             self.btn_smart_rec.configure(state="disabled")
        
        # Overlay'i göster
        self.overlay.show()
        
        # v160.5: Minimize main window to see target app
        # Kullanıcı isteği: "bizim uygulama ön planda... arka planda o... gelmiyor"
        self.iconify()
        
        # Runner'ı başlat
        self.runner.run_scenario(
            self.current_scenario, 
            on_finish=self._on_scenario_finished,
            start_index=start_index
        )

    def stop_scenario(self):
        self.runner.stop()

    def _on_scenario_finished(self, success, error_msg):
        # Overlay Gizle
        self.overlay.hide()
        
        # v160.5: Restore main window
        self.deiconify()
        self.state('normal')
        
        # Pencereyi öne getir
        self.lift()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        
        self.btn_run.configure(state="normal", text="▶ Senaryoyu Çalıştır", fg_color="#2CC985")
        if success:
            status = "Başarılı"
        else:
            status = "Hata"
        messagebox.showinfo("Sonuç", f"Senaryo tamamlandı: {status}\n{error_msg}")

    # --- Database Operations ---
    def save_to_db(self):
        # v75: Allow saving empty scenarios
        
        # v70.3: Eğer senaryo zaten kayıtlıysa, direkt güncelle (Sorma)
        if self.current_scenario.id and self.current_scenario.name and self.current_scenario.name != "Yeni Senaryo":
            res = self.db.save_scenario(self.current_scenario)
            if res:
                messagebox.showinfo("Başarılı", "Senaryo güncellendi.")
            else:
                messagebox.showerror("Hata", "Güncellenemedi.")
            return
            
        dialog = ctk.CTkInputDialog(text="Senaryo Adı:", title="Kaydet")
        name = dialog.get_input()
        if name:
            self.current_scenario.name = name
            res = self.db.save_scenario(self.current_scenario)
            if res:
                messagebox.showinfo("Başarılı", f"Senaryo veritabanına kaydedildi. ID: {res}")
            else:
                messagebox.showerror("Hata", "Veritabanına kaydedilemedi.")

    def show_scenarios(self):
        if self.scenario_browser_win and self.scenario_browser_win.winfo_exists():
            self.scenario_browser_win.focus_force()
            self.scenario_browser_win.lift()
            return
            
        self.scenario_browser_win = DatabaseBrowser(self, self.db, self.on_load_from_db)
        self.scenario_browser_win.grab_set()

    def on_load_from_db(self, scenario):
        self.current_scenario = scenario
        self.refresh_step_list()
        messagebox.showinfo("Yüklendi", f"'{scenario.name}' senaryosu yüklendi.")

    def add_validation_action(self):
        # Seçenekler sunan bir pencere aç
        dialog = ctk.CTkToplevel(self)
        dialog.title("Doğrulama Türü Seç")
        dialog.geometry("300x200")
        dialog.grab_set()
        
        lbl = ctk.CTkLabel(dialog, text="Hangi tür doğrulama eklemek istersiniz?", wraplength=250)
        lbl.pack(pady=10)
        
        def pick_window():
            dialog.destroy()
            title = ctk.CTkInputDialog(text="Kontrol edilecek pencere başlığı:", title="Pencere Doğrulama").get_input()
            if title:
                action = Action(type="VALIDATE_WINDOW", params={"title": title, "timeout": 5}, description=f"Validate Window: {title}")
                self.current_scenario.add_action(action)
                self.refresh_step_list()

        def pick_element():
            dialog.destroy()
            win_title = ctk.CTkInputDialog(text="Pencere başlığı:", title="Element Doğrulama").get_input()
            if not win_title: return
            el_name = ctk.CTkInputDialog(text="Element adı (Buton/Yazı):", title="Element Doğrulama").get_input()
            if el_name:
                action = Action(type="VALIDATE_ELEMENT", params={"window_title": win_title, "element_name": el_name, "timeout": 5}, description=f"Validate Element '{el_name}' in '{win_title}'")
                self.current_scenario.add_action(action)
                self.refresh_step_list()

        btn_win = ctk.CTkButton(dialog, text="Pencere Açık mı?", command=pick_window)
        btn_win.pack(pady=5, padx=20, fill="x")
        
        btn_el = ctk.CTkButton(dialog, text="Element/Buton Var mı?", command=pick_element)
        btn_el.pack(pady=5, padx=20, fill="x")

    def add_assert_action(self):
        # GÜNCELLEME (v51): SnipTool ile görsel seçimi ve timeout ayarı
        self.start_snip_tool(self._on_manual_assert_snip_complete)

    def _on_manual_assert_snip_complete(self, filepath, offset=(0, 0)):
        # Pencerenin odağını geri al (Z-order fix)
        self.focus_force()
        self.lift()
        
        name = simpledialog.askstring("Kütüphaneye Kaydet", f"Doğrulama Görseli Adı (Offset: {offset}):", parent=self)
        if name is None: return
        if not name.strip(): name = f"manual_assert_{os.path.basename(filepath)}"
        self.db.save_asset(name, filepath)

        # Timeout sor
        # parent=self ekleyerek ana pencerenin arkasında kalmasını engelliyoruz
        timeout_str = simpledialog.askstring("Bekleme Süresi", "Maksimum kaç saniye beklensin? (Erken gelirse beklemez)", initialvalue="10", parent=self)
        try:
            timeout = int(timeout_str) if timeout_str else 10
        except: timeout = 10
        
        action = Action(type="ASSERT_EXISTS", 
                        params={"target": filepath, "timeout": timeout}, 
                        description=f"Wait for: {name} ({timeout}s)",
                        offset=offset)
        self.current_scenario.add_action(action)
        self.refresh_step_list()
        
        # v70.3: Manuel otomatik kaydet
        if self.current_scenario.id:
            self.db.save_scenario(self.current_scenario)

    def export_scenario(self):
        """v71.1: Çoklu Seçim ile Dışa Aktarma"""
        scenarios = self.db.list_scenarios()
        if not scenarios:
            messagebox.showwarning("Uyarı", "Dışa aktarılacak senaryo yok.")
            return

        # Seçim Diyalogu
        dialog = ctk.CTkToplevel(self)
        dialog.title("Dışa Aktar")
        dialog.geometry("400x500")
        dialog.grab_set()

        lbl = ctk.CTkLabel(dialog, text="Dışa Aktarılacak Senaryoları Seçin:", font=("Arial", 14, "bold"))
        lbl.pack(pady=10)

        scroll_frame = ctk.CTkScrollableFrame(dialog, height=300)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        vars_map = {} # {id: (IntVar, name)}

        # "Tümünü Seç"
        def toggle_all():
             state = all_var.get()
             for s_id, (var, _) in vars_map.items():
                 var.set(state)

        all_var = ctk.IntVar(value=0)
        cb_all = ctk.CTkCheckBox(scroll_frame, text="Tümünü Seç", variable=all_var, command=toggle_all, font=("Arial", 12, "bold"))
        cb_all.pack(anchor="w", pady=5)
        
        # Liste
        for s_id, name, desc, created in scenarios:
            var = ctk.IntVar(value=0)
            vars_map[s_id] = (var, name)
            cb = ctk.CTkCheckBox(scroll_frame, text=name, variable=var)
            cb.pack(anchor="w", pady=2, padx=10)

        def do_export():
            selected_ids = [s_id for s_id, (var, _) in vars_map.items() if var.get() == 1]
            if not selected_ids:
                messagebox.showwarning("Uyarı", "Hiçbir senaryo seçilmedi.")
                return

            save_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")], initialfile=f"export_{len(selected_ids)}_scenarios.json")
            if not save_path: return

            export_data = {"scenarios": [], "_embedded_assets": {}}
            
            # Asset toplama
            import base64
            all_assets = self.db.list_assets() # (id, name, created, data)
            asset_map = {name: data for _, name, _, data in all_assets if data}
            
            used_asset_names = set()

            for s_id in selected_ids:
                sc = self.db.load_scenario_by_id(s_id)
                if sc:
                    export_data["scenarios"].append(sc.as_dict())
                    # Senaryodaki assetleri bul
                    from core.scenario import Action
                    for action_dict in sc.as_dict()["actions"]: # Dict olarak geliyor
                        # Action dict yapısını kontrol et
                        params = action_dict.get("params", {})
                        target = params.get("target")
                        if target and isinstance(target, str):
                            # Asset ismini çıkar
                            asset_name = os.path.basename(target)
                            if asset_name in asset_map:
                                used_asset_names.add(asset_name)
                                # Ayrıca "clean_name" olarak da asset ismini kullanıyoruz importta, o yüzden direkt asset ismini target yapıyoruz export verisinde?
                                # Hayır, import ederken temizliyoruz.
            
            # Embed Assets
            for name in used_asset_names:
                export_data["_embedded_assets"][name] = base64.b64encode(asset_map[name]).decode('utf-8')

            # v160.1: Export Linked Selectors
            # We need to find which selectors are used in these scenarios.
            # Look for actions with type 'CLICK_SELECTOR' or any action having 'selector_name' params.
            used_selector_names = set()
            for s_id in selected_ids:
                 sc = self.db.load_scenario_by_id(s_id)
                 if sc:
                     for action in sc.actions:
                         if action.params and "selector_name" in action.params:
                             used_selector_names.add(action.params["selector_name"])

            if used_selector_names:
                export_data["selectors"] = []
                # Fetch all selectors to find matches (or fetch by name if we had a method)
                all_selectors = self.db.list_selectors() # (id, name, type, content, created, image)
                for sel in all_selectors:
                    # sel schema might vary based on DB version, check list_selectors implementation
                    # Standard: id, name, type, content, created_at, image_data
                    if len(sel) == 6:
                        s_id, s_name, s_type, s_content, s_created, s_image = sel
                    else:
                        s_id, s_name, s_type, s_content, s_created = sel
                        s_image = None
                    
                    if s_name in used_selector_names:
                        # Prepare dict
                        sel_dict = {
                            "name": s_name,
                            "type": s_type,
                            "content": s_content,
                            "image_data": base64.b64encode(s_image).decode('utf-8') if s_image else None
                        }
                        export_data["selectors"].append(sel_dict)

            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=4, ensure_ascii=False)
                messagebox.showinfo("Başarılı", f"{len(selected_ids)} senaryo dışa aktarıldı.")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Hata", f"Dışa aktarma hatası: {e}")

        btn_exp = ctk.CTkButton(dialog, text="Seçilenleri Dışa Aktar", command=do_export, fg_color="#2CC985")
        btn_exp.pack(pady=20, fill="x", padx=20)

    def import_scenario(self):
        """Dışarıdan gelen JSON senaryoyu içe aktarır ve resimleri DB'ye yazar (v63)."""
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not file_path: return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Assetleri içeri al
            import base64
            from core.config import ASSETS_DIR
            
            # v71: ASSETS_DIR varlığından emin ol
            try: os.makedirs(ASSETS_DIR, exist_ok=True)
            except: pass
            
            if "_embedded_assets" in data:
                for name, b64_data in data["_embedded_assets"].items():
                    try:
                        binary = base64.b64decode(b64_data)
                        tmp_path = os.path.join(ASSETS_DIR, f"imported_{name}")
                        # Uzantı kontrolü
                        if not os.path.splitext(tmp_path)[1]:
                             tmp_path += ".png"
                             
                        with open(tmp_path, 'wb') as f_out:
                            f_out.write(binary)
                        
                        self.db.save_asset(name, tmp_path)
                    except Exception as e:
                        print(f"Asset import hatası ({name}): {e}")
            
            # v160.1: Import Selectors
            if "selectors" in data:
                for sel_dict in data["selectors"]:
                    try:
                        name = sel_dict["name"]
                        sType = sel_dict["type"]
                        content = sel_dict["content"]
                        b64_img = sel_dict.get("image_data")
                        
                        img_bytes = None
                        if b64_img:
                            img_bytes = base64.b64decode(b64_img)
                        
                        # Save Selector
                        # Check existance? save_selector inserts new. 
                        # Ideally we should check if exists or update, but for now let's insert (DB autoincrements ID)
                        # But name might be unique requirement? DB schema doesn't force unique name on selectors usually?
                        # Let's just save.
                        self.db.save_selector(name, content, sType, image_data=img_bytes)
                        
                        # Also save to Assets per requirement
                        if img_bytes:
                             self.db.save_asset(name, img_bytes)

                    except Exception as e:
                        print(f"Selector import hatası: {e}")
            
            scenarios_list = []
            if "scenarios" in data: # v71.1: Çoklu Senaryo Formatı
                 scenarios_list = data["scenarios"]
            else: # Eski (Tek Senaryo)
                 # _embedded_assets vs çıkarıp kalanı scenario dict olarak alalım
                 data_copy = data.copy()
                 if "_embedded_assets" in data_copy: del data_copy["_embedded_assets"]
                 scenarios_list = [data_copy]
            
            imported_count = 0
            for sc_dict in scenarios_list:
                scenario = Scenario.from_dict(sc_dict)
                # v71: Konum Temizleme (Path Sanitization)
                for action in scenario.actions:
                    if action.params and "target" in action.params:
                        target = action.params["target"]
                        if target and isinstance(target, str):
                            if os.path.sep in target or "/" in target:
                                clean_name = os.path.basename(target)
                                action.params["target"] = clean_name
                                if action.description and target in action.description:
                                    action.description = action.description.replace(target, clean_name)
                
                # Yeni ID ile kaydet (Çakışmayı önlemek için yeni insert)
                scenario.id = None # ID'yi sıfırla ki yeni insert yapsın
                self.db.save_scenario(scenario)
                imported_count += 1

            self.refresh_step_list()
            messagebox.showinfo("Başarılı", f"{imported_count} senaryo içe aktarıldı.")
        except Exception as e:
            messagebox.showerror("Hata", f"İçe aktarma hatası: {e}")

    def show_asset_browser(self):
        if self.asset_browser_win and self.asset_browser_win.winfo_exists():
            self.asset_browser_win.focus_force()
            self.asset_browser_win.lift()
            return
            
        # v66: Sadece Görüntüleme Modu (View Only)
        self.asset_browser_win = AssetBrowser(self, self.db, None, mode="view")
        self.asset_browser_win.grab_set()

    def change_step_image(self, index):
        """v64: Mevcut adımın görselini kütüphaneden başka bir görselle değiştirir."""
        if self.asset_browser_win and self.asset_browser_win.winfo_exists():
            self.asset_browser_win.destroy()
        
        def on_selected(path, name):
            action = self.current_scenario.actions[index]
            action.params["target"] = name # v66: Hedef olarak ismi kullan
            # Description'ı da güncellemeye çalışalım
            if "Click:" in action.description or "Repo:" in action.description:
                action.description = f"{action.type} (Repo): {name}"
            self.refresh_step_list()
            messagebox.showinfo("Değiştirildi", f"Adım görseli '{name}' ile güncellendi.")

        self.asset_browser_win = AssetBrowser(self, self.db, on_selected, mode="pick")
        self.asset_browser_win.grab_set()

    def on_asset_selected(self, asset_path, asset_name):
        action = Action(type="CLICK", params={"target": asset_path, "by_image": True}, description=f"Click (Repo): {asset_name}")
        self.current_scenario.add_action(action)
        self.refresh_step_list()
        messagebox.showinfo("Eklendi", f"'{asset_name}' kütüphaneden senaryoya eklendi.")

    def show_selector_browser(self):
        if hasattr(self, 'selector_browser_win') and self.selector_browser_win and self.selector_browser_win.winfo_exists():
            self.selector_browser_win.focus_force()
            self.selector_browser_win.lift()
            return

        def on_select(selector_data):
            pass

        self.selector_browser_win = SelectorBrowser(self, self.db, on_select, mode="view")
        self.selector_browser_win.grab_set()

    def start_inspector(self, click_type="left"):
        # v80: Lauch Spy Tool
        self.last_click_type = click_type # Store for callback
        self.iconify() # Hide window
        InspectorOverlay(self, self._on_spy_selected)
        
    def _on_spy_selected(self, *args):
        self.deiconify() # Show window
        
        click_type = getattr(self, "last_click_type", "left")
        
        # Handle different callback signatures
        selector = None
        desc = ""
        image_data = None # v110: Image Support
        
        if len(args) == 1:
            selector = args[0]
            desc = "Selector Action"
        elif len(args) == 3:
            _, selector, desc = args
        elif len(args) == 4:
            _, selector, desc, image_data = args
        else:
            return

        if not selector: return

        # v130: Volatile Attribute Filtering (Input Sanitization)
        # If AutomationId exists and ControlType suggests input (Edit, Document),
        # Remove 'ControlName' because it likely contains the input text (Value).
        # v130+ Broadened Volatile Types
        # Some inputs appear as Text, Pane, Group in UIA.
        volatile_types = ["EditControl", "DocumentControl", "ComboBoxControl", 
                          "TextControl", "PaneControl", "GroupControl", "CustomControl"]
        
        # We should prompt if there is a Name that might be dynamic content.
        # But for Pane/Group, Name might be static label.
        # For Edit/Document, Name IS usually the content.
        
        should_prompt = False
        val_name = selector.get("ControlName")
        ctype = selector.get("ControlType")

        if val_name:
            if ctype in ["EditControl", "DocumentControl", "ComboBoxControl"]:
                 should_prompt = True
            elif ctype in ["TextControl", "PaneControl", "GroupControl", "CustomControl"]:
                 # heuristic: if name is numeric or looks like data
                 if val_name.isdigit() or len(val_name) > 20: 
                     should_prompt = True
                 # Or if we have an AutomationId, maybe we can afford to ask
                 elif selector.get("AutomationId"):
                     should_prompt = True

        if should_prompt:
            val_name = selector.get("ControlName")
            # ...
            val_name = selector.get("ControlName")
            if val_name:
                # v130+ Prompt User
                msg = (f"Bu bir giriş alanı ve metin içeriyor ('{val_name}').\n\n"
                       "Selector'a metin içeriğini de eklemek ister misiniz?\n\n"
                       "EVET: Sadece bu metni içerdiğinde bulur (Doğrulama için).\n"
                       "HAYIR: Metin ne olursa olsun bulur (Veri girişi için - Önerilen).")
                
                if not messagebox.askyesno("Metin İçeriği", msg):
                    removed_val = selector.pop("ControlName")
                    print(f"Volatile attribute filtered by user request: ControlName='{removed_val}'")

        # Ask User for Name (for DB and Action)
        default_name = selector.get("ControlName") or selector.get("AutomationId") or "Element"
        name = simpledialog.askstring("Seçiciyi Kaydet", "Bu element için bir isim girin:", initialvalue=default_name)
        
        if not name: return

        # Save to DB (v110: pass image_data)
        self.db.save_selector(name, selector, image_data=image_data)

        # v160.1: Also save as Visual Element (Asset) if image exists
        if image_data:
            # Use a prefix to distinguish, or just the same name?
            # User wants: "Kaydettiğimiz selector görsellerini aynı zamanda Visual Elements e de kaydedelim"
            # Let's use the same name to be neat, maybe with a prefix if needed, but name should be unique in assets too?
            # Assets and Selectors are different tables, but let's try to keep name unique or just save it.
            # If name exists in assets, it might duplicate or error. save_asset creates new entry.
            self.db.save_asset(name, image_data)  # Pass bytes directly
        
        # Create Action
        # We use the NAME as reference if we want to be like 'Asset', but for now let's embed the selector 
        # OR use the name to look it up? 
        # The user request says "Visual Elements" (repo) and "Selectors" (repo). 
        # So we should probably store the ID or Name.
        # But for robust execution, embedding the selector in params is better, 
        # and maybe just referencing the name for UI.
        
        # Let's create a "CLICK_SELECTOR" action
        params = {
            "selector": selector, # Embed for now (or could use ID if we implement a driver that reads from DB)
            "selector_name": name,
            "button": click_type,
            "timeout": 10
        }
        
        type_desc = "Click"
        if click_type == "right": type_desc = "Right Click"
        elif click_type == "double": type_desc = "Double Click"

        action = Action(type="CLICK_SELECTOR", params=params, description=f"{type_desc}: {name}")
        self.current_scenario.add_action(action)
        self.refresh_step_list()
        
        if self.current_scenario.id:
            self.db.save_scenario(self.current_scenario)
            
        messagebox.showinfo("Başarılı", "Seçici kaydedildi ve aksiyon eklendi!")
        # We need to implement TYPE_SELECTOR in runner loop too if not exists
        # For now let's stick to known types or map them.
        # Actually structure_driver.type_text? No, just click and type using Keyboard.
        # Let's add explicit 'TYPE_SELECTOR' support later or map to Click+Type
        ctk.CTkButton(dialog, text="Ekle", command=apply).pack(pady=20)
        
        # Wait for dialog
        dialog.wait_window()


class AssetBrowser(ctk.CTkToplevel):
    def __init__(self, master, db, callback, mode="view"):
        super().__init__(master)
        self.title("Görsel Depo")
        self.geometry("600x700")
        self.db = db
        self.callback = callback
        self.mode = mode # view | pick
        
        from PIL import Image, ImageTk
        self.pil_image_refs = [] # Keep refs to avoid garbage collection
        
        title = "Kayıtlı Görseller (Veritabanı)"
        if self.mode == "pick":
            title += " - Seçim Modu"
            
        self.lbl = ctk.CTkLabel(self, text=title, font=("Arial", 16, "bold"))
        self.lbl.pack(pady=10)
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.refresh_list()
        
    def refresh_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.pil_image_refs = []
            
        assets = self.db.list_assets()
        for a_id, name, created, data in assets:
            frame = ctk.CTkFrame(self.scrollable_frame)
            frame.pack(fill="x", pady=5, padx=5)
            
            # PHASE 1: PREVIEW (v63)
            img_label = None
            if data:
                try:
                    import io
                    from PIL import Image, ImageTk
                    pil_img = Image.open(io.BytesIO(data))
                    # Resize for preview
                    pil_img.thumbnail((60, 60))
                    tk_img = ImageTk.PhotoImage(pil_img)
                    self.pil_image_refs.append(tk_img)
                    img_label = ctk.CTkLabel(frame, image=tk_img, text="")
                    img_label.pack(side="left", padx=5)
                except Exception as e:
                    print(f"Error loading image for preview: {e}")
            
            # Metadata
            lbl_info = ctk.CTkLabel(frame, text=f"{name}\n({len(data or b'')/1024:.1f} KB)", anchor="w", justify="left")
            lbl_info.pack(side="left", padx=10, expand=True, fill="x")
            
            # Button Logic
            btn_zoom = ctk.CTkButton(frame, text="🔍", width=30, fg_color="gray", command=lambda d=data, n=name: self.show_zoom(d, n))
            btn_zoom.pack(side="right", padx=2)

            if self.mode == "pick":
                # v66: Path yerine Name kullanıyoruz çünkü dosyalar siliniyor.
                btn_use = ctk.CTkButton(frame, text="Seç", width=60, command=lambda n=name: self.use_asset(n, n))
                btn_use.pack(side="right", padx=5)
            
            btn_del = ctk.CTkButton(frame, text="🗑️", width=30, fg_color="red", command=lambda i=a_id: self.delete_asset(i))
            btn_del.pack(side="right", padx=2)

    def show_zoom(self, data, name):
        """v70: Resim Büyütme (Zoom)"""
        if not data: return
        
        top = ctk.CTkToplevel(self)
        top.title(f"Önizleme: {name}")
        top.attributes('-topmost', True) # v70.2 Fix: Arkada kalmasın
        top.geometry("800x600")
        
        try:
            import io
            from PIL import Image, ImageTk
            pil_img = Image.open(io.BytesIO(data))
            
            # Ekrana sığdır
            img_w, img_h = pil_img.size
            if img_w > 800 or img_h > 600:
                pil_img.thumbnail((800, 600))
                
            tk_img = ImageTk.PhotoImage(pil_img)
            
            lbl = ctk.CTkLabel(top, text="", image=tk_img)
            lbl.image = tk_img # Keep ref
            lbl.pack(expand=True, fill="both")
        except Exception as e:
            messagebox.showerror("Hata", f"Görüntülenemedi: {e}")

    def use_asset(self, path, name):
        # v66: path parametresi aslında 'name' olarak geliyor yukarıdan
        self.callback(path, name)
        self.destroy()

    def delete_asset(self, a_id):
        if messagebox.askyesno("Onay", "Bu görseli kütüphaneden silmek istediğinize emin misiniz?"):
            if self.db.delete_asset(a_id):
                self.refresh_list()
            else:
                messagebox.showerror("Hata", "Silinemedi.")



class DatabaseBrowser(ctk.CTkToplevel):
    def __init__(self, master, db, callback):
        super().__init__(master)
        self.title("Senaryo Kütüphanesi")
        self.geometry("400x500")
        self.db = db
        self.callback = callback
        
        self.lbl = ctk.CTkLabel(self, text="Kayıtlı Senaryolar", font=("Arial", 16, "bold"))
        self.lbl.pack(pady=10)
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.refresh_list()
        
    def refresh_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        scenarios = self.db.list_scenarios()
        for s_id, name, desc, created in scenarios:
            frame = ctk.CTkFrame(self.scrollable_frame)
            frame.pack(fill="x", pady=2)
            
            lbl_name = ctk.CTkLabel(frame, text=f"{name}\n({created[:16]})", anchor="w", justify="left")
            lbl_name.pack(side="left", padx=5, expand=True, fill="x")
            
            btn_load = ctk.CTkButton(frame, text="Seç", width=60, command=lambda i=s_id: self.load_one(i))
            btn_load.pack(side="right", padx=5, pady=5)
            
            btn_del = ctk.CTkButton(frame, text="🗑️", width=30, fg_color="red", command=lambda i=s_id: self.delete_one(i))
            btn_del.pack(side="right", padx=2)

    def load_one(self, s_id):
        scenario = self.db.load_scenario_by_id(s_id)
        if scenario:
            self.callback(scenario)
            self.destroy()

    def delete_one(self, s_id):
        if messagebox.askyesno("Onay", "Bu senaryoyu silmek istediğinize emin misiniz?"):
            if self.db.delete_scenario(s_id):
                self.refresh_list()
            else:
                messagebox.showerror("Hata", "Silinemedi.")


class SelectorBrowser(ctk.CTkToplevel):
    def __init__(self, master, db, callback, mode="view"):
        super().__init__(master)
        self.title("Seçici Kütüphanesi")
        self.geometry("800x600") # v167.32: Genişletildi
        self.db = db
        self.callback = callback
        self.mode = mode
        self.pil_image_refs = []
        
        self.lbl = ctk.CTkLabel(self, text="Kayıtlı Seçiciler (Selectors)", font=("Arial", 16, "bold"))
        self.lbl.pack(pady=10)
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.refresh_list()
        
    def refresh_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.pil_image_refs = [] # Referansları tut
            
        selectors = self.db.list_selectors()
        
        if not selectors:
            ctk.CTkLabel(self.scrollable_frame, text="Henüz kayıtlı seçici yok.", text_color="gray").pack(pady=20)
            return

        for sel in selectors:
            # sel: (id, name, type, content, created_at, image_data)
            # Eski şema/veriyi zarifçe işle
            if len(sel) == 6:
                sel_id, name, sel_type, content, created_at, image_data = sel
            else:
                sel_id, name, sel_type, content, created_at = sel
                image_data = None
            
            frame = ctk.CTkFrame(self.scrollable_frame)
            frame.pack(fill="x", pady=5, padx=5)
            
            # v167.33: Layout Refactor - Top Row (Content), Bottom Row (Buttons)
            top_row = ctk.CTkFrame(frame, fg_color="transparent")
            top_row.pack(fill="x", padx=5, pady=5)
            
            # --- Görsel Küçük Resim (Sol) ---
            if image_data:
                try:
                    import io
                    from PIL import Image, ImageTk
                    pil_img = Image.open(io.BytesIO(image_data))
                    pil_img.thumbnail((80, 80)) # Seçiciler için daha büyük küçük resim
                    tk_img = ImageTk.PhotoImage(pil_img)
                    self.pil_image_refs.append(tk_img)
                    
                    img_lbl = ctk.CTkLabel(top_row, image=tk_img, text="")
                    img_lbl.pack(side="left", padx=5, pady=5)
                except Exception as e:
                    print(f"Selector görseli yükleme hatası: {e}")

            # --- Bilgi (Orta) ---
            info_frame = ctk.CTkFrame(top_row, fg_color="transparent")
            info_frame.pack(side="left", padx=10, pady=5, fill="x", expand=True)
            
            # v167.32: Uzun isimleri kısalt
            display_name = name
            if len(display_name) > 40:
                display_name = display_name[:37] + "..."
            
            ctk.CTkLabel(info_frame, text=display_name, font=("Arial", 14, "bold")).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Type: {sel_type} | Date: {created_at}", font=("Arial", 10)).pack(anchor="w")
            
            # Tam İçeriği Göster (Sarılabilir)
            content_str = str(content)
            txt = ctk.CTkTextbox(info_frame, height=60, font=("Consolas", 10), activate_scrollbars=True)
            txt.insert("1.0", content_str)
            txt.configure(state="disabled") # Salt-okunur
            txt.pack(fill="x", pady=2)

            # --- Kontroller (Alt Satır) ---
            # v167.33: Butonları alta taşı
            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=5) # side default top (under top_row)
            
            # Butonları sağa yasla (veya ortaya)
            # Zoom Butonu (Sadece görsel varsa)
            if image_data:
                ctk.CTkButton(btn_frame, text="🔍", width=30, fg_color="gray", 
                              command=lambda d=image_data, n=name: self.show_zoom(d, n)).pack(side="left", padx=2)

            # Düzenle Butonu (Kalem)
            ctk.CTkButton(btn_frame, text="✏️", width=30, fg_color="orange", 
                          command=lambda i=sel_id, c=content, n=name: self.edit_selector(i, n, c)).pack(side="left", padx=2)

            # Sil Butonu
            ctk.CTkButton(btn_frame, text="🗑️", width=40, fg_color="darkred", 
                          command=lambda i=sel_id: self.delete_selector(i)).pack(side="left", padx=2)

            # v161.0: Seç Butonu (Sadece 'pick' modunda) - EN SAĞA (ÖNEMLİ)
            if self.mode == "pick":
                ctk.CTkButton(btn_frame, text="✅ SEÇ", width=100, fg_color="#27AE60", hover_color="#1E8449", font=("Arial", 12, "bold"),
                              command=lambda s=sel: self.callback(s)).pack(side="right", padx=5)
                          
    def edit_selector(self, s_id, name, content_str):
        """v125: Seçici Düzenle (İndeks Ekle, vb.)"""
        try:
            # Mevcut içeriği ayrıştır
            import json
            current_data = json.loads(content_str) if isinstance(content_str, str) else content_str
        except:
            current_data = {}

        # Yeni İndeks İste
        current_idx = current_data.get("foundIndex", 1)
        
        # Şimdilik Basit Girdi Diyalogu (tam JSON düzenlemeye genişletilebilir)
        new_idx = simpledialog.askinteger("Düzenle", f"'{name}' için Index numarası girin:\n(1 = İlk bulunan, 2 = İkinci...)", initialvalue=current_idx, minvalue=1)
        
        if new_idx is not None:
            current_data["foundIndex"] = new_idx
            
            # Geri kaydet
            new_content = json.dumps(current_data)
            if self.db.update_selector(s_id, new_content):
                messagebox.showinfo("Başarılı", f"Selector güncellendi! (Index: {new_idx})")
                self.refresh_list()
            else:
                messagebox.showerror("Hata", "Güncelleme başarısız.")

    def show_zoom(self, data, name):
        """v115: Selector Resim Büyütme (Zoom)"""
        if not data: return
        
        top = ctk.CTkToplevel(self)
        top.title(f"Önizleme: {name}")
        top.attributes('-topmost', True) 
        top.geometry("800x600")
        
        try:
            import io
            from PIL import Image, ImageTk
            pil_img = Image.open(io.BytesIO(data))
            
            # Ekrana sığdır
            img_w, img_h = pil_img.size
            if img_w > 800 or img_h > 600:
                pil_img.thumbnail((800, 600))
                
            tk_img = ImageTk.PhotoImage(pil_img)
            
            lbl = ctk.CTkLabel(top, text="", image=tk_img)
            lbl.image = tk_img # Referansı tut
            lbl.pack(expand=True, fill="both")
        except Exception as e:
            messagebox.showerror("Hata", f"Görüntülenemedi: {e}")

    def delete_selector(self, selector_id):
        if messagebox.askyesno("Onay", "Bu seçiciyi silmek istediğinize emin misiniz?"):
            if self.db.delete_selector(selector_id):
                self.refresh_list()
            else:
                messagebox.showerror("Hata", "Silinemedi.")
