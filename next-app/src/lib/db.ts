import Database from 'better-sqlite3'
import { PATHS } from './paths'

/**
 * SQLite 单例。schema 由 PG DDL 逐字迁移（见移植规格第 3 章）：
 * - SERIAL → INTEGER PRIMARY KEY AUTOINCREMENT
 * - TIMESTAMP/TIMESTAMPTZ → TEXT（ISO8601 / localtime，字典序即时间序）
 * - updated_at 补触发器（原 PG 无 ON UPDATE，靠应用层显式 SET，这里补齐）
 * 新增 transcripts.chat_messages_json：原 messages_router 的 transcript 级
 * 聊天历史误写进 chat_messages 表（外键必炸，规格 9.6-a），改存本列。
 */
let db: Database.Database | null = null

export function getDb(): Database.Database {
  if (db) return db
  db = new Database(PATHS.dbPath)
  db.pragma('journal_mode = WAL')
  db.pragma('foreign_keys = ON')
  db.pragma('busy_timeout = 5000')
  initSchema(db)
  return db
}

function initSchema(d: Database.Database) {
  d.exec(`
    CREATE TABLE IF NOT EXISTS transcripts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      audio_path TEXT NOT NULL,
      video_path TEXT,
      media_type TEXT NOT NULL DEFAULT 'audio',
      segments_json TEXT NOT NULL,
      summaries_json TEXT,
      translations_json TEXT,
      chat_messages_json TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    );
    CREATE INDEX IF NOT EXISTS idx_transcripts_audio_path ON transcripts(audio_path);

    CREATE TABLE IF NOT EXISTS chat_sessions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    );
    CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at ON chat_sessions(updated_at DESC);

    CREATE TABLE IF NOT EXISTS chat_messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
      message_type TEXT NOT NULL CHECK (message_type IN ('user','ai')),
      content TEXT NOT NULL,
      timestamp TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    );
    CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
    CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at DESC);

    CREATE TABLE IF NOT EXISTS jobs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      url TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'pending',
      created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
      started_at TEXT,
      finished_at TEXT,
      result_json TEXT,
      error TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_jobs_status_created ON jobs(status, created_at DESC);

    CREATE TABLE IF NOT EXISTS translate_progress (
      transcript_id INTEGER PRIMARY KEY,
      status TEXT NOT NULL DEFAULT 'idle',
      progress INTEGER NOT NULL DEFAULT 0,
      translated_count INTEGER NOT NULL DEFAULT 0,
      total_count INTEGER NOT NULL DEFAULT 0,
      target_lang_code TEXT,
      message TEXT,
      updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS segment_embeddings (
      transcript_id INTEGER NOT NULL,
      chunk_index INTEGER NOT NULL,
      segment_indices TEXT NOT NULL,
      vec BLOB NOT NULL,
      PRIMARY KEY (transcript_id, chunk_index)
    );

    -- 原 PG 无 updated_at 触发器，列表排序会失真；SQLite 侧补齐
    CREATE TRIGGER IF NOT EXISTS trg_transcripts_updated_at
      AFTER UPDATE ON transcripts
      BEGIN UPDATE transcripts SET updated_at = datetime('now','localtime') WHERE id = NEW.id; END;
    CREATE TRIGGER IF NOT EXISTS trg_chat_sessions_updated_at
      AFTER UPDATE ON chat_sessions
      BEGIN UPDATE chat_sessions SET updated_at = datetime('now','localtime') WHERE id = NEW.id; END;
  `)

  // 老库补列（等价 PG 的 ALTER TABLE ... ADD COLUMN IF NOT EXISTS）
  const cols = d.prepare(`PRAGMA table_info(transcripts)`).all() as { name: string }[]
  if (!cols.some((c) => c.name === 'chat_messages_json')) {
    d.exec(`ALTER TABLE transcripts ADD COLUMN chat_messages_json TEXT`)
  }
}
