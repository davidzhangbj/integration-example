import { useState } from 'react'
import { Outlet, NavLink } from 'react-router-dom'
import './Layout.css'

function Layout() {
  const [isFlinkOpen, setIsFlinkOpen] = useState(true)

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col shadow-sm">
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-800">OceanBase</h1>
          <p className="text-sm text-gray-500">集成工具演示</p>
        </div>
        
        <nav className="flex-1 overflow-y-auto p-4">
          {/* Flink Menu */}
          <div className="mb-2">
            <button
              onClick={() => setIsFlinkOpen(!isFlinkOpen)}
              className="w-full flex items-center justify-between px-3 py-2 text-gray-700 hover:bg-gray-50 rounded-lg transition-colors font-medium"
            >
              <span>Flink</span>
              <svg
                className={`w-4 h-4 transition-transform ${isFlinkOpen ? 'rotate-90' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
            
            {/* Flink Submenu */}
            {isFlinkOpen && (
              <div className="ml-4 mt-1">
                <NavLink
                  to="/flink/flinkomt"
                  className={({ isActive }) =>
                    `block px-3 py-2 text-sm rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-50 text-blue-700 font-medium'
                        : 'text-gray-600 hover:bg-gray-50'
                    }`
                  }
                >
                  FlinkOMT
                </NavLink>
              </div>
            )}
          </div>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout

