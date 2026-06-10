import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useRateAnswer, useStartSession, useSubmitAnswer } from '@/api/client'
import { QuizCard } from '@/components/QuizCard'
import { RatingButtonGroup } from '@/components/RatingButton'
import { ScoreCard } from '@/components/ScoreCard'
import { Button } from '@/components/ui/button'
import type { GradingResult, Question, Rating } from '@/lib/schemas'

type QuizPhase = 'loading' | 'answering' | 'grading' | 'rated' | 'done'

export function QuizSession() {
  const { id = '' } = useParams()
  const start = useStartSession()
  const submit = useSubmitAnswer()
  const rate = useRateAnswer()

  const [phase, setPhase] = useState<QuizPhase>('loading')
  const [sessionId, setSessionId] = useState('')
  const [question, setQuestion] = useState<Question | null>(null)
  const [index, setIndex] = useState(0)
  const [total, setTotal] = useState(0)
  const [answer, setAnswer] = useState('')
  const [result, setResult] = useState<GradingResult | null>(null)
  const [selectedRating, setSelectedRating] = useState<Rating | null>(null)
  const [flipped, setFlipped] = useState(false)

  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const startedRef = useRef(false)
  const nextBtnRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!id || startedRef.current) return
    startedRef.current = true
    start.mutate(
      { courseId: id, source: 'generated', limit: 5 },
      {
        onSuccess: (data) => {
          setSessionId(data.session_id)
          setQuestion(data.question)
          setIndex(data.question_index)
          setTotal(data.total_questions)
          setPhase('answering')
        },
        onError: () => setPhase('done'),
      },
    )
  }, [id, start])

  useEffect(() => {
    if (phase === 'answering') {
      textareaRef.current?.focus()
    }
  }, [phase, question])

  const handleSubmit = useCallback(() => {
    if (!sessionId || !answer.trim() || phase !== 'answering') return
    setPhase('grading')
    submit.mutate(
      { sessionId, answer },
      {
        onSuccess: (data) => {
          setResult(data)
          setFlipped(true)
          setPhase('rated')
        },
        onError: () => setPhase('answering'),
      },
    )
  }, [sessionId, answer, phase, submit])

  const handleRate = useCallback(
    (rating: Rating) => {
      if (!sessionId || phase !== 'rated') return
      setSelectedRating(rating)
      rate.mutate(
        { sessionId, rating, cardId: result?.card_id },
        {
          onSuccess: (data) => {
            if (!data.has_next) {
              setPhase('done')
              return
            }
            if (data.next_question) {
              setQuestion(data.next_question)
              setIndex(data.question_index ?? index + 1)
            }
            setAnswer('')
            setResult(null)
            setSelectedRating(null)
            setFlipped(false)
            setPhase('answering')
          },
        },
      )
    },
    [sessionId, phase, rate, result?.card_id, index],
  )

  const handleNextWithoutRating = useCallback(() => {
    if (selectedRating) return
    handleRate('还行')
  }, [selectedRating, handleRate])

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Enter' || event.shiftKey) return
      const target = event.target as HTMLElement
      if (target.tagName === 'TEXTAREA' && phase === 'answering') {
        event.preventDefault()
        handleSubmit()
        return
      }
      if (phase === 'rated' && !rate.isPending) {
        if (selectedRating) return
        event.preventDefault()
        handleRate('还行')
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [phase, handleSubmit, handleRate, selectedRating, rate.isPending])

  if (phase === 'loading' || start.isPending) {
    return <p className="type-muted">正在加载题目…</p>
  }

  if (start.isError) {
    return (
      <div className="space-y-4 max-w-2xl">
        <p className="text-[var(--destructive)]">
          无法开始练习：请先在课程页生成变式题。
        </p>
        <Button asChild variant="outline">
          <Link to={`/course/${id}`}>返回课程</Link>
        </Button>
      </div>
    )
  }

  if (phase === 'done') {
    return (
      <div className="max-w-2xl space-y-4">
        <h1 className="type-page">本轮练习完成</h1>
        <p className="type-muted">
          错题已自动写入 mistake-log 和 cards.yaml。
        </p>
        <Button asChild>
          <Link to={`/course/${id}`}>返回课程</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center justify-between type-muted">
        <span>
          第 {index}/{total} 题
        </span>
        <Link to={`/course/${id}`} className="hover:text-[var(--foreground)]">
          退出
        </Link>
      </div>
      <div className="h-1.5 rounded-full bg-[var(--muted)] overflow-hidden">
        <div
          className="h-full bg-[var(--primary)] transition-all duration-500 ease-out"
          style={{ width: `${(index / total) * 100}%` }}
        />
      </div>

      <QuizCard
        flipped={flipped}
        front={
          question ? (
            <div>
              <p className="type-muted uppercase tracking-wide mb-3">
                {question.topic}
              </p>
              <p className="type-question">{question.prompt}</p>
              <textarea
                ref={textareaRef}
                className="type-input mt-4 w-full min-h-32 rounded-md border border-[var(--border)] bg-[var(--background)] p-3 focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                placeholder="输入你的答案…"
                value={answer}
                disabled={phase !== 'answering'}
                onChange={(event) => setAnswer(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault()
                    handleSubmit()
                  }
                }}
              />
              <Button
                className="mt-4"
                disabled={submit.isPending || !answer.trim() || phase !== 'answering'}
                onClick={handleSubmit}
              >
                {submit.isPending ? '判分中…' : '提交答案'}
              </Button>
              <p className="type-muted mt-2">
                Enter 提交 · Shift+Enter 换行
              </p>
            </div>
          ) : null
        }
        back={
          result ? (
            <div className="space-y-5">
              <ScoreCard result={result} />
              <div>
                <p className="font-medium mb-2">掌握程度</p>
                <RatingButtonGroup
                  value={selectedRating}
                  onSelect={handleRate}
                  disabled={rate.isPending}
                />
                <p className="type-muted mt-3">
                  选择评分后自动下一题 · Enter 默认「还行」
                </p>
              </div>
              <Button
                ref={nextBtnRef}
                className="sr-only"
                tabIndex={-1}
                onClick={handleNextWithoutRating}
              >
                下一题
              </Button>
            </div>
          ) : null
        }
      />
    </div>
  )
}
