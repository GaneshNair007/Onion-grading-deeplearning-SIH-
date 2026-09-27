import { ReactNode, CSSProperties } from 'react'

interface TechLabelProps {
  children: ReactNode
  cyan?: boolean
  className?: string
  style?: CSSProperties
}

export default function TechLabel({ children, cyan = false, className = '', style }: TechLabelProps) {
  return (
    <span className={`${cyan ? 'tech-label-cyan' : 'tech-label'} ${className}`} style={style}>
      {children}
    </span>
  )
}
