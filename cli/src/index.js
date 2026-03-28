#!/usr/bin/env node

/**
 * Multi-Agent Team CLI - 手动模式
 * 支持：Agent 切换、实时状态、文件操作
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
    logs: [],
};

const args = process.argv.slice(2);
let apiUrl = DEFAULT_API_URL;
let wsUrl = DEFAULT_WS_URL;
let workDir = process.cwd();

for (let i = 0; i < args.length; i++) {
    if (args[i] === '--host' && args[i + 1]) {
        apiUrl = `http://${args[i + 1]}:8000`;
        wsUrl = `ws://${args[i + 1]}:8000/ws`;
        i++;
    } else if (args[i] === '--workdir' && args[i + 1]) {
        workDir = args[i + 1];
        i++;
    } else if (args[i] === '--help' || args[i] === '-h') {
        console.log(`
Multi-Agent Team CLI v3.0.0 (手动模式)

用法:
  agent-team [选项]

选项:
  --host <hostname>     指定后端 API 地址
  --workdir <directory> 指定工作目录
  --help, -h           显示帮助

命令:
  1-9, 0, -, =   切换 Agent
  /agents        列出所有 Agent
  /status        查看状态
  /clear         清屏
  /exit          退出
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

function printLogo() {
    const logo = `
${c('  ╔═══════════════════════════════════════════════════════════╗', 'cyan')}
${c('  ║', 'cyan')}${c('     ███╗   ███╗ █████╗  ██████╗██████╗ ██╗██████╗     ', 'white')}${c('║', 'cyan')}
${c('  ║', 'cyan')}${c('     ████╗ ████║██╔══██╗██╔════╝██╔══██╗██║██╔══██╗    ', 'white')}${c('║', 'cyan')}
${c('  ║', 'cyan')}${c('     ██╔████╔██║███████║██║     ██████╔╝██║██║  ██║    ', 'white')}${c('║', 'cyan')}
${c('  ║', 'cyan')}${c('     ██║╚██╔╝██║██╔══██║██║     ██╔══██╗██║██║  ██║    ', 'white')}${c('║', 'cyan')}
${c('  ║', 'cyan')}${c('     ██║ ╚═╝ ██║██║  ██║╚██████╗██║  ██║██║██████╔╝    ', 'white')}${c('║', 'cyan')}
${c('  ║', 'cyan')}${c('     ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═════╝    ', 'white')}${c('║', 'cyan')}
${c('  ╚═══════════════════════════════════════════════════════════╝', 'cyan')}
`;
    console.log(logo);
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

function printAgentList() {
    console.log(c('\n┌─────────────────── Agent 列表 ───────────────────┐', 'cyan'));
    const agentList = Object.entries(state.agents);
    if (agentList.length === 0) {
        console.log(c('│  等待连接...', 'gray'));
    } else {
        for (const [name, info] of agentList) {
            const emoji = agentEmoji[name] || '🤖';
            const marker = name === state.currentAgent ? c(' ◄ 当前', 'green') : '';
            console.log(c('│', 'cyan') + c(` [${info.key}] ${emoji} ${name.padEnd(18)}`, 'white') + marker);
        }
    }
    console.log(c('└────────────────────────────────────────────────┘', 'cyan'));
}

function printStatus() {
    const agent = state.agents[state.currentAgent];
    const status = agent ? agent.status : 'unknown';
    const statusColor = status === 'working' ? 'yellow' : 'green';
    
    console.log(c('\n┌─────────────────── 当前状态 ───────────────────┐', 'cyan'));
    console.log(c('│', 'cyan') + c(` 当前 Agent: ${agentEmoji[state.currentAgent] || '🤖'} ${state.currentAgent}`, 'white'));
    console.log(c('│', 'cyan') + c(` 状态: ${status}`, statusColor));
    console.log(c('│', 'cyan') + c(` 工作目录: ${workDir}`, 'gray'));
    console.log(c('└────────────────────────────────────────────────┘', 'cyan'));
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
    console.log();

    try {
        startSpinner(`${state.currentAgent} 正在处理...`);
        
        const response = await axios.post(`${apiUrl}/chat`, {
            message: message,
            agent: state.currentAgent,
            work_dir: workDir,
        }, { timeout: 300000 });

        stopSpinner();
        
        const { agent, response: reply } = response.data;
        
        console.log();
        printMessage(reply, agent);
        
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
        showPrompt();
    }
}

function printMessage(content, agent) {
    const emoji = agentEmoji[agent] || '🤖';
    const prefix = c(`${emoji} ${agent}`, 'cyan');
    
    const lines = content.split('\n');
    lines.forEach((line, i) => {
        if (line.trim()) {
            console.log(i === 0 ? `${prefix}  ${line}` : `  ${line}`);
        }
    });
}

function switchAgent(key) {
    const agentName = agentKeys[key];
    if (agentName) {
        state.currentAgent = agentName;
        const emoji = agentEmoji[agentName] || '🤖';
        console.log(c(`\n🔄 已切换到: ${emoji} ${agentName}`, 'yellow'));
        return true;
    }
    return false;
}

function showPrompt() {
    const emoji = agentEmoji[state.currentAgent] || '🤖';
    console.log();
    rl.question(c(`[${emoji} ${state.currentAgent}] > `, 'green'), handleInput);
}

function handleInput(input) {
    const message = input.trim();
    
    if (!message) {
        showPrompt();
        return;
    }
    
    if (message.startsWith('/')) {
        const cmd = message.toLowerCase();
        switch (cmd) {
            case '/exit':
            case '/quit':
            case '/q':
                console.log(c('\n👋 再见！\n', 'green'));
                process.exit(0);
            case '/clear':
            case '/cls':
                clear();
                printLogo();
                printStatus();
                showPrompt();
                break;
            case '/agents':
            case '/list':
                printAgentList();
                showPrompt();
                break;
            case '/status':
                printStatus();
                showPrompt();
                break;
            case '/help':
                console.log(`
${c('可用命令:', 'cyan')}
  ${c('1-9, 0, -, =', 'white')}  切换 Agent
  ${c('/agents', 'white')}      列出所有 Agent
  ${c('/status', 'white')}      查看状态
  ${c('/clear', 'white')}       清屏
  ${c('/exit', 'white')}        退出
`);
                showPrompt();
                break;
            default:
                console.log(c(`\n❓ 未知命令: ${message}`, 'yellow'));
                showPrompt();
        }
        return;
    }
    
    if (message.length === 1 && agentKeys[message]) {
        switchAgent(message);
        showPrompt();
        return;
    }
    
    sendMessage(message);
}

async function start() {
    clear();
    printLogo();
    console.log(c('\n  正在连接...', 'gray'));
    
    try {
        await connectWebSocket();
        clear();
        printLogo();
        printStatus();
        printAgentList();
        console.log(c('\n  输入消息与 Agent 对话，按数字键切换 Agent', 'gray'));
    } catch (err) {
        console.log(c('\n❌ 无法连接到后端，请确保 server.py 正在运行', 'red'));
        console.log(c(`   地址: ${apiUrl}`, 'gray'));
    }
    
    showPrompt();
}

process.on('SIGINT', () => {
    console.log(c('\n\n👋 再见！\n', 'green'));
    process.exit(0);
});

process.on('uncaughtException', (err) => {
    console.log(c(`\n❌ 错误: ${err.message}`, 'red'));
    process.exit(1);
});

start();
