import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface LanguageSwitcherProps {
  displayLanguage: string
  availableLanguages: string[]
  onLanguageChange: (language: string) => void
  getLanguageName: (code: string) => string
}

export default function LanguageSwitcher({
  displayLanguage,
  availableLanguages,
  onLanguageChange,
  getLanguageName,
}: Readonly<LanguageSwitcherProps>) {
  const validLanguages = availableLanguages.filter(lang => lang && lang.trim() !== '')

  return (
    <Select value={displayLanguage} onValueChange={onLanguageChange}>
      <SelectTrigger className="w-28 h-9">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {validLanguages.map((lang) => (
          <SelectItem key={lang} value={lang}>
            {getLanguageName(lang)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
