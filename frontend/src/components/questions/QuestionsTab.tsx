import { BookOpenCheck, FlaskConical, HelpCircle, Loader2, Pencil, Plus, Sparkles, Trash2 } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { NativeSelect } from '@/components/ui/native-select'
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import { useAsyncData } from '@/hooks/useAsyncData'
import {
  createQuestion,
  deleteQuestion,
  fetchQuestionAnalyses,
  fetchQuestions,
  generateQuestionAnalysis,
  updateQuestion,
} from '@/services/api'
import type { Question, QuestionStatus, ResearchAnalysis } from '@/types'

const STATUS_LABELS: Record<QuestionStatus, string> = {
  open: '待解决',
  answered: '已解答',
  suspended: '已挂起',
}

const STATUS_BADGE_CLASSES: Record<QuestionStatus, string> = {
  open: 'border-sky-300 bg-sky-50 text-sky-700 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-400',
  answered: 'border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-400',
  suspended: 'border-border bg-muted text-muted-foreground',
}

const STATUS_ITEMS: Array<{ value: QuestionStatus; label: string }> = [
  { value: 'open', label: '待解决' },
  { value: 'answered', label: '已解答' },
  { value: 'suspended', label: '挂起' },
]

interface QuestionFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  projectId: number
  question: Question | null
  onSaved: () => void
}

