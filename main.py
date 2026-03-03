import sys
import os
import logging

# Global Log Seviyesi Force
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Proje kök dizinini path'e ekle
abs_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(abs_path)

# PyInstaller statik analizi için içe aktarımları en tepeye taşıdık
from core.config import initialize_persistence
from ui.main_window import MainWindow

def main():
    initialize_persistence()
    print("Desktop Otomasyon Başlatılıyor...")
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
