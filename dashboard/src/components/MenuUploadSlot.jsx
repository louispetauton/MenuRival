import React, { useRef, useState } from 'react'
import { Upload, CheckCircle, XCircle, RefreshCw, Loader } from 'lucide-react'

const ACCEPTED = '.pdf,.jpg,.jpeg,.png,.webp'

export default function MenuUploadSlot({ restaurantId, menuType, label, onParsed }) {
  const [state, setState] = useState('empty') // empty | uploading | done | error
  const [itemCount, setItemCount] = useState(0)
  const [errorMsg, setErrorMsg] = useState('')
  const inputRef = useRef(null)

  const handleFile = async (file) => {
    if (!file) return
    setState('uploading')
    const form = new FormData()
    form.append('restaurant_id', restaurantId)
    form.append('menu_type', menuType)
    form.append('file', file)
    try {
      const res = await fetch('/api/ingest/photo', { method: 'POST', body: form })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Upload failed')
      }
      const data = await res.json()
      setItemCount(data.item_count)
      setState('done')
      if (onParsed) onParsed(data)
    } catch (e) {
      setErrorMsg(e.message)
      setState('error')
    }
  }

  const onDrop = (e) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    handleFile(file)
  }

  const onFileChange = (e) => handleFile(e.target.files[0])

  if (state === 'uploading') {
    return (
      <div className="border border-slate-200 rounded-lg p-3 flex flex-col items-center justify-center gap-1 min-h-[80px] bg-indigo-50">
        <Loader className="w-4 h-4 text-indigo-500 animate-spin" />
        <span className="text-xs text-indigo-600">Parsing with Claude...</span>
      </div>
    )
  }

  if (state === 'done') {
    return (
      <div className="border border-emerald-200 rounded-lg p-3 flex flex-col items-center justify-center gap-1 min-h-[80px] bg-emerald-50">
        <CheckCircle className="w-4 h-4 text-emerald-500" />
        <span className="text-xs font-medium text-emerald-700">{itemCount} items</span>
        <button
          onClick={() => setState('empty')}
          className="text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1 mt-1"
        >
          <RefreshCw className="w-3 h-3" /> Re-upload
        </button>
      </div>
    )
  }

  if (state === 'error') {
    return (
      <div className="border border-red-200 rounded-lg p-3 flex flex-col items-center justify-center gap-1 min-h-[80px] bg-red-50">
        <XCircle className="w-4 h-4 text-red-500" />
        <span className="text-xs text-red-600 text-center">{errorMsg}</span>
        <button
          onClick={() => setState('empty')}
          className="text-xs text-slate-500 hover:text-slate-700 mt-1"
        >
          Try again
        </button>
      </div>
    )
  }

  return (
    <div
      className="border-2 border-dashed border-slate-200 rounded-lg p-3 flex flex-col items-center justify-center gap-1 min-h-[80px] cursor-pointer hover:border-indigo-300 hover:bg-indigo-50 transition-colors"
      onClick={() => inputRef.current?.click()}
      onDrop={onDrop}
      onDragOver={(e) => e.preventDefault()}
    >
      <Upload className="w-4 h-4 text-slate-400" />
      <span className="text-xs font-medium text-slate-500">{label}</span>
      <span className="text-xs text-slate-400">Drop PDF or image</span>
      <input ref={inputRef} type="file" accept={ACCEPTED} className="hidden" onChange={onFileChange} />
    </div>
  )
}
