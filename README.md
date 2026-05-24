# 🎟️ Tikatik — Etkinlik Bilet Satış Uygulaması

Tikatik, konser, tiyatro, festival ve daha fazlası için online bilet satın almayı kolaylaştıran bir Django web uygulamasıdır.

---

##  Özellikler

-  **Kullanıcı Yönetimi** — Kayıt, giriş, profil sayfası
-  **Etkinlik Listeleme** — Şehir,kategori ve tarihe göre filtreleme
-  **Bilet Satın Alma** — A/B/C koltuk tipi seçimi, adet belirleme, sahte ödeme formu
-  **QR Kod Bileti** — Her satın alınan bilete otomatik QR kod üretimi
-  **Yorum & Puanlama** — Etkinliklere yorum yap, 1–5 arası puan ver
-  **Bildirim Sistemi** — Takip edilen sanatçı/oyuncu etkinlikleri için anlık bildirim
-  **Takip Sistemi** — Sanatçı ve oyuncuları takibe al
-  **Etkinlik Önerileri** — Geçmiş bilet geçmişine göre öneri
-  **Satıcı Paneli** — Etkinlik oluşturma, yönetme, bilet satış görüntüleme
-  **Admin Paneli** — Kullanıcı, etkinlik ve sanatçı yönetimi

---

##  Kullanılan Teknolojiler

| Katman      | Teknoloji                          |
|-------------|------------------------------------|
| Backend     | Python 3, Django 5.2               |
| Frontend    | Bootstrap 5.3, Bootstrap Icons, Inter (Google Fonts) |
| Veritabanı  | SQLite (geliştirme)                |
| QR Kod      | `qrcode` kütüphanesi               |
| Görsel      | Pillow                             |
| ML (Öneri) | scikit-learn, numpy                |
| Sunucu      | Gunicorn + WhiteNoise              |

---

##  Kurulum

## 1. Repoyu klonla
   
git clone https://github.com/ElifGuvenn/Bilet-Satis-Uygulamasi-.git

cd Bilet-Satis-Uygulamasi-/firstproject

## 2. Sanal ortam oluştur ve aktif et
   
python -m venv venv

Windows

venv\Scripts\activate

macOS / Linux

source venv/bin/activate

## 3. Bağımlılıkları yükle

pip install -r requirements.txt

## 4. Veritabanını oluştur

python manage.py migrate

## 5. Süper kullanıcı oluştur (isteğe bağlı)

python manage.py createsuperuser

## 6. Uygulamayı çalıştır

python manage.py runserver

Tarayıcıda http://127.0.0.1:8000 adresini aç.

## Kullanıcı Rolleri
 
Rol Yetkiler

Müşteri	Etkinlik görüntüle, bilet al, yorum yap, sanatçı takip et,bildirimleri ve sistem önerilerini görüntüle.

Satıcı	Etkinlik oluştur ve yönet, satış istatistiklerini gör,etkinlik yorumlarını görüntüle

Admin	Tüm kullanıcıları, etkinlikleri ve sanatçıları yönet


