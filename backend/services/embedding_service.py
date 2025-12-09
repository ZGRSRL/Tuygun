"""
Embedding Service - Metinleri vektörlere çevirir
"""
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

# Model: all-MiniLM-L6-v2 (Hızlı, Hafif, CPU dostu, Türkçe performansı makul)
MODEL_NAME = "all-MiniLM-L6-v2"
_model = None

def get_model():
    """Embedding modelini yükler (lazy loading)"""
    global _model
    if _model is None:
        logger.info(f"Embedding modeli yükleniyor: {MODEL_NAME}...")
        try:
            _model = SentenceTransformer(MODEL_NAME)
            logger.info("Model başarıyla yüklendi.")
        except Exception as e:
            logger.error(f"Model yüklenirken hata: {e}")
            raise
    return _model

def generate_embedding(text: str) -> list:
    """
    Metni vektöre çevirir (384 boyutlu float listesi)
    
    Args:
        text: Vektörleştirilecek metin
        
    Returns:
        384 boyutlu float listesi (embedding)
    """
    if not text or not text.strip():
        return []
    
    try:
        model = get_model()
        # Metindeki yeni satırları temizle ve normalize et
        clean_text = text.replace("\n", " ").replace("\r", " ").strip()
        
        # Çok uzun metinleri parçalara böl (max 512 token)
        if len(clean_text) > 2000:
            # İlk 2000 karakteri al (basit yaklaşım)
            clean_text = clean_text[:2000]
        
        embedding = model.encode(clean_text, normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Embedding oluşturulurken hata: {e}")
        return []

def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Birden fazla metni toplu olarak vektörleştirir (daha hızlı)
    
    Args:
        texts: Vektörleştirilecek metin listesi
        
    Returns:
        Embedding listesi
    """
    if not texts:
        return []
    
    try:
        model = get_model()
        # Metinleri temizle
        clean_texts = [
            text.replace("\n", " ").replace("\r", " ").strip()[:2000]
            for text in texts
            if text and text.strip()
        ]
        
        if not clean_texts:
            return []
        
        embeddings = model.encode(clean_texts, normalize_embeddings=True)
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Toplu embedding oluşturulurken hata: {e}")
        return []

