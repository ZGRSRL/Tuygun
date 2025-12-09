"""
RAG (Retrieval-Augmented Generation) Servisi
Semantic search + LLM ile akıllı sohbet
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import Document
from services.embedding_service import generate_embedding
import logging
import json

logger = logging.getLogger(__name__)

def search_similar_documents(db: Session, query: str, limit: int = 3):
    """
    Soruyu vektöre çevirir ve veritabanında en yakın dokümanları bulur.
    PGVector'ın 'cosine distance' operatörünü kullanır.
    """
    # 1. Soruyu Vektörleştir
    query_vector = generate_embedding(query)
    
    if not query_vector:
        logger.warning("Query embedding oluşturulamadı")
        return []

    try:
        # 2. Vektör Araması (Cosine Distance)
        # Document.embedding ile sorgu vektörü arasındaki mesafeye göre sırala
        # pgvector'da cosine_distance operatörü kullanıyoruz
        results = db.query(Document).filter(
            Document.embedding.isnot(None),
            Document.content.isnot(None)
        ).order_by(
            Document.embedding.cosine_distance(query_vector)
        ).limit(limit).all()
        
        return results
    except Exception as e:
        logger.error(f"Vector search hatası: {e}")
        # Fallback: Basit text search
        try:
            results = db.query(Document).filter(
                Document.content.isnot(None),
                Document.content.ilike(f"%{query}%")
            ).limit(limit).all()
            return results
        except Exception as fallback_error:
            logger.error(f"Fallback search hatası: {fallback_error}")
            return []


async def chat_with_data(db: Session, user_message: str):
    """
    RAG Pipeline: Retrieval -> Augmentation -> Generation
    """
    # 1. İlgili Dokümanları Bul (Retrieval)
    relevant_docs = search_similar_documents(db, user_message, limit=3)
    
    if not relevant_docs:
        return {
            "answer": "Üzgünüm, veritabanımda bu konuyla ilgili bir bilgi bulamadım. RSS'den yeni makaleler eklemeyi deneyebilirsin.",
            "sources": []
        }

    # 2. Context Oluştur
    context_text = ""
    sources = []
    
    for doc in relevant_docs:
        # İçeriği al (maksimum 1500 karakter)
        doc_content = doc.content[:1500] if doc.content else ""
        
        # URL'yi metadata'dan çek
        doc_url = None
        try:
            if doc.doc_metadata:
                metadata = json.loads(doc.doc_metadata)
                doc_url = metadata.get('url')
        except:
            pass
        
        context_text += f"-- KAYNAK: {doc.title} --\n{doc_content}\n\n"
        sources.append({
            "id": doc.id,
            "title": doc.title,
            "url": doc_url,
            "content": doc_content,
            "similarity": 0.0  # Hesaplaması maliyetli ise şimdilik 0 geçebiliriz
        })

    # 3. LLM Prompt Hazırla (Augmentation)
    prompt = f"""Sen TUYGUN adında akıllı bir analitik asistansın.
Aşağıdaki "KAYNAK BİLGİLER"i kullanarak kullanıcının sorusunu cevapla.

KURALLAR:
1. Sadece verilen kaynaklardaki bilgiyi kullan. Uydurma.
2. Cevabın net, profesyonel ve Türkçe olsun.
3. Kaynaklarda bilgi yoksa "Bilmiyorum" de.
4. Cevabını kısa ve öz tut (maksimum 5-6 cümle).

KAYNAK BİLGİLER:
{context_text}

KULLANICI SORUSU:
{user_message}

CEVAP:"""

    # 4. Cevap Üret (Generation) - Ollama kullan
    try:
        import ollama
        ollama_response = ollama.generate(
            model='llama3',
            prompt=prompt
        )
        answer = ollama_response.get('response', '').strip()
        
        if not answer:
            answer = "Üzgünüm, şu anda cevap üretemiyorum. Lütfen tekrar deneyin."
    except Exception as e:
        logger.error(f"Ollama hatası: {e}")
        answer = "Üzgünüm, AI servisi şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin."
    
    return {
        "answer": answer,
        "sources": sources
    }

