import { applyD1Migrations, env } from "cloudflare:test";

// Aplica las migraciones de worker/migrations a la D1 de prueba antes de cada archivo.
await applyD1Migrations(env.DB, (env as any).TEST_MIGRATIONS);
