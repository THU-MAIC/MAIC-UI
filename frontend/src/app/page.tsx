'use client'

import React, { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/components/providers/AuthProvider'
import Link from 'next/link'
import Image from 'next/image'
import { Button } from '@/components/ui/Button'

export default function HomePage() {
  const { isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (isAuthenticated) {
      router.replace('/dashboard')
    }
  }, [isAuthenticated, router])

  if (isAuthenticated) {
    return null
  }

  const features = [
    {
      title: '先读懂知识 再生成课件',
      subtitle: 'SMART PARSING',
      description:
        '不是把文字丢给AI，而是先理解知识点的关系和重点，再生成课件——就像先备课再上课',
      iconSrc: '/icons/1.jpg'
    },
    {
      title: '三步走 稳稳不出错',
      subtitle: 'STEP-BY-STEP GENERATION',
      description:
        '先定结构、再填内容、最后加交互，像搭积木一样一步步来，不会一口气生成一堆乱的东西',
      iconSrc: '/icons/2.jpg'
    },
    {
      title: '哪里不满意改哪里',
      subtitle: 'INCREMENTAL EDITING',
      description:
        '不需要整页重新生成，像用橡皮擦一样，改哪里擦哪里，老师调整内容省时又省力',
      iconSrc: '/icons/3.jpg'
    },
    {
      title: '知识点自动长成可玩的页面',
      subtitle: 'GENERATIVE UI',
      description:
        '输入知识点，AI自动生成能点击、能操作的交互界面，学生不是在看，而是在"动手"学',
      iconSrc: '/icons/4.jpg'
    },
    {
      title: '教完就能练 练完有反馈',
      subtitle: 'TEACH-LEARN-PRACTICE LOOP',
      description:
        '老师备课、学生学习一套系统搞定，教、学、练、评无缝衔接，形成真正闭环',
      iconSrc: '/icons/5.jpg'
    },
    {
      title: '抽象难懂的 动起来就明白',
      subtitle: 'DYNAMIC VISUALIZATION',
      description:
        '把复杂的概念和步骤变成动态可视化过程，学生不再对着文字发呆，一步步看就能懂',
      iconSrc: '/icons/6.jpg'
    }
  ]

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-[radial-gradient(circle_at_15%_20%,_#f6f8ff_0%,_#ebefff_35%,_#e8ebf5_65%,_#e8eaef_100%)] [font-family:'Poppins','Noto_Sans_SC','PingFang_SC','Microsoft_YaHei',sans-serif]">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 z-0 h-[240px] bg-[linear-gradient(180deg,rgba(156,138,228,0.3)_0%,rgba(178,160,234,0.18)_38%,rgba(235,239,255,0)_100%)]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 bottom-0 z-0 h-[240px] bg-[linear-gradient(0deg,rgba(160,140,230,0.24)_0%,rgba(185,169,238,0.14)_36%,rgba(235,239,255,0)_100%)]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute bottom-0 left-1/2 z-0 h-[210px] w-[80%] -translate-x-1/2 bg-[radial-gradient(ellipse_at_bottom,rgba(166,147,234,0.28)_0%,rgba(191,178,239,0.14)_45%,rgba(235,239,255,0)_78%)] blur-[2px]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute left-[-8%] top-[10%] z-0 h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle,rgba(151,126,238,0.24)_0%,rgba(173,150,240,0.13)_42%,rgba(235,239,255,0)_74%)] blur-[8px]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute right-[-10%] top-[28%] z-0 h-[520px] w-[520px] rounded-full bg-[radial-gradient(circle,rgba(162,139,241,0.24)_0%,rgba(183,164,243,0.12)_40%,rgba(235,239,255,0)_74%)] blur-[10px]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute bottom-[18%] left-1/2 z-0 h-[360px] w-[68%] -translate-x-1/2 bg-[radial-gradient(ellipse_at_center,rgba(170,150,238,0.18)_0%,rgba(191,176,242,0.1)_42%,rgba(235,239,255,0)_78%)] blur-[10px]"
      />
      <div className="relative z-10 mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-10 rounded-2xl border border-white/60 bg-white/35 px-5 py-4 backdrop-blur-md shadow-[0_20px_60px_rgba(29,42,79,0.08)]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="text-xl font-semibold tracking-tight text-slate-900">MAIC-UI</div>
              <div className="hidden md:flex items-center text-sm text-slate-600">
                <span className="mr-3">|</span>
                <span>Where knowledge grows, interfaces bloom. Where interaction flows, thinking deepens.</span>
              </div>
            </div>
            <Link href="/register">
              <button className="rounded-2xl bg-white px-6 py-3 text-sm font-medium text-slate-900 shadow-sm ring-1 ring-slate-200 transition hover:shadow-md">
                Sign Up
              </button>
            </Link>
          </div>
        </header>

        <section className="grid grid-cols-1 items-center gap-8 lg:grid-cols-12">
          <div className="flex h-full items-center lg:col-span-5 p-2 md:p-4">
            <div>
            <h1 className="text-[4.35rem] font-semibold leading-[1.02] tracking-[0.015em] text-slate-900 [text-shadow:0_1px_0_rgba(255,255,255,0.55),0_14px_26px_rgba(41,60,110,0.18)] md:text-[5.4rem]">
              MAIC-UI
            </h1>
            <h2 className="mt-5 whitespace-nowrap text-[1.95rem] font-semibold leading-[1.12] tracking-[0.01em] text-slate-900 [text-shadow:0_1px_0_rgba(255,255,255,0.45),0_10px_20px_rgba(52,74,128,0.14)] md:text-[2.35rem]">
              全学段AI交互式教学生成系统
            </h2>
            <p className="mt-6 max-w-none whitespace-nowrap text-[1.38rem] leading-[1.25] tracking-[0.01em] text-slate-600 md:text-[1.58rem]">
              让知识生长出界面 让交互渗透进思维
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Link href="/register">
                <Button className="rounded-2xl bg-gradient-to-r from-[#3267f2] to-[#2a59de] px-10 py-4 text-lg text-white shadow-[0_10px_24px_rgba(50,103,242,0.28)] transition-all duration-200 hover:-translate-y-0.5 hover:from-[#3b6ff5] hover:to-[#315fe3] hover:shadow-[0_14px_28px_rgba(50,103,242,0.34)]">
                  开始体验
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="outline" className="rounded-2xl border-slate-200 bg-white/78 px-10 py-4 text-lg text-slate-700 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:bg-white hover:shadow-md">
                  登录
                </Button>
              </Link>
            </div>
            </div>
          </div>

          <div className="lg:col-span-7">
            <div className="relative h-full min-h-[440px] md:min-h-[540px]">
              <div className="relative z-10 mx-auto mt-10 w-full max-w-[760px] lg:translate-x-8">
                <div className="relative overflow-visible bg-transparent">
                  <div>
                  <Image
                    src="/images/photo3-lite.png"
                    alt="AI课堂场景"
                    width={1200}
                    height={900}
                    priority
                    fetchPriority="high"
                    sizes="(max-width: 1024px) 100vw, 55vw"
                    className="mx-auto h-full max-h-[560px] w-full object-contain"
                  />
                </div>
                </div>
              </div>
            </div>
          </div>
        </section>
        <section className="relative mt-20">
          <div aria-hidden="true" className="pointer-events-none absolute left-1/2 -top-[11.55rem] z-10 h-36 w-[min(126vw,2550px)] -translate-x-1/2">
            <svg viewBox="0 0 1200 120" preserveAspectRatio="none" className="h-full w-full">
              <defs>
                <linearGradient id="glassRibbon" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="rgba(255,255,255,0.54)" />
                  <stop offset="40%" stopColor="rgba(255,255,255,0.22)" />
                  <stop offset="100%" stopColor="rgba(255,255,255,0.03)" />
                </linearGradient>
                <linearGradient id="glassStroke" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="rgba(255,255,255,0)" />
                  <stop offset="16%" stopColor="rgba(255,255,255,0.62)" />
                  <stop offset="50%" stopColor="rgba(238,246,255,0.98)" />
                  <stop offset="84%" stopColor="rgba(255,255,255,0.62)" />
                  <stop offset="100%" stopColor="rgba(255,255,255,0)" />
                </linearGradient>
              </defs>
              <path
                d="M0,42 C142,84 276,103 442,109 C532,113 570,127 600,127 C630,127 668,113 758,109 C924,103 1058,84 1200,42 L1200,74 C1058,100 924,115 758,119 C668,122 630,129 600,129 C570,129 532,122 442,119 C276,115 142,100 0,74 Z"
                fill="url(#glassRibbon)"
              />
              <path
                d="M0,42 C142,84 276,103 442,109 C532,113 570,127 600,127 C630,127 668,113 758,109 C924,103 1058,84 1200,42"
                fill="none"
                stroke="url(#glassStroke)"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <path
                d="M0,52 C142,92 276,110 442,115 C532,118 570,131 600,131 C630,131 668,118 758,115 C924,110 1058,92 1200,52"
                fill="none"
                stroke="rgba(255,255,255,0.26)"
                strokeWidth="1.15"
                strokeLinecap="round"
              />
            </svg>
          </div>
          <div
            aria-hidden="true"
            className="pointer-events-none absolute left-1/2 -top-[10rem] z-10 h-40 w-[min(134vw,2800px)] -translate-x-1/2 bg-[radial-gradient(ellipse_at_center,rgba(255,255,255,0.25)_0%,rgba(241,246,255,0.2)_33%,rgba(236,240,255,0.12)_55%,rgba(236,240,255,0)_100%)] blur-[5px]"
          />
          <div
            aria-hidden="true"
            className="pointer-events-none absolute left-1/2 -top-[6.1rem] z-10 h-20 w-[34rem] -translate-x-1/2 rounded-[999px] bg-[radial-gradient(ellipse_at_center,rgba(255,255,255,0.68)_0%,rgba(255,255,255,0.33)_36%,rgba(255,255,255,0.08)_60%,rgba(255,255,255,0)_100%)] blur-[4px]"
          />
          <button
            aria-label="Scroll down"
            onClick={() =>
              window.scrollTo({
                top: document.documentElement.scrollHeight,
                behavior: 'smooth'
              })
            }
            className="absolute left-1/2 -top-24 z-20 inline-flex h-14 w-14 -translate-x-1/2 items-center justify-center rounded-full border border-white/80 bg-white/90 text-slate-500 shadow-[0_14px_28px_rgba(66,88,145,0.2),inset_0_1px_0_rgba(255,255,255,0.45)] backdrop-blur-md transition-all duration-200 hover:-translate-y-0.5 hover:text-slate-700"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M7 9l5 5 5-5M7 4l5 5 5-5" />
            </svg>
          </button>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <div key={feature.title} className="flex min-h-[23rem] flex-col items-center rounded-2xl border border-slate-200/80 bg-white/90 px-8 py-9 text-center shadow-[0_14px_40px_rgba(40,50,90,0.08)]">
                <span className="inline-flex h-20 w-20 items-center justify-center overflow-hidden rounded-2xl shadow-lg">
                  <img src={feature.iconSrc} alt={`${feature.title} icon`} className="h-full w-full object-cover" />
                </span>
                <h3 className="mt-8 whitespace-nowrap text-[1.55rem] font-semibold tracking-tight text-slate-900 md:text-[1.72rem]">{feature.title}</h3>
                <p className="mt-3 text-sm font-semibold uppercase tracking-[0.16em] text-slate-500">{feature.subtitle}</p>
                <p className="mt-6 overflow-hidden text-[1rem] leading-[1.55] text-slate-500 [display:-webkit-box] [-webkit-box-orient:vertical] [-webkit-line-clamp:2]">{feature.description}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
