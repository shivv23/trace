import React from 'react'
import { motion } from 'framer-motion'
import clsx from 'clsx'

export default function ConfidenceGauge({ confidence, size = 'sm' }) {
  const { overall = 0, label = 'low' } = confidence || {}
  const percentage = Math.round(overall * 100)

  const colorMap = {
    high: { stroke: '#34d399', bg: '#34d39920', text: 'text-emerald-400', label: 'High' },
    medium: { stroke: '#fbbf24', bg: '#fbbf2420', text: 'text-amber-400', label: 'Medium' },
    low: { stroke: '#f87171', bg: '#f8717120', text: 'text-red-400', label: 'Low' },
  }

  const colors = colorMap[label] || colorMap.low
  const radius = size === 'sm' ? 14 : 24
  const strokeWidth = size === 'sm' ? 3 : 4
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (percentage / 100) * circumference

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex items-center gap-1.5"
      title={`${percentage}% confidence (${colors.label})`}
    >
      <svg width={(radius + strokeWidth) * 2} height={(radius + strokeWidth) * 2} className="transform -rotate-90">
        <circle
          cx={radius + strokeWidth}
          cy={radius + strokeWidth}
          r={radius}
          stroke={colors.bg}
          strokeWidth={strokeWidth}
          fill="none"
        />
        <motion.circle
          cx={radius + strokeWidth}
          cy={radius + strokeWidth}
          r={radius}
          stroke={colors.stroke}
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1, ease: 'easeOut' }}
        />
      </svg>
      <span className={clsx('text-[10px] font-medium', colors.text)}>
        {percentage}%
      </span>
    </motion.div>
  )
}
