# User Management API

## Rate Limiting ve Güvenlik

### Rate Limiting

API istekleri için rate limiting uygulanmaktadır. Rate limiting Redis cache üzerinden yönetilmektedir.

#### Genel Limitler

| İstek Tipi   | Limit | Periyot | Reset Süresi |
| :----------- | :---- | :------ | :----------- |
| Tüm İstekler | 1000  | 1 saat  | 3600 saniye  |
| Mutasyonlar  | 100   | 1 saat  | 3600 saniye  |
| Query'ler    | 1000  | 1 saat  | 3600 saniye  |

#### Endpoint Bazlı Limitler

| Endpoint        | Limit | Periyot   |
| :-------------- | :---- | :-------- |
| /auth/login     | 5     | 15 dakika |
| /auth/register  | 3     | 15 dakika |
| /user/create    | 10    | 1 saat    |
| /profile/update | 20    | 1 saat    |

### Güvenlik

#### Token Yönetimi

- JWT token'lar kullanılır
- Access token süresi: 1 saat
- Refresh token süresi: 7 gün
- Token yenileme limiti: Günde 10 kez

## HTTP Başlıkları

Tüm isteklerde aşağıdaki başlıklar kullanılmalıdır:

| Başlık        | Değer                 | Açıklama                                                                    |
| ------------- | --------------------- | --------------------------------------------------------------------------- |
| Content-Type  | application/json      | İstek gövdesinin JSON formatında olduğunu belirtir                          |
| Authorization | Bearer {access_token} | JWT access token'ı. Örnek: `Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...` |

### Örnek İstek Başlıkları

