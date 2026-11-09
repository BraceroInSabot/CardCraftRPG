import { useEffect, useRef, useState } from 'react'
import { IMAGE_RULES } from '../domain/types'

export interface ImageDraft {
  file: File | null
  removed: boolean
  previewUrl: string | null
  error: string | null
  choose(file: File | null): void
  remove(): void
}

/** Holds the image the user picked (or removed) until the card is saved. */
export function useImageDraft(currentUrl: string | null): ImageDraft {
  const [file, setFile] = useState<File | null>(null)
  const [objectUrl, setObjectUrl] = useState<string | null>(null)
  const [removed, setRemoved] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const urlRef = useRef<string | null>(null)

  useEffect(() => () => {
    if (urlRef.current) URL.revokeObjectURL(urlRef.current)
  }, [])

  const replaceObjectUrl = (next: File | null) => {
    if (urlRef.current) URL.revokeObjectURL(urlRef.current)
    urlRef.current = next ? URL.createObjectURL(next) : null
    setObjectUrl(urlRef.current)
  }

  return {
    file,
    removed,
    error,
    previewUrl: objectUrl ?? (removed ? null : currentUrl),
    choose(next) {
      setError(null)
      if (next && !IMAGE_RULES.types.includes(next.type)) {
        setError('Choose a PNG, JPEG, WebP or GIF image.')
        return
      }
      if (next && next.size > IMAGE_RULES.maxBytes) {
        setError('Images must be at most 5 MB.')
        return
      }
      setFile(next)
      replaceObjectUrl(next)
    },
    remove() {
      setError(null)
      setFile(null)
      replaceObjectUrl(null)
      setRemoved(true)
    },
  }
}
