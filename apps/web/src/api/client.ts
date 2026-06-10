import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  ApiConnectionError,
  ApiValidationError,
  fetchJson,
  fetchValidated,
} from '@/lib/api'
import {
  coursesResponseSchema,
  dueTodayResponseSchema,
  examAnalysisResponseSchema,
  gradingResultSchema,
  materialsResponseSchema,
  planResponseSchema,
  rateResponseSchema,
  sessionStartSchema,
  type Rating,
} from '@/lib/schemas'

export { ApiConnectionError, ApiValidationError }

function onMutationError(error: unknown) {
  if (error instanceof ApiConnectionError) {
    toast.error('后端未连接', { description: error.message })
    return
  }
  if (error instanceof ApiValidationError) {
    toast.error('数据格式异常', { description: error.message })
    return
  }
  if (error instanceof Error) {
    toast.error('操作失败', { description: error.message })
  }
}

export function useCourses() {
  return useQuery({
    queryKey: ['courses'],
    queryFn: () => fetchValidated('/courses', coursesResponseSchema),
    retry: (failureCount, error) =>
      error instanceof ApiConnectionError ? failureCount < 1 : failureCount < 2,
  })
}

export function useDueToday(subject?: string) {
  const query = subject ? `?subject=${encodeURIComponent(subject)}` : ''
  return useQuery({
    queryKey: ['due', subject ?? 'all'],
    queryFn: () => fetchValidated(`/due-today${query}`, dueTodayResponseSchema),
  })
}

export function useMaterials(courseId: string) {
  return useQuery({
    queryKey: ['materials', courseId],
    queryFn: () =>
      fetchValidated(`/courses/${courseId}/materials`, materialsResponseSchema),
    enabled: Boolean(courseId),
  })
}

export function useAnalysis(courseId: string) {
  return useQuery({
    queryKey: ['analysis', courseId],
    queryFn: () =>
      fetchValidated(
        `/courses/${courseId}/exam-analysis/latest`,
        examAnalysisResponseSchema,
      ),
    enabled: Boolean(courseId),
    retry: false,
  })
}

export function usePlan(courseId: string) {
  return useQuery({
    queryKey: ['plan', courseId],
    queryFn: () => fetchValidated(`/courses/${courseId}/plan`, planResponseSchema),
    enabled: Boolean(courseId),
    retry: false,
  })
}

export function useAnalyzeExam(courseId: string) {
  const client = useQueryClient()
  return useMutation({
    mutationFn: () =>
      fetchJson(`/courses/${courseId}/exam-analysis?goal=pass`, {
        method: 'POST',
      }),
    onSuccess: () => {
      toast.success('试卷分析完成')
      void client.invalidateQueries({ queryKey: ['analysis', courseId] })
      void client.invalidateQueries({ queryKey: ['courses'] })
    },
    onError: onMutationError,
  })
}

export function useGenerateQuestions(courseId: string) {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (count?: number) =>
      fetchJson(`/courses/${courseId}/questions?count=${count ?? 5}`, {
        method: 'POST',
      }),
    onSuccess: () => {
      toast.success('变式题已生成')
      void client.invalidateQueries({ queryKey: ['courses'] })
    },
    onError: onMutationError,
  })
}

export function useMakePlan(courseId: string) {
  const client = useQueryClient()
  return useMutation({
    mutationFn: () =>
      fetchJson(`/courses/${courseId}/plan?minutes=90&goal=pass`, {
        method: 'POST',
      }),
    onSuccess: () => {
      toast.success('复习计划已生成')
      void client.invalidateQueries({ queryKey: ['plan', courseId] })
    },
    onError: onMutationError,
  })
}

export function useStartSession() {
  return useMutation({
    mutationFn: ({
      courseId,
      source = 'generated',
      limit = 5,
    }: {
      courseId: string
      source?: string
      limit?: number
    }) =>
      fetchValidated(
        `/review-session/start?course_id=${courseId}&source=${source}&limit=${limit}`,
        sessionStartSchema,
        { method: 'POST' },
      ),
    onError: onMutationError,
  })
}

export function useSubmitAnswer() {
  return useMutation({
    mutationFn: ({
      sessionId,
      answer,
    }: {
      sessionId: string
      answer: string
    }) =>
      fetchValidated(
        `/review-session/answer?session_id=${sessionId}&answer=${encodeURIComponent(answer)}`,
        gradingResultSchema,
        { method: 'POST' },
      ),
    onError: onMutationError,
  })
}

export function useRateAnswer() {
  return useMutation({
    mutationFn: ({
      sessionId,
      rating,
      cardId,
    }: {
      sessionId: string
      rating: Rating
      cardId?: string | null
    }) => {
      const params = new URLSearchParams({
        session_id: sessionId,
        rating,
      })
      if (cardId) params.set('card_id', cardId)
      return fetchValidated(
        `/review-session/rate?${params.toString()}`,
        rateResponseSchema,
        { method: 'POST' },
      )
    },
    onError: onMutationError,
  })
}

export function useAgentRun() {
  return useMutation({
    mutationFn: ({
      courseId,
      message,
    }: {
      courseId: string
      message: string
    }) =>
      fetchJson(
        `/agent/run?course_id=${courseId}&message=${encodeURIComponent(message)}&goal=pass`,
        { method: 'POST' },
      ),
    onSuccess: () => toast.success('Agent 已执行'),
    onError: onMutationError,
  })
}
