import logging
import json
from datetime import datetime, timedelta
from django.conf import settings
import os

def get_logger(name):
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)

    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f'{name}.log')
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    return logger

def log_error(module_name, message, context=None):
    logger = get_logger(module_name)
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "level": "ERROR",
        "message": message,
        "context": context or {}
    }
    logger.error(json.dumps(log_data, ensure_ascii=False))

def log_info(module_name, message, context=None):
    try:
        logger = get_logger(module_name)
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'message': message,
            'context': context or {}
        }
        logger.info(json.dumps(log_data, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Loglama hatası: {str(e)}")

def log_warning(module_name, message, context=None):
    try:
        logger = get_logger(module_name)
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': 'WARNING',
            'message': message,
            'context': context or {}
        }
        logger.warning(json.dumps(log_data, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Loglama hatası: {str(e)}")

class LogCleaner:
    def __init__(self, module_name):
        self.module_name = module_name
        self.logs_dir = os.path.join(settings.BASE_DIR, 'logs')
        self.log_file = os.path.join(self.logs_dir, f'{self.module_name}.log')
        self.max_size_mb = 10
        self.max_age_days = 30
        self.backup_dir = os.path.join(self.logs_dir, 'backups')

    def check_file_size(self):
        if os.path.exists(self.log_file):
            file_size = os.path.getsize(self.log_file)
            return file_size > self.max_size_mb * 1024 * 1024
        return False

    def check_file_age(self):
        if os.path.exists(self.log_file):
            file_time = os.path.getmtime(self.log_file)
            current_time = datetime.now().timestamp()
            age_days = (current_time - file_time) / (24 * 3600)
            return age_days > self.max_age_days
        return False

    def create_backup(self):
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        backup_file = os.path.join(
            self.backup_dir,
            f'{self.module_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
        
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r', encoding='utf-8') as src:
                with open(backup_file, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            log_info(self.module_name, f"Log yedeği oluşturuldu: {backup_file}")

    def clean_old_logs(self):
        try:
            if not os.path.exists(self.log_file):
                return

            cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
            temp_file = f"{self.log_file}.tmp"
            
            with open(self.log_file, 'r', encoding='utf-8') as src:
                with open(temp_file, 'w', encoding='utf-8') as dst:
                    for line in src:
                        try:
                            log_data = json.loads(line)
                            log_date = datetime.fromisoformat(log_data['timestamp'])
                            if log_date > cutoff_date:
                                dst.write(line)
                        except json.JSONDecodeError:
                            continue

            os.replace(temp_file, self.log_file)
            log_info(self.module_name, f"Eski loglar temizlendi. Son {self.max_age_days} günün logları korundu.")

        except Exception as e:
            log_error(self.module_name, f"Log temizleme hatası: {str(e)}")
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def rotate_logs(self):
        try:
            if not os.path.exists(self.log_file):
                return

            if self.check_file_size():
                self.create_backup()
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    f.write('')
                log_info(self.module_name, "Log dosyası rotasyonu yapıldı.")

            if self.check_file_age():
                self.create_backup()
                self.clean_old_logs()

        except Exception as e:
            log_error(self.module_name, f"Log rotasyon hatası: {str(e)}")

    def clean_logs(self):
        try:
            self.rotate_logs()
            log_info(self.module_name, "Log temizleme işlemi tamamlandı.")
        except Exception as e:
            log_error(self.module_name, f"Log temizleme işlemi başarısız: {str(e)}")
    
    
    