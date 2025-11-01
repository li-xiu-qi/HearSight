import { useState, useCallback } from 'react'

const AVAILABLE_LANGUAGES = [
  { code: 'original', name: '原文', nameEn: 'Original' },
  { code: 'zh', name: '中文', nameEn: 'Chinese' },
  { code: 'en', name: '英文', nameEn: 'English' },
  { code: 'ja', name: '日文', nameEn: 'Japanese' },
  { code: 'ko', name: '韩文', nameEn: 'Korean' },
  { code: 'es', name: '西班牙文', nameEn: 'Spanish' },
  { code: 'fr', name: '法文', nameEn: 'French' },
  { code: 'de', name: '德文', nameEn: 'German' },
  { code: 'ru', name: '俄文', nameEn: 'Russian' },
]

export const useLanguageSwitch = (originalLanguage: string = 'original') => {
  const [displayLanguage, setDisplayLanguage] = useState(originalLanguage)
  const [availableLanguages, setAvailableLanguages] = useState<string[]>([originalLanguage])

  const addLanguage = useCallback((languageCode: string) => {
    if (!languageCode || languageCode.trim() === '') {
      return
    }
    setAvailableLanguages(prev => {
      if (!prev.includes(languageCode)) {
        return [...prev, languageCode]
      }
      return prev
    })
  }, [])

  const switchLanguage = useCallback((languageCode: string) => {
    if (availableLanguages.includes(languageCode)) {
      setDisplayLanguage(languageCode)
    }
  }, [availableLanguages])

  const getLanguageName = useCallback((code: string) => {
    const lang = AVAILABLE_LANGUAGES.find(l => l.code === code)
    return lang ? lang.name : code
  }, [])

  const validLanguages = availableLanguages.filter(lang => lang && lang.trim() !== '')

  return {
    displayLanguage,
    availableLanguages: validLanguages,
    allLanguages: AVAILABLE_LANGUAGES,
    addLanguage,
    switchLanguage,
    getLanguageName,
  }
}
