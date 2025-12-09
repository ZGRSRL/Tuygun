-- zgrwise veritabanı için tablo oluşturma scripti

-- Enum tipleri oluştur
CREATE TYPE document_status AS ENUM ('indexed', 'processing', 'error');
CREATE TYPE source_status AS ENUM ('active', 'syncing', 'error', 'pending');
CREATE TYPE activity_type AS ENUM ('document', 'query', 'embedding', 'source');

-- Sources tablosu
CREATE TABLE IF NOT EXISTS sources (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    type VARCHAR NOT NULL,
    status source_status DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    total_embeddings INTEGER DEFAULT 0,
    source_config TEXT,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sources_name ON sources(name);

-- Documents tablosu
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    type VARCHAR NOT NULL,
    source_id VARCHAR NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    size VARCHAR NOT NULL,
    size_bytes INTEGER,
    embeddings_count INTEGER DEFAULT 0,
    status document_status DEFAULT 'processing',
    file_path VARCHAR,
    content_hash VARCHAR,
    doc_metadata TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_title ON documents(title);
CREATE INDEX IF NOT EXISTS idx_documents_source_id ON documents(source_id);

-- Activities tablosu
CREATE TABLE IF NOT EXISTS activities (
    id VARCHAR PRIMARY KEY,
    type activity_type NOT NULL,
    title VARCHAR NOT NULL,
    description TEXT,
    activity_metadata TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activities_created_at ON activities(created_at);



