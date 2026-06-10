import type { ZodType } from 'zod'
import { ZodError } from 'zod'

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'
const FETCH_TIMEOUT_MS = 8_000

export class ApiConnectionError extends Error {
  constructor(message = '无法连接后端 API') {
    super(message)
    this.name = 'ApiConnectionError'
  }
}

export class ApiValidationError extends Error {
  constructor(message = 'API 响应格式异常') {
    super(message)
    this.name = 'ApiValidationError'
  }
}

export async function fetchValidated<T>(
  url: string,
  schema: ZodType<T>,
  init?: RequestInit,
): Promise<T> {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS)
  try {
    const response = await fetch(`${API_BASE}${url}`, {
      ...init,
      signal: controller.signal,
    })
    if (!response.ok) {
      const text = await response.text()
      throw new Error(text || response.statusText)
    }
    const json: unknown = await response.json()
    return schema.parse(json)
  } catch (error) {
    if (error instanceof ZodError) {
      console.error('API schema mismatch:', error.flatten())
      throw new ApiValidationError('后端返回数据格式不符合预期')
    }
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiConnectionError('请求超时，请确认后端是否在 localhost:8000 运行')
    }
    if (error instanceof TypeError) {
      throw new ApiConnectionError()
    }
    throw error
  } finally {
    window.clearTimeout(timer)
  }
}

export async function fetchJson(url: string, init?: RequestInit): Promise<unknown> {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS)
  try {
    const response = await fetch(`${API_BASE}${url}`, {
      ...init,
      signal: controller.signal,
    })
    if (!response.ok) {
      const text = await response.text()
      throw new Error(text || response.statusText)
    }
    return await response.json()
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiConnectionError('请求超时，请确认后端是否在 localhost:8000 运行')
    }
    if (error instanceof TypeError) {
      throw new ApiConnectionError()
    }
    throw error
  } finally {
    window.clearTimeout(timer)
  }
}
