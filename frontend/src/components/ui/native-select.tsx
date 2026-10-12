import { cn } from 'cn'

export interface NativeSelectOption {
  value: string
  label: string
}

interface NativeSelectProps {
  id?: string
  value: string
  onChange: (value: string) => void
  items: NativeSelectOption[]
  placeholder?: string
  className?: string
}

/**
 * 原生 <select> 下拉：样式与 Input 一致，行为 100% 可靠。
 * 替代 Base UI Select——后者在当前 React/浏览器环境下弹不出选项面板。
 */
export function NativeSelect({
  id,
  value,
  onChange,
  items,
  placeholder,
  className,
}: NativeSelectProps) {
  return (
    <select
      id={id}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={cn(
        'h-9 w-full rounded-lg border border-input bg-transparent px-3 text-sm outline-none transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 dark:bg-input/30 dark:[&>option]:bg-background',
        value ? 'text-foreground' : 'text-muted-foreground',
        className
      )}
    >
      {placeholder && (
        <option value="" disabled>
          {placeholder}
        </option>
      )}
      {items.map((item) => (
        <option key={item.value} value={item.value}>
          {item.label}
        </option>
      ))}
    </select>
  )
}
