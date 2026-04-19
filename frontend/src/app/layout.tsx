import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/components/providers/AuthProvider'
import { ModelSettingsProvider } from '@/components/providers/ModelSettingsProvider'
import { LanguageProvider } from '@/components/providers/LanguageProvider'

export const metadata: Metadata = {
  title: 'MAIC-UI',
  description: 'AI-augmented textbook platform for personalized learning',
  icons: {
    icon: '/images/favicon.jpg',
    shortcut: '/images/favicon.jpg',
    apple: '/images/favicon.jpg',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh">
      <body>
        <AuthProvider>
          <ModelSettingsProvider>
            <LanguageProvider>
              {children}
            </LanguageProvider>
          </ModelSettingsProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
