import {
  ArrowLeft,
  Columns3,
  FileSpreadsheet,
  ImagePlus,
  Loader2,
  Pencil,
  Plus,
  Trash2,
} from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import { useAsyncData } from '@/hooks/useAsyncData'
import {
  attachmentUrl,
  createRun,
  deleteRun,
  fetchExperimentDetail,
  updateRun,
  uploadRunAttachment,
} from '@/services/api'
import { parseCsv, toNumberIfPossible, type CsvParseResult } from '@/lib/csv'
import type { Experiment, ExperimentRun, MetricDef } from '@/types'
import { AnalysisPanel } from './AnalysisPanel'

/** CSV 导入的行数上限（防止一次误导入过多记录） */
const CSV_MAX_ROWS = 100

const STATUS_LABELS: Record<Experiment['status'], string> = {
  draft: '设计中',
  running: '进行中',
  done: '已完成',
  failed: '失败',
  paused: '已暂停',
}

const STATUS_BADGE_CLASSES: Record<Experiment['status'], string> = {
  draft: 'border-border bg-muted text-muted-foreground',
  running: 'border-sky-300 bg-sky-50 text-sky-700 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-400',
  done: 'border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-400',
  failed: 'border-red-300 bg-red-50 text-red-600 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-400',
  paused: 'border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-400',
}

/** 判断两个值谁更优（按指标方向） */
function isBetter(a: unknown, b: unknown, higherIsBetter: boolean): boolean {
  const numA = typeof a === 'number' ? a : Number(a)
  const numB = typeof b === 'number' ? b : Number(b)
  if (Number.isNaN(numA) || Number.isNaN(numB)) return false
  return higherIsBetter ? numA > numB : numA < numB
}

function fmtValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—'
  return String(value)
}

interface RunFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  experimentId: number
  metrics: MetricDef[]
  run: ExperimentRun | null
  onSaved: () => void
}

