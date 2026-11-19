import { Columns3, Pencil, Plus, Quote, Sparkles, Trash2, X } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { NativeSelect } from '@/components/ui/native-select'
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import { useAsyncData } from '@/hooks/useAsyncData'
import {
  compareCards,
  createCard,
  deleteCard,
  fetchCards,
  fetchQuestions,
  updateCard,
} from '@/services/api'
import type { DocumentInfo, EvidenceType, LiteratureCard, Question } from '@/types'

const EVIDENCE_LABELS: Record<EvidenceType, string> = {
  support: '支持',
  against: '反对',
  neutral: '参考',
}

const EVIDENCE_BADGE_CLASSES: Record<EvidenceType, string> = {
  support: 'border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-400',
  against: 'border-red-300 bg-red-50 text-red-600 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-400',
  neutral: 'border-border bg-muted text-muted-foreground',
}

const EVIDENCE_ITEMS: Array<{ value: EvidenceType; label: string }> = [
  { value: 'support', label: '支持' },
  { value: 'against', label: '反对' },
  { value: 'neutral', label: '参考' },
]

/** 卡片中的文本字段（不含结构化字段 evidenceSnippets） */
type CardTextField =
  | 'title'
  | 'authors'
  | 'year'
  | 'researchQuestion'
  | 'method'
  | 'materialsDatasets'
  | 'metrics'
  | 'keyResults'
  | 'innovations'
  | 'limitations'
  | 'relevance'

/** 卡片编辑表单字段定义 */
const CARD_FIELDS: Array<{ key: CardTextField; label: string; rows?: number }> = [
  { key: 'title', label: '论文标题' },
  { key: 'authors', label: '作者' },
  { key: 'year', label: '年份' },
  { key: 'researchQuestion', label: '该文研究的问题', rows: 2 },
  { key: 'method', label: '方法简述', rows: 3 },
  { key: 'materialsDatasets', label: '数据集/材料/实验对象', rows: 2 },
  { key: 'metrics', label: '评价指标', rows: 2 },
  { key: 'keyResults', label: '主要结果', rows: 4 },
  { key: 'innovations', label: '创新点', rows: 3 },
  { key: 'limitations', label: '局限', rows: 3 },
  { key: 'relevance', label: '与我们研究的关联', rows: 3 },
]

/** 对比表中的字段（与编辑表单一致，去掉元信息） */
const COMPARE_FIELDS = CARD_FIELDS

interface SnippetDraft {
  quote: string
  page: string
}

interface CardFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  projectId: number
  card: LiteratureCard | null
  questions: Question[]
  onSaved: () => void
}

