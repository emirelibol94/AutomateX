# 🚀 AutomateX - Özellik Listesi (v167.33)

AutomateX, gelişmiş görüntü işleme ve yapısal seçim (UI Automation) teknolojilerini birleştiren güçlü bir yerel otomasyon platformudur.

## 🧠 Akıllı Araçlar
*   **Smart Recorder (Akıllı Kaydedici):** Siz bilgisayarda normal işlerinizi yaparken AutomateX arka planda tıklamalarınızı ve yazılarınızı otomatik olarak senaryoya dönüştürür.
*   **Inspector / Spy Tool:** Uygulamaların kod yapısına sızarak ID, Name ve Class gibi yapısal seçicileri yakalar. Çözünürlük bağımsız çalışma sağlar.
*   **Snip Tool (Kırpma Aracı):** Ekranda tıklanacak alanı anında kırpıp robotun hafızasına (Veritabanı) kaydetmenizi sağlar.

## 🛠️ Desteklenen Aksiyonlar
### Etkileşim
*   **Akıllı Tıklama:** Görsel (OpenCV), Metin veya Seçici (UIA) bazlı; sol, sağ ve çift tıklama desteği.
*   **Metin Yazma:** PowerShell tabanlı güvenli pano entegrasyonu ile Türkçe karakter sorunu olmadan hızlı metin girişi.
*   **Özel Tuşlar:** Enter, Tab, Esc ve F1-F12 gibi tüm özel tuş kombinasyonları.
*   **Sürükle & Bırak:** Bir görseli tutup başka bir yere sürükleme.

### Smart (Zeki) İşlemler
*   **Smart Scroll:** Belirli bir görseli veya butonu bulana kadar sayfayı otomatik kaydırma.
*   **Popup Handler:** Beklenmedik uyarı pencerelerini algılayıp "Tamam" veya "X" butonuna basarak süreci durdurmadan temizleme.
*   **Metin Okuma (OCR/UIA):** Ekrandaki bir alandan veri okuyup bunu değişkenlere atama (Örn: Bir IBAN numarasını okuyup başka yere yazma).

### Mantık ve Kontrol
*   **Değişken Yönetimi:** `${degisken_adi}` formatında dinamik veri kullanımı.
*   **Döngüler (Loops):** Belirli işlemleri istenen sayıda veya sonsuz kez tekrar etme.
*   **Koşullar (If/Else):** "Eğer ekranda X görseli varsa Y yap" gibi mantıksal dallanma.
*   **Bekleme (Wait/Assert):** Sabit süreli bekleme veya "görsel belirene kadar bekle" özelliği.

## 📂 Yönetim ve Verimlilik
*   **Görsel Depo (Visual Elements):** Senaryolarda kullanılan tüm ekran görüntülerini yönetme, önizleme ve temizleme.
*   **Senaryo Kütüphanesi:** Kaydedilen senaryoları tek tıkla yükleme, yedekleme (Export) ve içe aktarma (Import).
*   **Sıralama (⚡ Işınlanma):** Adımları sürükle-bırak dışında, sadece numara yazarak anında farklı bir sıraya taşıma.

## 🛡️ Güvenlik ve Mimari
*   **%100 Yerel (Local-Only):** Verileriniz asla internete çıkmaz, tüm işlemler sizin bilgisayarınızda gerçekleşir.
*   **SQLite Veritabanı:** Görseller ve senaryolar tek bir `.db` dosyasında güvenle saklanır; klasör kalabalığı yapmaz.
*   **DPI Scaling:** Farklı ekran çözünürlükleri ve ölçeklendirme oranlarında (100%, 125%, 150%) kusursuz çalışma.
