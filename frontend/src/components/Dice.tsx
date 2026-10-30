import { motion } from 'framer-motion'

const PIPS: Record<number, number[]> = {
  1: [4], 2: [0, 8], 3: [0, 4, 8], 4: [0, 2, 6, 8], 5: [0, 2, 4, 6, 8], 6: [0, 2, 3, 5, 6, 8],
}

function Die({ value, rollKey }: { value: number; rollKey: number }) {
  return (
    <motion.div
      key={rollKey}
      className="die"
      initial={{ rotate: -200, scale: 0.6, opacity: 0.4 }}
      animate={{ rotate: 0, scale: 1, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 260, damping: 16 }}
      aria-label={`die showing ${value}`}
    >
      {Array.from({ length: 9 }, (_, i) => (
        <span key={i} className={PIPS[value]?.includes(i) ? 'pip' : 'pip empty'} />
      ))}
    </motion.div>
  )
}

export function Dice({ dice, rollKey }: { dice: [number, number]; rollKey: number }) {
  if (!dice[0]) return <div className="dice placeholder">🎲 🎲</div>
  return (
    <div className="dice">
      <Die value={dice[0]} rollKey={rollKey} />
      <Die value={dice[1]} rollKey={rollKey + 0.5} />
    </div>
  )
}