/** 新建 / 编辑研究问题抽屉 */
function QuestionFormSheet({ open, onOpenChange, projectId, question, onSaved }: QuestionFormSheetProps) {
  const [content, setContent] = useState('')
  const [answerSummary, setAnswerSummary] = useState('')
  const [status, setStatus] = useState<QuestionStatus>('open')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!open) return
    setContent(question?.content ?? '')
    setAnswerSummary(question?.answerSummary ?? '')
    setStatus(question?.status ?? 'open')
    setError('')
  }, [open, question])

  const handleSubmit = async () => {
    if (!content.trim()) {
      setError('请输入研究问题')
      return
    }
    setSubmitting(true)
    try {
      if (question) {
        await updateQuestion(question.id, {
          content: content.trim(),
          answerSummary: answerSummary.trim() || null,
          status,
        })
        toast.add({ title: '研究问题已更新', type: 'success' })
      } else {
        await createQuestion(projectId, { content: content.trim(), status })
        toast.add({ title: '研究问题已创建', type: 'success' })
      }
      onOpenChange(false)
      onSaved()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>{question ? '编辑研究问题' : '新建研究问题'}</SheetTitle>
          <SheetDescription>
            问题是科研闭环的起点：文献证据与实验都可以挂到问题下。
          </SheetDescription>
        </SheetHeader>
        <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="question-content">研究问题</Label>
            <Textarea
              id="question-content"
              rows={3}
              placeholder="如：方法A是否在数据集X上优于方法B？"
              value={content}
              onChange={(e) => setContent(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="question-answer">解答摘要（可选）</Label>
            <Textarea
              id="question-answer"
              rows={3}
              placeholder="初步结论、阶段性回答……"
              value={answerSummary}
              onChange={(e) => setAnswerSummary(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label>状态</Label>
            <NativeSelect
              value={status}
              onChange={(value) => setStatus((value || 'open') as QuestionStatus)}
              items={STATUS_ITEMS}
            />
          </div>
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

/** 单个问题的分析历史 + 生成入口 */
function QuestionAnalyses({ questionId }: { questionId: number }) {
  const navigate = useNavigate()
  const loadAnalyses = useCallback(() => fetchQuestionAnalyses(questionId), [questionId])
  const { data: analyses, loading } = useAsyncData(loadAnalyses)
  const [generating, setGenerating] = useState(false)

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      const analysis = await generateQuestionAnalysis(questionId)
      toast.add({
        title: analysis.source === 'demo' ? '分析已生成（演示模式）' : 'AI 研究分析已生成',
        description: '七段式输出：事实/证据/推测/假设判定/不确定性/建议',
        type: 'success',
      })
      navigate(`/analysis/${analysis.id}`)
    } catch {
      // 错误提示（无实验数据 400 / 无 Key 演示等）已由 api 层统一 toast 展示
    } finally {
      setGenerating(false)
    }
  }

  if (loading) {
    return <p className="text-xs text-muted-foreground">加载分析历史中…</p>
  }
  const list = analyses ?? []
  return (
    <div className="flex flex-col gap-2">
      <Button
        size="sm"
        variant="outline"
        disabled={generating}
        onClick={() => void handleGenerate()}
      >
        {generating ? <Loader2 className="size-3.5 animate-spin" /> : <Sparkles className="size-3.5" />}
        {generating ? '正在聚合真实数据并分析…' : '生成研究分析'}
      </Button>
      {list.length > 0 && (
        <div className="flex flex-col gap-1">
          {list.map((analysis: ResearchAnalysis) => (
            <button
              key={analysis.id}
              type="button"
              onClick={() => navigate(`/analysis/${analysis.id}`)}
              className="flex items-center justify-between gap-2 rounded-lg border border-border px-3 py-1.5 text-left text-xs transition-colors hover:border-primary/50"
            >
              <span className="truncate">
                {analysis.createdAt.slice(0, 16).replace('T', ' ')} 的分析
              </span>
              <Badge variant={analysis.source === 'demo' ? 'secondary' : 'default'}>
                {analysis.source === 'demo' ? '演示' : 'AI'}
              </Badge>
            </button>
          ))}
        </div>
      )}
      <p className="text-[11px] text-muted-foreground">
        生成后可在分析报告页确认（可修改）、拒绝建议，采纳即创建实验与任务。
      </p>
    </div>
  )
}

/** 研究问题 Tab：问题列表 + 证据计数 + 状态管理 + 研究分析入口 */
export function QuestionsTab({ projectId }: { projectId: number }) {
  const loadQuestions = useCallback(() => fetchQuestions(projectId), [projectId])
  const { data, loading, reload } = useAsyncData(loadQuestions)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Question | null>(null)
  const [confirmingDelete, setConfirmingDelete] = useState<number | null>(null)

  const handleDelete = async (id: number) => {
    if (confirmingDelete !== id) {
      setConfirmingDelete(id)
      return
    }
    try {
      await deleteQuestion(id)
      setConfirmingDelete(null)
      toast.add({ title: '研究问题已删除', description: '关联的卡片与实验不受影响', type: 'success' })
      void reload()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    }
  }

  if (loading) {
    return <p className="py-10 text-center text-sm text-muted-foreground">加载研究问题中…</p>
  }

  const questions = data ?? []

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <HelpCircle className="size-5 text-muted-foreground" />
          <h3 className="text-base font-semibold">研究问题</h3>
          <Badge variant="secondary">{questions.length} 个</Badge>
        </div>
        <Button onClick={() => { setEditing(null); setFormOpen(true) }}>
          <Plus className="size-4" />
          新建问题
        </Button>
      </div>

      <p className="text-xs text-muted-foreground">
        每个问题聚合它的文献证据（支持/反对/参考）与实验——研究知道了什么，这里一目了然。
      </p>

      {questions.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border py-10 text-center text-sm text-muted-foreground">
          还没有研究问题。先写下你当前要回答的研究问题，再围绕它积累文献证据与实验。
        </div>
      ) : (
        questions.map((question) => (
          <Card key={question.id}>
            <CardHeader className="border-b border-border">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <CardTitle className="text-base">{question.content}</CardTitle>
                  <Badge variant="outline" className={STATUS_BADGE_CLASSES[question.status]}>
                    {STATUS_LABELS[question.status]}
                  </Badge>
                </div>
                <div className="flex shrink-0 gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 gap-1 px-2 text-xs"
                    onClick={() => { setEditing(question); setFormOpen(true) }}
                  >
                    <Pencil className="size-3.5" />
                    编辑
                  </Button>
                  <Button
                    size="sm"
                    variant={confirmingDelete === question.id ? 'destructive' : 'ghost'}
                    className="h-7 gap-1 px-2 text-xs"
                    onClick={() => void handleDelete(question.id)}
                  >
                    <Trash2 className="size-3.5" />
                    {confirmingDelete === question.id ? '确认删除' : '删除'}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              {question.answerSummary && (
                <p className="rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">解答摘要：</span>
                  {question.answerSummary}
                </p>
              )}
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline" className="border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-400">
                  <BookOpenCheck className="mr-1 size-3" />
                  支持证据 {question.evidenceSupport}
                </Badge>
                <Badge variant="outline" className="border-red-300 bg-red-50 text-red-600 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-400">
                  反对证据 {question.evidenceAgainst}
                </Badge>
                <Badge variant="outline" className="border-border bg-muted text-muted-foreground">
                  参考 {question.evidenceNeutral}
                </Badge>
                <Badge variant="outline" className="border-sky-300 bg-sky-50 text-sky-700 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-400">
                  <FlaskConical className="mr-1 size-3" />
                  实验 {question.experimentsCount}
                </Badge>
              </div>
              <div className="mt-1 border-t border-border/60 pt-3">
                <QuestionAnalyses questionId={question.id} />
              </div>
            </CardContent>
          </Card>
        ))
      )}

      <QuestionFormSheet
        open={formOpen}
        onOpenChange={setFormOpen}
        projectId={projectId}
        question={editing}
        onSaved={() => void reload()}
      />
    </div>
  )
}
