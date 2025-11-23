-- Créer la base de données
CREATE DATABASE gestion_visiteurs;

-- Connecter à la base
\c gestion_visiteurs

-- Créer les tables users
CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50),
    prenom VARCHAR(50),
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    structure VARCHAR(100) NOT NULL,
    role VARCHAR(20) DEFAULT 'utilisateur' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Créer la table visiteurs
CREATE TABLE IF NOT EXISTS public.visiteurs (
    id SERIAL PRIMARY KEY,
    image_path TEXT,
    nom VARCHAR(50) NOT NULL,
    prenom VARCHAR(50) NOT NULL,
    phone_number VARCHAR(20),
    date_of_birth VARCHAR(10),
    place_of_birth VARCHAR(100),
    id_type VARCHAR(50),
    id_number VARCHAR(50),
    motif VARCHAR(200),
    date DATE NOT NULL,
    arrival_time TIME,
    exit_time TIME,
    observation TEXT
);

-- Créer la table visitor_shares
CREATE TABLE IF NOT EXISTS public.visitor_shares (
    id SERIAL PRIMARY KEY,
    visitor_id INTEGER NOT NULL REFERENCES visiteurs(id) ON DELETE CASCADE,
    shared_by_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shared_with_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shared_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',
    CONSTRAINT no_self_share CHECK (shared_by_user_id != shared_with_user_id)
);

-- Créer la table document_shares
CREATE TABLE IF NOT EXISTS public.document_shares (
    id SERIAL PRIMARY KEY,
    shared_by_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shared_with_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file BYTEA,
    filename VARCHAR(255) NOT NULL,
    document_type VARCHAR(50),
    shared_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',
    CONSTRAINT no_self_share_doc CHECK (shared_by_user_id != shared_with_user_id)
);

-- Créer la table password_reset_tokens
CREATE TABLE IF NOT EXISTS public.password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(64) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Créer les indexes
CREATE INDEX IF NOT EXISTS idx_visitor_shares_visitor_id ON visitor_shares(visitor_id);
CREATE INDEX IF NOT EXISTS idx_visitor_shares_user_id ON visitor_shares(shared_with_user_id);
CREATE INDEX IF NOT EXISTS idx_document_shares_user_id ON document_shares(shared_with_user_id);

-- Remettre à jour les séquences
SELECT setval(pg_get_serial_sequence('users','id'), COALESCE(MAX(id), 0), false) FROM users;
SELECT setval(pg_get_serial_sequence('visiteurs','id'), COALESCE(MAX(id), 0), false) FROM visiteurs;
SELECT setval(pg_get_serial_sequence('visitor_shares','id'), COALESCE(MAX(id), 0), false) FROM visitor_shares;
SELECT setval(pg_get_serial_sequence('document_shares','id'), COALESCE(MAX(id), 0), false) FROM document_shares;
SELECT setval(pg_get_serial_sequence('password_reset_tokens','id'), COALESCE(MAX(id), 0), false) FROM password_reset_tokens;