/** 新增 / 编辑运行记录抽屉：结构化指标输入 + 复现信息 + 自由 JSON 粘贴 + 附件上传 */
function RunFormSheet({ open, onOpenChange, experimentId, metrics, run, onSaved }: RunFormSheetProps) {
  const [metricValues, setMetricValues] = useState<Record<string, string>>({})
  const [configJson, setConfigJson] = useState('')
  const [resultsJson, setResultsJson] = useState('')
  const [randomSeed, setRandomSeed] = useState('')
  const [gitCommit, setGitCommit] = useState('')
  const [environmentJson, setEnvironmentJson] = useState('')
  const [logPath, setLogPath] = useState('')
  const [resultFilesText, setResultFilesText] = useState('')
  const [notes, setNotes] = useState('')
  const [startedAt, setStartedAt] = useState('')
  const [finishedAt, setFinishedAt] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [attachmentFiles, setAttachmentFiles] = useState<File[]>([])
  const [uploadingAttachment, setUploadingAttachment] = useState(false)

  useEffect(() => {
    if (!open) return
    setMetricValues({})
    setConfigJson(run ? JSON.stringify(run.config ?? {}, null, 2) : '{}')
    setResultsJson(run ? JSON.stringify(run.results ?? {}, null, 2) : '{}')
    setRandomSeed(run?.randomSeed != null ? String(run.randomSeed) : '')
    setGitCommit(run?.gitCommit ?? '')
    setEnvironmentJson(run ? JSON.stringify(run.environment ?? {}, null, 2) : '{}')
    setLogPath(run?.logPath ?? '')
    setResultFilesText((run?.resultFiles ?? []).join('\n'))
    setNotes(run?.notes ?? '')
    setStartedAt(run?.startedAt ?? '')
    setFinishedAt(run?.finishedAt ?? '')
    setAttachmentFiles([])
    setError('')
  }, [open, run])

  const parseJsonField = (text: string, field: string): Record<string, unknown> | null => {
    if (!text.trim()) return {}
    try {
      const value = JSON.parse(text)
      if (value === null || typeof value !== 'object' || Array.isArray(value)) {
        setError(`${field}必须是 JSON 对象（如 {"Accuracy": 87.3}）`)
        return null
      }
      return value
    } catch {
      setError(`${field}不是合法 JSON，请检查格式`)
      return null
    }
  }

  const handleSubmit = async () => {
    setError('')
    const config = parseJsonField(configJson, '运行参数')
    if (config === null) return
    const results = parseJsonField(resultsJson, '实际指标')
    if (results === null) return
    const environment = parseJsonField(environmentJson, '环境信息')
    if (environment === null) return
    let seed: number | null = null
    if (randomSeed.trim() !== '') {
      seed = Number(randomSeed)
      if (Number.isNaN(seed) || !Number.isInteger(seed) || seed < 0) {
        setError('随机种子必须是非负整数')
        return
      }
    }
    // 结构化指标输入合并进结果
    for (const [name, value] of Object.entries(metricValues)) {
      if (value.trim() === '') continue
      const num = Number(value)
      results[name] = Number.isNaN(num) ? value : num
    }
    const resultFiles = resultFilesText
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
    setSubmitting(true)
    try {
      const payload = {
        config,
        results,
        randomSeed: seed,
        gitCommit: gitCommit.trim() || null,
        environment,
        logPath: logPath.trim() || null,
        resultFiles,
        notes: notes.trim() || null,
        startedAt: startedAt || null,
        finishedAt: finishedAt || null,
      }
      if (run) {
        await updateRun(run.id, payload)
        toast.add({ title: '运行记录已更新', type: 'success' })
      } else {
        await createRun(experimentId, payload)
        toast.add({ title: '运行记录已添加', type: 'success' })
      }
      onOpenChange(false)
      onSaved()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setSubmitting(false)
    }
  }

  const handleUploadAttachments = async () => {
    if (!run || attachmentFiles.length === 0) return
    setUploadingAttachment(true)
    try {
      for (const file of attachmentFiles) {
        await uploadRunAttachment(run.id, file)
      }
      toast.add({ title: '附件已上传', type: 'success' })
      setAttachmentFiles([])
      onSaved()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setUploadingAttachment(false)
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>{run ? `编辑运行记录 #${run.runNo}` : '新增运行记录'}</SheetTitle>
          <SheetDescription>
            录入本次运行的真实条件与结果（执行在实验室/服务器上，这里只做记录）。
          </SheetDescription>
        </SheetHeader>
        <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-4">
          {metrics.length > 0 && (
            <div className="rounded-xl border border-border p-3">
              <p className="mb-2 text-xs font-medium text-muted-foreground">结构化指标（自动并入结果）</p>
              <div className="grid grid-cols-2 gap-3">
                {metrics.map((metric) => (
                  <div key={metric.name} className="flex flex-col gap-1">
                    <Label className="text-xs">
                      {metric.name}{metric.unit && `（${metric.unit}）`}
                    </Label>
                    <Input
                      value={metricValues[metric.name] ?? ''}
                      onChange={(e) =>
                        setMetricValues((prev) => ({ ...prev, [metric.name]: e.target.value }))
                      }
                      placeholder="数值"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
          <div className="flex flex-col gap-2">
            <Label htmlFor="run-config">运行参数（JSON 对象）</Label>
            <Textarea
              id="run-config"
              rows={4}
              className="font-mono text-xs"
              placeholder='{"lr": 0.001, "epochs": 50}'
              value={configJson}
              onChange={(e) => setConfigJson(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="run-results">实际指标（JSON 对象）</Label>
            <Textarea
              id="run-results"
              rows={4}
              className="font-mono text-xs"
              placeholder='{"Accuracy": 87.3}'
              value={resultsJson}
              onChange={(e) => setResultsJson(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              只录入真实测得的数值；系统不会替你生成任何结果。
            </p>
          </div>
          <div className="rounded-xl border border-border p-3">
            <p className="mb-2 text-xs font-medium text-muted-foreground">复现信息（推荐填写，方便日后回溯）</p>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-2">
                <Label htmlFor="run-seed">随机种子</Label>
                <Input
                  id="run-seed"
                  placeholder="如：42"
                  value={randomSeed}
                  onChange={(e) => setRandomSeed(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="run-commit">代码 Git Commit</Label>
                <Input
                  id="run-commit"
                  placeholder="如：a1b2c3d"
                  value={gitCommit}
                  onChange={(e) => setGitCommit(e.target.value)}
                />
              </div>
            </div>
            <div className="mt-3 flex flex-col gap-2">
              <Label htmlFor="run-env">环境信息（JSON 对象，可选）</Label>
              <Textarea
                id="run-env"
                rows={3}
                className="font-mono text-xs"
                placeholder='{"python": "3.12.3", "torch": "2.4.0"}'
                value={environmentJson}
                onChange={(e) => setEnvironmentJson(e.target.value)}
              />
            </div>
            <div className="mt-3 grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-2">
                <Label htmlFor="run-log">日志路径</Label>
                <Input
                  id="run-log"
                  placeholder="如：D:/logs/exp1-run1.log"
                  value={logPath}
                  onChange={(e) => setLogPath(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="run-files">结果文件路径（每行一个）</Label>
                <Textarea
                  id="run-files"
                  rows={2}
                  className="font-mono text-xs"
                  placeholder={'D:/results/exp1-run1.csv\nD:/results/exp1-run1.png'}
                  value={resultFilesText}
                  onChange={(e) => setResultFilesText(e.target.value)}
                />
              </div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-2">
              <Label>开始日期</Label>
              <Input type="date" value={startedAt} onChange={(e) => setStartedAt(e.target.value)} />
            </div>
            <div className="flex flex-col gap-2">
              <Label>结束日期</Label>
              <Input type="date" value={finishedAt} onChange={(e) => setFinishedAt(e.target.value)} />
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="run-notes">备注（现象/问题/观察）</Label>
            <Textarea
              id="run-notes"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>
          {run && (
            <div className="flex flex-col gap-2 rounded-xl border border-border p-3">
              <Label className="text-xs">追加附件图片（PNG/JPG，每条记录最多 3 张）</Label>
              <Input
                type="file"
                accept="image/png,image/jpeg"
                multiple
                onChange={(e) => setAttachmentFiles(Array.from(e.target.files ?? []))}
              />
              {attachmentFiles.length > 0 && (
                <Button
                  size="sm"
                  variant="outline"
                  disabled={uploadingAttachment}
                  onClick={() => void handleUploadAttachments()}
                >
                  {uploadingAttachment ? <Loader2 className="size-3.5 animate-spin" /> : <ImagePlus className="size-3.5" />}
                  上传 {attachmentFiles.length} 个附件
                </Button>
              )}
            </div>
          )}
          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>
        <SheetFooter>
          <Button variant="outline" disabled={submitting} onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button disabled={submitting} onClick={() => void handleSubmit()}>
            {submitting ? '保存中…' : '保存'}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}

interface CsvImportSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  experimentId: number
  onImported: () => void
}

/**
 * CSV 结果导入：表头为列名，每行 = 一次运行记录；
 * 名为 note 的列写入备注，其余列按名称写入实际指标（数字自动解析），
 * 空单元格跳过。导入前必须预览确认，数据逐条走真实 createRun 接口。
 */
function CsvImportSheet({ open, onOpenChange, experimentId, onImported }: CsvImportSheetProps) {
  const [fileName, setFileName] = useState('')
  const [parsed, setParsed] = useState<CsvParseResult | null>(null)
  const [error, setError] = useState('')
  const [importing, setImporting] = useState(false)
  const [progress, setProgress] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!open) return
    setFileName('')
    setParsed(null)
    setError('')
    setProgress('')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [open])

  const handleFile = (file: File) => {
    setError('')
    setParsed(null)
    setFileName(file.name)
    const reader = new FileReader()
    reader.onload = () => {
      const text = String(reader.result ?? '')
      const result = parseCsv(text)
      if (result.headers.length === 0 || result.rows.length === 0) {
        setError('CSV 内容为空或只有表头，无法导入')
        return
      }
      if (result.headers.every((h) => h === '')) {
        setError('表头为空，请在第一行写明列名（指标名）')
        return
      }
      if (result.rows.length > CSV_MAX_ROWS) {
        setError(`一次最多导入 ${CSV_MAX_ROWS} 条运行记录（当前 ${result.rows.length} 条），请拆分文件`)
        return
      }
      setParsed(result)
    }
    reader.onerror = () => setError('读取文件失败，请确认是 UTF-8 编码的 CSV')
    reader.readAsText(file, 'utf-8')
  }

  const handleImport = async () => {
    if (!parsed) return
    setImporting(true)
    setError('')
    try {
      let success = 0
      for (let index = 0; index < parsed.rows.length; index++) {
        const row = parsed.rows[index]
        const results: Record<string, unknown> = {}
        let note: string | null = null
        parsed.headers.forEach((header, col) => {
          const raw = (row[col] ?? '').trim()
          if (raw === '' || header === '') return
          if (header.toLowerCase() === 'note') {
            note = raw
            return
          }
          results[header] = toNumberIfPossible(raw)
        })
        setProgress(`正在导入第 ${index + 1} / ${parsed.rows.length} 条…`)
        await createRun(experimentId, { results, notes: note })
        success += 1
      }
      toast.add({
        title: `已导入 ${success} 条运行记录`,
        description: '已按真实数值写入，可在下方运行记录与结果对比中查看',
        type: 'success',
      })
      onOpenChange(false)
      onImported()
    } catch (err) {
      // createRun 失败：停止导入并明确提示，避免部分导入造成困惑
      setError(
        err instanceof Error && err.message
          ? `导入中断：${err.message}（已成功导入部分记录，请检查后重试剩余数据）`
          : '导入中断，请稍后重试'
      )
    } finally {
      setImporting(false)
      setProgress('')
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-xl">
        <SheetHeader>
          <SheetTitle>CSV 导入实验结果</SheetTitle>
          <SheetDescription>
            表头为列名，每行 = 一次运行记录；名为 note 的列写入备注，其余列按名称写入实际指标。
          </SheetDescription>
        </SheetHeader>
        <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-4">
          <div className="flex flex-wrap items-center gap-3">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) handleFile(file)
              }}
            />
            <Button variant="outline" disabled={importing} onClick={() => fileInputRef.current?.click()}>
              <FileSpreadsheet className="size-4" />
              选择 CSV 文件
            </Button>
            {fileName && <span className="text-xs text-muted-foreground">{fileName}</span>}
          </div>

          {parsed && (
            <>
              <p className="rounded-lg bg-muted px-3 py-2 text-xs text-muted-foreground">
                解析成功：<span className="font-medium text-foreground">{parsed.rows.length}</span> 条记录，
                列：{parsed.headers.filter(Boolean).join('、') || '（空表头列将被忽略）'}
                {parsed.rows.length > 10 && '（预览前 10 条）'}
              </p>
              <div className="overflow-x-auto rounded-lg border border-border">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border bg-muted/50 text-left text-muted-foreground">
                      {parsed.headers.map((h, i) => (
                        <th key={i} className="px-2.5 py-1.5 font-medium">{h || `列${i + 1}`}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {parsed.rows.slice(0, 10).map((row, r) => (
                      <tr key={r} className="border-b border-border/50">
                        {parsed.headers.map((_, c) => (
                          <td key={c} className="px-2.5 py-1.5 tabular-nums">{row[c] ?? ''}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {error && <p className="text-sm text-red-500">{error}</p>}
          {importing && progress && (
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              {progress}
            </p>
          )}
        </div>
        <SheetFooter>
          <Button variant="outline" disabled={importing} onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button disabled={!parsed || importing} onClick={() => void handleImport()}>
            {importing ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
            {importing ? '导入中…' : `确认导入 ${parsed?.rows.length ?? 0} 条运行记录`}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}

/** 实验详情：信息 + 运行记录列表 + 结果对比 + AI 分析面板 */
export function ExperimentDetail({
  experimentId,
  onBack,
  onChanged,
}: {
  experimentId: number
  onBack: () => void
  onChanged: () => void
}) {
  const loadDetail = useCallback(() => fetchExperimentDetail(experimentId), [experimentId])
  const { data, loading, reload } = useAsyncData(loadDetail)
  const [runFormOpen, setRunFormOpen] = useState(false)
  const [csvOpen, setCsvOpen] = useState(false)
  const [editingRun, setEditingRun] = useState<ExperimentRun | null>(null)
  const [confirmingDelete, setConfirmingDelete] = useState<number | null>(null)
  const [showCompare, setShowCompare] = useState(false)

  const handleDeleteRun = async (id: number) => {
    if (confirmingDelete !== id) {
      setConfirmingDelete(id)
      return
    }
    try {
      await deleteRun(id)
      setConfirmingDelete(null)
      toast.add({ title: '运行记录已删除', type: 'success' })
      void reload()
      onChanged()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    }
  }

  if (loading) {
    return <p className="py-10 text-center text-sm text-muted-foreground">加载实验详情中…</p>
  }

  const experiment = data?.experiment
  if (!experiment) {
    return <p className="py-10 text-center text-sm text-muted-foreground">实验不存在</p>
  }
  const runs = data?.runs ?? []

  // 对比表数据（本地从 runs 计算：按实验指标定义 + 结果键对齐）
  const compareNames = [
    ...experiment.metrics.map((m) => m.name),
    ...new Set(runs.flatMap((r) => Object.keys(r.results ?? {}))),
  ].filter((name, index, arr) => arr.indexOf(name) === index)
  const direction = new Map(experiment.metrics.map((m) => [m.name, m.higherIsBetter]))

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Button variant="outline" size="sm" onClick={onBack}>
          <ArrowLeft className="size-3.5" />
          返回实验列表
        </Button>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={runs.length < 2}
            onClick={() => setShowCompare((v) => !v)}
          >
            <Columns3 className="size-3.5" />
            {showCompare ? '收起对比' : '结果对比'}
          </Button>
          <Button variant="outline" size="sm" onClick={() => setCsvOpen(true)}>
            <FileSpreadsheet className="size-3.5" />
            CSV 导入
          </Button>
          <Button size="sm" onClick={() => { setEditingRun(null); setRunFormOpen(true) }}>
            <Plus className="size-3.5" />
            新增运行记录
          </Button>
        </div>
      </div>

      {/* 实验信息 */}
      <Card>
        <CardHeader className="border-b border-border">
          <div className="flex flex-wrap items-center gap-2">
            <CardTitle className="text-base">{experiment.title}</CardTitle>
            <Badge variant="outline" className={STATUS_BADGE_CLASSES[experiment.status]}>
              {STATUS_LABELS[experiment.status]}
            </Badge>
            {experiment.stalled && <Badge variant="destructive">实验停滞，建议推进或更新状态</Badge>}
          </div>
          <CardDescription className="mt-1">{experiment.objective}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {experiment.hypothesis && (
            <p className="text-sm">
              <span className="font-medium text-muted-foreground">待验证假设：</span>
              {experiment.hypothesis}
            </p>
          )}
          <div className="grid grid-cols-1 gap-x-5 gap-y-1.5 text-sm sm:grid-cols-2">
            {experiment.variables && (
              <p>
                <span className="font-medium text-muted-foreground">实验变量：</span>
                {experiment.variables}
              </p>
            )}
            {experiment.controlConditions && (
              <p>
                <span className="font-medium text-muted-foreground">对照条件：</span>
                {experiment.controlConditions}
              </p>
            )}
            {experiment.dataset && (
              <p>
                <span className="font-medium text-muted-foreground">数据集：</span>
                {experiment.dataset}
              </p>
            )}
            {experiment.model && (
              <p>
                <span className="font-medium text-muted-foreground">模型：</span>
                {experiment.model}
              </p>
            )}
          </div>
          {Object.keys(experiment.config ?? {}).length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium text-muted-foreground">实验配置</p>
              <pre className="rounded-lg border border-border bg-muted/50 px-3 py-2 font-mono text-xs whitespace-pre-wrap">
                {JSON.stringify(experiment.config, null, 2)}
              </pre>
            </div>
          )}
          {experiment.design && (
            <div className="text-sm leading-relaxed text-muted-foreground">
              <p className="mb-1 font-medium text-foreground">实验方案</p>
              <pre className="font-sans whitespace-pre-wrap">{experiment.design}</pre>
            </div>
          )}
          {experiment.metrics.length > 0 && (
            <p className="text-xs text-muted-foreground">
              指标：{experiment.metrics.map((m) => `${m.name}${m.unit ? `（${m.unit}）` : ''}${m.higherIsBetter ? '' : '[低好]'}`).join('、')}
            </p>
          )}
        </CardContent>
      </Card>

      {/* 结果对比 */}
      {showCompare && (
        <Card>
          <CardHeader className="border-b border-border">
            <CardTitle className="text-base">运行结果对比</CardTitle>
            <CardDescription>同一指标横向对比，最优值以绿色标出</CardDescription>
          </CardHeader>
          <CardContent className="overflow-x-auto pt-4">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="py-2 pr-3 font-medium">运行</th>
                  {compareNames.map((name) => (
                    <th key={name} className="py-2 pr-3 font-medium">
                      {name}
                      {direction.has(name) && !direction.get(name) && (
                        <span className="ml-1 text-[10px]">(低好)</span>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => {
                  const values = compareNames.map((name) => run.results?.[name])
                  return (
                    <tr key={run.id} className="border-b border-border/60">
                      <td className="py-2 pr-3 text-xs">
                        运行 #{run.runNo}
                        {run.startedAt && (
                          <span className="ml-1 text-muted-foreground">({run.startedAt})</span>
                        )}
                      </td>
                      {compareNames.map((name, index) => {
                        const value = values[index]
                        const higher = direction.get(name) ?? true
                        const best = runs
                          .map((r) => r.results?.[name])
                          .filter((v) => v !== undefined && v !== null)
                          .reduce<unknown | null>(
                            (acc, v) => (acc === null || isBetter(v, acc, higher) ? v : acc),
                            null
                          )
                        const isBest = value !== undefined && value !== null && best !== null && value === best
                        return (
                          <td
                            key={name}
                            className={`py-2 pr-3 tabular-nums ${
                              isBest ? 'font-medium text-emerald-600 dark:text-emerald-400' : 'text-muted-foreground'
                            }`}
                          >
                            {fmtValue(value)}
                          </td>
                        )
                      })}
                    </tr>
                  )
                })}
              </tbody>
            </table>
            {runs.length < 2 && (
              <p className="mt-3 text-xs text-muted-foreground">至少 2 次运行才能形成对比。</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* 运行记录列表 */}
      <div className="flex flex-col gap-3">
        <p className="text-sm font-medium">运行记录（{runs.length} 次）</p>
        {runs.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border py-8 text-center text-sm text-muted-foreground">
            还没有运行记录。完成一次实验后，点「新增运行记录」录入真实结果。
          </div>
        ) : (
          runs.map((run) => (
            <Card key={run.id}>
              <CardHeader className="border-b border-border">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <CardTitle className="text-sm font-medium">
                    运行 #{run.runNo}
                    {run.startedAt && run.finishedAt && (
                      <span className="ml-2 text-xs font-normal text-muted-foreground">
                        {run.startedAt} ~ {run.finishedAt}
                      </span>
                    )}
                  </CardTitle>
                  <div className="flex shrink-0 gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-7 gap-1 px-2 text-xs"
                      onClick={() => { setEditingRun(run); setRunFormOpen(true) }}
                    >
                      <Pencil className="size-3.5" />
                      编辑
                    </Button>
                    <Button
                      size="sm"
                      variant={confirmingDelete === run.id ? 'destructive' : 'ghost'}
                      className="h-7 gap-1 px-2 text-xs"
                      onClick={() => void handleDeleteRun(run.id)}
                    >
                      <Trash2 className="size-3.5" />
                      {confirmingDelete === run.id ? '确认删除' : '删除'}
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                {(run.randomSeed != null || run.gitCommit || run.logPath) && (
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                    {run.randomSeed != null && <span>种子 {run.randomSeed}</span>}
                    {run.gitCommit && <span>Commit {run.gitCommit}</span>}
                    {run.logPath && <span className="break-all">日志 {run.logPath}</span>}
                  </div>
                )}
                {Object.keys(run.results ?? {}).length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(run.results ?? {}).map(([key, value]) => (
                      <span
                        key={key}
                        className="rounded-lg border border-border bg-muted/50 px-2.5 py-1 text-xs"
                      >
                        <span className="text-muted-foreground">{key}: </span>
                        <span className="font-medium tabular-nums">{fmtValue(value)}</span>
                      </span>
                    ))}
                  </div>
                )}
                {run.resultFiles.length > 0 && (
                  <p className="text-xs text-muted-foreground">
                    <span className="font-medium">结果文件：</span>
                    {run.resultFiles.join('；')}
                  </p>
                )}
                {run.notes && (
                  <p className="text-xs leading-relaxed text-muted-foreground">{run.notes}</p>
                )}
                {run.attachments.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {run.attachments.map((name) => (
                      <a key={name} href={attachmentUrl(name)} target="_blank" rel="noreferrer">
                        <img
                          src={attachmentUrl(name)}
                          alt="附件"
                          className="h-24 rounded-lg border border-border object-cover"
                        />
                      </a>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* AI 分析面板（决策闭环） */}
      <Card className="border-primary/20">
        <CardHeader className="border-b border-border">
          <CardTitle className="text-base">结果分析与下一步决策</CardTitle>
          <CardDescription>
            AI 分析只基于上面的真实运行记录；结论可一键转为看板任务或新实验草稿
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-4">
          <AnalysisPanel
            experimentId={experimentId}
            runCount={runs.length}
            onConverted={() => {
              void reload()
              onChanged()
            }}
          />
        </CardContent>
      </Card>

      <RunFormSheet
        open={runFormOpen}
        onOpenChange={setRunFormOpen}
        experimentId={experimentId}
        metrics={experiment.metrics}
        run={editingRun}
        onSaved={() => {
          void reload()
          onChanged()
        }}
      />

      <CsvImportSheet
        open={csvOpen}
        onOpenChange={setCsvOpen}
        experimentId={experimentId}
        onImported={() => {
          void reload()
          onChanged()
        }}
      />
    </div>
  )
}
