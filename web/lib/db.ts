import { Pool, types } from "pg";

// Return dates and timestamps as plain strings so the server and browser agree.
types.setTypeParser(1082, (value) => value);
types.setTypeParser(1114, (value) => `${value.replace(" ", "T")}Z`);

let pool: Pool | null = null;

export function getPool(): Pool {
  if (!pool) {
    const connectionString = process.env.DATABASE_URL;
    if (!connectionString) {
      throw new Error("DATABASE_URL is not set");
    }
    // Supabase's pooler presents a certificate chain Node does not trust by default.
    pool = new Pool({ connectionString, max: 1, ssl: { rejectUnauthorized: false } });
  }
  return pool;
}
