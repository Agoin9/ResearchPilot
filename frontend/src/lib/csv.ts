/**
 * 轻量 CSV 解析：支持引号包裹的字段（含逗号/换行）、双引号转义、CRLF/LF、BOM。
 * 只用于本地实验结果导入（文件通常很小），不引入额外依赖。
 */

export interface CsvParseResult {
  /** 表头（第一行各列名，去空格） */
  headers: string[]
  /** 数据行（每行一个字符串数组，长度与 headers 对齐，缺失补空串） */
  rows: string[][]
}

/** 单条 CSV 字段解析（处理引号与转义），返回 { value, nextIndex } */
function parseField(text: string, start: number): { value: string; next: number } {
  if (text[start] === '"') {
    let value = ''
    let i = start + 1
    while (i < text.length) {
      const ch = text[i]
      if (ch === '"') {
        // 双引号转义（""）或字段结束
        if (text[i + 1] === '"') {
          value += '"'
          i += 2
          continue
        }
        return { value, next: i + 1 }
      }
      value += ch
      i += 1
    }
    // 引号未闭合：按到结尾处理
    return { value, next: text.length }
  }
  const end = text.indexOf(',', start)
  if (end === -1) return { value: text.slice(start), next: text.length }
  return { value: text.slice(start), next: end }
}

export function parseCsv(text: string): CsvParseResult {
  // 去掉 UTF-8 BOM，统一换行
  const clean = text.charCodeAt(0) === 0xfeff ? text.slice(1) : text
  const normalized = clean.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
  const lines = normalized.split('\n')

  const records: string[][] = []
  let buffer = ''
  for (const line of lines) {
    buffer += (buffer ? '\n' : '') + line
    // 统计引号个数（跳过 "" 转义对），奇数 → 字段内换行，并入下一行
    let quotes = 0
    for (let i = 0; i < buffer.length; i++) {
      if (buffer[i] === '"') {
        if (buffer[i + 1] === '"') {
          i += 1
          continue
        }
        quotes += 1
      }
    }
    if (quotes % 2 === 1) continue
    if (buffer.trim() === '') {
      buffer = ''
      continue
    }
    // 解析这一行记录
    const fields: string[] = []
    let i = 0
    while (i < buffer.length) {
      if (buffer[i] === ',') {
        fields.push('')
        i += 1
        continue
      }
      const { value, next } = parseField(buffer, i)
      fields.push(value)
      i = next
      if (i < buffer.length && buffer[i] === ',') i += 1
    }
    if (buffer.endsWith(',')) fields.push('')
    records.push(fields)
    buffer = ''
  }

  if (records.length === 0) return { headers: [], rows: [] }
  const headers = records[0].map((h) => h.trim())
  const rows = records.slice(1).map((row) => {
    const padded = [...row]
    while (padded.length < headers.length) padded.push('')
    return padded.slice(0, headers.length)
  })
  return { headers, rows }
}

/** 判断单元格值是否可解析为数字（含负号/小数点/科学计数法）；空串返回空串 */
export function toNumberIfPossible(value: string): number | string {
  const trimmed = value.trim()
  if (trimmed === '') return trimmed
  if (/^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$/.test(trimmed)) {
    const num = Number(trimmed)
    if (!Number.isNaN(num)) return num
  }
  return trimmed
}
