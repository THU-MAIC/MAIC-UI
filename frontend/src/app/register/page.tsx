'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuth } from '@/components/providers/AuthProvider'
import { useLanguage } from '@/components/providers/LanguageProvider'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'

const registerSchema = z
  .object({
    email: z.string().email('请输入有效邮箱地址'),
    username: z
      .string()
      .min(3, '用户名至少需要 3 个字符')
      .max(20, '用户名不能超过 20 个字符')
      .regex(/^[a-zA-Z0-9_-]+$/, '用户名只允许字母、数字、连字符和下划线'),
    password: z
      .string()
      .min(8, '密码至少需要 8 个字符')
      .regex(/[A-Za-z]/, '密码至少包含一个字母')
      .regex(/\d/, '密码至少包含一个数字'),
    confirmPassword: z.string(),
    fullName: z.string().optional(),
    gradeLevel: z.number().int().min(0).max(12).optional()
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: '两次输入的密码不一致',
    path: ['confirmPassword']
  })

type RegisterFormData = z.infer<typeof registerSchema>

export default function RegisterPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()
  const { register: registerUser } = useAuth()
  const { language, setLanguage, t } = useLanguage()

  const languages = [
    { value: 'zh', label: '中文' },
    { value: 'en', label: 'English' },
  ]

  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema)
  })

  const onSubmit = async (data: RegisterFormData) => {
    setIsLoading(true)
    setError('')

    try {
      await registerUser({
        email: data.email,
        username: data.username,
        password: data.password,
        full_name: data.fullName || undefined,
        grade_level: data.gradeLevel || 0,
        interests: [],
        learning_preferences: {}
      })
      router.push('/dashboard')
    } catch (err: any) {
      if (err.response?.data?.detail) {
        setError(err.response.data.detail)
      } else {
        setError(t('register.error_generic'))
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-[url('/images/photo0.jpg')] bg-cover bg-center bg-no-repeat">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_45%,rgba(255,255,255,0.34)_0%,rgba(255,255,255,0.15)_35%,rgba(255,255,255,0)_66%)]"
      />

      {/* Language selector in top right corner */}
      <div className="absolute top-4 right-4 z-20">
        <div className="flex gap-2 rounded-full bg-white/30 backdrop-blur-sm p-1">
          {languages.map((lang) => (
            <button
              key={lang.value}
              onClick={() => setLanguage(lang.value as 'zh' | 'en')}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition ${
                language === lang.value
                  ? 'bg-white/80 text-slate-900'
                  : 'text-white hover:bg-white/40'
              }`}
            >
              {lang.label}
            </button>
          ))}
        </div>
      </div>

      <div className="relative z-10 flex min-h-screen items-center justify-start px-5 py-8 sm:px-8 lg:px-16 xl:px-24">
        <div className="relative ml-4 w-full max-w-[520px] overflow-hidden rounded-[34px] border border-white/75 bg-white/12 p-8 shadow-[0_20px_70px_rgba(38,58,112,0.24)] backdrop-blur-2xl sm:ml-8 sm:p-9 lg:ml-12">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_45%_35%,rgba(255,255,255,0.42)_0%,rgba(255,255,255,0.2)_34%,rgba(255,255,255,0.08)_66%,rgba(255,255,255,0.02)_100%)]"
          />
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-[1px] rounded-[36px] border border-white/35"
          />

          <div className="relative z-10">
            <h2 className="whitespace-nowrap text-center text-[2.1rem] font-extrabold leading-tight text-slate-900">
              {t('register.subtitle')}
            </h2>

            <p className="mt-3 text-center text-sm text-slate-700/95">
              {language === 'zh' ? '或者' : 'Or'}{' '}
              <Link href="/login" className="font-semibold text-blue-700 hover:text-blue-800">
                {t('register.login_link')}
              </Link>
            </p>

            <form className="mt-7 space-y-4" onSubmit={handleSubmit(onSubmit)}>
              <Input
                label={t('register.email')}
                type="email"
                placeholder={t('register.email_placeholder')}
                {...register('email')}
                error={errors.email?.message}
                className="h-12 rounded-full border-white/70 bg-white/46 px-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.65)]"
              />

              <Input
                label={t('register.username')}
                type="text"
                placeholder={language === 'zh' ? '设置一个用户名' : 'Set a username'}
                {...register('username')}
                error={errors.username?.message}
                className="h-12 rounded-full border-white/70 bg-white/46 px-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.65)]"
              />

              <Input
                label={t('register.full_name')}
                type="text"
                placeholder={t('register.full_name_placeholder')}
                {...register('fullName')}
                error={errors.fullName?.message}
                className="h-12 rounded-full border-white/70 bg-white/46 px-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.65)]"
              />

              <Input
                label={language === 'zh' ? '年级（可选）' : 'Grade (optional)'}
                type="number"
                min="0"
                max="12"
                placeholder={language === 'zh' ? '0-12，0 代表幼儿园' : '0-12, 0 for kindergarten'}
                {...register('gradeLevel', { valueAsNumber: true })}
                error={errors.gradeLevel?.message}
                className="h-12 rounded-full border-white/70 bg-white/46 px-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.65)]"
              />

              <Input
                label={t('register.password')}
                type="password"
                placeholder={t('register.password_placeholder')}
                {...register('password')}
                error={errors.password?.message}
                className="h-12 rounded-full border-white/70 bg-white/46 px-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.65)]"
              />

              <Input
                label={language === 'zh' ? '确认密码' : 'Confirm Password'}
                type="password"
                placeholder={language === 'zh' ? '请再次输入密码' : 'Enter password again'}
                {...register('confirmPassword')}
                error={errors.confirmPassword?.message}
                className="h-12 rounded-full border-white/70 bg-white/46 px-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.65)]"
              />

              {error && (
                <div className="rounded-xl border border-red-300/70 bg-red-50/85 px-4 py-3 text-red-700 backdrop-blur">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                className="mt-1 h-11 w-full rounded-xl bg-gradient-to-r from-[#2d6af5] to-[#2558dd] text-base font-semibold text-white shadow-[0_12px_28px_rgba(45,106,245,0.35)] hover:from-[#3874f7] hover:to-[#2f61e2]"
                isLoading={isLoading}
                disabled={isLoading}
              >
                {t('register.submit')}
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
