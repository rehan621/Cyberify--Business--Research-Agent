-- ============================================
-- Cyberify Research Agent - Database Schema
-- ============================================

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) UNIQUE NOT NULL,
    username    VARCHAR(100) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Workspaces Table (Feature 5 - Research Workspace)
CREATE TABLE IF NOT EXISTS workspaces (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Research History Table (Feature 8)
CREATE TABLE IF NOT EXISTS research_history (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id) ON DELETE CASCADE,
    workspace_id    INTEGER REFERENCES workspaces(id) ON DELETE SET NULL,
    query           TEXT NOT NULL,
    status          VARCHAR(50) DEFAULT 'pending',  -- pending, running, completed, failed
    report          TEXT,
    sources         JSONB,
    confidence_score FLOAT,
    created_at      TIMESTAMP DEFAULT NOW(),
    completed_at    TIMESTAMP
);

-- Uploaded Documents Table (Feature 4 - RAG)
CREATE TABLE IF NOT EXISTS documents (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id) ON DELETE CASCADE,
    workspace_id    INTEGER REFERENCES workspaces(id) ON DELETE SET NULL,
    filename        VARCHAR(255) NOT NULL,
    file_type       VARCHAR(50),   -- pdf, docx, txt
    file_path       TEXT,
    chroma_doc_id   VARCHAR(255),  -- reference in ChromaDB
    uploaded_at     TIMESTAMP DEFAULT NOW()
);

-- LangGraph Checkpoints Table (Feature 3 - Stateful Memory)
CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id       VARCHAR(255) PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id) ON DELETE CASCADE,
    checkpoint_data JSONB,
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- Chat History Table (Feature 10 - AI Chat Mode)
CREATE TABLE IF NOT EXISTS chat_messages (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id) ON DELETE CASCADE,
    research_id     INTEGER REFERENCES research_history(id) ON DELETE SET NULL,
    role            VARCHAR(20) NOT NULL,  -- user, assistant
    content         TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_research_user ON research_history(user_id);
CREATE INDEX IF NOT EXISTS idx_docs_user ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_workspace_user ON workspaces(user_id);