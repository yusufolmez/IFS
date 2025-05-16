import os
from datetime import datetime
from django.conf import settings
from .logging import log_error, log_info, log_warning

class LogMonitor:
    def __init__(self):
        self.logs_dir = os.path.join(settings.BASE_DIR, 'logs')
        self.backup_dir = os.path.join(self.logs_dir, 'backups')
        self.alert_threshold_mb = 100  
        self.alert_threshold_days = 90  

    def check_log_sizes(self):
        """Tüm log dosyalarının boyutlarını kontrol eder"""
        try:
            total_size = 0
            for filename in os.listdir(self.logs_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(self.logs_dir, filename)
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  
                    total_size += file_size
                    
                    if file_size > self.alert_threshold_mb:
                        log_warning('system_monitoring', 
                                  f'Log dosyası boyutu aşıldı: {filename} - {file_size:.2f}MB',
                                  {'file': filename, 'size_mb': file_size})

            if total_size > self.alert_threshold_mb:
                log_warning('system_monitoring',
                          f'Toplam log boyutu aşıldı: {total_size:.2f}MB',
                          {'total_size_mb': total_size})

            return total_size

        except Exception as e:
            log_error('system_monitoring', 'Log boyutu kontrolü sırasında hata', {'error': str(e)})
            return 0

    def check_log_ages(self):
        """Log dosyalarının yaşlarını kontrol eder"""
        try:
            current_time = datetime.now().timestamp()
            for filename in os.listdir(self.logs_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(self.logs_dir, filename)
                    file_time = os.path.getmtime(file_path)
                    age_days = (current_time - file_time) / (24 * 3600)
                    
                    if age_days > self.alert_threshold_days:
                        log_warning('system_monitoring',
                                  f'Log dosyası çok eski: {filename} - {age_days:.0f} gün',
                                  {'file': filename, 'age_days': age_days})

        except Exception as e:
            log_error('system_monitoring', 'Log yaşı kontrolü sırasında hata', {'error': str(e)})

    def send_alerts(self):
        """Kritik durumları bildirir"""
        try:
            total_size = self.check_log_sizes()
            self.check_log_ages()
            
            if total_size > self.alert_threshold_mb:
                # Burada email gönderme veya başka bildirim mekanizmaları eklenebilir
                log_error('system_monitoring',
                         'Kritik log boyutu uyarısı',
                         {'total_size_mb': total_size})

        except Exception as e:
            log_error('system_monitoring', 'Alert gönderme sırasında hata', {'error': str(e)})

    def get_log_statistics(self):
        """Log istatistiklerini döndürür"""
        try:
            stats = {
                'total_size_mb': 0,
                'file_count': 0,
                'oldest_log_days': 0,
                'files': []
            }
            
            current_time = datetime.now().timestamp()
            
            for filename in os.listdir(self.logs_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(self.logs_dir, filename)
                    file_size = os.path.getsize(file_path) / (1024 * 1024)
                    file_time = os.path.getmtime(file_path)
                    age_days = (current_time - file_time) / (24 * 3600)
                    
                    stats['total_size_mb'] += file_size
                    stats['file_count'] += 1
                    stats['oldest_log_days'] = max(stats['oldest_log_days'], age_days)
                    stats['files'].append({
                        'name': filename,
                        'size_mb': file_size,
                        'age_days': age_days
                    })
            
            return stats

        except Exception as e:
            log_error('system_monitoring', 'Log istatistikleri alınırken hata', {'error': str(e)})
            return None 