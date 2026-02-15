import fs from 'fs'
import path from 'path'

/**
 * Vite plugin to log API responses to a local file for testing purposes.
 * Only active in development mode.
 */
export function apiLoggerPlugin() {
  const logFile = path.resolve(process.cwd(), 'api-logs.txt')
  
  // Clear log file on startup
  fs.writeFileSync(logFile, `=== API Response Logs ===\nStarted: ${new Date().toISOString()}\n${'='.repeat(50)}\n\n`)
  
  function logToFile(entry) {
    const timestamp = new Date().toISOString()
    const logEntry = `[${timestamp}]\n${entry}\n${'─'.repeat(50)}\n\n`
    fs.appendFileSync(logFile, logEntry)
  }
  
  return {
    name: 'vite-api-logger',
    
    configureServer(server) {
      // Middleware to intercept and log API responses
      server.middlewares.use((req, res, next) => {
        const apiPaths = ['/users', '/tasks', '/energy', '/api']
        const isApiCall = apiPaths.some(p => req.url?.startsWith(p))
        
        if (!isApiCall) {
          return next()
        }
        
        const originalWrite = res.write.bind(res)
        const originalEnd = res.end.bind(res)
        const chunks = []
        
        res.write = (chunk, ...args) => {
          if (chunk) {
            chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
          }
          return originalWrite(chunk, ...args)
        }
        
        res.end = (chunk, ...args) => {
          if (chunk) {
            chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
          }
          
          // Log the response
          try {
            const body = Buffer.concat(chunks).toString('utf8')
            let formattedBody = body
            
            // Try to pretty-print JSON
            try {
              const parsed = JSON.parse(body)
              formattedBody = JSON.stringify(parsed, null, 2)
            } catch {
              // Not JSON, keep as-is
            }
            
            const logEntry = [
              `${req.method} ${req.url}`,
              `Status: ${res.statusCode}`,
              `Response:`,
              formattedBody
            ].join('\n')
            
            logToFile(logEntry)
            console.log(`📝 Logged API response: ${req.method} ${req.url}`)
          } catch (err) {
            console.error('Failed to log API response:', err)
          }
          
          return originalEnd(chunk, ...args)
        }
        
        next()
      })
      
      console.log(`\n📋 API Logger active - responses logged to: ${logFile}\n`)
    }
  }
}
