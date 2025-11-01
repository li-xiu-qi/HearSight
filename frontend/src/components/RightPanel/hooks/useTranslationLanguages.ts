import { useEffect } from "react"
import type { Segment } from "@/types"

interface UseTranslationLanguagesParams {
  readonly segments: Segment[]
  readonly addLanguage: (code: string) => void
}

export const useTranslationLanguages = ({ segments, addLanguage }: UseTranslationLanguagesParams) => {
  useEffect(() => {
    if (!segments.length) {
      return
    }
    const collected = new Set<string>()
    segments.forEach((segment) => {
      const { translation } = segment
      if (!translation || typeof translation !== "object") {
        return
      }
      Object.entries(translation).forEach(([language, text]) => {
        if (typeof text === "string" && text.trim() && language.trim()) {
          collected.add(language)
        }
      })
    })
    collected.forEach(addLanguage)
  }, [segments, addLanguage])
}
