# 📘 AutomateX - Kapsamlı Kullanım Kılavuzu (v167.33)

Bu kılavuz, AutomateX'i en verimli şekilde kullanmanız için gereken tüm adımları detaylıca açıklar.

---

## 🏗️ 1. Temel Kavramlar

AutomateX iki ana yöntemle çalışır:
1.  **Görsel Tanıma (Image Recognition):** "Alanı kırp" mantığıyla çalışır. Ekranda o resmi gördüğü an tıklar.
2.  **Yapısal Tanıma (Selectors):** Uygulamanın koduna bakar. Butonun adı veya ID'si değişmediği sürece ekran çözünürlüğünden etkilenmez.

---

## 🚀 2. İlk Senaryoyu Oluşturma

1.  Uygulamayı açın ve **"Yeni Senaryo"** butonuna basın.
2.  Senaryonuza isim verin (Örn: `E-Fatura Giriş`).

### 🖱️ Adım Ekleme (Tıklama)
*   Sol panelden **"Sol Tıkla"** butonuna basın.
*   Ekran kararacaktır. Farenizle tıklanacak butonun etrafını kare içine alın.
*   Gelen pencerede görsele bir isim verin (Örn: `GirişButonu`).
*   **Opsiyonel:** "Ofset" ayarıyla tıkladığı yeri milimetrik kaydırabilirsiniz.

### ⌨️ Yazı Yazma (Type)
*   **"Metin Yaz"** butonuna basın.
*   Yazılacak metni girin.
*   **Hız:** "0.01" çok hızlı, "0.1" ise insan yazımı gibi görünür.

---

## 🤖 3. İleri Düzey Araçlar

### 📸 Akıllı Kaydedici (Smart Recorder)
1.  **"📸 Kaydı Başlat"** butonuna basın. UI gizlenecektir.
2.  Normal işlerinizi yapın (Tarayıcı açın, şifre girin, butona basın).
3.  İşiniz bittiğinde **ESC** tuşuna basın.
4.  AutomateX yaptığınız her şeyi otomatik olarak adım liste haline getirmiştir!

### 🎯 Spy Tool (Inspector)
1.  **"🔍 Spy Tool"** butonuna basın.
2.  Ekranda kırmızı çerçeveler belirecektir.
3.  Hedef butonun üzerine gelip **CTRL + Sol Tık** yapın.
4.  Bu işlem butonun "kimlik bilgisini" (ID) kaydeder. Görselden daha garantidir.

---

## 🛡️ 4. Hata Önleme ve Popup Yönetimi

### Popup Yakalayacı (Popup Handler)
Eğer programın ortasında aniden bir "Güncelleme Var" veya "Hata Oluştu" uyarısı çıkıyorsa:
1.  **"🛡️ Popup Yakala"** butonunu senaryonun başına veya popup'ın çıkabileceği yere ekleyin.
2.  Popup'ın "X" veya "Kapat" butonunu seçin.
3.  Robot çalışırken bu butonu görürse tıklar, görmezse beklemeden devam eder.

### Değişken Kullanımı
*   Bir adımı düzenlerken (✏️) metin kısmına `${TC_NO}` yazabilirsiniz.
*   Senaryonun en başında **"Değişken Tanımla"** diyerek `TC_NO = 123456...` şeklinde değer atayabilirsiniz.
*   Böylece aynı senaryoyu her seferinde farklı verilerle (Örn: farklı kullanıcılarla) çalıştırabilirsiniz.

---

## ⚡ 5. İpucu ve Püf Noktaları

*   **ESC Tuşu:** Acil durumlarda robotu durdurmak için **ESC** tuşuna basılı tutun.
*   **Hızlı Sıralama:** Adımları taşımak için butonun yanındaki numarayı silip yeni sıra numarasını yazın ve **ENTER**'a basın.
*   **Debug (Buradan Başlat):** Bir senaryoyu baştan değil de ortadan başlatmak için adım yanındaki yeşil **▶** butonuna basın.
*   **Visual Elements:** Gereksizleşen veya yanlış kırptığınız resimleri "Visual Elements" deposundan temizleyin ki veritabanı şişmesin.

---

## 🛠️ 6. Bakım ve Taşınabilirlik

*   **Dosya Yedekleme:** `data/automation.db` dosyası kalbinizdir. Bu dosyayı yedeklerseniz tüm senaryolarınız güvende olur.
*   **Exporter:** Senaryolarınızı başka bir arkadaşınıza göndermek için **"Dışa Aktar"** butonunu kullanabilirsiniz.
