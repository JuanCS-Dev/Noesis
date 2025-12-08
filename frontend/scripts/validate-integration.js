#!/usr/bin/env node
/**
 * NOESIS Integration Validation Script
 * =====================================
 * 
 * Validates all frontend-backend integrations before demo.
 * Run: node scripts/validate-integration.js
 */

const http = require('http');
const https = require('https');

// Configuration
const CONFIG = {
  maximus: {
    baseUrl: 'http://localhost:8001',
    endpoints: [
      { path: '/api/consciousness/reactive-fabric/metrics', name: 'Reactive Fabric Metrics' },
      { path: '/api/consciousness/safety/status', name: 'Safety Status' },
      { path: '/api/consciousness/state', name: 'Consciousness State' },
      { path: '/api/consciousness/arousal', name: 'Arousal State' },
    ]
  },
  reflector: {
    baseUrl: 'http://localhost:8002',
    endpoints: [
      { path: '/api/reflector/health', name: 'Reflector Health' },
      { path: '/api/reflector/health/detailed', name: 'Tribunal Health' },
    ]
  },
  gateway: {
    baseUrl: 'http://localhost:8000',
    endpoints: [
      { path: '/health', name: 'API Gateway Health' },
    ]
  },
  frontend: {
    baseUrl: 'http://localhost:3000',
    endpoints: [
      { path: '/', name: 'Frontend Home' },
    ]
  }
};

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m',
};

function log(color, symbol, message) {
  console.log(`${color}${symbol}${colors.reset} ${message}`);
}

function success(msg) { log(colors.green, '✓', msg); }
function error(msg) { log(colors.red, '✗', msg); }
function warn(msg) { log(colors.yellow, '⚠', msg); }
function info(msg) { log(colors.cyan, '→', msg); }
function header(msg) { console.log(`\n${colors.bold}${colors.blue}═══ ${msg} ═══${colors.reset}\n`); }

/**
 * Make HTTP request and return result
 */
function checkEndpoint(baseUrl, endpoint) {
  return new Promise((resolve) => {
    const url = `${baseUrl}${endpoint.path}`;
    const protocol = url.startsWith('https') ? https : http;
    
    const timeout = setTimeout(() => {
      resolve({ 
        success: false, 
        name: endpoint.name, 
        url, 
        error: 'Timeout (5s)',
        status: null 
      });
    }, 5000);

    const req = protocol.get(url, (res) => {
      clearTimeout(timeout);
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        const isOk = res.statusCode >= 200 && res.statusCode < 400;
        resolve({
          success: isOk,
          name: endpoint.name,
          url,
          status: res.statusCode,
          data: isOk ? tryParseJSON(data) : null,
          error: isOk ? null : `HTTP ${res.statusCode}`,
        });
      });
    });

    req.on('error', (err) => {
      clearTimeout(timeout);
      resolve({
        success: false,
        name: endpoint.name,
        url,
        error: err.code === 'ECONNREFUSED' ? 'Connection refused (service offline?)' : err.message,
        status: null,
      });
    });
  });
}

function tryParseJSON(str) {
  try {
    return JSON.parse(str);
  } catch {
    return null;
  }
}

/**
 * Test WebSocket connection
 */
function checkWebSocket(url, name) {
  return new Promise((resolve) => {
    // Simple TCP check since we don't have ws library
    const urlObj = new URL(url.replace('ws://', 'http://').replace('wss://', 'https://'));
    const protocol = urlObj.protocol === 'https:' ? https : http;
    
    const timeout = setTimeout(() => {
      resolve({ success: false, name, url, error: 'Timeout' });
    }, 3000);

    const req = protocol.get({
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname,
      headers: {
        'Upgrade': 'websocket',
        'Connection': 'Upgrade',
        'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
        'Sec-WebSocket-Version': '13',
      }
    }, (res) => {
      clearTimeout(timeout);
      // 101 = Switching Protocols (WebSocket upgrade success)
      // 426 = Upgrade Required (endpoint exists but needs proper WS client)
      const isWsReady = res.statusCode === 101 || res.statusCode === 426 || res.statusCode === 200;
      resolve({
        success: isWsReady,
        name,
        url,
        status: res.statusCode,
        error: isWsReady ? null : `HTTP ${res.statusCode}`,
      });
    });

    req.on('error', (err) => {
      clearTimeout(timeout);
      resolve({
        success: false,
        name,
        url,
        error: err.code === 'ECONNREFUSED' ? 'Connection refused' : err.message,
      });
    });
  });
}

