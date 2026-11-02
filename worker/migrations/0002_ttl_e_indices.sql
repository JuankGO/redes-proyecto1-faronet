ALTER TABLE mensajes ADD COLUMN expira INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_mensajes_tema ON mensajes (tema, creado);
CREATE INDEX IF NOT EXISTS idx_mensajes_expira ON mensajes (expira);
CREATE INDEX IF NOT EXISTS idx_buzon_expira ON buzon (expira);
CREATE INDEX IF NOT EXISTS idx_directorio_expira ON directorio (expira);
CREATE INDEX IF NOT EXISTS idx_nonces_expira ON nonces (expira);
