import { motion, HTMLMotionProps } from 'framer-motion'
import { ReactNode } from 'react'

interface GlassCardProps extends HTMLMotionProps<'div'> {
  children: ReactNode
  delay?: number
  className?: string
  hud?: boolean
}

export default function GlassCard({
  children,
  delay = 0,
  className = '',
  ...rest
}: GlassCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: false, amount: 0.15 }}
      transition={{ duration: 0.7, delay, ease: [0.16, 1, 0.3, 1] }}
      className={`glass-card p-8 md:p-10 ${className}`}
      {...rest}
    >
      {children}
    </motion.div>
  )
}
