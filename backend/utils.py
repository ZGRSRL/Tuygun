"""
Utility fonksiyonları
"""
from datetime import datetime, timedelta
from typing import Optional
import re
import uuid

def format_time_ago(dt: Optional[datetime]) -> str:
    """
    Datetime'ı Türkçe "X saat önce" formatına çevirir
    """
    if dt is None:
        return "Hiç"
    
    # Timezone-aware datetime'a çevir
    if dt.tzinfo is None:
        # Eğer timezone yoksa UTC olarak kabul et
        from datetime import timezone
        dt = dt.replace(tzinfo=timezone.utc)
    
    from datetime import timezone
    now = datetime.now(timezone.utc)
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "Az önce"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} dk önce"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} saat önce"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days} gün önce"
    elif diff < timedelta(days=30):
        weeks = diff.days // 7
        return f"{weeks} hafta önce"
    elif diff < timedelta(days=365):
        months = diff.days // 30
        return f"{months} ay önce"
    else:
        years = diff.days // 365
        return f"{years} yıl önce"

def format_file_size(size_bytes: Optional[int]) -> str:
    """
    Byte'ı human-readable formata çevirir (KB, MB, GB)
    """
    if size_bytes is None:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            if unit == 'B':
                return f"{int(size_bytes)} {unit}"
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

