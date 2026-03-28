#!/usr/bin/env node

/**
 * Multi-Agent Team CLI - 手动模式
 * 简洁界面设计
 */

const WebSocket = require('ws');
const axios = require('axios');
const readline = require('readline');

const DEFAULT_API_URL = 'http://localhost:8000';
const DEFAULT_WS_URL = 'ws://localhost:8000/ws';

const ESC = '\x1b[';
const colors = {
    reset: `${ESC}0m`,
    bold: `${ESC}1m`,
    dim: `${ESC}2m`,
    cyan: `${ESC}96m`,
    green: `${ESC}92m`,
    yellow: `${ESC}93m`,
    white: `${ESC}97m`,
    gray: `${ESC}90m`,
    red: `${ESC}91m`,
    blue: `${ESC}94m`,
    magenta: `${ESC}95m`,
};

function c(text, color) {
    return `${colors[color] || ''}${text}${colors.reset}`;
}

const state = {
    connected: false,
    isProcessing: false,
    agents: {},
    currentAgent: 'ProductManager',
    workDir: process.cwd(),
    contextUsed: '0.0%',
    processingStatus: '',
    outputLines: [],
};

const args = process.argv.slice(2);
let apiUrl = DEFAULT_API_URL;
let wsUrl = DEFAULT_WS_URL;

for (let i = 0; i < args.length; i++) {
    if (args[i] === '--host' && args[i + 1]) {
        apiUrl = `http://${args[i + 1]}:8000`;
        wsUrl = `ws://${args[i + 1]}:8000/ws`;
        i++;
    } else if (args[i] === '--help' || args[i] === '-h') {
        console.log(`
Multi-Agent Team CLI v3.0.0

用法: agent-team [选项]

选项:
  --host <hostname>     指定后端 API 地址
  --help, -h           显示帮助

快捷键:
  1-9, 0, -, =         切换 Agent
  /agents              列出所有 Agent
  /status              查看状态
  /clear               清屏
  /exit                退出
`);
        process.exit(0);
    }
}

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
});

function clear() {
    readline.cursorTo(process.stdout, 0, 0);
    readline.clearScreenDown(process.stdout);
}

function moveCursor(row) {
    readline.cursorTo(process.stdout, 0, row);
}

const spinnerFrames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
let spinnerInterval = null;
let currentSpinnerFrame = 0;

const agentEmoji = {
    ProductManager: '📋',
    Architect: '🏗️',
    DataEngineer: '🗄️',
    UIDesigner: '🎨',
    FrontendDev: '🎯',
    BackendDev: '⚙️',
    CodeReviewer: '🔍',
    Tester: '🧪',
    SecurityAuditor: '🔒',
    PerformanceOptimizer: '⚡',
    DevOps: '🚀',
    TechnicalWriter: '📝',
};

const agentKeys = {
    '0': 'PerformanceOptimizer',
    '1': 'ProductManager',
    '2': 'Architect',
    '3': 'DataEngineer',
    '4': 'UIDesigner',
    '5': 'FrontendDev',
    '6': 'BackendDev',
    '7': 'CodeReviewer',
    '8': 'Tester',
    '9': 'SecurityAuditor',
    '-': 'DevOps',
    '=': 'TechnicalWriter',
};

function getTerminalHeight() {
    return process.stdout.rows || 24;
}

function getOutputAreaHeight() {
    return getTerminalHeight() - 8;
}

function printHeader() {
    const emoji = agentEmoji[state.currentAgent] || '🤖';
    const status = state.connected ? c('●', 'green') : c('○', 'red');
    
    console.log(c('┌' + '─'.repeat(78) + '┐', 'cyan'));
    console.log(c('│', 'cyan') + c('  Agent Team ', 'bold') + c('v3.0.0', 'gray') + ' '.repeat(52) + c('│', 'cyan'));
    console.log(c('│', 'cyan') + ' '.repeat(78) + c('│', 'cyan'));
    console.log(c('│', 'cyan') + `  ${status} ${emoji} ${state.currentAgent}` + ' '.repeat(78 - 6 - state.currentAgent.length) + c('│', 'cyan'));
    console.log(c('│', 'cyan') + `  ${c(state.workDir.substring(0, 70), 'gray')}` + ' '.repeat(78 - 4 - Math.min(state.workDir.length, 70)) + c('│', 'cyan'));
    console.log(c('└' + '─'.repeat(78) + '┘', 'cyan'));
}

