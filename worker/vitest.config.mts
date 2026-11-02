import path from "node:path";
import { cloudflareTest, readD1Migrations } from "@cloudflare/vitest-plugin";
import { defineConfig } from "vitest/config";

export default defineConfig(async () => {
	const migraciones = await readD1Migrations(path.join(__dirname, "migrations"));
	return {
		plugins: [
			cloudflareTest({
				wrangler: { configPath: "./wrangler.jsonc" },
				miniflare: {

					bindings: {
						GATEWAY_PUB: "03a107bff3ce10be1d70dd18e74bc09967e4d6309ba50d5f1ddc8664125531b8",
						TEST_MIGRATIONS: migraciones,
					},
				},
			}),
		],
		test: { setupFiles: ["./test/aplicar-migraciones.ts"] },
	};
});
