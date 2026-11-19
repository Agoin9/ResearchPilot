import {
  ArrowRight,
  FlaskConical,
  History,
  Loader2,
  NotebookPen,
  Sparkles,
} from 'lucide-react'
import { useCallback, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import { useAsyncData } from '@/hooks/useAsyncData'
import {
  createAnalysisNote,
  fetchAnalyses,
  generateAnalysis,
  suggestionToExperiment,
  suggestionToTask,
} from '@/services/api'
import type { ExperimentAnalysis, Suggestion } from '@/types'

const SUGGESTION_LABELS: Record<Suggestion['type'], string> = {
  new_task: '新任务',
  new_experiment: '新实验',
  read_literature: '补文献',
  modify_design: '改设计',
}

const SUGGESTION_ACTIONS: Array<{ type: Suggestion['type']; label: string }> = [
  { type: 'new_task', label: '转为任务' },
  { type: 'new_experiment', label: '转为实验草稿' },
]

/** 实验详情内的 AI 分析面板：生成分析 / 手工笔记 / 建议转任务（决策闭环） */
export function AnalysisPanel({
  experimentId,
  runCount,
  onConverted,
}: {
  experimentId: number
  runCount: number
  onConverted: () => void
}) {
  const loadAnalyses = useCallback(() => fetchAnalyses(experimentId), [experimentId])
  const { data, loading, reload } = useAsyncData(loadAnalyses)
  const [generating, setGenerating] = useState(false)
  const [noteOpen, setNoteOpen] = useState(false)
  const [noteContent, setNoteContent] = useState('')
  const [savingNote, setSavingNote] = useState(false)
  const [converting, setConverting] = useState<{ analysisId: number; index: number } | null>(null)

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      await generateAnalysis(experimentId)
      toast.add({ title: 'AI 分析已生成', description: '基于真实运行记录，结论请结合自己的判断', type: 'success' })
      void reload()
    } catch {
      // 错误提示（无运行记录 / 无 Key）已由 api 层统一 toast 展示
    } finally {
      setGenerating(false)
    }
  }

  const handleSaveNote = async () => {
    if (!noteContent.trim()) {
      toast.add({ title: '请输入分析内容', type: 'info' })
      return
    }
    setSavingNote(true)
    try {
      await createAnalysisNote(experimentId, noteContent.trim())
      toast.add({ title: '手工分析笔记已保存', type: 'success' })
      setNoteContent('')
      setNoteOpen(false)
      void reload()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setSavingNote(false)
    }
  }

  const handleConvert = async (analysis: ExperimentAnalysis, index: number, suggestion: Suggestion) => {
    setConverting({ analysisId: analysis.id, index })
    try {
      if (suggestion.type === 'new_task') {
        const task = await suggestionToTask(analysis.id, index)
        toast.add({
          title: '已转为科研任务',
          description: `「${task.title.slice(0, 30)}…」已加入看板（带来源标记）`,
          type: 'success',
        })
      } else {
        await suggestionToExperiment(analysis.id, index)
        toast.add({ title: '已转为实验草稿', description: '请在实验列表中补充方案后推进', type: 'success' })
      }
      onConverted()
      void reload()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setConverting(null)
    }
  }

  if (loading) {
    return <p className="py-8 text-center text-sm text-muted-foreground">加载分析中…</p>
  }

  const analyses = data ?? []

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <Button disabled={generating} onClick={() => void handleGenerate()}>
          {generating ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
          {generating ? '正在分析…' : '基于真实记录生成 AI 分析'}
        </Button>
        <Button variant="outline" onClick={() => setNoteOpen((v) => !v)}>
          <NotebookPen className="size-4" />
          手工分析笔记
        </Button>
        <p className="text-xs text-muted-foreground">
          分析只基于已录入的 {runCount} 条真实运行记录，不编造任何结果
        </p>
      </div>

      {noteOpen && (
        <Card>
          <CardContent className="flex flex-col gap-3 pt-4">
            <Textarea
              rows={5}
              placeholder="写下你自己的分析：结果说明了什么、与假设是否一致、下一步打算……"
              value={noteContent}
              onChange={(e) => setNoteContent(e.target.value)}
            />
            <div className="flex justify-end gap-2">
              <Button variant="outline" size="sm" disabled={savingNote} onClick={() => setNoteOpen(false)}>
                取消
              </Button>
              <Button size="sm" disabled={savingNote} onClick={() => void handleSaveNote()}>
                {savingNote ? '保存中…' : '保存笔记'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {analyses.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border py-8 text-center text-sm text-muted-foreground">
          还没有分析记录。录入运行结果后点「生成 AI 分析」，或直接写手工笔记。
        </div>
      ) : (
        analyses.map((analysis) => (
          <Card key={analysis.id} className="border-primary/30">
            <CardHeader className="border-b border-border">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <CardTitle className="text-sm font-medium">
                    <History className="mr-1.5 inline size-4" />
                    {analysis.createdAt.slice(0, 16).replace('T', ' ')} 的分析
                  </CardTitle>
                  <CardDescription>
                    依据运行记录：{analysis.runIds.map((id) => `#${id}`).join('、')}
                  </CardDescription>
                </div>
                <Badge variant={analysis.source === 'manual' ? 'secondary' : 'default'}>
                  {analysis.source === 'manual' ? '手工笔记' : 'AI 生成'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="flex flex-col gap-4 pt-4">
              <div className="text-sm leading-relaxed [&_h2]:mt-3 [&_h2]:mb-1.5 [&_h2]:text-base [&_h2]:font-semibold [&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-5">
                <ReactMarkdown>{analysis.content}</ReactMarkdown>
              </div>

              {analysis.suggestions.length > 0 && (
                <div className="flex flex-col gap-2">
                  <p className="text-xs font-medium text-muted-foreground">下一步建议</p>
                  {analysis.suggestions.map((suggestion, index) => (
                    <div
                      key={index}
                      className="flex flex-wrap items-start justify-between gap-2 rounded-lg border border-border bg-background/60 p-3"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5">
                          <Badge variant="outline" className="border-primary/40 text-primary">
                            {SUGGESTION_LABELS[suggestion.type]}
                          </Badge>
                          {suggestion.converted && <Badge variant="secondary">已转换</Badge>}
                        </div>
                        <p className="mt-1.5 text-sm">{suggestion.content}</p>
                        {suggestion.reason && (
                          <p className="mt-1 text-xs text-muted-foreground">理由：{suggestion.reason}</p>
                        )}
                      </div>
                      {!suggestion.converted && SUGGESTION_ACTIONS.some((a) => a.type === suggestion.type) && (
                        <Button
                          size="sm"
                          disabled={converting?.analysisId === analysis.id && converting?.index === index}
                          onClick={() => void handleConvert(analysis, index, suggestion)}
                        >
                          {converting?.analysisId === analysis.id && converting?.index === index ? (
                            <Loader2 className="size-3.5 animate-spin" />
                          ) : suggestion.type === 'new_task' ? (
                            <ArrowRight className="size-3.5" />
                          ) : (
                            <FlaskConical className="size-3.5" />
                          )}
                          {SUGGESTION_ACTIONS.find((a) => a.type === suggestion.type)?.label}
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        ))
      )}
    </div>
  )
}
