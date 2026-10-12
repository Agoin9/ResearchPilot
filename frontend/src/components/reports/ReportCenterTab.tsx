import {
  ClipboardList,
  Copy,
  Download,
  FileText,
  Loader2,
  Pencil,
  Save,
  Sparkles,
  X,
} from 'lucide-react'
import { useCallback, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { NativeSelect } from '@/components/ui/native-select'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import { useAsyncData } from '@/hooks/useAsyncData'
import {
  fetchMeetingReports,
  generateMeetingReport,
  reportExportUrl,
  updateReportContent,
} from '@/services/api'
import type { ReportInfo, ReportType } from '@/types'

const REPORT_TYPE_ITEMS = [
  { value: 'meeting', label: '组会周报' },
  { value: 'supervisor', label: '导师汇报' },
]

const toIso = (d: Date) => d.toISOString().slice(0, 10)

function defaultRange(): { start: string; end: string } {
  const end = new Date()
  const start = new Date()
  start.setDate(end.getDate() - 6)
  return { start: toIso(start), end: toIso(end) }
}

/** 汇报中心 Tab：生成组会周报/导师汇报，支持编辑保存、复制、导出 Markdown */
export function ReportCenterTab({ projectId }: { projectId: number }) {
  const loadReports = useCallback(() => fetchMeetingReports(projectId), [projectId])
  const { data: reports, loading, reload } = useAsyncData(loadReports)
  const [range, setRange] = useState(defaultRange())
  const [reportType, setReportType] = useState<ReportType>('meeting')
  const [generating, setGenerating] = useState(false)
  const [selected, setSelected] = useState<ReportInfo | null>(null)
  const [editing, setEditing] = useState(false)
  const [editContent, setEditContent] = useState('')
  const [saving, setSaving] = useState(false)

  const handleGenerate = async () => {
    if (!range.start || !range.end) {
      toast.add({ title: '请选择时间范围', type: 'info' })
      return
    }
    if (range.end < range.start) {
      toast.add({ title: '结束日期不能早于开始日期', type: 'info' })
      return
    }
    setGenerating(true)
    try {
      const report = await generateMeetingReport(projectId, {
        reportType,
        weekStart: range.start,
        weekEnd: range.end,
      })
      setSelected(report)
      setEditing(false)
      if (report.source === 'demo') {
        toast.add({ title: '演示模式', description: '未配置 DeepSeek Key，返回模板汇报', type: 'info' })
      } else {
        toast.add({ title: '汇报生成成功', type: 'success' })
      }
      void reload()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setGenerating(false)
    }
  }

  const handleSave = async () => {
    if (!selected || !editContent.trim()) {
      toast.add({ title: '汇报内容不能为空', type: 'info' })
      return
    }
    setSaving(true)
    try {
      const updated = await updateReportContent(selected.id, editContent.trim())
      setSelected(updated)
      setEditing(false)
      toast.add({ title: '已保存', type: 'success' })
      void reload()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setSaving(false)
    }
  }

  const handleCopy = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content)
      toast.add({ title: '已复制 Markdown 到剪贴板', type: 'success' })
    } catch {
      toast.add({ title: '复制失败，请手动选择文本复制', type: 'warning' })
    }
  }

  if (loading) {
    return <p className="py-10 text-center text-sm text-muted-foreground">加载汇报中…</p>
  }

  return (
    <div className="flex flex-col gap-4">
      {/* 生成表单 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">生成汇报</CardTitle>
          <CardDescription>
            从数据库读取任务、进度、风险与重规划历史，交给 DeepSeek 撰写
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap items-end gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="weekStart">开始日期</Label>
            <Input
              id="weekStart"
              type="date"
              value={range.start}
              onChange={(e) => setRange((prev) => ({ ...prev, start: e.target.value }))}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="weekEnd">结束日期</Label>
            <Input
              id="weekEnd"
              type="date"
              value={range.end}
              onChange={(e) => setRange((prev) => ({ ...prev, end: e.target.value }))}
            />
          </div>
          <div className="flex w-40 flex-col gap-2">
            <Label>汇报类型</Label>
            <NativeSelect
              value={reportType}
              onChange={(value) => setReportType((value || 'meeting') as ReportType)}
              items={REPORT_TYPE_ITEMS}
            />
          </div>
          <Button disabled={generating} onClick={() => void handleGenerate()}>
            {generating ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                正在生成汇报…
              </>
            ) : (
              <>
                <Sparkles className="size-4" />
                生成汇报
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-4">
        {/* 历史列表 */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-sm">历史汇报</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {!reports || reports.length === 0 ? (
              <p className="py-6 text-center text-xs text-muted-foreground">还没有生成过汇报</p>
            ) : (
              reports.map((report) => (
                <button
                  key={report.id}
                  type="button"
                  onClick={() => {
                    setSelected(report)
                    setEditing(false)
                  }}
                  className={`rounded-lg border p-2.5 text-left transition-colors ${
                    selected?.id === report.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border bg-background hover:border-primary/40'
                  }`}
                >
                  <p className="truncate text-xs font-medium">{report.title}</p>
                  <p className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Badge variant="outline" className="h-4 px-1 text-[10px]">
                      {report.source === 'demo' ? '演示' : 'AI'}
                    </Badge>
                    {report.createdAt.slice(0, 10)}
                  </p>
                </button>
              ))
            )}
          </CardContent>
        </Card>

        {/* 当前汇报 */}
        <Card className="lg:col-span-3">
          {!selected ? (
            <CardContent className="flex flex-col items-center gap-2 py-12 text-center">
              <FileText className="size-8 text-muted-foreground" />
              <p className="text-sm font-medium">选择时间范围和汇报类型后点「生成汇报」</p>
              <p className="text-xs text-muted-foreground">
                内容包含：本周完成、未完成及原因、当前风险、下周计划、需要导师支持
              </p>
            </CardContent>
          ) : (
            <>
              <CardHeader className="border-b border-border">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <CardTitle className="text-base">{selected.title}</CardTitle>
                    <CardDescription>
                      {selected.source === 'demo' ? '演示模式（模板生成）' : 'DeepSeek 生成'} ·
                      更新于 {selected.updatedAt.slice(0, 16).replace('T', ' ')}
                    </CardDescription>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {selected.source === 'demo' && <Badge variant="secondary">演示模式</Badge>}
                    {editing ? (
                      <>
                        <Button size="sm" variant="outline" disabled={saving} onClick={() => setEditing(false)}>
                          <X className="size-3.5" />
                          取消
                        </Button>
                        <Button size="sm" disabled={saving} onClick={() => void handleSave()}>
                          {saving ? <Loader2 className="size-3.5 animate-spin" /> : <Save className="size-3.5" />}
                          保存
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button size="sm" variant="outline" onClick={() => {
                          setEditContent(selected.content)
                          setEditing(true)
                        }}>
                          <Pencil className="size-3.5" />
                          编辑
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => void handleCopy(selected.content)}>
                          <Copy className="size-3.5" />
                          复制 Markdown
                        </Button>
                        <a href={reportExportUrl(selected.id)} download>
                          <Button size="sm" variant="outline">
                            <Download className="size-3.5" />
                            导出 .md
                          </Button>
                        </a>
                      </>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-4">
                {editing ? (
                  <Textarea
                    rows={22}
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="font-mono text-xs"
                  />
                ) : (
                  <div className="text-sm leading-relaxed [&_h1]:mt-4 [&_h1]:mb-2 [&_h1]:text-lg [&_h1]:font-semibold [&_h2]:mt-4 [&_h2]:mb-2 [&_h2]:text-base [&_h2]:font-semibold [&_h3]:mt-3 [&_h3]:mb-1.5 [&_h3]:text-sm [&_h3]:font-semibold [&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:my-2 [&_ol]:list-decimal [&_ol]:pl-5 [&_li]:my-0.5 [&_p]:my-1.5 [&_strong]:font-semibold [&_blockquote]:border-l-2 [&_blockquote]:border-border [&_blockquote]:pl-3 [&_blockquote]:text-muted-foreground">
                    <ReactMarkdown>{selected.content}</ReactMarkdown>
                  </div>
                )}
              </CardContent>
            </>
          )}
        </Card>
      </div>

      <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <ClipboardList className="size-3.5" />
        提示：汇报数据窗口内的任务完成/进度记录会自动纳入；无 API Key 时自动进入演示模式。
      </p>
    </div>
  )
}
