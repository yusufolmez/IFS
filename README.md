# IFS (Internship Follow-up System) 🎓

Staj takip süreçlerini kolaylaştırmak ve dijitalleştirmek için tasarlanmış modern bir web uygulaması.

## �� Özellikler

- Staj başvuru süreçlerinin yönetimi
- Staj günlüğü oluşturma ve takibi
- Staj değerlendirme sistemi
- Rol bazlı yetkilendirme (Öğrenci, Şirket, Admin)
- GraphQL API ile veri yönetimi
- E-posta bildirim sistemi
- Otomatik görev planlama (Cron jobs)

## 🛠️ Teknolojiler

- **Backend:** Django 4.2.20
- **API:** GraphQL (Graphene)
- **Veritabanı:** PostgreSQL 15
- **Önbellek:** Redis
- **Containerization:** Docker & Docker Compose
- **Kimlik Doğrulama:** JWT (JSON Web Tokens)

## 📋 Gereksinimler

- Docker ve Docker Compose
- Python 3.8 veya üzeri (lokal geliştirme için)
- Git

## 🚀 Kurulum

1. Projeyi klonlayın:
```bash
git clone <proje-url>
cd core
```

2. Ortam değişkenleri dosyasını oluşturun:
```bash
cp .env.example .env
```

3. .env dosyasını düzenleyin ve gerekli değişkenleri ayarlayın:
```env
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
REDIS_PASSWORD=your_redis_password
```

4. Docker containerlarını başlatın:
```bash
docker-compose up -d
```

5. Veritabanı migrationlarını uygulayın:
```bash
docker-compose exec web python manage.py migrate
```

6. Süper kullanıcı oluşturun:
```bash
docker-compose exec web python manage.py createsuperuser
```

## 🌐 Erişim

- **Django Admin Panel:** http://localhost:8000/admin
- **GraphQL Playground:** http://localhost:8000/graphql

## 📊 Sistem Mimarisi

Uygulama aşağıdaki ana bileşenlerden oluşur:

- **userManage:** Kullanıcı yönetimi ve yetkilendirme sistemi
  - Öğrenci, şirket ve admin rolleri
  - JWT tabanlı kimlik doğrulama

- **internshipManage:** Staj süreçleri yönetimi
  - Staj başvuru işlemleri
  - Staj günlüğü yönetimi
  - Staj değerlendirme sistemi
  - E-posta bildirimleri

- **Cron Jobs:** Zamanlanmış görevler
  - Otomatik e-posta bildirimleri
  - Durum güncellemeleri

## 🔧 Geliştirme

Lokal geliştirme ortamı için:

1. Virtual environment oluşturun:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

2. Bağımlılıkları yükleyin:
```bash
pip install -r requirements.txt
```

3. Geliştirme sunucusunu başlatın:
```bash
python manage.py runserver
```

## 📝 Loglar

Uygulama logları `logs/` dizininde tutulur ve Docker volume olarak saklanır.

