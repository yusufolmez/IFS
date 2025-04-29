# Kullanıcı tipleri
USER_TYPES = {
    'ADMIN': 'admin',
    'STUDENT': 'student',
    'COMPANY': 'company'
}

# Hata mesajları
ERROR_MESSAGES = {
    'USER_NOT_FOUND': 'Kullanıcı bulunamadı',
    'INVALID_INPUT': 'Geçersiz giriş',
    'AUTHENTICATION_REQUIRED': 'Lütfen giriş yapınız',
    'INVALID_USER_TYPE': 'Geçersiz kullanıcı tipi',
    'NO_UPDATE_FIELDS': 'Herhangi bir güncelleme yapılmadı. En az bir alan doldurulmalıdır',
    'ADMIN_UPDATE_FORBIDDEN': 'Admin kullanıcısı güncellenemez',
    'STUDENT_NOT_FOUND': 'Öğrenci bulunamadı',
    'COMPANY_NOT_FOUND': 'Şirket bulunamadı'
}

# Validasyon regex'leri
VALIDATION_PATTERNS = {
    'PHONE': r'^\+?1?\d{9,15}$',
    'EMAIL': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'PASSWORD': r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$'
} 