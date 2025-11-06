import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import FlinkOMTPage from './pages/FlinkOMTPage'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/flink/flinkomt" replace />} />
          <Route path="flink/flinkomt" element={<FlinkOMTPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