function printAgentBar() {
    const agents = Object.entries(agentKeys);
    let line = '  ';
    agents.forEach(([key, name]) => {
        const emoji = agentEmoji[name] || '🤖';
        const isCurrent = name === state.currentAgent;
        const text = isCurrent ? c(`[${key}]${emoji}`, 'green') : c(`[${key}]${emoji}`, 'gray');
        line += text + ' ';
    });
    line += c('  ? 帮助', 'dim');
    console.log(line);
}

function printSeparator() {
    console.log(c('─'.repeat(80), 'gray'));
}

function printOutput() {
    const maxHeight = getOutputAreaHeight();
    const lines = state.outputLines.slice(-maxHeight);
    
    lines.forEach(line => {
        console.log(line);
    });
    
    const emptyLines = maxHeight - lines.length;
    for (let i = 0; i < emptyLines; i++) {
        console.log();
    }
}

function printInputArea() {
    const height = getTerminalHeight();
    moveCursor(height - 2);
    readline.clearLine(process.stdout, 0);
    
    if (state.isProcessing) {
        const frame = spinnerFrames[currentSpinnerFrame];
        const statusText = state.processingStatus || '处理中';
        console.log(c(`  ${frame} ${statusText}`, 'cyan'));
    } else {
        console.log(c('  输入您的消息或 @ 文件路径', 'gray'));
    }
    
    moveCursor(height - 1);
    readline.clearLine(process.stdout, 0);
    process.stdout.write(c('> ', 'green'));
}

function addOutput(text, type = 'normal') {
    const lines = text.split('\n');
    lines.forEach(line => {
        if (type === 'user') {
            state.outputLines.push(c(`  > ${line}`, 'green'));
        } else if (type === 'agent') {
            state.outputLines.push(`  ${line}`);
        } else if (type === 'system') {
            state.outputLines.push(c(`  ${line}`, 'yellow'));
        } else if (type === 'error') {
            state.outputLines.push(c(`  ❌ ${line}`, 'red'));
        } else {
            state.outputLines.push(`  ${line}`);
        }
    });
    refreshScreen();
}

function refreshScreen() {
    clear();
    printHeader();
    printAgentBar();
    printSeparator();
    printOutput();
    printSeparator();
    printInputArea();
}

function startSpinner(text) {
    state.isProcessing = true;
    state.processingStatus = text;
    currentSpinnerFrame = 0;
    
    spinnerInterval = setInterval(() => {
        currentSpinnerFrame = (currentSpinnerFrame + 1) % spinnerFrames.length;
        printInputArea();
    }, 100);
}

function stopSpinner() {
    state.isProcessing = false;
    state.processingStatus = '';
    if (spinnerInterval) {
        clearInterval(spinnerInterval);
        spinnerInterval = null;
    }
}

let ws = null;

function connectWebSocket() {
    return new Promise((resolve, reject) => {
        ws = new WebSocket(wsUrl);
        
        ws.on('open', () => {
            state.connected = true;
            resolve();
        });
        
        ws.on('message', (data) => {
            try {
                const msg = JSON.parse(data.toString());
                handleWsMessage(msg);
            } catch (e) {}
        });
        
        ws.on('close', () => {
            state.connected = false;
        });
        
        ws.on('error', (err) => {
            reject(err);
        });
    });
}

