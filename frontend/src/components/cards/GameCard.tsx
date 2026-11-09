import { useLayoutEffect, useRef, useState, type CSSProperties } from 'react'
import type { CardModel } from '../../resources/types'
import classes from './GameCard.module.css'

const MAX_BODY_PT = 8.5
const MIN_BODY_PT = 5.5
const STEP_PT = 0.25

/** Shrinks the description until it fits the space left on the card. */
function useFitText(text: string) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [size, setSize] = useState(MAX_BODY_PT)

  useLayoutEffect(() => {
    const container = containerRef.current
    if (!container) return
    const paragraph = container.firstElementChild as HTMLElement | null
    if (!paragraph) return

    const fit = () => {
      let current = MAX_BODY_PT
      paragraph.style.fontSize = `${current}pt`
      while (current > MIN_BODY_PT && paragraph.scrollHeight > container.clientHeight) {
        current -= STEP_PT
        paragraph.style.fontSize = `${current}pt`
      }
      setSize(current)
    }

    fit()
    let cancelled = false
    document.fonts?.ready.then(() => !cancelled && fit())
    return () => {
      cancelled = true
    }
  }, [text])

  return { containerRef, size }
}

export function GameCard({ card }: { card: CardModel }) {
  const { containerRef, size } = useFitText(card.body)

  return (
    <article className={classes.card} style={{ '--frame': card.frameColor } as CSSProperties}>
      <header className={classes.band}>
        <span>{card.category}</span>
        {card.origin && <span className={classes.origin}>{card.origin}</span>}
      </header>
      <div className={classes.inner}>
        <h3 className={classes.title}>{card.title}</h3>
        {card.tags.length > 0 && (
          <div className={classes.tags}>
            {card.tags.map((tag) => (
              <span key={tag.label} className={classes.tag} style={{ '--tag': tag.color } as CSSProperties}>
                {tag.label}
              </span>
            ))}
          </div>
        )}
        <div className={classes.body} ref={containerRef}>
          <p style={{ fontSize: `${size}pt` }} className={card.body ? undefined : classes.empty}>
            {card.body || 'No description yet.'}
          </p>
        </div>
        {card.stats.length > 0 && (
          <dl className={classes.stats}>
            {card.stats.map((stat) => (
              <div key={stat.label} className={classes.stat}>
                <dt>{stat.label}</dt>
                <dd>{stat.value}</dd>
              </div>
            ))}
          </dl>
        )}
        {card.footnote && <p className={classes.footnote}>{card.footnote}</p>}
      </div>
    </article>
  )
}
