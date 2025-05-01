from django.conf import settings
from core.utils.logging import LogCleaner
from core.utils.monitoring import LogMonitor
from core.utils.logging import log_info, log_error

def cleanup_logs():
    try:
        for module_name, config in settings.LOGGING_CLEANUP.items():
            cleaner = LogCleaner(module_name)
            cleaner.max_size_mb = config['max_size_mb']
            cleaner.max_age_days = config['max_age_days']
            cleaner.clean_logs()
        
        log_info('system_monitoring', 'Tüm modüllerin log temizleme işlemi tamamlandı')
    except Exception as e:
        log_error('system_monitoring', 'Log temizleme işlemi başarısız', {'error': str(e)})

def monitor_logs():
    try:
        monitor = LogMonitor()
        monitor.alert_threshold_mb = settings.LOG_MONITORING['alert_threshold_mb']
        monitor.alert_threshold_days = settings.LOG_MONITORING['alert_threshold_days']
        monitor.send_alerts()
        
        stats = monitor.get_log_statistics()
        if stats:
            log_info('system_monitoring', 'Log istatistikleri', stats)
            
    except Exception as e:
        log_error('system_monitoring', 'Log izleme işlemi başarısız', {'error': str(e)}) 