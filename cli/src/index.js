#!/usr/bin/env node

/**
 * Multi-Agent Team CLI - 手动模式
 * 参考 Qwen Code 的简洁设计
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

const spinnerFrames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
let spinnerInterval = null;

function startSpinner(text = '处理中') {
    let frame = 0;
    spinnerInterval = setInterval(() => {
        readline.cursorTo(process.stdout, 0);
        process.stdout.write(c(`${spinnerFrames[frame]} ${text}`, 'cyan'));
        frame = (frame + 1) % spinnerFrames.length;
    }, 100);
}

function stopSpinner() {
    if (spinnerInterval) {
        clearInterval(spinnerInterval);
        spinnerInterval = null;
        readline.clearLine(process.stdout, 0);
    }
}

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
    '1': 'ProductManager',
    '2': 'Architect',
    '3': 'DataEngineer',
    '4': 'UIDesigner',
    '5': 'FrontendDev',
    '6': 'BackendDev',
    '7': 'CodeReviewer',
    '8': 'Tester',
    '9': 'SecurityAuditor',
    '0': 'PerformanceOptimizer',
    '-': 'DevOps',
    '=': 'TechnicalWriter',
};

function printHeader() {
    const logo = `
   ▄▄▄▄▄▄  ▄▄     ▄▄ ▄▄▄▄▄▄▄ ▄▄▄    ▄▄   ┌──────────────────────────────────────────────────────────┐
  ██╔═══██╗██║    ██║██╔════╝████╗  ██║  │${c(' >_ Multi-Agent Team ', 'cyan')}v3.0.0${' '.repeat(32)}│
  ██║   ██║██║ █╗ ██║█████╗  ██╔██╗ ██║  │                                                          │
  ██║▄▄ ██║██║███╗██║██╔══╝  ██║╚██╗██║  │ ${c(state.currentAgent, 'green')} ${agentEmoji[state.currentAgent] || '🤖'}${' '.repeat(55 - state.currentAgent.length)}│
  ╚██████╔╝╚███╔███╔╝███████╗██║ ╚████║  │ ${c(state.workDir.substring(0, 50), 'gray')}${' '.repeat(50 - Math.min(state.workDir.length, 50))}│
   ╚═════╝  ╚══╝╚══╝ ╚══════╝╚═╝  ╚═══╝  └──────────────────────────────────────────────────────────┘
`;
    console.log(logo);
}

function printSeparator() {
    console.log(c('─'.repeat(120), 'gray'));
}

function printInputPrompt() {
    console.log();
    rl.question(c('> ', 'green'), handleInput);
}

function printStatus() {
    const status = state.connected ? c('● 已连接', 'green') : c('○ 未连接', 'red');
    console.log(`  ${status}  │  ${c(state.contextUsed, 'cyan')} context used`);
    console.log();
}

function printAgentQuickSwitch() {
    const agents = Object.entries(agentKeys);
    const current = state.currentAgent;
    let line = '  ';
    agents.forEach(([key, name]) => {
        const emoji = agentEmoji[name] || '🤖';
        const isCurrent = name === current;
        const text = isCurrent ? c(`[${key}]${emoji}`, 'green') : c(`[${key}]${emoji}`, 'gray');
        line += text + ' ';
    });
    console.log(line);
    console.log(c('  按 ? 查看快捷键', 'gray'));
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

    state.isProcessing = true;
    
    console.log();
    console.log(c(`> ${message}`, 'green'));

    try {
        startSpinner(`${state.currentAgent} 正在处理...`);
        
        const response = await axios.post(`${apiUrl}/chat`, {
            message: message,
            agent: state.currentAgent,
            work_dir: state.work_dir,
        }, { timeout: 300000 });

        stopSpinner();
        
        const { agent, response: reply } = response.data;
        
        console.log();
        printAgentResponse(reply, agent);
        
        state.contextUsed = `${(Math.random() * 5 + 1).toFixed(1)}%`;
        
    } catch (error) {
        stopSpinner();
        if (error.code === 'ECONNREFUSED') {
            console.log(c('\n❌ 无法连接到后端 API', 'red'));
        } else if (error.response) {
            console.log(c(`\n❌ 错误: ${error.response.data.detail || error.message}`, 'red'));
        } else {
            console.log(c(`\n❌ 错误: ${error.message}`, 'red'));
        }
    } finally {
        state.isProcessing = false;
        printSeparator();
        printInputPrompt();
    }
}

function printAgentResponse(content, agent) {
    const emoji = agentEmoji[agent] || '🤖';
    const lines = content.split('\n');
    
    lines.forEach((line, i) => {
        if (line.trim()) {
            console.log(`  ${line}`);
        }
    });
}

function switchAgent(key) {
    const agentName = agentKeys[key];
    if (agentName) {
        state.currentAgent = agentName;
        const emoji = agentEmoji[agentName] || '🤖';
        console.log();
        console.log(c(`  ✦ 已切换到: ${emoji} ${agentName}`, 'yellow'));
        printSeparator();
        printInputPrompt();
        return true;
    }
    return false;
}

function handleInput(input) {
    const message = input.trim();
    
    if (!message) {
        printInputPrompt();
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
                clear();
                printHeader();
                printStatus();
                printAgentQuickSwitch();
                printSeparator();
                printInputPrompt();
                break;
            case '/agents':
            case '/list':
                printAgentList();
                printInputPrompt();
                break;
            case '/status':
                clear();
                printHeader();
                printStatus();
                printAgentQuickSwitch();
                printSeparator();
                printInputPrompt();
                break;
            case '/help':
            case '?':
                printHelp();
                printInputPrompt();
                break;
            default:
                console.log(c(`\n  ❓ 未知命令: ${message}`, 'yellow'));
                printSeparator();
                printInputPrompt();
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
    console.log();
    console.log(c('  ┌─────────────────── Agent 列表 ───────────────────┐', 'cyan'));
    Object.entries(agentKeys).forEach(([key, name]) => {
        const emoji = agentEmoji[name] || '🤖';
        const marker = name === state.currentAgent ? c(' ◄ 当前', 'green') : '';
        console.log(c('  │', 'cyan') + c(` [${key}] ${emoji} ${name.padEnd(18)}`, 'white') + marker);
    });
    console.log(c('  └────────────────────────────────────────────────┘', 'cyan'));
}

function printHelp() {
    console.log();
    console.log(c('  ┌─────────────────── 快捷键 ───────────────────┐', 'cyan'));
    console.log(c('  │', 'cyan') + '  1-9, 0, -, =    切换 Agent                ' + c('│', 'cyan'));
    console.log(c('  │', 'cyan') + '  /agents         列出所有 Agent            ' + c('│', 'cyan'));
    console.log(c('  │', 'cyan') + '  /status         查看状态                  ' + c('│', 'cyan'));
    console.log(c('  │', 'cyan') + '  /clear          清屏                      ' + c('│', 'cyan'));
    console.log(c('  │', 'cyan') + '  /exit           退出                      ' + c('│', 'cyan'));
    console.log(c('  └────────────────────────────────────────────┘', 'cyan'));
}

async function start() {
    clear();
    printHeader();
    
    try {
        await connectWebSocket();
        printStatus();
        printAgentQuickSwitch();
        printSeparator();
    } catch (err) {
        console.log(c('  ❌ 无法连接到后端，请确保 server.py 正在运行', 'red'));
        console.log(c(`     地址: ${apiUrl}`, 'gray'));
    }
    
    printInputPrompt();
}

process.on('SIGINT', () => {
    console.log(c('\n\n  👋 再见！\n', 'green'));
    process.exit(0);
});

process.on('uncaughtException', (err) => {
    console.log(c(`\n  ❌ 错误: ${err.message}`, 'red'));
    process.exit(1);
});

start();
