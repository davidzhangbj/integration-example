import { useState } from 'react'
import axios from 'axios'

function FlinkOMTPage() {
  const [step, setStep] = useState(1) // 1: 配置, 2: 运行中, 3: 完成
  const [status, setStatus] = useState('idle') // idle, running, success, error
  const [jobId, setJobId] = useState(null)
  const [logs, setLogs] = useState([])
  const [sqlQuery, setSqlQuery] = useState({ starrocks: '', oceanbase: '' })
  const [queryResults, setQueryResults] = useState({ starrocks: null, oceanbase: null })
  const [queryLoading, setQueryLoading] = useState({ starrocks: false, oceanbase: false })
  const [connectionTestStatus, setConnectionTestStatus] = useState({ starrocks: null, oceanbase: null, flink: null })
  const [connectionTestLoading, setConnectionTestLoading] = useState({ starrocks: false, oceanbase: false, flink: false })
  const [config, setConfig] = useState({
    starrocks: {
      host: 'localhost',
      port: '9030',
      username: 'root',
      password: '123456',
      tables: 'test[1-2].orders[0-9]' // 迁移的表，格式可以是 db.table 或 db[1-2].table[1-2]
    },
    oceanbase: {
      host: 'localhost',
      port: '2881',
      username: 'root@test',
      password: '123456'
    },
    flinkOMT: {
      checkpointInterval: '60000',
      parallelism: '1'
    }
  })
  const [showPassword, setShowPassword] = useState({
    starrocks: false,
    oceanbase: false
  })

  const handleConfigChange = (section, field, value) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }))
  }

  const validateConfig = () => {
    const { starrocks, oceanbase } = config
    if (!starrocks.host || !starrocks.port || !starrocks.username || 
        !starrocks.tables) {
      alert('请填写完整的 StarRocks 配置')
      return false
    }
    if (!oceanbase.host || !oceanbase.port || !oceanbase.username) {
      alert('请填写完整的 OceanBase 配置')
      return false
    }
    return true
  }

  const startJob = async () => {
    if (!validateConfig()) return

    setStatus('running')
    setStep(2)
    setLogs([{ time: new Date().toLocaleTimeString(), message: '正在启动 FlinkOMT 任务...' }])

    try {
      const response = await axios.post('/api/start-job', config)
      setJobId(response.data.jobId)
      setLogs(prev => [...prev, {
        time: new Date().toLocaleTimeString(),
        message: `任务已提交，Job ID: ${response.data.jobId}`
      }])
      
      // 开始轮询任务状态
      pollJobStatus(response.data.jobId)
    } catch (error) {
      setStatus('error')
      setLogs(prev => [...prev, {
        time: new Date().toLocaleTimeString(),
        message: `错误: ${error.response?.data?.error || error.message}`
      }])
    }
  }

  const pollJobStatus = async (id) => {
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`/api/job-status/${id}`)
        const jobStatus = response.data
        
        setLogs(prev => {
          const newLogs = [...prev]
          if (jobStatus.logs && jobStatus.logs.length > 0) {
            jobStatus.logs.forEach(log => {
              if (!newLogs.find(l => l.message === log && l.time === jobStatus.lastUpdate)) {
                newLogs.push({
                  time: jobStatus.lastUpdate || new Date().toLocaleTimeString(),
                  message: log
                })
              }
            })
          }
          return newLogs.slice(-50) // 只保留最近50条日志
        })

        if (jobStatus.status === 'RUNNING') {
          setStatus('running')
        } else if (jobStatus.status === 'FINISHED') {
          setStatus('success')
          setStep(3)
          clearInterval(interval)
        } else if (jobStatus.status === 'FAILED' || jobStatus.status === 'CANCELED') {
          setStatus('error')
          clearInterval(interval)
        }
      } catch (error) {
        console.error('获取任务状态失败:', error)
      }
    }, 2000) // 每2秒查询一次

    // 10分钟后停止轮询
    setTimeout(() => clearInterval(interval), 600000)
  }

  const stopJob = async () => {
    if (!jobId) return

    try {
      await axios.post(`/api/stop-job/${jobId}`)
      setStatus('idle')
      setStep(1)
      setJobId(null)
      setLogs([{ time: new Date().toLocaleTimeString(), message: '任务已停止' }])
    } catch (error) {
      alert(`停止任务失败: ${error.response?.data?.error || error.message}`)
    }
  }

  const reset = () => {
    setStep(1)
    setStatus('idle')
    setJobId(null)
    setLogs([])
  }

  const testConnection = async (type) => {
    setConnectionTestLoading(prev => ({ ...prev, [type]: true }))
    setConnectionTestStatus(prev => ({ ...prev, [type]: null }))

    try {
      if (type === 'flink') {
        // Flink 连接测试不需要配置参数
        const response = await axios.get('/api/health/flink')
        setConnectionTestStatus(prev => ({
          ...prev,
          flink: {
            connected: response.data.connected,
            message: response.data.message || response.data.error,
            error: response.data.error
          }
        }))
      } else {
        // StarRocks 和 OceanBase 需要配置参数
        const response = await axios.post(`/api/health/${type}`, {
          [type]: config[type]
        })
        setConnectionTestStatus(prev => ({
          ...prev,
          [type]: {
            connected: response.data.connected,
            message: response.data.message || response.data.error,
            error: response.data.error
          }
        }))
      }
    } catch (error) {
      setConnectionTestStatus(prev => ({
        ...prev,
        [type]: {
          connected: false,
          message: error.response?.data?.error || error.message,
          error: error.response?.data?.error || error.message
        }
      }))
    } finally {
      setConnectionTestLoading(prev => ({ ...prev, [type]: false }))
    }
  }

  const renderConnectionTestResult = (type) => {
    const status = connectionTestStatus[type]
    if (!status) return null

    if (status.connected) {
      return (
        <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded-md">
          <div className="flex items-center text-green-800 text-sm">
            <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            {status.message || '连接成功'}
          </div>
        </div>
      )
    } else {
      return (
        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center text-red-800 text-sm">
            <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            {status.error || status.message || '连接失败'}
          </div>
        </div>
      )
    }
  }

  const executeSql = async (dbType) => {
    const sql = sqlQuery[dbType].trim()
    if (!sql) {
      alert('请输入 SQL 语句')
      return
    }

    setQueryLoading(prev => ({ ...prev, [dbType]: true }))
    setQueryResults(prev => ({ ...prev, [dbType]: null }))

    try {
      const response = await axios.post('/api/execute-sql', {
        dbType,
        sql,
        config: config[dbType]
      })

      setQueryResults(prev => ({ ...prev, [dbType]: response.data }))
    } catch (error) {
      setQueryResults(prev => ({
        ...prev,
        [dbType]: { error: error.response?.data?.error || error.message }
      }))
    } finally {
      setQueryLoading(prev => ({ ...prev, [dbType]: false }))
    }
  }

  const renderQueryResult = (dbType) => {
    const result = queryResults[dbType]
    if (!result) return null

    if (result.error) {
      return (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="text-red-800 font-medium">执行失败</div>
          <div className="text-red-600 text-sm mt-1">{result.error}</div>
        </div>
      )
    }

    if (result.success && result.columns && result.rows) {
      return (
        <div className="mt-4 border rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-4 py-2 border-b">
            <span className="text-sm font-medium text-gray-700">
              查询结果 ({result.rowCount} 行)
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {result.columns.map((col, idx) => (
                    <th
                      key={idx}
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {result.rows.map((row, rowIdx) => (
                  <tr key={rowIdx}>
                    {result.columns.map((col, colIdx) => (
                      <td
                        key={colIdx}
                        className="px-4 py-3 whitespace-nowrap text-sm text-gray-900"
                      >
                        {row[col] !== null && row[col] !== undefined
                          ? String(row[col])
                          : 'NULL'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )
    }

    if (result.success && result.message) {
      return (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="text-green-800">{result.message}</div>
        </div>
      )
    }

    return null
  }

  return (
    <div className="min-h-full bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="container mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            FlinkOMT Demo
          </h1>
          <p className="text-lg text-gray-600">
            StarRocks → OceanBase 数据同步演示
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-lg shadow-xl p-6 max-w-6xl mx-auto">
          {/* Progress Steps */}
          <div className="flex justify-center mb-8">
            <div className="flex items-center space-x-4">
              <div className={`flex items-center ${step >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
                <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 ${
                  step >= 1 ? 'border-blue-600 bg-blue-50' : 'border-gray-300'
                }`}>
                  1
                </div>
                <span className="ml-2 font-medium">配置连接</span>
              </div>
              <div className={`w-16 h-1 ${step >= 2 ? 'bg-blue-600' : 'bg-gray-300'}`}></div>
              <div className={`flex items-center ${step >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
                <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 ${
                  step >= 2 ? 'border-blue-600 bg-blue-50' : 'border-gray-300'
                }`}>
                  2
                </div>
                <span className="ml-2 font-medium">运行任务</span>
              </div>
              <div className={`w-16 h-1 ${step >= 3 ? 'bg-blue-600' : 'bg-gray-300'}`}></div>
              <div className={`flex items-center ${step >= 3 ? 'text-blue-600' : 'text-gray-400'}`}>
                <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 ${
                  step >= 3 ? 'border-blue-600 bg-blue-50' : 'border-gray-300'
                }`}>
                  3
                </div>
                <span className="ml-2 font-medium">完成</span>
              </div>
            </div>
          </div>

          {/* Configuration Form */}
          {step === 1 && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* StarRocks Config */}
                <div className="border rounded-lg p-4 bg-gray-50">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold text-gray-800 flex items-center">
                      <span className="w-3 h-3 bg-blue-500 rounded-full mr-2"></span>
                      StarRocks 源数据库
                    </h2>
                    <button
                      onClick={() => testConnection('starrocks')}
                      disabled={connectionTestLoading.starrocks || !config.starrocks.host || !config.starrocks.port}
                      className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {connectionTestLoading.starrocks ? '测试中...' : '测试连接'}
                    </button>
                  </div>
                  {renderConnectionTestResult('starrocks')}
                  <div className="space-y-3 mt-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">主机</label>
                      <input
                        type="text"
                        value={config.starrocks.host}
                        onChange={(e) => handleConfigChange('starrocks', 'host', e.target.value)}
                        className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">端口</label>
                      <input
                        type="text"
                        value={config.starrocks.port}
                        onChange={(e) => handleConfigChange('starrocks', 'port', e.target.value)}
                        className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                      <input
                        type="text"
                        value={config.starrocks.username}
                        onChange={(e) => handleConfigChange('starrocks', 'username', e.target.value)}
                        className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">密码</label>
                      <div className="relative">
                        <input
                          type={showPassword.starrocks ? "text" : "password"}
                          value={config.starrocks.password}
                          onChange={(e) => handleConfigChange('starrocks', 'password', e.target.value)}
                          className="w-full px-3 py-2 pr-10 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(prev => ({ ...prev, starrocks: !prev.starrocks }))}
                          className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 focus:outline-none"
                        >
                          {showPassword.starrocks ? (
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.29 3.29m0 0A9.97 9.97 0 015 12c0 1.657.458 3.207 1.257 4.532M3 3l18 18" />
                            </svg>
                          ) : (
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                          )}
                        </button>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center">
                        迁移的表
                        <div className="relative group ml-2">
                          <svg
                            className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-help"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z"
                              clipRule="evenodd"
                            />
                          </svg>
                          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                            格式为database.table，支持正则表达式
                            <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
                              <div className="border-4 border-transparent border-t-gray-800"></div>
                            </div>
                          </div>
                        </div>
                      </label>
                      <input
                        type="text"
                        value={config.starrocks.tables}
                        onChange={(e) => handleConfigChange('starrocks', 'tables', e.target.value)}
                        className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="例如: db1.table1 或者 db[1-2].table[1-2]"
                      />
                    </div>
                  </div>
                </div>

                {/* OceanBase Config */}
                <div className="border rounded-lg p-4 bg-gray-50">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold text-gray-800 flex items-center">
                      <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
                      OceanBase 目标数据库
                    </h2>
                    <button
                      onClick={() => testConnection('oceanbase')}
                      disabled={connectionTestLoading.oceanbase || !config.oceanbase.host || !config.oceanbase.port}
                      className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {connectionTestLoading.oceanbase ? '测试中...' : '测试连接'}
                    </button>
                  </div>
                  {renderConnectionTestResult('oceanbase')}
                  <div className="space-y-3 mt-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">主机</label>
                      <input
                        type="text"
                        value={config.oceanbase.host}
                        onChange={(e) => handleConfigChange('oceanbase', 'host', e.target.value)}
                        className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">端口</label>
                      <input
                        type="text"
                        value={config.oceanbase.port}
                        onChange={(e) => handleConfigChange('oceanbase', 'port', e.target.value)}
                        className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                      <input
                        type="text"
                        value={config.oceanbase.username}
                        onChange={(e) => handleConfigChange('oceanbase', 'username', e.target.value)}
                        className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">密码</label>
                      <div className="relative">
                        <input
                          type={showPassword.oceanbase ? "text" : "password"}
                          value={config.oceanbase.password}
                          onChange={(e) => handleConfigChange('oceanbase', 'password', e.target.value)}
                          className="w-full px-3 py-2 pr-10 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(prev => ({ ...prev, oceanbase: !prev.oceanbase }))}
                          className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 focus:outline-none"
                        >
                          {showPassword.oceanbase ? (
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.29 3.29m0 0A9.97 9.97 0 015 12c0 1.657.458 3.207 1.257 4.532M3 3l18 18" />
                            </svg>
                          ) : (
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* FlinkOMT Advanced Config */}
              <div className="border rounded-lg p-4 bg-gray-50">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-gray-800">FlinkOMT 高级配置</h2>
                  <button
                    onClick={() => testConnection('flink')}
                    disabled={connectionTestLoading.flink}
                    className="px-3 py-1.5 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {connectionTestLoading.flink ? '测试中...' : '测试 Flink 集群'}
                  </button>
                </div>
                {renderConnectionTestResult('flink')}
                <div className="grid grid-cols-2 gap-4 mt-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">检查点间隔 (ms)</label>
                    <input
                      type="text"
                      value={config.flinkOMT.checkpointInterval}
                      onChange={(e) => handleConfigChange('flinkOMT', 'checkpointInterval', e.target.value)}
                      className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">并行度</label>
                    <input
                      type="text"
                      value={config.flinkOMT.parallelism}
                      onChange={(e) => handleConfigChange('flinkOMT', 'parallelism', e.target.value)}
                      className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-center">
                <button
                  onClick={startJob}
                  className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-lg shadow-lg"
                >
                  启动同步任务
                </button>
              </div>

              {/* SQL Query Section */}
              <div className="mt-8 border-t pt-6">
                <h2 className="text-xl font-semibold mb-4 text-gray-800">数据库查询工具</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* StarRocks Query */}
                  <div className="border rounded-lg p-4 bg-gray-50">
                    <div className="mb-3">
                      <h3 className="font-medium text-gray-800 flex items-center">
                        <span className="w-3 h-3 bg-blue-500 rounded-full mr-2"></span>
                        StarRocks
                      </h3>
                    </div>
                    <textarea
                      value={sqlQuery.starrocks}
                      onChange={(e) => setSqlQuery(prev => ({ ...prev, starrocks: e.target.value }))}
                      placeholder="输入 SQL 语句，例如：SELECT * FROM test1.orders1 LIMIT 10"
                      className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                      rows="4"
                    />
                    <button
                      onClick={() => executeSql('starrocks')}
                      disabled={queryLoading.starrocks || !sqlQuery.starrocks.trim()}
                      className="mt-3 w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {queryLoading.starrocks ? '执行中...' : '执行 SQL'}
                    </button>
                    {renderQueryResult('starrocks')}
                  </div>

                  {/* OceanBase Query */}
                  <div className="border rounded-lg p-4 bg-gray-50">
                    <div className="mb-3">
                      <h3 className="font-medium text-gray-800 flex items-center">
                        <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
                        OceanBase
                      </h3>
                    </div>
                    <textarea
                      value={sqlQuery.oceanbase}
                      onChange={(e) => setSqlQuery(prev => ({ ...prev, oceanbase: e.target.value }))}
                      placeholder="输入 SQL 语句，例如：SELECT * FROM test1.orders1 LIMIT 10"
                      className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 font-mono text-sm"
                      rows="4"
                    />
                    <button
                      onClick={() => executeSql('oceanbase')}
                      disabled={queryLoading.oceanbase || !sqlQuery.oceanbase.trim()}
                      className="mt-3 w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {queryLoading.oceanbase ? '执行中...' : '执行 SQL'}
                    </button>
                    {renderQueryResult('oceanbase')}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Running Status */}
          {step === 2 && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="inline-flex items-center px-6 py-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-3"></div>
                  <span className="text-lg font-medium text-blue-800">任务运行中...</span>
                </div>
                {jobId && (
                  <p className="mt-2 text-sm text-gray-600">Job ID: {jobId}</p>
                )}
              </div>

              {/* Logs */}
              <div className="bg-gray-900 rounded-lg p-4 h-96 overflow-y-auto">
                <div className="text-green-400 font-mono text-sm space-y-1">
                  {logs.map((log, idx) => (
                    <div key={idx} className="flex">
                      <span className="text-gray-500 mr-3">[{log.time}]</span>
                      <span>{log.message}</span>
                    </div>
                  ))}
                  {logs.length === 0 && (
                    <div className="text-gray-500">等待日志输出...</div>
                  )}
                </div>
              </div>

              <div className="flex justify-center space-x-4">
                <button
                  onClick={stopJob}
                  className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                >
                  停止任务
                </button>
                <button
                  onClick={reset}
                  className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  重置
                </button>
              </div>
            </div>
          )}

          {/* Success */}
          {step === 3 && (
            <div className="text-center space-y-6">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full">
                <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-800">同步任务完成！</h2>
              <p className="text-gray-600">数据已成功从 StarRocks 同步到 OceanBase</p>
              <button
                onClick={reset}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                重新开始
              </button>
            </div>
          )}
        </div>

        {/* Info Card */}
        <div className="mt-6 bg-white rounded-lg shadow-xl p-6 max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-800">关于 FlinkOMT</h3>
            <a
              href="https://www.oceanbase.com/docs/common-oceanbase-database-cn-1000000003487323"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center text-blue-600 hover:text-blue-800 transition-colors text-sm font-medium"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              查看文档
              <svg className="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
          </div>
          <div className="text-gray-600 space-y-2 text-sm">
            <p>• FlinkOMT 是 Apache Flink 的一个扩展，用于捕获数据库的变更数据</p>
            <p>• 本演示展示了如何使用 FlinkOMT 将数据从 StarRocks 实时同步到 OceanBase</p>
            <p>• 支持全量同步和增量同步，可以实时捕获源数据库的变更</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default FlinkOMTPage