function handleWsMessage(msg) {
    if (msg.type === 'connected' || msg.type === 'agent_status') {
        if (msg.agents) {
            msg.agents.forEach(agent => {
                state.agents[agent.name] = agent;
            });
        }
        if (msg.agent && msg.status) {
            if (state.agents[msg.agent]) {
                state.agents[msg.agent].status = msg.status;
            }
        }
    }
}

async function sendMessage(message) {
    if (state.isProcessing) return;

    addOutput(message, 'user');
    startSpinner(`${agentEmoji[state.currentAgent]} ${state.currentAgent} 正在思考...`);

    try {
        const response = await axios.post(`${apiUrl}/chat`, {
            message: message,
            agent: state.currentAgent,
            work_dir: state.workDir,
        }, { timeout: 300000 });

        stopSpinner();
        
        const { agent, response: reply } = response.data;
        
        addOutput(reply, 'agent');
        
        state.contextUsed = `${(Math.random() * 5 + 1).toFixed(1)}%`;
        
    } catch (error) {
        stopSpinner();
        if (error.code === 'ECONNREFUSED') {
            addOutput('无法连接到后端 API', 'error');
        } else if (error.response) {
            addOutput(error.response.data.detail || error.message, 'error');
        } else {
            addOutput(error.message, 'error');
        }
    }
    
    refreshScreen();
}

function switchAgent(key) {
    const agentName = agentKeys[key];
    if (agentName) {
        state.currentAgent = agentName;
        const emoji = agentEmoji[agentName] || '🤖';
        addOutput(`已切换到: ${emoji} ${agentName}`, 'system');
        refreshScreen();
        return true;
    }
    return false;
}

function handleInput(input) {
    const message = input.trim();
    
    if (!message) {
        refreshScreen();
        return;
    }
    
    if (message.startsWith('/')) {
        const cmd = message.toLowerCase();
        switch (cmd) {
            case '/exit':
            case '/quit':
            case '/q':
                console.log(c('\n  👋 再见！\n', 'green'));
                process.exit(0);
            case '/clear':
            case '/cls':
                state.outputLines = [];
                refreshScreen();
                break;
            case '/agents':
            case '/list':
                printAgentList();
                break;
            case '/status':
                refreshScreen();
                break;
            case '/help':
            case '?':
                printHelp();
                break;
            default:
                addOutput(`未知命令: ${message}`, 'system');
        }
        return;
    }
    
    if (message.length === 1 && agentKeys[message]) {
        switchAgent(message);
        return;
    }
    
    sendMessage(message);
}

function printAgentList() {
    addOutput('┌─────────────────── Agent 列表 ───────────────────┐', 'system');
    Object.entries(agentKeys).forEach(([key, name]) => {
        const emoji = agentEmoji[name] || '🤖';
        const marker = name === state.currentAgent ? ' ◄ 当前' : '';
        addOutput(`│ [${key}] ${emoji} ${name}${marker}`, 'system');
    });
    addOutput('└────────────────────────────────────────────────┘', 'system');
}

function printHelp() {
    addOutput('┌─────────────────── 快捷键 ───────────────────┐', 'system');
    addOutput('│  0-9, -, =       切换 Agent                 │', 'system');
    addOutput('│  /agents         列出所有 Agent             │', 'system');
    addOutput('│  /clear          清屏                       │', 'system');
    addOutput('│  /exit           退出                       │', 'system');
    addOutput('└────────────────────────────────────────────┘', 'system');
}

async function start() {
    refreshScreen();
    
    try {
        await connectWebSocket();
        refreshScreen();
    } catch (err) {
        addOutput('无法连接到后端，请确保 server.py 正在运行', 'error');
        addOutput(`地址: ${apiUrl}`, 'system');
    }
    
    rl.on('line', handleInput);
}

process.on('SIGINT', () => {
    console.log(c('\n\n  👋 再见！\n', 'green'));
    process.exit(0);
});

process.on('uncaughtException', (err) => {
    console.log(c(`\n  ❌ 错误: ${err.message}`, 'red'));
    process.exit(1);
});

process.stdout.on('resize', () => {
    refreshScreen();
});

start();
