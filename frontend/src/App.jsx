import React from 'react'

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 text-center">
      <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 max-w-lg w-full">
        <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4 font-bold text-xl">
          BF
        </div>
        <h1 className="text-2xl font-bold text-slate-800">BillFlow Dashboard</h1>
        <p className="text-slate-500 mt-2 text-sm">
          Subscription & Billing Automation System using Recurring Revenue Model
        </p>
        <div className="mt-6 p-4 bg-purple-50 rounded-lg text-purple-700 text-xs font-semibold">
          🚀 Frontend initialized and connected to API backend
        </div>
      </div>
    </div>
  )
}