/**
 * Test SSE endpoint
 */
function checkSSE(baseUrl, path, name) {
  return new Promise((resolve) => {
    const url = `${baseUrl}${path}`;
    const protocol = url.startsWith('https') ? https : http;
    
    const timeout = setTimeout(() => {
      resolve({ success: false, name, url, error: 'Timeout' });
    }, 3000);

    const req = protocol.get(url, {
      headers: { 'Accept': 'text/event-stream' }
    }, (res) => {
      clearTimeout(timeout);
      // SSE typically returns 200 with content-type text/event-stream
      const contentType = res.headers['content-type'] || '';
      const isSSE = res.statusCode === 200 && contentType.includes('text/event-stream');
      resolve({
        success: isSSE || res.statusCode === 200,
        name,
        url,
        status: res.statusCode,
        contentType,
        error: null,
      });
      // Close connection since we just want to verify
      req.destroy();
    });

    req.on('error', (err) => {
      clearTimeout(timeout);
      resolve({
        success: false,
        name,
        url,
        error: err.message,
      });
    });
  });
}

/**
 * Validate data structure from metrics endpoint
 */
function validateMetricsStructure(data) {
  const required = ['health_score', 'tig', 'esgt', 'arousal', 'safety'];
  const missing = required.filter(key => !(key in data));
  return {
    valid: missing.length === 0,
    missing,
  };
}

/**
 * Run all validations
 */
