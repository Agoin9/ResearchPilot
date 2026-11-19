import {
  Bookmark,
  FileText,
  Layers,
  Loader2,
  Trash2,
  Upload,
} from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from '@/components/ui/toast'
import { useAsyncData } from '@/hooks/useAsyncData'
import {
  deleteDocument,
  extractDocumentCard,
  fetchDocumentDetail,
  fetchDocuments,
  fetchProjectNotes,
  uploadDocument,
} from '@/services/api'
import type { DocumentInfo, QaEntry } from '@/types'
import { DocumentQaPanel, SavedNoteList } from './DocumentQaPanel'
import { LiteratureCardsView } from './LiteratureCardsView'

interface DocumentLibraryTabProps {
  projectId: number
  /** 初始二级视图：'qa' 原文问答 / 'cards' 研究卡片（文献研究库页默认卡片视图） */
  initialView?: 'qa' | 'cards'
}

const formatDate = (iso: string) => {
  const [, month, day] = iso.split('-')
  return `${month}-${day}`
}

/** 文献库 Tab：上传 PDF、切片原文、AI 问答（带引用）、我的笔记 + 研究卡片（v2 证据库） */
export function DocumentLibraryTab({ projectId, initialView = 'qa' }: DocumentLibraryTabProps) {
  const loadDocuments = useCallback(() => fetchDocuments(projectId), [projectId])
  const { data: documents, loading, error, reload } = useAsyncData(loadDocuments)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [uploading, setUploading] = useState(false)
  const [view, setView] = useState<'qa' | 'cards'>(initialView)
  const [cardsVersion, setCardsVersion] = useState(0)
  // 证据片段定位请求：切换到原文视图并高亮包含该摘录的切片
  const [highlightQuote, setHighlightQuote] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 项目切换时重置选中状态
  useEffect(() => {
    setSelectedId(null)
  }, [projectId])

  const selected = documents?.find((doc) => doc.id === selectedId) ?? null

  const handleUpload = async (file: File) => {
    setUploading(true)
    try {
      const doc = await uploadDocument(projectId, file)
      toast.add({
        title: '文献上传成功',
        description: `已提取 ${doc.chunkCount} 个片段`,
        type: 'success',
      })
      setSelectedId(doc.id)
      void reload()
    } catch {
      // 错误提示（含扫描版 PDF 提示）已由 api 层统一 toast 展示
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleDelete = async (doc: DocumentInfo) => {
    try {
      await deleteDocument(doc.id)
      toast.add({ title: '文献已删除', type: 'success' })
      if (selectedId === doc.id) setSelectedId(null)
      void reload()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    }
  }

  /** 对文献 AI 抽取研究卡片（无 Key 时演示模式返回空模板） */
  const handleExtractCard = async (documentId: number) => {
    try {
      const result = await extractDocumentCard(documentId)
      setCardsVersion((v) => v + 1)
      if (result.warning) {
        toast.add({ title: '演示模式', description: result.warning, type: 'info' })
      } else {
        toast.add({ title: '卡片抽取完成', description: '请人工核对各字段后保存', type: 'success' })
      }
    } catch {
      // 错误提示（如"该文献已有研究卡片"）已由 api 层统一 toast 展示
    }
  }

  /** 证据片段点击：切到原文视图 → 选中该文献 → 高亮包含摘录的原文切片 */
  const handleLocateSnippet = (documentId: number, quote: string, page: string | null) => {
    setView('qa')
    setSelectedId(documentId)
    setHighlightQuote(quote)
    if (page) {
      toast.add({
        title: `定位原文片段（页码 p.${page}）`,
        description: '将滚动到包含该摘录的原文切片；PDF 按页渲染暂未支持，以切片形式展示',
        type: 'info',
      })
    }
  }

  if (loading) {
    return <p className="py-10 text-center text-sm text-muted-foreground">加载文献库中…</p>
  }
  if (error) {
    return (
      <Card>
        <CardContent className="py-8">
          <p className="text-center text-sm text-red-500">{error}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <FileText className="size-5 text-muted-foreground" />
          <h3 className="text-base font-semibold">文献库</h3>
          <Badge variant="secondary">{documents?.length ?? 0} 篇</Badge>
        </div>
        <div className="flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf,.pdf"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) void handleUpload(file)
            }}
          />
          <Button disabled={uploading} onClick={() => fileInputRef.current?.click()}>
            {uploading ? <Loader2 className="size-4 animate-spin" /> : <Upload className="size-4" />}
            {uploading ? '提取文字中…' : '上传 PDF'}
          </Button>
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        支持含文字层的 PDF（每段约 500~800 字切块）；扫描版 PDF 暂不支持，会给出提示。
      </p>

      {/* v2 二级视图：原文问答 / 研究卡片（结构化证据库） */}
      <Tabs value={view} onValueChange={(value) => setView(value as 'qa' | 'cards')}>
        <TabsList>
          <TabsTrigger value="qa">
            <FileText className="mr-1.5 size-3.5" />
            原文问答
          </TabsTrigger>
          <TabsTrigger value="cards">
            <Layers className="mr-1.5 size-3.5" />
            研究卡片
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {view === 'cards' ? (
        <LiteratureCardsView
          key={cardsVersion}
          projectId={projectId}
          documents={documents ?? []}
          onExtractFromDocument={(documentId) => void handleExtractCard(documentId)}
          onLocateSnippet={handleLocateSnippet}
        />
      ) : (
        <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-5">
          {/* 左侧：文献列表 */}
          <div className="flex flex-col gap-2 lg:col-span-2">
            {!documents || documents.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border py-10 text-center text-sm text-muted-foreground">
                还没有文献，点击右上角「上传 PDF」
              </div>
            ) : (
              documents.map((doc) => (
                <button
                  key={doc.id}
                  type="button"
                  onClick={() => setSelectedId(doc.id)}
                  className={`flex items-start justify-between gap-2 rounded-xl border p-3 text-left transition-colors ${
                    selectedId === doc.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border bg-background hover:border-primary/40'
                  }`}
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{doc.title}</p>
                    <p className="mt-0.5 truncate text-xs text-muted-foreground">
                      {doc.fileName} · {doc.chunkCount} 个片段 · {formatDate(doc.createdAt)}
                    </p>
                  </div>
                  <span
                    role="button"
                    tabIndex={0}
                    className="shrink-0 rounded-md p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                    onClick={(e) => {
                      e.stopPropagation()
                      void handleDelete(doc)
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.stopPropagation()
                        void handleDelete(doc)
                      }
                    }}
                  >
                    <Trash2 className="size-4" />
                  </span>
                </button>
              ))
            )}
          </div>

          {/* 右侧：问答 + 原文切片 */}
          <div className="flex flex-col gap-4 lg:col-span-3">
            {selected ? (
              <>
                <DocumentDetailPanel
                  documentId={selected.id}
                  highlightQuote={highlightQuote}
                  onHighlightDone={() => setHighlightQuote(null)}
                />
                <div className="rounded-xl border border-border bg-card p-3">
                  <p className="mb-2 flex items-center gap-1.5 text-sm font-medium">
                    <Bookmark className="size-4" />
                    我的笔记
                  </p>
                  <ProjectNotes projectId={projectId} />
                </div>
              </>
            ) : (
              <div className="rounded-xl border border-dashed border-border py-10 text-center text-sm text-muted-foreground">
                选择左侧文献开始精读与提问
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

/** 选中文献的详情：原文切片 + 问答面板（点击引用跳到原文；证据片段可高亮定位） */
function DocumentDetailPanel({
  documentId,
  highlightQuote,
  onHighlightDone,
}: {
  documentId: number
  highlightQuote: string | null
  onHighlightDone: () => void
}) {
  const loadDetail = useCallback(() => fetchDocumentDetail(documentId), [documentId])
  const { data, loading, error } = useAsyncData(loadDetail)
  const [highlightChunk, setHighlightChunk] = useState<number | null>(null)
  const chunkRefs = useRef<Record<number, HTMLDivElement | null>>({})

  const jumpToChunk = (chunkIndex: number) => {
    setHighlightChunk(chunkIndex)
    const el = chunkRefs.current[chunkIndex]
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  // 证据片段定位：在原文切片中查找包含摘录的切片并高亮滚动
  useEffect(() => {
    if (!highlightQuote || !data) return
    const normalized = (s: string) => s.replace(/\s+/g, '')
    const target = normalized(highlightQuote)
    const tryMatch = (length: number): number | null => {
      const prefix = target.slice(0, length)
      if (prefix.length < 4) return null
      for (const chunk of data.chunks) {
        if (normalized(chunk.content).includes(prefix)) return chunk.chunkIndex
      }
      return null
    }
    const found = tryMatch(30) ?? tryMatch(15) ?? tryMatch(8)
    if (found !== null) {
      // 等待切片渲染完成后再滚动
      setTimeout(() => {
        setHighlightChunk(found)
        const el = chunkRefs.current[found]
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 80)
      toast.add({ title: `已定位到原文片段 ${found}`, description: '高亮区域即证据出处', type: 'success' })
    } else {
      toast.add({
        title: '未在原文切片中找到该摘录',
        description: '可能因原文排版或摘录改写导致；可手动浏览右侧切片核对页码附近内容',
        type: 'warning',
      })
    }
    onHighlightDone()
  }, [highlightQuote, data, onHighlightDone])

  if (loading) {
    return <p className="py-6 text-center text-sm text-muted-foreground">加载文献内容中…</p>
  }
  if (error || !data) {
    return (
      <p className="rounded-xl border border-border py-6 text-center text-sm text-red-500">
        {error ?? '文献加载失败'}
      </p>
    )
  }

  return (
    <Card>
      <CardHeader className="border-b border-border">
        <CardTitle className="text-base">{data.title}</CardTitle>
        <CardDescription>
          {data.chunkCount} 个片段 · 全文约 {data.fullText.length} 字
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <DocumentQaPanel documentId={documentId} onJumpToChunk={jumpToChunk} />

        <div>
          <p className="mb-2 text-xs font-medium text-muted-foreground">
            原文切片（点击引用自动定位）
          </p>
          <div className="flex max-h-96 flex-col gap-2 overflow-y-auto pr-1">
            {data.chunks.map((chunk) => (
              <div
                key={chunk.id}
                ref={(el) => {
                  chunkRefs.current[chunk.chunkIndex] = el
                }}
                className={`rounded-lg border p-3 text-xs leading-relaxed text-muted-foreground transition-colors ${
                  highlightChunk === chunk.chunkIndex
                    ? 'border-primary bg-primary/10 text-foreground'
                    : 'border-border bg-background/60'
                }`}
              >
                <span className="mr-1.5 font-medium text-primary tabular-nums">
                  [片段 {chunk.chunkIndex}]
                </span>
                {chunk.content}
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

/** 项目下已保存的笔记（跟随项目变化刷新） */
function ProjectNotes({ projectId }: { projectId: number }) {
  const loadNotes = useCallback(() => fetchProjectNotes(projectId), [projectId])
  const { data, loading } = useAsyncData(loadNotes)

  if (loading) {
    return <p className="py-4 text-center text-xs text-muted-foreground">加载笔记中…</p>
  }
  if (!data || data.length === 0) {
    return <p className="py-4 text-center text-xs text-muted-foreground">还没有保存的笔记</p>
  }
  return <SavedNoteList notes={data as QaEntry[]} />
}
