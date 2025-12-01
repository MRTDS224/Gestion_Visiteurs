-- Créer la base de données
CREATE DATABASE gestion_visiteurs;

-- Connecter à la base
\c gestion_visiteurs

-- Créer la table users
CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50),
    prenom VARCHAR(50),
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    structure VARCHAR(100) NOT NULL,
    role VARCHAR(20) DEFAULT 'utilisateur' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Créer la table visitors
CREATE TABLE IF NOT EXISTS public.visitors (
    id SERIAL PRIMARY KEY,
    image_path TEXT NOT NULL,
    phone_number VARCHAR NOT NULL,
    place_of_birth VARCHAR NOT NULL,
    motif VARCHAR NOT NULL,
    date VARCHAR NOT NULL,
    arrival_time VARCHAR NOT NULL,
    exit_time VARCHAR,
    observation TEXT
);

-- Créer la table visitor_shares
CREATE TABLE IF NOT EXISTS public.visitor_shares (
    id SERIAL PRIMARY KEY,
    visitor_id INTEGER NOT NULL REFERENCES visitors(id) ON DELETE CASCADE,
    shared_by_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shared_with_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    place_of_birth VARCHAR NOT NULL,
    phone_number VARCHAR NOT NULL,
    motif TEXT,
    image_data BYTEA NOT NULL,
    shared_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    status VARCHAR DEFAULT 'active' NOT NULL,
    CONSTRAINT no_self_share CHECK (shared_by_user_id != shared_with_user_id)
);

-- Créer la table document_shares
CREATE TABLE IF NOT EXISTS public.document_shares (
    id SERIAL PRIMARY KEY,
    shared_by_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shared_to_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file BYTEA,
    file_name VARCHAR,
    document_type VARCHAR(50),
    shared_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    status VARCHAR DEFAULT 'active' NOT NULL,
    CONSTRAINT no_self_share_doc CHECK (shared_by_user_id != shared_to_user_id)
);

-- Créer la table password_reset_tokens
CREATE TABLE IF NOT EXISTS public.password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(64) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_visitor_shares_visitor_id ON visitor_shares(visitor_id);
CREATE INDEX IF NOT EXISTS idx_visitor_shares_user_id ON visitor_shares(shared_with_user_id);
CREATE INDEX IF NOT EXISTS idx_document_shares_user_id ON document_shares(shared_to_user_id);

-- Séquences
SELECT setval(pg_get_serial_sequence('users','id'), COALESCE(MAX(id), 0), false) FROM users;
SELECT setval(pg_get_serial_sequence('visitors','id'), COALESCE(MAX(id), 0), false) FROM visitors;
SELECT setval(pg_get_serial_sequence('visitor_shares','id'), COALESCE(MAX(id), 0), false) FROM visitor_shares;
SELECT setval(pg_get_serial_sequence('document_shares','id'), COALESCE(MAX(id), 0), false) FROM document_shares;
SELECT setval(pg_get_serial_sequence('password_reset_tokens','id'), COALESCE(MAX(id), 0), false) FROM password_reset_tokens;