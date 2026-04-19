'use client'

import React, { useState } from 'react'

interface QRCodeHoverProps {
  qrCodePath?: string
  position?: 'right' | 'left'
  top?: string
}

export function QRCodeHover({
  qrCodePath = '/问卷二维码_0122.png',
  position = 'right',
  top = '50%'
}: QRCodeHoverProps) {
  const [isHovered, setIsHovered] = useState(false)

  return (
    <div
      className="fixed z-50"
      style={{
        [position]: '20px',
        top: top,
        transform: 'translateY(-50%)'
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Trigger Button/Icon */}
      <button
        className={`
          bg-blue-600 hover:bg-blue-700 text-white rounded-full
          shadow-lg transition-all duration-300 flex items-center justify-center
          ${isHovered ? 'w-12 h-12' : 'w-10 h-10'}
        `}
        aria-label="反馈二维码"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"
          />
        </svg>
      </button>

      {/* QR Code Popup */}
      <div
        className={`
          absolute bg-white rounded-lg shadow-2xl p-4
          transition-all duration-300 ease-in-out
          ${position === 'right' ? 'right-full mr-3' : 'left-full ml-3'}
          ${isHovered
            ? 'opacity-100 scale-100 pointer-events-auto'
            : 'opacity-0 scale-95 pointer-events-none'
          }
        `}
        style={{
          top: '50%',
          transform: 'translateY(-50%)',
          minWidth: '200px'
        }}
      >
        {/* QR Code Image */}
        <div className="relative">
          <img
            src={qrCodePath}
            alt="反馈问卷二维码"
            className="w-48 h-48 object-contain rounded-lg"
          />

          {/* Label */}
          <div className="mt-3 text-center">
            <p className="text-sm font-semibold text-gray-900 mb-1">
              3分钟填写反馈，领最多10元现金红包！
            </p>
            <p className="text-xs text-gray-500">
              感谢您的宝贵意见
            </p>
          </div>
        </div>

        {/* Arrow pointing to button */}
        <div
          className={`
            absolute top-1/2 -translate-y-1/2 w-0 h-0
            border-y-8 border-y-transparent
            ${position === 'right'
              ? '-right-4 border-l-8 border-l-white'
              : '-left-4 border-r-8 border-r-white'
            }
          `}
        />
      </div>
    </div>
  )
}
