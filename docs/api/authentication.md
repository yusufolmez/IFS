# Authentication API

## Giriş (Login)

Kullanıcı girişi için kullanılan mutasyon. Email veya kullanıcı adı ile giriş yapılabilir.

### Mutasyon

```graphql
mutation {
  auth(usernameoremail: String!, password: String!) {
    tokens {
      accessToken
      refreshToken
    }
  }
}
```

### Parametreler

| Parametre       | Tip    | Zorunlu | Açıklama                        |
| --------------- | ------ | ------- | ------------------------------- |
| usernameoremail | String | Evet    | Kullanıcı adı veya email adresi |
| password        | String | Evet    | Kullanıcı şifresi               |

### Dönüş Değerleri

| Alan         | Tip    | Açıklama          |
| ------------ | ------ | ----------------- |
| accessToken  | String | JWT access token  |
| refreshToken | String | JWT refresh token |

### Örnek İstek

```graphql
mutation {
  auth(usernameoremail: "user@example.com", password: "password123") {
    tokens {
      accessToken
      refreshToken
    }
  }
}
```

### Başarılı Yanıt

```json
{
  "data": {
    "auth": {
      "tokens": {
        "accessToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refreshToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
      }
    }
  }
}
```

### Hata Durumları

| Hata Kodu           | Açıklama                           |
| ------------------- | ---------------------------------- |
| USER_NOT_FOUND      | Kullanıcı bulunamadı               |
| INVALID_CREDENTIALS | Geçersiz kullanıcı adı veya şifre  |
| TOO_MANY_ATTEMPTS   | Çok fazla başarısız giriş denemesi |

### Rate Limiting

- 60 saniye içinde maksimum 5 başarısız giriş denemesi yapılabilir
- Limit aşıldığında 1 dakika beklenmesi gerekir

### Güvenlik Notları

- Şifreler asla plain text olarak gönderilmemelidir
- Access token'ın geçerlilik süresi 1 saattir
- Refresh token'ın geçerlilik süresi 7 gündür

## Token Yenileme (Refresh Token)

Access token'ın süresi dolduğunda yeni bir token almak için kullanılır.

### Mutasyon

```graphql
mutation {
  refreshToken(refreshToken: String!) {
    tokens {
      accessToken
      refreshToken
    }
  }
}
```

### Parametreler

| Parametre    | Tip    | Zorunlu | Açıklama              |
| ------------ | ------ | ------- | --------------------- |
| refreshToken | String | Evet    | Geçerli refresh token |

### Rate Limiting

- 30 saniye içinde maksimum 1 yenileme isteği yapılabilir

## Çıkış (Logout)

Kullanıcı çıkışı için kullanılan mutasyon. Access ve refresh token'ları geçersiz kılar.

### Mutasyon

```graphql
mutation {
  logout(access_token: String!, refresh_token: String!) {
    success
    message
  }
}
```

### Parametreler

| Parametre     | Tip    | Zorunlu | Açıklama              |
| ------------- | ------ | ------- | --------------------- |
| access_token  | String | Evet    | Geçerli access token  |
| refresh_token | String | Evet    | Geçerli refresh token |

### Rate Limiting

- 30 saniye içinde maksimum 1 çıkış isteği yapılabilir

### Örnek İstek

```graphql
mutation {
  logout(
    access_token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    refresh_token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
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
    "logout": {
      "success": true,
      "message": "Çıkış işlemi başarılı."
    }
  }
}
```

### Hata Durumları

| Hata Kodu         | Açıklama               |
| ----------------- | ---------------------- |
| INVALID_TOKENS    | Geçersiz token'lar     |
| TOO_MANY_ATTEMPTS | Çok sık çıkış denemesi |