```http
POST /graphql/ HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Kullanıcı Oluşturma

Yeni bir kullanıcı oluşturmak için kullanılan mutasyon.

### Mutasyon

```graphql
mutation {
  userCreate(
    username: String!
    email: String!
    password: String!
    role_id: ID!
    user_type: String!
    first_name: String
    last_name: String
    student_number: String
    department: String
    faculty: String
    date_of_birth: Date
    profile_picture: Upload
    company_name: String
    contact_person: String
    website: String
    tax_number: String
    phone_number: String
    address: String
  ) {
    success
    message
  }
}
```

### Parametreler

| Parametre       | Tip    | Zorunlu | Açıklama                         |
| --------------- | ------ | ------- | -------------------------------- |
| username        | String | Evet    | Kullanıcı adı                    |
| email           | String | Evet    | Email adresi                     |
| password        | String | Evet    | Şifre                            |
| role_id         | ID     | Evet    | Rol ID'si                        |
| user_type       | String | Evet    | Kullanıcı tipi (student/company) |
| first_name      | String | Hayır   | Ad (öğrenci için)                |
| last_name       | String | Hayır   | Soyad (öğrenci için)             |
| student_number  | String | Hayır   | Öğrenci numarası                 |
| department      | String | Hayır   | Bölüm                            |
| faculty         | String | Hayır   | Fakülte                          |
| date_of_birth   | Date   | Hayır   | Doğum tarihi                     |
| profile_picture | Upload | Hayır   | Profil fotoğrafı                 |
| company_name    | String | Hayır   | Şirket adı                       |
| contact_person  | String | Hayır   | İletişim kişisi                  |
| website         | String | Hayır   | Web sitesi                       |
| tax_number      | String | Hayır   | Vergi numarası                   |
| phone_number    | String | Hayır   | Telefon numarası                 |
| address         | String | Hayır   | Adres                            |

### İzinler

- Bu mutasyonu kullanmak için `userManage.UserAdd` iznine sahip olunmalıdır

### Rate Limiting

- 15 saniye içinde maksimum 1 kullanıcı oluşturma isteği yapılabilir

### Örnek İstek (Öğrenci)

```graphql
mutation {
  userCreate(
    username: "student1"
    email: "student1@example.com"
    password: "password123"
    roleId: "1"
    usertype: "student"
    firstName: "John"
    lastName: "Doe"
    studentNumber: "2023001"
    department: "Computer Engineering"
    faculty: "Engineering"
  ) {
    success
    message
  }
}
```

### Başarılı Yanıt

```json
{
  "data": {
    "userCreate": {
      "user": {
        "id": "1",
        "username": "student1",
        "email": "student1@example.com"
      },
      "success": true,
      "message": "Kullanıcı başarıyla oluşturuldu"
    }
  }
}
```

### Hata Durumları

| Hata Kodu         | Açıklama                   |
| ----------------- | -------------------------- |
| PERMISSION_DENIED | Yetki hatası               |
| USERNAME_EXISTS   | Kullanıcı adı zaten mevcut |
| EMAIL_EXISTS      | Email adresi zaten mevcut  |
| INVALID_ROLE      | Geçersiz rol               |
| INVALID_USER_TYPE | Geçersiz kullanıcı tipi    |

### Validasyon Kuralları

- Username en az 3 karakter olmalı
- Email geçerli bir formatta olmalı
- Şifre en az 8 karakter olmalı
- Öğrenci numarası benzersiz olmalı
- Vergi numarası benzersiz olmalı

## Profil Güncelleme (Admin)

Admin tarafından kullanıcı profili güncelleme işlemi.

### Mutasyon

```graphql
mutation {
  updateUserByAdmin(
    user_id: ID!
    usernameoremail: String
    email: String
    password: String
    roleId: ID
    userType: String
    firstName: String
    lastName: String
    studentNumber: String
    department: String
    faculty: String
    dateOfBirth: Date
    profilePicture: Upload
    companyName: String
    contactPerson: String
    website: String
    taxNumber: String
    phoneNumber: String
    address: String
  ) {
    success
    message
  }
}
```

### Parametreler

| Parametre | Tip | Zorunlu | Açıklama                               |
| --------- | --- | ------- | -------------------------------------- |
| user_id   | ID  | Evet    | Güncellenecek kullanıcının ID'si       |
| ...       | ... | ...     | Diğer parametreler userCreate ile aynı |

### İzinler

- Bu mutasyonu kullanmak için `userManage.UserUpdate` iznine sahip olunmalıdır

### Rate Limiting

- 15 saniye içinde maksimum 1 güncelleme isteği yapılabilir

### Örnek İstek

```graphql
mutation {
  updateUserByAdmin(
    userId: "1"
    firstName: "Ahmet"
    lastName: "Yılmaz"
    department: "Bilgisayar Mühendisliği"
  ) {
    success
    message
  }
}
```

### Hata Durumları

| Hata Kodu               | Açıklama                         |
| ----------------------- | -------------------------------- |
| ADMIN_CANNOT_BE_UPDATED | Admin kullanıcısı güncellenemez  |
| NO_FIELDS_TO_UPDATE     | Güncellenecek alan belirtilmemiş |
| ROLE_NOT_FOUND          | Rol bulunamadı                   |
| STUDENT_NOT_FOUND       | Öğrenci bulunamadı               |
| COMPANY_NOT_FOUND       | Şirket bulunamadı                |

## Profil Güncelleme (Kullanıcı)

Kullanıcının kendi profilini güncellemesi.

### Mutasyon

```graphql
mutation {
  updatemyprofile(
    username: String
    password: String
    newPassword: String
    confirmPassword: String
    firstName: String
    lastName: String
    studentNumber: String
    department: String
    faculty: String
    dateOfBirth: Date
    profilePicture: Upload
    companyName: String
    contactPerson: String
    website: String
    tax_number: String
    phone_number: String
    address: String
  ) {
    success
    message
  }
}
```

### Parametreler

| Parametre        | Tip    | Zorunlu | Açıklama                               |
| ---------------- | ------ | ------- | -------------------------------------- |
| password         | String | Hayır   | Mevcut şifre (şifre değişikliği için)  |
| new_password     | String | Hayır   | Yeni şifre                             |
| confirm_password | String | Hayır   | Yeni şifre onayı                       |
| ...              | ...    | ...     | Diğer parametreler userCreate ile aynı |

### Rate Limiting

- 15 saniye içinde maksimum 1 güncelleme isteği yapılabilir

### Validasyon Kuralları

- Telefon numarası geçerli bir formatta olmalı
- Yeni şifre ve onay şifresi eşleşmeli
- Şifre değişikliği için mevcut şifre doğru olmalı
- Admin kullanıcıları için profil güncelleme işlemi yapılamaz

## Query'ler

### Kullanıcı Sorgulama

```graphql
query {
  user(id: ID!) {
    id
    username
    email
    isActive
  }
}
```

### Kullanıcı Listesi

```graphql
query {
  users {
    edges {
      node {
        id
        username
        email
        isActive
        role {
          id
          name
        }
      }
    }
  }
}
```

### Öğrenci Sorgulama

```graphql
query {
  student(id: ID!) {
    id
    studentNumber
    department
    faculty
    dateOfBirth
    user {
      id
      username
      email
    }
  }
}
```

### Öğrenci Listesi

```graphql
query {
  students {
    edges {
      node {
        id
        studentNumber
        department
        faculty
        dateOfBirth
        user {
          id
          username
          email
        }
      }
    }
  }
}
```

### Şirket Sorgulama

```graphql
query {
  company(id: ID!) {
    id
    companyName
    contactPerson
    website
    taxNumber
    phoneNumber
    address
    user {
      id
      username
      email
    }
  }
}
```

### Şirket Listesi

```graphql
query {
  companies {
    edges {
      node {
        id
        companyName
        contactPerson
        website
        taxNumber
        phoneNumber
        address
        user {
          id
          username
          email
        }
      }
    }
  }
}
```

### Mevcut Kullanıcı Bilgileri

```graphql
query {
  me {
    id
    username
    email
    isActive
    firstName
    lastName
    studentNumber
    department
    faculty
    phoneNumber
    address
    dateOfBirth
    profilePicture
    internshipsStudent {
      edges {
        node {
          id
          startDate
          endDate
          position
          description
          status
          totalWorkingDays
          company {
            id
            companyName
            contactPerson
            website
            taxNumber
            phoneNumber
            address
          }
          diaries {
            edges {
              node {
                id
                date
                hoursWorked
                dayNumber
                status
                text
                tasks
                feedback
              }
            }
          }
          evaluations {
            edges {
              node {
                id
                attendance
                performance
                adaptation
                technicalSkills
                communicationSkills
                teamwork
                comments
                overallScore
                isApproved
              }
            }
          }
        }
      }
    }
  }
}
```

### Mevcut Şirket Bilgileri

```graphql
query {
  mycompany {
    id
    companyName
    contactPerson
    website
    taxNumber
    phoneNumber
    address
  }
}
```

### Örnek Sorgular

#### Öğrenci Profil Bilgileri

```graphql
query {
  me {
    id
    firstName
    lastName
    studentNumber
    department
    faculty
    phoneNumber
    address
    dateOfBirth
    profilePicture
  }
}
```

#### Staj Listesi

```graphql
query {
  me {
    internshipsStudent {
      edges {
        node {
          id
          startDate
          endDate
          position
          status
          company {
            companyName
          }
        }
      }
    }
  }
}
```

#### Staj Detayları

```graphql
query {
  me {
    internshipsStudent {
      edges {
        node {
          id
          startDate
          endDate
          position
          description
          status
          totalWorkingDays
          company {
            companyName
            contactPerson
          }
          diaries {
            edges {
              node {
                date
                hoursWorked
                dayNumber
                status
                text
                tasks
                feedback
              }
            }
          }
          evaluations {
            edges {
              node {
                attendance
                performance
              }
            }
          }
        }
      }
    }
  }
}
```

### Temel Kullanıcı Bilgileri

| Alan     | Tip      | Açıklama            |
| :------- | :------- | :------------------ |
| id       | ID       | Kullanıcı ID'si     |
| username | String   | Kullanıcı adı       |
| email    | String   | Email adresi        |
| isActive | Boolean  | Kullanıcı aktif mi? |
| role     | RoleType | Kullanıcı rolü      |

### Öğrenci Bilgileri

| Alan           | Tip    | Açıklama                |
| :------------- | :----- | :---------------------- |
| firstName      | String | Ad                      |
| lastName       | String | Soyad                   |
| studentNumber  | String | Öğrenci numarası        |
| department     | String | Bölüm                   |
| faculty        | String | Fakülte                 |
| phoneNumber    | String | Telefon numarası        |
| address        | String | Adres                   |
| dateOfBirth    | Date   | Doğum tarihi            |
| profilePicture | String | Profil fotoğrafı URL'si |

### Staj Bilgileri

| Alan             | Tip              | Açıklama                                                                 |
| :--------------- | :--------------- | :----------------------------------------------------------------------- |
| id               | ID               | Staj ID'si                                                               |
| startDate        | Date             | Başlangıç tarihi                                                         |
| endDate          | Date             | Bitiş tarihi                                                             |
| position         | String           | Pozisyon                                                                 |
| description      | String           | Açıklama                                                                 |
| status           | String           | Durum (pending/approved_by_company/approved_by_admin/rejected/completed) |
| totalWorkingDays | Int              | Toplam çalışma günü                                                      |
| company          | CompanyType      | Şirket bilgileri                                                         |
| diaries          | [DiaryType]      | Staj günlükleri                                                          |
| evaluations      | [EvaluationType] | Değerlendirmeler                                                         |

### Şirket Bilgileri

| Alan          | Tip    | Açıklama         |
| :------------ | :----- | :--------------- |
| id            | ID     | Şirket ID'si     |
| companyName   | String | Şirket adı       |
| contactPerson | String | İletişim kişisi  |
| website       | String | Web sitesi       |
| taxNumber     | String | Vergi numarası   |
| phoneNumber   | String | Telefon numarası |
| address       | String | Adres            |

### Staj Günlüğü

| Alan        | Tip    | Açıklama                    |
| :---------- | :----- | :-------------------------- |
| id          | ID     | Günlük ID'si                |
| date        | Date   | Tarih                       |
| hoursWorked | Float  | Çalışılan saat (0-24 arası) |
| dayNumber   | Int    | Gün numarası                |
| status      | String | Durum (draft/submitted)     |
| text        | String | Günlük metni                |
| tasks       | String | Yapılan işler               |
| feedback    | String | Geri bildirim               |

### Değerlendirme

| Alan                | Tip     | Açıklama                    |
| :------------------ | :------ | :-------------------------- |
| id                  | ID      | Değerlendirme ID'si         |
| attendance          | Float   | Devam durumu (0-100)        |
| performance         | Float   | Performans (0-100)          |
| adaptation          | Float   | Uyum (0-100)                |
| technicalSkills     | Float   | Teknik beceriler (0-100)    |
| communicationSkills | Float   | İletişim becerileri (0-100) |
| teamwork            | Float   | Takım çalışması (0-100)     |
| comments            | String  | Yorumlar                    |
| overallScore        | Float   | Genel puan (0-100)          |
| isApproved          | Boolean | Onay durumu                 |

### Notlar

- `internshipsStudent` alanı sadece öğrenci kullanıcılar için doldurulur
- Staj bilgileri, günlükler ve değerlendirmeler isteğe bağlı olarak sorgulanabilir
- İlişkili verileri sorgularken performans açısından sadece ihtiyaç duyulan alanları seçmek önerilir
- Staj durumları: pending, approved_by_company, approved_by_admin, rejected, completed
- Günlük durumları: draft, submitted
- Değerlendirme puanları 0-100 arasında olmalıdır
- Çalışma saatleri 0-24 arasında olmalıdır

## Hata Kodları ve Çözümleri

### Genel Hatalar

| Kod | Açıklama          | Çözüm                                               |
| :-- | :---------------- | :-------------------------------------------------- |
| 400 | Geçersiz İstek    | İstek formatını kontrol edin                        |
| 401 | Yetkisiz Erişim   | Token'ı kontrol edin veya yeniden giriş yapın       |
| 403 | Erişim Reddedildi | Yetkinizi kontrol edin                              |
| 404 | Kaynak Bulunamadı | URL'yi kontrol edin                                 |
| 429 | Çok Fazla İstek   | Rate limit süresini bekleyin                        |
| 500 | Sunucu Hatası     | Tekrar deneyin veya destek ekibiyle iletişime geçin |

### Özel Hatalar

| Kod                 | Açıklama                  | Çözüm                              |
| :------------------ | :------------------------ | :--------------------------------- |
| USER_NOT_FOUND      | Kullanıcı bulunamadı      | Kullanıcı adını kontrol edin       |
| INVALID_CREDENTIALS | Geçersiz kimlik bilgileri | Şifreyi kontrol edin               |
| TOKEN_EXPIRED       | Token süresi doldu        | Token'ı yenileyin                  |
| RATE_LIMIT_EXCEEDED | İstek limiti aşıldı       | Limit süresini bekleyin            |
| VALIDATION_ERROR    | Doğrulama hatası          | İstek parametrelerini kontrol edin |
| PERMISSION_DENIED   | Yetki hatası              | Yetkinizi kontrol edin             |

### Sık Karşılaşılan Hatalar

1. **Token Hatası**

   - Belirti: 401 Unauthorized
   - Çözüm: Token'ı yenileyin veya yeniden giriş yapın

2. **Rate Limit Hatası**

   - Belirti: 429 Too Many Requests
   - Çözüm: İstek sayısını azaltın veya limit süresini bekleyin

3. **Validasyon Hatası**

   - Belirti: 400 Bad Request
   - Çözüm: İstek parametrelerini kontrol edin

4. **Yetki Hatası**
   - Belirti: 403 Forbidden
   - Çözüm: Yetkinizi kontrol edin veya admin ile iletişime geçin

## Test Ortamı

### Test Kullanıcıları

| Rol     | Kullanıcı Adı | Şifre      | Açıklama               |
| :------ | :------------ | :--------- | :--------------------- |
| Admin   | admin_test    | admin123   | Tam yetkili test admin |
| Öğrenci | student_test  | student123 | Test öğrenci hesabı    |
| Şirket  | company_test  | company123 | Test şirket hesabı     |

### Test Verileri

#### Öğrenci Test Verileri

```json
{
  "username": "student_test",
  "email": "student@test.com",
  "firstName": "Test",
  "lastName": "Öğrenci",
  "studentNumber": "2024001",
  "department": "Bilgisayar Mühendisliği",
  "faculty": "Mühendislik"
}
```

#### Şirket Test Verileri

```json
{
  "username": "company_test",
  "email": "company@test.com",
  "companyName": "Test Şirket A.Ş.",
  "contactPerson": "Test Kişi",
  "website": "https://test.com",
  "taxNumber": "1234567890"
}
```

#### Staj Test Verileri

```json
{
  "startDate": "2024-07-01",
  "endDate": "2024-08-31",
  "position": "Test Pozisyon",
  "description": "Test staj açıklaması"
}
```
