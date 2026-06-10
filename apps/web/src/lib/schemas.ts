import { z } from 'zod'

export const courseSummarySchema = z.object({
  course_id: z.string(),
  name: z.string(),
  materials_count: z.number(),
  stage: z.string(),
  due_items_count: z.number(),
  last_reviewed: z.string().nullable().optional(),
})

export const coursesResponseSchema = z.object({
  courses: z.array(courseSummarySchema),
})

export const dueItemSchema = z.object({
  id: z.string(),
  topic: z.string(),
  prompt: z.string(),
  due: z.string(),
  source: z.string(),
})

export const dueCourseSchema = z.object({
  course_id: z.string(),
  name: z.string(),
  items: z.array(dueItemSchema),
})

export const dueTodayResponseSchema = z.object({
  courses: z.array(dueCourseSchema),
})

export const materialFileSchema = z.object({
  id: z.string(),
  path: z.string(),
  name: z.string(),
  material_type: z.string(),
  ext: z.string(),
  status: z.string(),
  tags: z.array(z.string()).default([]),
})

export const materialsResponseSchema = z.object({
  course_id: z.string(),
  files: z.array(materialFileSchema),
})

export const evidenceSchema = z.object({
  source_file: z.string(),
  reason: z.string(),
})

export const prioritySchema = z.object({
  topic: z.string(),
  chapter: z.string().optional(),
  weight: z.number(),
  question_types: z.array(z.string()),
  evidence: z.array(evidenceSchema),
  recommended_action: z.string(),
})

export const examAnalysisResponseSchema = z.object({
  analysis_id: z.string(),
  course_id: z.string(),
  priorities_count: z.number(),
  confidence: z.string(),
  priorities: z.array(prioritySchema),
})

export const questionSchema = z.object({
  id: z.string(),
  prompt: z.string(),
  topic: z.string(),
  expected_answer: z.string().optional(),
  scoring_points: z.array(z.string()).optional(),
  time_limit_sec: z.number().optional(),
  course_id: z.string().optional(),
  question_type: z.string().optional(),
  difficulty: z.string().optional(),
  label: z.string().optional(),
})

export const sessionStartSchema = z.object({
  session_id: z.string(),
  question_index: z.number(),
  total_questions: z.number(),
  question: questionSchema,
})

export const gradingResultSchema = z.object({
  verdict: z.enum(['correct', 'partial', 'wrong']),
  score_hint: z.string(),
  covered_points: z.array(z.string()).default([]),
  omissions: z.array(z.string()).default([]),
  better_answer: z.string().default(''),
  follow_up_question: z.string().default(''),
  card_id: z.string().nullable().optional(),
  has_next: z.boolean().optional(),
  next_question: questionSchema.nullable().optional(),
  awaiting_rating: z.boolean().optional(),
})

export const rateResponseSchema = z.object({
  card_id: z.string().nullable().optional(),
  rating: z.string(),
  due: z.string(),
  has_next: z.boolean(),
  question_index: z.number().optional(),
  total_questions: z.number().optional(),
  next_question: questionSchema.nullable().optional(),
})

export const planResponseSchema = z.object({
  goal: z.string().optional(),
  minutes: z.number().nullable().optional(),
  days: z.number().nullable().optional(),
  first_action: z.string().optional(),
  plan_md: z.string(),
  course_id: z.string().optional(),
})

export const healthResponseSchema = z.object({
  status: z.string(),
})

export type CourseSummary = z.infer<typeof courseSummarySchema>
export type DueCourse = z.infer<typeof dueCourseSchema>
export type MaterialFile = z.infer<typeof materialFileSchema>
export type Priority = z.infer<typeof prioritySchema>
export type Question = z.infer<typeof questionSchema>
export type GradingResult = z.infer<typeof gradingResultSchema>
export type SessionStart = z.infer<typeof sessionStartSchema>
export type RateResponse = z.infer<typeof rateResponseSchema>
export type Rating = '忘了' | '困难' | '还行' | '很熟'

export const RATINGS = ['忘了', '困难', '还行', '很熟'] as const satisfies readonly Rating[]
