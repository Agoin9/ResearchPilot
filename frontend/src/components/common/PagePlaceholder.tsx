import { Construction, Home } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'

interface PagePlaceholderProps {
  title: string
  description: string
}

/** 未开发页面的占位组件：标注"正在开发中"，可返回首页 */
export function PagePlaceholder({ title, description }: PagePlaceholderProps) {
  const navigate = useNavigate()

  return (
    <div className="flex h-full flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card px-6 py-24 text-center">
      <div className="flex size-14 items-center justify-center rounded-full bg-primary/10">
        <Construction className="size-7 text-primary" />
      </div>
      <h3 className="mt-4 text-lg font-semibold">{title}</h3>
      <p className="mt-1.5 max-w-md text-sm text-muted-foreground">
        {description}
      </p>
      <Button className="mt-6" variant="outline" onClick={() => navigate('/')}>
        <Home className="size-4" />
        返回首页
      </Button>
    </div>
  )
}
