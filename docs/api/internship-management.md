### Staj Yönetim Sistemi Dokümantasyonu

Bu dokümantasyon, staj yönetim sisteminin temel bileşenlerini ve işlevlerini açıklamaktadır.

## İçindekiler

1. [Veri Modelleri](#veri-modelleri)

1. [Staj (Internship)](#staj-internship)
2. [Staj Günlüğü (InternshipDiary)](#staj-günlüğü-internshipdiary)
3. [Değerlendirme (Evaluation)](#değerlendirme-evaluation)



2. [GraphQL API](#graphql-api)

1. [Sorgular (Queries)](#sorgular-queries)
2. [Mutasyonlar (Mutations)](#mutasyonlar-mutations)



3. [İş Akışları](#i̇ş-akışları)

1. [Staj Başvuru Süreci](#staj-başvuru-süreci)
2. [Staj Günlüğü Yönetimi](#staj-günlüğü-yönetimi)
3. [Değerlendirme Süreci](#değerlendirme-süreci)





## Veri Modelleri

### Staj (Internship)

Staj modeli, öğrencilerin şirketlere yaptıkları staj başvurularını ve staj sürecini takip eder.

| Alan | Tür | Açıklama
|-----|-----|-----
| student | ForeignKey | Staj yapan öğrenci
| company | ForeignKey | Stajın yapıldığı şirket
| start_date | DateField | Stajın başlangıç tarihi
| end_date | DateField | Stajın bitiş tarihi
| total_working_days | IntegerField | Toplam çalışma günü sayısı
| position | CharField | Staj pozisyonu
| description | TextField | Staj açıklaması
| status | CharField | Staj durumu (Beklemede, Şirket Onaylı, Admin Onaylı, Reddedildi, Tamamlandı)


#### Staj Durumları

- **Beklemede (pending)**: Başvuru yapıldı, şirket onayı bekleniyor
- **Şirket Onaylı (approved_by_company)**: Şirket tarafından onaylandı, admin onayı bekleniyor
- **Admin Onaylı (approved_by_admin)**: Sistem yöneticisi tarafından onaylandı
- **Reddedildi (rejected)**: Başvuru reddedildi
- **Tamamlandı (completed)**: Staj tamamlandı


### Staj Günlüğü (InternshipDiary)

Staj günlüğü modeli, öğrencilerin staj süresince günlük aktivitelerini kaydetmelerini sağlar.

| Alan | Tür | Açıklama
|-----|-----|-----
| internship | ForeignKey | İlişkili staj kaydı
| date | DateField | Günlük tarihi
| hours_worked | DecimalField | Çalışılan saat
| day_number | IntegerField | Stajın kaçıncı günü olduğu
| status | CharField | Günlük durumu (Taslak, Gönderildi)
| text | TextField | Günlük içeriği
| tasks | CharField | Yapılan görevler
| feedback | TextField | Geri bildirim


#### Günlük Durumları

- **Taslak (draft)**: Günlük kaydedildi ancak henüz gönderilmedi
- **Gönderildi (submitted)**: Günlük gönderildi ve artık değiştirilemez


### Değerlendirme (Evaluation)

Değerlendirme modeli, şirketlerin stajyerleri değerlendirmesini sağlar.

| Alan | Tür | Açıklama
|-----|-----|-----
| internship | ForeignKey | İlişkili staj kaydı
| attendance | IntegerField | Devam puanı (0-100)
| performance | IntegerField | Performans puanı (0-100)
| adaptation | IntegerField | Uyum puanı (0-100)
| technical_skills | IntegerField | Teknik beceriler puanı (0-100)
| communication_skills | IntegerField | İletişim becerileri puanı (0-100)
| teamwork | IntegerField | Takım çalışması puanı (0-100)
| comments | TextField | Yorumlar
| overall_score | DecimalField | Genel puan (0-100)
| is_approved | BooleanField | Değerlendirme onaylandı mı?


## GraphQL API

### Sorgular (Queries)

Sistem, aşağıdaki veri sorgularını destekler:

#### Staj Sorguları

```plaintext
# Belirli bir stajı ID'ye göre sorgulama
{
  internship(id: "ID") {
    id
    student {
      firstName
      lastName
    }
    company {
      companyName
    }
    startDate
    endDate
    status
  }
}

# Tüm stajları filtreleme
{
  internships(student: "ID", status: "pending") {
    edges {
      node {
        id
        position
        description
        status
      }
    }
  }
}
```

#### Staj Günlüğü Sorguları

```plaintext
# Belirli bir staja ait günlükleri sorgulama
{
  internshipDiaries(internship: "ID") {
    edges {
      node {
        id
        date
        hoursWorked
        dayNumber
        status
        text
      }
    }
  }
}
```

#### Değerlendirme Sorguları

```plaintext
# Belirli bir staja ait değerlendirmeyi sorgulama
{
  evaluations(internship: "ID") {
    edges {
      node {
        id
        attendance
        performance
        overallScore
        isApproved
      }
    }
  }
}
```

### Mutasyonlar (Mutations)

Sistem, aşağıdaki veri değişikliklerini destekler:

#### Staj Mutasyonları

1. **Staj Başvurusu Oluşturma**


```plaintext
mutation {
  createInternshipApplication(
    companyId: "ID",
    startDate: "2023-06-01",
    endDate: "2023-07-30",
    position: "Yazılım Geliştirici",
    description: "Backend geliştirme stajı"
  ) {
    success
    message
  }
}
```

2. **Staj Başvurusu Güncelleme**


```plaintext
mutation {
  updateInternshipApplication(
    internshipId: "ID",
    startDate: "2023-06-15",
    endDate: "2023-08-15"
  ) {
    success
    message
  }
}
```

3. **Şirket Tarafından Staj Durumu Güncelleme**


```plaintext
mutation {
  updateInternshipApplicationStatusByCompany(
    internshipId: "ID",
    status: APPROVED_BY_COMPANY
  ) {
    success
    message
  }
}
```

4. **Admin Tarafından Staj Durumu Güncelleme**


```plaintext
mutation {
  updateInternshipApplicationStatusByAdmin(
    internshipId: "ID",
    status: APPROVED_BY_ADMIN
  ) {
    success
    message
  }
}
```

5. **Staj Başvurusu Silme**


```plaintext
mutation {
  deleteInternshipApplication(
    internshipId: "ID"
  ) {
    success
    message
  }
}
```

#### Staj Günlüğü Mutasyonları

1. **Staj Günlüğü Oluşturma**


```plaintext
mutation {
  createInternshipDiary(
    internshipId: "ID",
    date: "2023-06-15",
    hoursWorked: 8.5,
    dayNumber: 10,
    status: DRAFT,
    text: "Bugün veritabanı tasarımı üzerinde çalıştım",
    tasks: "DB tasarımı, API geliştirme"
  ) {
    success
    message
  }
}
```

2. **Staj Günlüğü Güncelleme**


```plaintext
mutation {
  updateInternshipDiary(
    internshipDiaryId: "ID",
    text: "Güncellenmiş günlük içeriği",
    hoursWorked: 9.0
  ) {
    success
    message
  }
}
```

3. **Staj Günlüğü Durumu Güncelleme**


```plaintext
mutation {
  updateInternshipDiaryStatus(
    internshipDiaryId: "ID",
    status: SUBMITTED
  ) {
    success
    message
  }
}
```

4. **Staj Günlüğü Silme**


```plaintext
mutation {
  deleteInternshipDiary(
    diaryId: "ID"
  ) {
    success
    message
  }
}
```

#### Değerlendirme Mutasyonları

1. **Değerlendirme Oluşturma**


```plaintext
mutation {
  createEvaluation(
    internshipId: "ID",
    attendance: 90,
    performance: 85,
    adaptation: 95,
    technicalSkills: 80,
    communicationSkills: 90,
    teamwork: 85,
    comments: "Çok başarılı bir staj dönemi geçirdi",
    overallScore: 87.5,
    isApproved: false
  ) {
    success
    message
  }
}
```

2. **Değerlendirme Güncelleme**


```plaintext
mutation {
  updateEvaluation(
    evaluationId: "ID",
    performance: 90,
    comments: "Performansı beklentilerin üzerindeydi"
  ) {
    success
    message
  }
}
```

3. **Değerlendirme Onaylama**


```plaintext
mutation {
  evaluationApproval(
    evaluationId: "ID"
  ) {
    success
    message
  }
}
```

## İş Akışları

### Staj Başvuru Süreci

1. Öğrenci, sistem üzerinden bir şirkete staj başvurusu yapar
2. Şirket başvuruyu değerlendirir ve onaylar veya reddeder
3. Şirket onaylarsa, sistem yöneticisi (admin) başvuruyu değerlendirir
4. Admin onaylarsa, staj başlar
5. Staj tamamlandığında, durum "completed" olarak güncellenir


### Staj Günlüğü Yönetimi

1. Öğrenci, staj süresince her gün için günlük kaydı oluşturur
2. Günlük kaydı önce "draft" durumunda kaydedilir
3. Öğrenci günlüğü tamamladığında "submitted" durumuna geçirir
4. Gönderilen günlükler artık düzenlenemez veya silinemez


### Değerlendirme Süreci

1. Staj tamamlandığında, şirket öğrenciyi çeşitli kriterlere göre değerlendirir
2. Değerlendirme puanları 0-100 arasında olmalıdır
3. Genel puan, diğer puanların ortalamasına yakın olmalıdır
4. Şirket değerlendirmeyi onayladığında, değerlendirme süreci tamamlanır


## Güvenlik ve İzinler

Sistem, kullanıcı rollerine göre izin kontrolü yapar:

- Öğrenciler sadece kendi staj başvurularını ve günlüklerini yönetebilir
- Şirketler sadece kendilerine yapılan başvuruları değerlendirebilir
- Sistem yöneticileri tüm staj başvurularını onaylayabilir veya reddedebilir


Her işlem için uygun izinler kontrol edilir ve yetkisiz erişim denemeleri engellenir.

## Hata Yönetimi ve Loglama

Sistem, tüm işlemleri detaylı olarak loglar:

- Başarılı işlemler `log_info` ile kaydedilir
- Hatalar `log_error` ile kaydedilir
- Uyarılar `log_warning` ile kaydedilir


Bu loglar, sistem sorunlarını tespit etmek ve kullanıcı davranışlarını izlemek için kullanılır.