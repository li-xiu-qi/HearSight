import { NextRequest, NextResponse } from 'next/server'
import fs from 'node:fs'
import path from 'node:path'
import { getDb } from '@/lib/db'
import { PATHS, staticUrl } from '@/lib/paths'

/** POST /api/upload/rename — basename 级重命名 + transcripts.audio_path / jobs.result_json 联动 */
export async function POST(req: NextRequest) {
  const body = (await req.json().catch(() => null)) as
    | { old_filename?: string; new_filename?: string }
    | null
  const oldName = body?.old_filename
  const newName = body?.new_filename
  if (!oldName || !newName) {
    return NextResponse.json({ detail: 'old_filename 和 new_filename 都是必填项' }, { status: 400 })
  }
  const oldPath = path.join(PATHS.staticDir, path.basename(oldName))
  if (!fs.existsSync(oldPath)) {
    return NextResponse.json({ detail: `文件不存在: ${oldName}` }, { status: 404 })
  }
  const oldExt = path.extname(oldName)
  let finalName = newName.includes('.') ? newName : `${newName}${oldExt}`
  if (path.extname(finalName).toLowerCase() !== oldExt.toLowerCase()) {
    return NextResponse.json({ detail: `不能更改文件扩展名，原扩展名: ${oldExt}` }, { status: 400 })
  }
  finalName = finalName.replace(/[<>:"/\\|?*\x00-\x1f]/g, '_')
  let counter = 1
  let candidate = finalName
  while (fs.existsSync(path.join(PATHS.staticDir, candidate)) && candidate !== path.basename(oldName)) {
    const ext = path.extname(finalName)
    candidate = `${path.basename(finalName, ext)}-${counter}${ext}`
    counter += 1
  }
  const adjusted = candidate !== newName && !newName.includes('.') ? ` (已自动调整为 ${candidate})` : ''
  const newPath = path.join(PATHS.staticDir, candidate)

  try {
    await fs.promises.rename(oldPath, newPath)
  } catch (e) {
    return NextResponse.json({ detail: `文件重命名失败: ${e instanceof Error ? e.message : String(e)}` }, { status: 500 })
  }

  // DB 联动（失败仅告警，不阻断）
  const db = getDb()
  try {
    db.prepare(`UPDATE transcripts SET audio_path = ? WHERE audio_path = ?`).run(newPath, oldPath)
    const jobs = db.prepare(`SELECT id, result_json FROM jobs WHERE result_json LIKE ?`).all(`%${path.basename(oldName)}%`) as
      | { id: number; result_json: string | null }[]
    for (const job of jobs) {
      if (!job.result_json) continue
      const patch = (obj: Record<string, unknown>): Record<string, unknown> => {
        const out: Record<string, unknown> = {}
        for (const [k, v] of Object.entries(obj)) {
          if (typeof v === 'string' && v.includes(path.basename(oldName))) {
            out[k] = v.replace(path.basename(oldName), candidate)
          } else if (v && typeof v === 'object') {
            out[k] = patch(v as Record<string, unknown>)
          } else {
            out[k] = v
          }
        }
        return out
      }
      db.prepare(`UPDATE jobs SET result_json = ? WHERE id = ?`).run(
        JSON.stringify(patch(JSON.parse(job.result_json) as Record<string, unknown>)),
        job.id,
      )
    }
  } catch {
    /* 联动失败不阻断 */
  }

  return NextResponse.json({
    success: true,
    message: `文件重命名成功${adjusted}`,
    data: { old_filename: oldName, new_filename: candidate, static_url: staticUrl(candidate) },
  })
}