async function runValidation() {
  console.log(`
${colors.cyan}╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ${colors.bold}NOESIS INTEGRATION VALIDATOR${colors.reset}${colors.cyan}                              ║
║   Pre-Demo Health Check - Google DeepMind Hackathon           ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝${colors.reset}
`);

  const results = {
    passed: 0,
    failed: 0,
    warnings: 0,
    critical: [],
    optional: [],
  };

  // ========== CRITICAL: MAXIMUS Core Service ==========
  header('MAXIMUS Core Service (Port 8001)');
  
  for (const endpoint of CONFIG.maximus.endpoints) {
    const result = await checkEndpoint(CONFIG.maximus.baseUrl, endpoint);
    if (result.success) {
      success(`${result.name} - OK (${result.status})`);
      results.passed++;
      
      // Validate metrics structure
      if (endpoint.path.includes('metrics') && result.data) {
        const validation = validateMetricsStructure(result.data);
        if (validation.valid) {
          success('  └─ Data structure valid');
        } else {
          warn(`  └─ Missing fields: ${validation.missing.join(', ')}`);
          results.warnings++;
        }
      }
    } else {
      error(`${result.name} - FAILED: ${result.error}`);
      results.failed++;
      results.critical.push(result);
    }
  }

  // Test SSE endpoint
  info('Testing SSE Streaming...');
  const sseResult = await checkSSE(
    CONFIG.maximus.baseUrl, 
    '/api/consciousness/stream/sse', 
    'SSE Stream'
  );
  if (sseResult.success) {
    success(`SSE Stream - OK (${sseResult.contentType || sseResult.status})`);
    results.passed++;
  } else {
    error(`SSE Stream - FAILED: ${sseResult.error}`);
    results.failed++;
    results.critical.push(sseResult);
  }

  // Test WebSocket endpoint
  info('Testing WebSocket...');
  const wsResult = await checkWebSocket(
    'ws://localhost:8001/api/consciousness/ws',
    'WebSocket'
  );
  if (wsResult.success) {
    success(`WebSocket - OK (${wsResult.status})`);
    results.passed++;
  } else {
    warn(`WebSocket - ${wsResult.error} (non-critical for demo)`);
    results.warnings++;
    results.optional.push(wsResult);
  }

  // ========== OPTIONAL: Metacognitive Reflector ==========
  header('Metacognitive Reflector / Tribunal (Port 8002)');
  
  for (const endpoint of CONFIG.reflector.endpoints) {
    const result = await checkEndpoint(CONFIG.reflector.baseUrl, endpoint);
    if (result.success) {
      success(`${result.name} - OK (${result.status})`);
      results.passed++;
    } else {
      warn(`${result.name} - ${result.error} (Tribunal panel will show offline)`);
      results.warnings++;
      results.optional.push(result);
    }
  }

  // ========== OPTIONAL: API Gateway ==========
  header('API Gateway (Port 8000)');
  
  for (const endpoint of CONFIG.gateway.endpoints) {
    const result = await checkEndpoint(CONFIG.gateway.baseUrl, endpoint);
    if (result.success) {
      success(`${result.name} - OK (${result.status})`);
      results.passed++;
    } else {
      warn(`${result.name} - ${result.error}`);
      results.warnings++;
      results.optional.push(result);
    }
  }

  // ========== CRITICAL: Frontend ==========
  header('Frontend (Port 3000)');
  
  for (const endpoint of CONFIG.frontend.endpoints) {
    const result = await checkEndpoint(CONFIG.frontend.baseUrl, endpoint);
    if (result.success) {
      success(`${result.name} - OK (${result.status})`);
      results.passed++;
    } else {
      error(`${result.name} - FAILED: ${result.error}`);
      results.failed++;
      results.critical.push(result);
    }
  }

  // ========== SUMMARY ==========
  header('VALIDATION SUMMARY');
  
  console.log(`  ${colors.green}Passed:${colors.reset}   ${results.passed}`);
  console.log(`  ${colors.red}Failed:${colors.reset}   ${results.failed}`);
  console.log(`  ${colors.yellow}Warnings:${colors.reset} ${results.warnings}`);
  console.log();

  if (results.critical.length > 0) {
    console.log(`${colors.red}${colors.bold}CRITICAL FAILURES:${colors.reset}`);
    results.critical.forEach(r => {
      console.log(`  • ${r.name}: ${r.error}`);
    });
    console.log();
  }

  if (results.optional.length > 0) {
    console.log(`${colors.yellow}NON-CRITICAL (graceful fallback):${colors.reset}`);
    results.optional.forEach(r => {
      console.log(`  • ${r.name}: ${r.error}`);
    });
    console.log();
  }

  // Final verdict
  if (results.failed === 0) {
    console.log(`
${colors.green}${colors.bold}═══════════════════════════════════════════════════════════════
  ✓ VALIDATION PASSED - Ready for demo!
═══════════════════════════════════════════════════════════════${colors.reset}
`);
    process.exit(0);
  } else if (results.critical.some(r => r.name.includes('Frontend'))) {
    console.log(`
${colors.red}${colors.bold}═══════════════════════════════════════════════════════════════
  ✗ CRITICAL FAILURE - Frontend not running!
  
  Run: cd frontend && npm run dev
═══════════════════════════════════════════════════════════════${colors.reset}
`);
    process.exit(1);
  } else if (results.critical.some(r => r.url.includes('8001'))) {
    console.log(`
${colors.red}${colors.bold}═══════════════════════════════════════════════════════════════
  ✗ CRITICAL FAILURE - MAXIMUS Core Service not running!
  
  Run: ./wake_daimon.sh
  Or:  cd backend && docker-compose up maximus_core_service
═══════════════════════════════════════════════════════════════${colors.reset}
`);
    process.exit(1);
  } else {
    console.log(`
${colors.yellow}${colors.bold}═══════════════════════════════════════════════════════════════
  ⚠ PARTIAL SUCCESS - Some services offline but demo can proceed
  
  The frontend has graceful fallbacks for offline services.
═══════════════════════════════════════════════════════════════${colors.reset}
`);
    process.exit(0);
  }
}

// Run
runValidation().catch(err => {
  console.error('Validation script error:', err);
  process.exit(1);
});

