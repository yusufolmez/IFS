import logging
import json
from datetime import datetime
from django.conf import settings

logger = logging.getLogger('user_management')
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('user_management.log')
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Handler'ları logger'a ekle
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def log_error(message, context=None):
    """Hata logları için"""
    try:
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': 'ERROR',
            'message': message,
            'context': context or {}
        }
        logger.error(json.dumps(log_data, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Loglama hatası: {str(e)}")

def log_info(message, context=None):
    """Bilgi logları için"""
    try:
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'message': message,
            'context': context or {}
        }
        logger.info(json.dumps(log_data, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Loglama hatası: {str(e)}")

def log_warning(message, context=None):
    """Uyarı loglarını kaydeder"""
    logger.warning(f"Warning: {message}, Context: {context}") 