/** 新建 / 编辑研究卡片抽屉 */
function CardFormSheet({ open, onOpenChange, projectId, card, questions, onSaved }: CardFormSheetProps) {
  const [fields, setFields] = useState<Record<string, string>>({})
  const [evidenceType, setEvidenceType] = useState<EvidenceType>('neutral')
  const [questionId, setQuestionId] = useState<string>('')
  const [snippets, setSnippets] = useState<SnippetDraft[]>([])
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!open) return
    const next: Record<string, string> = {}
    for (const field of CARD_FIELDS) {
      next[field.key] = card ? String(card[field.key] ?? '') : ''
    }
    setFields(next)
    setEvidenceType(card?.evidenceType ?? 'neutral')
    setQuestionId(card?.questionId != null ? String(card.questionId) : '')
    setSnippets(
      (card?.evidenceSnippets ?? []).map((s) => ({ quote: s.quote, page: s.page ?? '' }))
    )
  }, [open, card])

  const updateSnippet = (index: number, patch: Partial<SnippetDraft>) => {
    setSnippets((prev) => prev.map((s, i) => (i === index ? { ...s, ...patch } : s)))
  }

  const handleSubmit = async () => {
    const payload: Record<string, unknown> = {}
    for (const field of CARD_FIELDS) {
      payload[field.key] = fields[field.key]?.trim() || null
    }
    payload.evidenceType = evidenceType
    payload.questionId = questionId ? Number(questionId) : null
    // 只保留有原文摘录的片段
    payload.evidenceSnippets = snippets
      .filter((s) => s.quote.trim() !== '')
      .map((s) => ({ quote: s.quote.trim(), page: s.page.trim() || null }))
    setSubmitting(true)
    try {
      if (card) {
        await updateCard(card.id, payload)
        toast.add({ title: '卡片已保存（标记为人工确认）', type: 'success' })
      } else {
        await createCard(projectId, payload)
        toast.add({ title: '卡片已创建', type: 'success' })
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
      <SheetContent className="sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>{card ? '编辑研究卡片' : '手工创建研究卡片'}</SheetTitle>
          <SheetDescription>字段留空是合法的——不确定的内容不要填。</SheetDescription>
        </SheetHeader>
        <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-2">
              <Label>证据立场</Label>
              <NativeSelect
                value={evidenceType}
                onChange={(value) => setEvidenceType((value || 'neutral') as EvidenceType)}
                items={EVIDENCE_ITEMS}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label>关联研究问题</Label>
              <NativeSelect
                value={questionId}
                onChange={(value) => setQuestionId(value)}
                items={questions.map((q) => ({ value: String(q.id), label: q.content.slice(0, 24) }))}
                placeholder="不关联"
              />
            </div>
          </div>
          {CARD_FIELDS.map((field) => (
            <div key={field.key} className="flex flex-col gap-2">
              <Label>{field.label}</Label>
              <Textarea
                rows={field.rows ?? 1}
                value={fields[field.key] ?? ''}
                onChange={(e) => setFields((prev) => ({ ...prev, [field.key]: e.target.value }))}
              />
            </div>
          ))}
          <div className="flex flex-col gap-2 rounded-xl border border-border p-3">
            <div className="flex items-center justify-between">
              <Label className="text-xs">原文证据片段（从原文摘录，标注页码）</Label>
              <Button
                size="sm"
                variant="outline"
                className="h-7 px-2 text-xs"
                onClick={() => setSnippets((prev) => [...prev, { quote: '', page: '' }])}
              >
                <Plus className="size-3.5" />
                添加片段
              </Button>
            </div>
            {snippets.length === 0 && (
              <p className="text-xs text-muted-foreground">
                摘录支持/反对你论点的原文句子，方便日后回溯原文核对。
              </p>
            )}
            {snippets.map((snippet, index) => (
              <div key={index} className="flex items-start gap-2">
                <div className="flex flex-1 flex-col gap-1.5">
                  <Textarea
                    rows={2}
                    placeholder="原文摘录（不超过 500 字）"
                    value={snippet.quote}
                    onChange={(e) => updateSnippet(index, { quote: e.target.value })}
                  />
                  <Input
                    placeholder="页码（如 5 或 6-7，可选）"
                    value={snippet.page}
                    onChange={(e) => updateSnippet(index, { page: e.target.value })}
                  />
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-7 w-7 shrink-0 px-0"
                  onClick={() => setSnippets((prev) => prev.filter((_, i) => i !== index))}
                >
                  <Trash2 className="size-3.5" />
                </Button>
              </div>
            ))}
          </div>
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

/** 对比视图：字段级横向对比表 */
function CardCompareView({
  cards,
  onClose,
}: {
  cards: LiteratureCard[]
  onClose: () => void
}) {
  return (
    <Card className="border-primary/40">
      <CardHeader className="border-b border-border">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <CardTitle className="text-base">卡片对比（{cards.length} 篇）</CardTitle>
            <CardDescription>同一字段横向对比，一眼看出方法差异与证据分布</CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={onClose}>
            <X className="size-3.5" />
            关闭对比
          </Button>
        </div>
      </CardHeader>
      <CardContent className="overflow-x-auto pt-4">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted-foreground">
              <th className="w-28 py-2 pr-3 font-medium">字段</th>
              {cards.map((card) => (
                <th key={card.id} className="min-w-48 py-2 pr-3 font-medium">
                  <div className="flex items-center gap-1.5">
                    <span className="truncate">{card.title || '未命名卡片'}</span>
                    <Badge variant="outline" className={EVIDENCE_BADGE_CLASSES[card.evidenceType]}>
                      {EVIDENCE_LABELS[card.evidenceType]}
                    </Badge>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {COMPARE_FIELDS.map((field) => (
              <tr key={field.key} className="border-b border-border/60 align-top">
                <td className="py-2 pr-3 text-xs font-medium text-muted-foreground">{field.label}</td>
                {cards.map((card) => (
                  <td key={card.id} className="py-2 pr-3 text-xs leading-relaxed break-words">
                    {card[field.key] || <span className="text-muted-foreground/50">—</span>}
                  </td>
                ))}
              </tr>
            ))}
            <tr className="border-b border-border/60 align-top">
              <td className="py-2 pr-3 text-xs font-medium text-muted-foreground">原文证据</td>
              {cards.map((card) => (
                <td key={card.id} className="py-2 pr-3 text-xs leading-relaxed">
                  {card.evidenceSnippets.length === 0 ? (
                    <span className="text-muted-foreground/50">—</span>
                  ) : (
                    <ul className="flex flex-col gap-1">
                      {card.evidenceSnippets.map((snippet, i) => (
                        <li key={i}>
                          "{snippet.quote.slice(0, 40)}…"
                          {snippet.page && (
                            <span className="ml-1 rounded bg-muted px-1 text-[10px]">p.{snippet.page}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </CardContent>
    </Card>
  )
}

/** 文献研究卡片视图：列表 + 筛选 + 新建/编辑 + 多选对比 + 从文献 AI 抽取 + 证据定位 */
export function LiteratureCardsView({
  projectId,
  documents,
  onExtractFromDocument,
  onLocateSnippet,
}: {
  projectId: number
  documents: DocumentInfo[]
  onExtractFromDocument: (documentId: number) => void
  /** 点击证据片段：定位到该文献的原文片段（由文献库 Tab 协调视图切换与高亮） */
  onLocateSnippet: (documentId: number, quote: string, page: string | null) => void
}) {
  const loadCards = useCallback(() => fetchCards(projectId), [projectId])
  const loadQuestions = useCallback(() => fetchQuestions(projectId), [projectId])
  const { data, loading, reload } = useAsyncData(loadCards)
  const { data: questions } = useAsyncData(loadQuestions)
  const [filterQuestion, setFilterQuestion] = useState('')
  const [filterEvidence, setFilterEvidence] = useState('')
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<LiteratureCard | null>(null)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [compareCardsData, setCompareCardsData] = useState<LiteratureCard[] | null>(null)
  const [confirmingDelete, setConfirmingDelete] = useState<number | null>(null)

  const cards = data ?? []

  const filteredCards = cards.filter(
    (card) =>
      (!filterQuestion || String(card.questionId) === filterQuestion) &&
      (!filterEvidence || card.evidenceType === filterEvidence)
  )

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    )
  }

  const handleCompare = async () => {
    if (selectedIds.length < 2) {
      toast.add({ title: '请先勾选至少 2 张卡片', type: 'info' })
      return
    }
    try {
      const result = await compareCards(projectId, selectedIds)
      setCompareCardsData(result.cards)
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    }
  }

  const handleDelete = async (id: number) => {
    if (confirmingDelete !== id) {
      setConfirmingDelete(id)
      return
    }
    try {
      await deleteCard(id)
      setConfirmingDelete(null)
      setSelectedIds((prev) => prev.filter((x) => x !== id))
      toast.add({ title: '卡片已删除', type: 'success' })
      void reload()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    }
  }

  const extractFromDocument = (doc: DocumentInfo) => {
    // 由父组件（文献库 Tab）统一处理抽取：先检查是否已有卡片，再调用接口
    void onExtractFromDocument(doc.id)
  }

  if (loading) {
    return <p className="py-10 text-center text-sm text-muted-foreground">加载研究卡片中…</p>
  }

  return (
    <div className="flex flex-col gap-4">
      {/* 工具栏 */}
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary">{cards.length} 张</Badge>
        <NativeSelect
          value={filterQuestion}
          onChange={setFilterQuestion}
          items={(questions ?? []).map((q) => ({ value: String(q.id), label: q.content.slice(0, 20) }))}
          placeholder="按问题筛选"
          className="w-48"
        />
        <NativeSelect
          value={filterEvidence}
          onChange={setFilterEvidence}
          items={EVIDENCE_ITEMS}
          placeholder="按立场筛选"
          className="w-32"
        />
        <div className="flex-1" />
        <Button
          variant="outline"
          size="sm"
          disabled={selectedIds.length < 2}
          onClick={() => void handleCompare()}
        >
          <Columns3 className="size-3.5" />
          对比所选（{selectedIds.length}）
        </Button>
        <Button size="sm" onClick={() => { setEditing(null); setFormOpen(true) }}>
          <Plus className="size-3.5" />
          手工新建
        </Button>
      </div>

      {compareCardsData && (
        <CardCompareView cards={compareCardsData} onClose={() => setCompareCardsData(null)} />
      )}

      {/* 从文献一键抽取 */}
      {documents.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 rounded-xl border border-dashed border-border p-3">
          <Sparkles className="size-4 text-primary" />
          <span className="text-xs text-muted-foreground">
            对已上传文献一键 AI 抽取结构化卡片：
          </span>
          {documents.map((doc) => (
            <Button
              key={doc.id}
              size="sm"
              variant="outline"
              className="h-7 text-xs"
              onClick={() => extractFromDocument(doc)}
            >
              {doc.title.slice(0, 16)}
            </Button>
          ))}
        </div>
      )}

      {/* 卡片列表 */}
      {filteredCards.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border py-10 text-center text-sm text-muted-foreground">
          {cards.length === 0
            ? '还没有研究卡片：对文献 AI 抽取，或手工新建。'
            : '没有符合筛选条件的卡片。'}
        </div>
      ) : (
        filteredCards.map((card) => (
          <Card key={card.id} className={selectedIds.includes(card.id) ? 'border-primary/50' : ''}>
            <CardHeader className="border-b border-border">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      className="size-4 shrink-0"
                      checked={selectedIds.includes(card.id)}
                      onChange={() => toggleSelect(card.id)}
                    />
                    <CardTitle className="text-sm font-medium">
                      {card.title || '未命名卡片'}
                    </CardTitle>
                    <Badge variant="outline" className={EVIDENCE_BADGE_CLASSES[card.evidenceType]}>
                      {EVIDENCE_LABELS[card.evidenceType]}
                    </Badge>
                    <Badge variant={card.source === 'manual' ? 'secondary' : 'default'}>
                      {card.source === 'manual' ? '人工' : card.source === 'demo' ? '演示' : 'AI 抽取'}
                    </Badge>
                  </div>
                  {card.authors && (
                    <p className="mt-1 text-xs text-muted-foreground">
                      {card.authors}{card.year ? ` · ${card.year}` : ''}
                    </p>
                  )}
                </div>
                <div className="flex shrink-0 gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 gap-1 px-2 text-xs"
                    onClick={() => { setEditing(card); setFormOpen(true) }}
                  >
                    <Pencil className="size-3.5" />
                    编辑
                  </Button>
                  <Button
                    size="sm"
                    variant={confirmingDelete === card.id ? 'destructive' : 'ghost'}
                    className="h-7 gap-1 px-2 text-xs"
                    onClick={() => void handleDelete(card.id)}
                  >
                    <Trash2 className="size-3.5" />
                    {confirmingDelete === card.id ? '确认删除' : '删除'}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              {card.method && (
                <p className="text-xs leading-relaxed">
                  <span className="font-medium text-muted-foreground">方法：</span>
                  {card.method}
                </p>
              )}
              {card.keyResults && (
                <p className="text-xs leading-relaxed">
                  <span className="font-medium text-muted-foreground">主要结果：</span>
                  {card.keyResults}
                </p>
              )}
              {card.innovations && (
                <p className="text-xs leading-relaxed">
                  <span className="font-medium text-muted-foreground">创新点：</span>
                  {card.innovations}
                </p>
              )}
              {card.evidenceSnippets.length > 0 && (
                <div className="flex flex-col gap-1.5">
                  <p className="text-xs font-medium text-muted-foreground">
                    原文证据（{card.evidenceSnippets.length}）
                  </p>
                  {card.evidenceSnippets.map((snippet, index) => (
                    <button
                      key={index}
                      type="button"
                      disabled={card.documentId == null}
                      onClick={() => onLocateSnippet(card.documentId as number, snippet.quote, snippet.page)}
                      className="flex items-start gap-2 rounded-lg border border-border bg-background/60 px-3 py-2 text-left text-xs text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <Quote className="mt-0.5 size-3.5 shrink-0 text-primary" />
                      <span className="min-w-0 flex-1 line-clamp-2">{snippet.quote}</span>
                      {snippet.page && (
                        <span className="shrink-0 rounded bg-muted px-1.5 py-0.5 text-[10px] tabular-nums">
                          p.{snippet.page}
                        </span>
                      )}
                    </button>
                  ))}
                  {card.documentId == null && (
                    <p className="text-[10px] text-muted-foreground/70">
                      该卡片未关联文献文件，无法定位原文
                    </p>
                  )}
                </div>
              )}
              {card.relevance && (
                <p className="text-xs leading-relaxed text-muted-foreground">
                  <span className="font-medium">关联：</span>
                  {card.relevance}
                </p>
              )}
            </CardContent>
          </Card>
        ))
      )}

      <CardFormSheet
        open={formOpen}
        onOpenChange={setFormOpen}
        projectId={projectId}
        card={editing}
        questions={questions ?? []}
        onSaved={() => void reload()}
      />
    </div>
  )
}
