import path from 'node:path'
import fs from 'node:fs'

/**
 * 存储布局。全库唯一数据根，默认 <repo>/app_datas（沿用原 Python 侧约定），
 * 可用 HEARSIGHT_DATA_DIR 覆盖（dgx-spark 上指向 ~/hearsight-data）。
 */
const repoRoot = process.env.HEARSIGHT_REPO_ROOT || path.resolve(process.cwd(), '..')
const dataDir = process.env.HEARSIGHT_DATA_DIR || path.join(repoRoot, 'app_datas')

export const PATHS = {
  repoRoot,
  dataDir,
  /** 上传与下载的媒体文件（原 static_dir） */
  staticDir: path.join(dataDir, 'download_videos'),
  /** SQLite 主库 */
  dbPath: path.join(dataDir, 'hearsight.db'),
  /** 临时目录（ffmpeg 中间产物） */
  tmpDir: path.join(dataDir, 'tmp'),
} as const

for (const dir of [PATHS.dataDir, PATHS.staticDir, PATHS.tmpDir]) {
  fs.mkdirSync(dir, { recursive: true })
}

/** 媒体文件 → /static/<basename> */
export function staticUrl(basename: string): string {
  return `/static/${encodeURIComponent(basename)}`
}

export function mediaPathFromBasename(basename: string): string {
  return path.join(PATHS.staticDir, basename)
}
