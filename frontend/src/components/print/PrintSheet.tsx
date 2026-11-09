import { createPortal } from 'react-dom'
import type { CardModel } from '../../resources/types'
import { GameCard } from '../cards/GameCard'

export const CARDS_PER_PAGE = 9 // 3 × 3 cards of 6 × 9 cm on A4

function chunk<T>(list: T[], size: number): T[][] {
  const pages: T[][] = []
  for (let i = 0; i < list.length; i += size) pages.push(list.slice(i, i + size))
  return pages
}

/**
 * Off-screen, real-size copy of the cards that is the only thing visible
 * when the browser prints (see `.print-root` in global.css).
 */
export function PrintSheet({ cards }: { cards: { id: number; card: CardModel }[] }) {
  return createPortal(
    <div className="print-root" aria-hidden>
      {chunk(cards, CARDS_PER_PAGE).map((page, index) => (
        <section className="print-page" key={index}>
          {page.map(({ id, card }) => (
            <div className="print-cell" key={id}>
              <GameCard card={card} />
            </div>
          ))}
        </section>
      ))}
    </div>,
    document.body,
  )
}
