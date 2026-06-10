import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Course } from './pages/Course'
import { Dashboard } from './pages/Dashboard'
import { ExamAnalysis } from './pages/ExamAnalysis'
import { Materials } from './pages/Materials'
import { PlanPage } from './pages/PlanPage'
import { QuizSession } from './pages/QuizSession'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="course/:id" element={<Course />} />
          <Route path="course/:id/materials" element={<Materials />} />
          <Route path="course/:id/analysis" element={<ExamAnalysis />} />
          <Route path="course/:id/plan" element={<PlanPage />} />
          <Route path="course/:id/quiz" element={<QuizSession />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
