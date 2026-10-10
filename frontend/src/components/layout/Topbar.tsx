import { Moon, Sun } from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { useTheme } from '@/hooks/useTheme'

/** 顶栏：页面标题 + 主题切换 + 用户头像 */
export function Topbar({ title }: { title: string }) {
  const { theme, toggleTheme } = useTheme()

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-card px-6">
      <h2 className="font-heading text-base font-semibold">{title}</h2>
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          aria-label={theme === 'dark' ? '切换到浅色模式' : '切换到深色模式'}
        >
          {theme === 'dark' ? (
            <Sun className="size-4" />
          ) : (
            <Moon className="size-4" />
          )}
        </Button>
        <Avatar className="size-8">
          <AvatarFallback className="bg-primary/10 text-xs text-primary">
            研
          </AvatarFallback>
        </Avatar>
      </div>
    </header>
  )
}
