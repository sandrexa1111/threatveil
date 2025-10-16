'use client'

import { useState } from 'react'

export default function Home() {
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; content: string }[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const sendMessage = async () => {
    if (!input.trim()) return
    const userMessage = { role: 'user' as const, content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    try {
      const res = await fetch(process.env.NEXT_PUBLIC_API_URL + '/api/v2/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage.content })
      })
      const data = await res.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.response || 'No response' }])
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error contacting Veil.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container mx-auto p-6 max-w-3xl">
      <h1 className="text-2xl font-semibold mb-4">Veil AI Security Analyst</h1>
      <div className="border rounded-lg bg-white p-4 h-[65vh] overflow-y-auto mb-4">
        {messages.length === 0 && (
          <div className="text-gray-500">Ask about vendor risks, recent threats, or remediation steps.</div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'} mb-2`}>
            <div className={`px-3 py-2 rounded-lg max-w-[80%] ${m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800'}`}>
              {m.content}
            </div>
          </div>
        ))}
        {loading && <div className="text-gray-400 italic">Veil is thinking…</div>}
      </div>
      <div className="flex gap-2">
        <input
          className="flex-1 border rounded-lg px-3 py-2"
          placeholder="Ask about vendor risks…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
        />
        <button
          className="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50"
          onClick={sendMessage}
          disabled={loading}
        >
          Send
        </button>
      </div>
    </main>
  )
}


