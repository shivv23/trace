import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { ThumbsUp, ThumbsDown } from 'lucide-react'
import clsx from 'clsx'

export default function FeedbackButtons({ rating, onRate }) {
  const [animating, setAnimating] = useState(null)

  const handleRate = (value) => {
    if (rating !== undefined) return
    setAnimating(value)
    setTimeout(() => {
      setAnimating(null)
      onRate(value)
    }, 300)
  }

  return (
    <div className="flex items-center gap-1">
      <motion.button
        whileTap={{ scale: 0.8 }}
        onClick={() => handleRate(1)}
        disabled={rating !== undefined}
        className={clsx(
          'p-1 rounded transition-all duration-200',
          rating === 1
            ? 'text-emerald-400 bg-emerald-500/10'
            : rating !== undefined
            ? 'text-surface-600'
            : 'text-surface-500 hover:text-surface-300 hover:bg-surface-800/50'
        )}
        title="Helpful"
      >
        <ThumbsUp size={12} className={animating === 1 ? 'animate-bounce' : ''} />
      </motion.button>
      <motion.button
        whileTap={{ scale: 0.8 }}
        onClick={() => handleRate(0)}
        disabled={rating !== undefined}
        className={clsx(
          'p-1 rounded transition-all duration-200',
          rating === 0
            ? 'text-red-400 bg-red-500/10'
            : rating !== undefined
            ? 'text-surface-600'
            : 'text-surface-500 hover:text-surface-300 hover:bg-surface-800/50'
        )}
        title="Not helpful"
      >
        <ThumbsDown size={12} className={animating === 0 ? 'animate-bounce' : ''} />
      </motion.button>
    </div>
  )
}
