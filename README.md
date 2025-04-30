# IFS (Internship Follow-up System)

## 1. Proje Genel Bakış

### 1.1 Amaç

IFS, staj takip ve yönetim sistemidir. Öğrencilerin staj başvurularını, staj günlüklerini ve değerlendirmelerini yönetmek için tasarlanmıştır.

### 1.2 Teknoloji Stack'i

- **Backend Framework:** Django 4.2.20
- **API:** GraphQL (Graphene)
- **Veritabanı:** SQLite (Geliştirme), PostgreSQL (Production)
- **Cache:** Redis
- **Authentication:** JWT (JSON Web Tokens)
- **Containerization:** Docker
- **Storage:** Azure Blob Storage

## 2. Kurulum

### 2.1 Gereksinimler

- Python 3.8+
- Docker ve Docker Compose
- Redis
- Azure Storage Account (Dosya yüklemeleri için)

### 2.2 Kurulum Adımları

1. Projeyi klonlayın:

```bash
git clone [repo-url]
cd IFS
```

2. Sanal ortam oluşturun ve aktifleştirin:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Bağımlılıkları yükleyin:

```bash
pip install -r core/requirements.txt
```

4. Environment değişkenlerini ayarlayın:

```bash
cp .env.example .env
# .env dosyasını düzenleyin
```

5. Docker ile çalıştırın:

```bash
docker-compose up -d
```

## 3. Proje Yapısı

```
IFS/
├── core/                    # Ana Django projesi
│   ├── userManage/         # Kullanıcı yönetimi modülü
│   ├── internshipManage/   # Staj yönetimi modülü
│   ├── templates/          # HTML şablonları
│   └── manage.py           # Django yönetim scripti
├── requirements.txt        # Python bağımlılıkları
├── docker-compose.yml     # Docker yapılandırması
└── Dockerfile             # Docker image yapılandırması
```

## 4. API Dokümantasyonu

### 4.1 Authentication Endpoints

#### Login

```graphql
mutation {
  auth(usernameoremail: String!, password: String!) {
    tokens {
      access_token
      refresh_token
    }
  }
}
```

#### Refresh Token

```graphql
mutation {
  refreshToken(refresh_token: String!) {
    tokens {
      access_token
      refresh_token
    }
  }
}
```

### 4.2 User Management Endpoints

#### Create User

```graphql
mutation {
  userCreate(
    username: String!
    email: String!
    password: String!
    role_id: ID!
    user_type: String!
  ) {
    user {
      id
      username
      email
    }
    success
    message
  }
}
```

## 5. Geliştirme

### 5.1 Kod Standartları

- PEP 8 uyumlu Python kodu
- Docstring kullanımı
- Modüler yapı

### 5.2 Git Workflow

- Feature branch workflow
- Pull request reviews
- Semantic versioning

## 6. Deployment

### 6.1 Production Ortamı

1. Environment değişkenlerini ayarlayın
2. PostgreSQL veritabanını yapılandırın
3. Redis cache'i yapılandırın
4. Azure Storage bağlantısını ayarlayın

### 6.2 Docker Deployment

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 7. Güvenlik

### 7.1 Authentication

- JWT tabanlı kimlik doğrulama
- Access ve Refresh token mekanizması
- Token blacklist sistemi

### 7.2 Authorization

- Rol tabanlı yetkilendirme
- Özel izin sistemi
- Rate limiting (Redis ile)

## 8. Monitoring ve Logging

### 8.1 Log Dosyaları

- `user_management.log`: Kullanıcı işlemleri
- `debug.log`: Sistem hataları

### 8.2 Cache Monitoring

- Redis cache durumu
- Rate limiting metrikleri
