import { BookmarkPlus, Loader2, Quote, Send } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { toast } from '@/components/ui/toast'
import { askDocument, fetchDocumentQa, saveQaNote } from '@/services/api'
import type { QaEntry } from '@/types'

interface DocumentQaPanelProps {
  documentId: number
  /** 点击引用时回调：跳到对应原文切片 */
  onJumpToChunk: (chunkIndex: number) => void
}

/** 文献问答面板：提问 → 答案 + 引用片段 + 置信度 + 保存笔记 + 历史记录 */
export function DocumentQaPanel({ documentId, onJumpToChunk }: DocumentQaPanelProps) {
  const [question, setQuestion] = useState('')
  const [asking, setAsking] = useState(false)
  const [history, setHistory] = useState<QaEntry[]>([])

  useEffect(() => {
    setHistory([])
    setQuestion('')
    fetchDocumentQa(documentId)
      .then(setHistory)
      .catch(() => setHistory([]))
  }, [documentId])

  const handleAsk = async () => {
    if (!question.trim()) {
      toast.add({ title: '请输入问题', type: 'info' })
      return
    }
    setAsking(true)
    try {
      const qa = await askDocument(documentId, question.trim())
      setHistory((prev) => [qa, ...prev])
      setQuestion('')
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setAsking(false)
    }
  }

  const handleSaveNote = async (qa: QaEntry) => {
    try {
      await saveQaNote(qa.id)
      setHistory((prev) => prev.map((item) => (item.id === qa.id ? { ...item, isSaved: true } : item)))
      toast.add({ title: '已保存为笔记', type: 'success' })
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2">
        <Input
          placeholder="对这篇文献提问，如：研究方法是什么？"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !asking) void handleAsk()
          }}
        />
        <Button disabled={asking} onClick={() => void handleAsk()} className="shrink-0">
          {asking ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
          {asking ? '思考中…' : '提问'}
        </Button>
      </div>

      {asking && (
        <p className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin text-primary" />
          正在检索相关片段并调用 DeepSeek 回答…
        </p>
      )}

      {history.length === 0 && !asking && (
        <p className="rounded-xl border border-dashed border-border py-6 text-center text-xs text-muted-foreground">
          还没有问答记录，输入问题开始与文献对话
        </p>
      )}

      {history.map((qa) => (
        <Card key={qa.id} className="gap-3">
          <CardHeader className="border-b border-border">
            <div className="flex items-start justify-between gap-2">
              <CardTitle className="text-sm font-medium">
                <span className="mr-1.5 text-primary">Q</span>
                {qa.question}
              </CardTitle>
              <div className="flex shrink-0 items-center gap-2">
                <Badge variant={qa.source === 'demo' ? 'secondary' : 'default'}>
                  {qa.source === 'demo' ? '演示模式' : 'DeepSeek'}
                </Badge>
                <Badge variant="outline" className="tabular-nums">
                  置信度 {Math.round(qa.confidence * 100)}%
                </Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{qa.answer}</p>

            {qa.citations.length > 0 && (
              <div>
                <p className="mb-1.5 flex items-center gap-1 text-xs font-medium text-muted-foreground">
                  <Quote className="size-3.5" />
                  来源片段（{qa.citations.length}）
                </p>
                <ul className="flex flex-col gap-1">
                  {qa.citations.map((citation, index) => (
                    <li key={index}>
                      <button
                        type="button"
                        onClick={() => onJumpToChunk(citation.chunkIndex)}
                        className="w-full rounded-lg border border-border bg-background/60 px-3 py-2 text-left text-xs text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground"
                      >
                        <span className="mr-1.5 font-medium text-primary tabular-nums">
                          [片段 {citation.chunkIndex}]
                        </span>
                        {citation.quote}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {!qa.isSaved && (
              <div className="flex justify-end">
                <Button size="sm" variant="outline" onClick={() => void handleSaveNote(qa)}>
                  <BookmarkPlus className="size-3.5" />
                  保存为笔记
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

/** 已保存笔记的只读展示（供文献库 Tab 的"我的笔记"区使用） */
export function SavedNoteList({ notes }: { notes: QaEntry[] }) {
  return (
    <div className="flex flex-col gap-3">
      {notes.map((note) => (
        <div key={note.id} className="rounded-xl border border-border bg-background p-3">
          <p className="text-sm font-medium">{note.question}</p>
          <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">
            {note.answer}
          </p>
          {note.citations.length > 0 && (
            <p className="mt-1.5 text-xs text-muted-foreground">
              来源：{note.citations.map((c) => `片段 ${c.chunkIndex}`).join('、')}
            </p>
          )}
        </div>
      ))}
    </div>
  )
}
