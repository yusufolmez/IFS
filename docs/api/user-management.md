# Django Kullanıcı Yönetim Sistemi Dokümantasyonu

Bu belge, Django tabanlı kullanıcı yönetim sisteminin yapısını, modellerini ve GraphQL API'sini açıklamaktadır.

## İçindekiler

1. [Modeller](#modeller)
   - [CustomPermission](#custompermission)
   - [CustomRole](#customrole)
   - [CustomUser](#customuser)
   - [Student](#student)
   - [Company](#company)
2. [GraphQL API](#graphql-api)
   - [Sorgu Tipleri (Query Types)](#sorgu-tipleri-query-types)
   - [Mutasyonlar (Mutations)](#mutasyonlar-mutations)
3. [Kimlik Doğrulama ve Yetkilendirme](#kimlik-doğrulama-ve-yetkilendirme)
4. [Kullanıcı İşlemleri](#kullanıcı-işlemleri)
5. [Güvenlik Önlemleri](#güvenlik-önlemleri)

## Modeller

### CustomPermission

Sistemdeki izinleri tanımlar.

| Alan | Tür | Açıklama |
|------|-----|----------|
| name | CharField | İzin adı |
| codename | CharField | Benzersiz izin kodu |
| description | CharField | İzin açıklaması |

### CustomRole

Sistemdeki rolleri ve bu rollere atanmış izinleri tanımlar.

| Alan | Tür | Açıklama |
|------|-----|----------|
| name | CharField | Rol adı |
| permissions | ManyToManyField | Rol ile ilişkilendirilmiş izinler |
| description | CharField | Rol açıklaması |
| created_at | DateTimeField | Oluşturulma tarihi |

**Metodlar:**
- `get_permission()`: Rolün sahip olduğu izin kodlarını liste olarak döndürür.

### CustomUser

Temel kullanıcı modelidir. Django'nun AbstractBaseUser sınıfını genişletir.

| Alan | Tür | Açıklama |
|------|-----|----------|
| username | CharField | Kullanıcı adı (benzersiz) |
| email | EmailField | E-posta adresi (benzersiz) |
| password | CharField | Şifre (hashlenir) |
| role | ForeignKey | Kullanıcı rolü (CustomRole'e referans) |
| is_active | BooleanField | Kullanıcı aktif mi? |
| is_staff | BooleanField | Yönetici paneline erişebilir mi? |
| is_superuser | BooleanField | Süper kullanıcı mı? |
| last_login | DateTimeField | Son giriş zamanı |
| created_at | DateTimeField | Oluşturulma tarihi |
| updated_at | DateTimeField | Güncellenme tarihi |

**Metodlar:**
- `has_perm(perm, obj=None)`: Kullanıcının belirli bir izne sahip olup olmadığını kontrol eder.
- `has_module_perms(app_label)`: Kullanıcının belirli bir uygulama için izinlere sahip olup olmadığını kontrol eder.

### Student

Öğrenci profil bilgilerini saklar.

| Alan | Tür | Açıklama |
|------|-----|----------|
| user | OneToOneField | İlişkili CustomUser |
| first_name | CharField | Ad |
| last_name | CharField | Soyad |
| student_number | CharField | Öğrenci numarası (benzersiz) |
| department | CharField | Bölüm |
| faculty | CharField | Fakülte |
| phone_number | CharField | Telefon numarası |
| address | TextField | Adres |
| date_of_birth | DateField | Doğum tarihi |
| profile_picture | ImageField | Profil resmi |
| created_at | DateTimeField | Oluşturulma tarihi |
| updated_at | DateTimeField | Güncellenme tarihi |

### Company

Şirket profil bilgilerini saklar.

| Alan | Tür | Açıklama |
|------|-----|----------|
| user | OneToOneField | İlişkili CustomUser |
| company_name | CharField | Şirket adı |
| contact_person | CharField | İletişim kişisi |
| phone_number | CharField | Telefon numarası |
| address | TextField | Adres |
| website | URLField | Web sitesi |
| tax_number | CharField | Vergi numarası |
| created_at | DateTimeField | Oluşturulma tarihi |
| updated_at | DateTimeField | Güncellenme tarihi |

## GraphQL API

### Sorgu Tipleri (Query Types)

Sistemde bulunan sorgu tipleri:

#### CustomUserNode

Kullanıcı bilgilerini sorgulamak için kullanılır.

**Filtreleme Alanları:**
- id (exact)
- username (exact, icontains)
- email (exact, icontains)
- is_active (exact)

#### StudentNode

Öğrenci bilgilerini sorgulamak için kullanılır.

**Filtreleme Alanları:**
- student_number (exact, icontains)
- department (exact, icontains)
- faculty (exact, icontains)
- user (exact)

#### CompanyNode

Şirket bilgilerini sorgulamak için kullanılır.

**Filtreleme Alanları:**
- company_name (exact, icontains)
- contact_person (exact, icontains)
- phone_number (exact)
- address (exact, icontains)
- website (exact, icontains)
- tax_number (exact)

### Kullanılabilir Sorgular

```graphql
# Tüm kullanıcıları listele (userManage.UserList izni gerekli)
query {
  users {
    edges {
      node {
        id
        username
        email
        isActive
      }
    }
  }
}

# Tüm öğrencileri listele (userManage.StudentList izni gerekli)
query {
  students {
    edges {
      node {
        id
        firstName
        lastName
        studentNumber
        department
        faculty
      }
    }
  }
}

# Tüm şirketleri listele (userManage.CompanyList izni gerekli)
query {
  companies {
    edges {
      node {
        id
        companyName
        contactPerson
        website
        taxNumber
      }
    }
  }
}

# Kendi öğrenci bilgilerini getir (giriş yapmış öğrenci için)
query {
  me {
    id
    firstName
    lastName
    studentNumber
    department
  }
}

# Kendi şirket bilgilerini getir (giriş yapmış şirket için)
query {
  mycompany {
    id
    companyName
    contactPerson
    website
  }
}
```

### Mutasyonlar (Mutations)

#### AuthMutation

Kullanıcı girişi için kullanılır. Access token ve refresh token döndürür.

**Argümanlar:**
- usernameoremail (String)
- password (String)

**Döndürülen Değerler:**
- tokens (access_token, refresh_token)

**Örnek:**
```graphql
mutation {
  auth(usernameoremail: "kullanici@örnek.com", password: "sifre123") {
    tokens {
      accessToken
      refreshToken
    }
  }
}
```

#### RefreshTokenMutation

Access token yenilemek için kullanılır.

**Argümanlar:**
- refresh_token (String)

**Döndürülen Değerler:**
- tokens (access_token, refresh_token)

**Örnek:**
```graphql
mutation {
  refreshToken(refreshToken: "eyJ0eXAiOiJKV...") {
    tokens {
      accessToken
      refreshToken
    }
  }
}
```

#### LogoutMutation

Kullanıcı çıkışı için kullanılır.

**Argümanlar:**
- access_token (String)
- refresh_token (String)

**Döndürülen Değerler:**
- success (Boolean)
- message (String)

**Örnek:**
```graphql
mutation {
  logout(
    accessToken: "eyJ0eXAiOiJKV...", 
    refreshToken: "eyJ0eXAiOiJKV..."
  ) {
    success
    message
  }
}
```

#### CreateUserMutation

Yeni kullanıcı oluşturmak için kullanılır. (userManage.UserAdd izni gerekli)

**Argümanlar:**
- username (String, zorunlu)
- email (String, zorunlu)
- password (String, zorunlu)
- role_id (ID, zorunlu)
- user_type (String, zorunlu)
- first_name (String, isteğe bağlı)
- last_name (String, isteğe bağlı)
- student_number (String, isteğe bağlı)
- department (String, isteğe bağlı)
- faculty (String, isteğe bağlı)
- date_of_birth (Date, isteğe bağlı)
- profile_picture (Upload, isteğe bağlı)
- company_name (String, isteğe bağlı)
- contact_person (String, isteğe bağlı)
- website (String, isteğe bağlı)
- tax_number (String, isteğe bağlı)
- phone_number (String, isteğe bağlı)
- address (String, isteğe bağlı)

**Döndürülen Değerler:**
- user (UserType)
- success (Boolean)
- message (String)

**Örnek:**
```graphql
mutation {
  userCreate(
    username: "yeni_kullanici",
    email: "yeni@örnek.com",
    password: "güçlü_şifre",
    roleId: "1",  # Örn: Öğrenci rolü
    userType: "STUDENT",
    firstName: "Ahmet",
    lastName: "Yılmaz",
    studentNumber: "20230001",
    department: "Bilgisayar Mühendisliği",
    faculty: "Mühendislik Fakültesi"
  ) {
    success
    message
    user {
      id
      username
      email
    }
  }
}
```

#### UpdateProfileByAdminMutation

Admin tarafından kullanıcı profilini güncellemek için kullanılır. (userManage.UserUpdate izni gerekli)

**Argümanlar:**
- user_id (ID, zorunlu)
- usernameoremail (String, isteğe bağlı)
- email (String, isteğe bağlı)
- password (String, isteğe bağlı)
- role_id (ID, isteğe bağlı)
- user_type (String, isteğe bağlı)
- [ve diğer kullanıcı profil bilgileri...]

**Döndürülen Değerler:**
- success (Boolean)
- message (String)

**Örnek:**
```graphql
mutation {
  updateUserByAdmin(
    userId: "1",
    department: "Yeni Bölüm",
    faculty: "Yeni Fakülte"
  ) {
    success
    message
  }
}
```

#### UpdateMyProfileMutation

Kullanıcının kendi profilini güncellemesi için kullanılır.

**Argümanlar:**
- username (String, isteğe bağlı)
- password (String, isteğe bağlı) - Mevcut şifre
- new_password (String, isteğe bağlı)
- confirm_password (String, isteğe bağlı)
- [ve diğer profil bilgileri...]

**Döndürülen Değerler:**
- success (Boolean)
- message (String)

**Örnek:**
```graphql
mutation {
  updatemyprofile(
    password: "mevcut_şifre",
    newPassword: "yeni_şifre",
    confirmPassword: "yeni_şifre",
    firstName: "Yeni Ad",
    lastName: "Yeni Soyad"
  ) {
    success
    message
  }
}
```

## Kimlik Doğrulama ve Yetkilendirme

Sistem, JWT (JSON Web Token) tabanlı kimlik doğrulama kullanır. 

### Token Yapısı

- **Access Token**: Kısa ömürlü, API isteklerini yetkilendirmek için kullanılır.
- **Refresh Token**: Uzun ömürlü, access token yenilemek için kullanılır.

### Güvenlik Önlemleri

1. **Hız Sınırlama (Rate Limiting)**: Redis kullanılarak belirli işlemlerde hız sınırlaması uygulanır.
   - Giriş denemeleri: Bir kullanıcı için 60 saniye içinde maksimum 5 giriş denemesi
   - Token yenileme: 30 saniye minimum aralık
   - Profil güncelleme: 15 saniye minimum aralık

2. **Token Kara Listesi**: Çıkış yapılan token'lar geçersiz kılınır (`TokenBlacklist` sınıfı ile).

3. **Parola Doğrulama**: Güçlü parola kriterleri uygulanır (`UserValidator` sınıfı tarafından).

4. **Oturum Kontrolü**: API isteklerinde kullanıcı kimlik doğrulaması yapılır.

5. **İzin Kontrolü**: Belirli API işlemleri için özel izinler gereklidir (`custom_permission_required` dekoratörü).

## Kullanıcı İşlemleri

### Kullanıcı Tipleri

Sistem şu kullanıcı tiplerini destekler:
1. **Öğrenci (STUDENT)**
2. **Şirket (COMPANY)**
3. **Admin (ADMIN)**

### E-posta Bildirimleri

Sistem aşağıdaki durumlarda e-posta bildirimleri gönderir:
- Kullanıcı kaydı
- Şifre değişikliği

## Güvenlik Önlemleri

1. **Giriş İşlemi Güvenliği**:
   - Fazla giriş denemesi limiti (5 deneme / 60 saniye)
   - Redis ile rate limiting
   - Hatalı giriş denemeleri loglanır

2. **Token Güvenliği**:
   - Token yenileme denemeleri için rate limiting
   - Token karaliste sistemi
   - Token doğrulama kontrolleri

3. **Veri Validasyonu**:
   - E-posta ve telefon numarası formatı kontrolü
   - Parola güvenlik politikaları
   - Veri bütünlüğü kontrolleri

4. **Hata İşleme ve Loglama**:
   - Tüm önemli işlemler loglanır
   - Hassas hataların kullanıcıya gösterilmemesi
   - Detaylı hata takibi

### Log Yönetimi

Sistem, kullanıcı yönetimi modülüyle ilgili olayları log eder:

- Kullanıcı girişleri
- Başarısız giriş denemeleri
- Profil güncellemeleri
- Token işlemleri
- Hata durumları
