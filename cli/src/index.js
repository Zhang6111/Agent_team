#!/usr/bin/env node

/**
 * Multi-Agent Team CLI - 增强版
 * 支持：实时状态、团队面板、进度条、加载动画
 */

const WebSocket = require('ws');
const axios = require('axios');
const readline = require('readline');

// ==================== 配置 ====================

const DEFAULT_API_URL = 'http://localhost:8000';
const DEFAULT_WS_URL = 'ws://localhost:8000/ws';

// ANSI 颜色代码
const ESC = '\x1b[';
const colors = {
    reset: `${ESC}0m`,
    bold: `${ESC}1m`,
    dim: `${ESC}2m`,
    italic: `${ESC}3m`,
    underline: `${ESC}4m`,
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

// ==================== 状态管理 ====================

// 状态管理
const state = {
    connected: false,
    isProcessing: false,
    currentTask: null,
    agents: {},
    logs: [],
    messageHistory: [],
    pendingResolve: null,   // 等待 WebSocket task_complete 事件的 resolve
};

// ==================== 解析参数 ====================

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
Multi-Agent Team CLI v2.0.0

用法:
  agent-team [选项]

选项:
  --host <hostname>     指定后端 API 地址
  --workdir <directory> 指定工作目录
  --help, -h           显示帮助

命令:
  /team    查看团队状态
  /status  查看任务进度
  /logs    查看操作日志
  /clear   清屏
  /exit    退出
`);
        process.exit(0);
    }
}

// ==================== 初始化 readline ====================

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
});

// ==================== 工具函数 ====================

function clear() {
    readline.cursorTo(process.stdout, 0, 0);
    readline.clearScreenDown(process.stdout);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ==================== 加载动画 ====================

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

// ==================== 打印 Logo ====================

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

// ==================== 团队面板 ====================

const agentEmoji = {
    ProjectDirector: '👔',
    ProductManager: '📋',
    UIDesigner: '🎨',
    Architect: '🏗️',
    DataEngineer: '🗄️',
    TechLead: '👨‍💻',
    FrontendDev: '🎯',
    BackendDev: '⚙️',
    CodeReviewer: '🔍',
    Tester: '🧪',
    BugFixer: '🔧',
    SecurityAuditor: '🔒',
    PerformanceOptimizer: '⚡',
    DevOps: '🚀',
    TechnicalWriter: '📝',
};

function printTeamPanel() {
    console.log(c('\n┌─────────────────── 团队状态 ───────────────────┐', 'cyan'));
    
    const agentList = Object.entries(state.agents);
    if (agentList.length === 0) {
        console.log(c('│  等待任务中...', 'gray'));
    } else {
        for (const [name, info] of agentList) {
            const emoji = agentEmoji[name] || '🤖';
            const statusColor = info.status === 'working' ? 'yellow' : 
                              info.status === 'done' ? 'green' : 'gray';
            const status = info.status === 'working' ? '工作中' : 
                          info.status === 'done' ? '完成' : '空闲';
            const task = info.current_task ? info.current_task.substring(0, 20) : '';
            
            console.log(c('│', 'cyan') + c(` ${emoji} ${name.padEnd(15)}`, 'white') + 
                       c(` [${status.padEnd(4)}]`, statusColor) + 
                       (task ? c(` ${task}`, 'gray') : ''));
        }
    }
    
    console.log(c('└────────────────────────────────────────────────┘', 'cyan'));
}

// ==================== 进度条 ====================

function printProgressBar(percentage, width = 30) {
    const filled = Math.round(width * percentage / 100);
    const bar = '█'.repeat(filled) + '░'.repeat(width - filled);
    return c(`[${bar}] ${percentage}%`, percentage < 30 ? 'red' : percentage < 70 ? 'yellow' : 'green');
}

// ==================== 状态面板 ====================

function printStatusPanel() {
    const total = Object.keys(state.agents).length;
    const working = Object.values(state.agents).filter(a => a.status === 'working').length;
    const done = Object.values(state.agents).filter(a => a.status === 'done').length;
    const progress = total > 0 ? Math.round(done / total * 100) : 0;

    console.log(c('\n┌─────────────────── 任务进度 ───────────────────┐', 'cyan'));
    console.log(c('│', 'cyan') + c(` 当前任务: ${state.currentTask || '无'}`, 'white'));
    console.log(c('│', 'cyan') + ` ${printProgressBar(progress)}`);
    console.log(c('│', 'cyan') + c(` 工作中: ${working}  |  完成: ${done}  |  总计: ${total}`, 'gray'));
    console.log(c('└────────────────────────────────────────────────┘', 'cyan'));
}

// ==================== 日志展示 ====================

function printLogs() {
    if (state.logs.length === 0) {
        console.log(c('\n暂无日志', 'gray'));
        return;
    }
    
    console.log(c('\n┌─────────────────── 操作日志 ───────────────────┐', 'cyan'));
    state.logs.slice(-10).forEach(log => {
        const time = new Date(log.timestamp).toLocaleTimeString();
        const color = log.type === 'error' ? 'red' : log.type === 'success' ? 'green' : 'white';
        console.log(c('│', 'cyan') + c(` [${time}]`, 'gray') + c(` ${log.message}`, color));
    });
    console.log(c('└────────────────────────────────────────────────┘', 'cyan'));
}

// ==================== 消息美化 ====================

function printMessage(content, role = 'assistant') {
    const roleConfig = {
        user: { prefix: c('👤 你', 'green'), color: 'white' },
        assistant: { prefix: c('🤖 Agent', 'cyan'), color: 'white' },
        system: { prefix: c('ℹ️ 系统', 'gray'), color: 'gray' },
        success: { prefix: c('✅ 成功', 'green'), color: 'green' },
        error: { prefix: c('❌ 错误', 'red'), color: 'red' },
        warning: { prefix: c('⚠️ 警告', 'yellow'), color: 'yellow' },
    };

    const config = roleConfig[role] || roleConfig.assistant;
    
    // 处理代码块
    content = content.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
        return c('┌─ ' + (lang || 'code') + ' ', 'gray') + '─'.repeat(20) + '\n' +
               c(code, 'yellow') + '\n' +
               c('└' + '─'.repeat(30), 'gray');
    });
    
    // 处理行
    const lines = content.split('\n');
    lines.forEach((line, i) => {
        if (line.trim()) {
            console.log(i === 0 ? `${config.prefix}  ${line}` : `  ${line}`);
        }
    });
}

// ==================== 分隔线 ====================

function printSeparator() {
    console.log(c('────────────────────────────────────────────────────────────────', 'gray'));
}

// ==================== WebSocket ====================

let ws = null;

function connectWebSocket() {
    return new Promise((resolve, reject) => {
        ws = new WebSocket(wsUrl);
        
        ws.on('open', () => {
            state.connected = true;
            addLog('已连接到服务器', 'success');
            resolve();
        });
        
        ws.on('message', (data) => {
            try {
                const msg = JSON.parse(data.toString());
                handleWsMessage(msg);
            } catch (e) {
                console.log(c(`[WS] ${data}`, 'gray'));
            }
        });
        
        ws.on('close', () => {
            state.connected = false;
            addLog('连接已断开', 'error');
        });
        
        ws.on('error', (err) => {
            addLog(`连接错误: ${err.message}`, 'error');
            reject(err);
        });
    });
}

function handleWsMessage(msg) {
    if (msg.type === 'connected') {
        if (msg.agents) {
            msg.agents.forEach(agent => {
                state.agents[agent.name] = agent;
            });
        }
    } else if (msg.type === 'status_update') {
        if (msg.agents) {
            msg.agents.forEach(agent => {
                state.agents[agent.name] = agent;
            });
        }
        if (msg.current_task) {
            state.currentTask = msg.current_task;
        }
        // 实时刷新状态面板
        if (state.isProcessing) {
            stopSpinner();
            process.stdout.write('\x1b[2K\r');  // 清除当前行
            printTeamPanelInline();
            startSpinner(state.currentTask ? `处理中: ${state.currentTask.substring(0, 40)}` : '处理中');
        }
    } else if (msg.type === 'log') {
        addLog(msg.message, msg.level);
        if (state.isProcessing) {
            stopSpinner();
            const color = msg.level === 'error' ? 'red' : msg.level === 'success' ? 'green' : 'gray';
            console.log(c(`  [${msg.level.toUpperCase()}] ${msg.message}`, color));
            startSpinner('继续处理中');
        }
    } else if (msg.type === 'task_complete') {
        // 任务完成，解析结果
        if (state.pendingResolve) {
            state.pendingResolve({ reply: msg.message, actions: msg.actions || [] });
            state.pendingResolve = null;
        }
    } else if (msg.type === 'task_error') {
        if (state.pendingResolve) {
            state.pendingResolve({ error: msg.error });
            state.pendingResolve = null;
        }
    }
}

// ==================== 日志管理 ====================

function addLog(message, type = 'info') {
    state.logs.push({ timestamp: new Date(), message, type });
    if (state.logs.length > 50) state.logs = state.logs.slice(-50);
}

// ==================== 团队面板（单行刷新版）====================

function printTeamPanelInline() {
    const working = Object.values(state.agents).filter(a => a.status === 'working');
    if (working.length > 0) {
        const names = working.map(a => `${agentEmoji[a.name] || '🤖'} ${a.name}`).join('  ');
        process.stdout.write(c(`  工作中: ${names}\n`, 'yellow'));
    }
}

// ==================== 渲染状态 ====================

function renderStatus() {
    clear();
    printLogo();
    console.log();
    printStatusPanel();
    console.log();
    printTeamPanel();
    console.log();
    printSeparator();
}

// ==================== API 调用（异步 WebSocket 驱动）====================

function waitForTaskResult() {
    return new Promise((resolve) => {
        state.pendingResolve = resolve;
        // 超时保护：30 分钟
        setTimeout(() => {
            if (state.pendingResolve) {
                state.pendingResolve = null;
                resolve({ error: '任务超时（30 分钟）' });
            }
        }, 30 * 60 * 1000);
    });
}

async function sendMessage(message) {
    if (state.isProcessing) return;

    state.isProcessing = true;
    state.currentTask = message;
    addLog(`发送: ${message.substring(0, 50)}`, 'info');

    console.log();
    printSeparator();
    console.log(c(`> ${message}`, 'green'));
    console.log();

    try {
        // 1. 发送请求，后端立即返回 task_id
        const response = await axios.post(`${apiUrl}/chat`, {
            message: message,
            work_dir: workDir,
        }, { timeout: 10000 });

        const { task_id } = response.data;
        console.log(c(`  任务已提交 [${task_id.substring(0, 8)}...]`, 'gray'));
        console.log();
        startSpinner('Agent 团队正在处理，实时进度见下方...');

        // 2. 等待 WebSocket 推送 task_complete / task_error
        const result = await waitForTaskResult();
        stopSpinner();

        if (result.error) {
            printMessage(result.error, 'error');
            addLog(result.error, 'error');
            showPrompt();
            return;
        }

        const { reply, actions } = result;

        // 添加到历史
        state.messageHistory.push({ role: 'user', content: message });
        state.messageHistory.push({ role: 'assistant', content: reply });

        console.log();
        printMessage(reply, 'assistant');

        // 3. 执行文件操作
        if (actions && actions.length > 0) {
            console.log();
            console.log(c('📋 执行操作:', 'cyan'));

            for (const action of actions) {
                if (action.type === 'create_file') {
                    console.log(c(`   ◐ 创建: ${action.path}`, 'gray'));
                    try {
                        await axios.post(`${apiUrl}/execute`, {
                            message: JSON.stringify({ actions: [action] }),
                            work_dir: workDir,
                        }, { timeout: 30000 });
                        console.log(c(`   ✅ 已创建 ${action.path}`, 'green'));
                        addLog(`创建文件: ${action.path}`, 'success');
                    } catch (err) {
                        console.log(c(`   ❌ 创建失败`, 'red'));
                        addLog(`创建失败: ${action.path}`, 'error');
                    }
                } else if (action.type === 'run_command') {
                    console.log(c(`   ⚠️  命令: ${action.command}`, 'yellow'));
                    const confirmed = await askQuestion(c('   是否执行？(y/n): ', 'yellow'));
                    if (confirmed.toLowerCase() === 'y') {
                        try {
                            await axios.post(`${apiUrl}/execute`, {
                                message: JSON.stringify({ actions: [action] }),
                                work_dir: workDir,
                            }, { timeout: 60000 });
                            console.log(c(`   ✅ 命令已执行`, 'green'));
                            addLog(`执行命令: ${action.command}`, 'success');
                        } catch (err) {
                            console.log(c(`   ❌ 执行失败`, 'red'));
                        }
                    } else {
                        console.log(c('   ⓧ 已取消', 'gray'));
                    }
                }
            }
        }

    } catch (error) {
        stopSpinner();
        if (error.code === 'ECONNREFUSED') {
            printMessage('无法连接到后端 API', 'error');
        } else {
            printMessage(`错误: ${error.message}`, 'error');
        }
        addLog(`错误: ${error.message}`, 'error');
    } finally {
        state.isProcessing = false;
        state.currentTask = null;
        showPrompt();
    }
}

// ==================== 输入处理 ====================

function askQuestion(question) {
    return new Promise(resolve => {
        rl.question(question, answer => resolve(answer));
    });
}

function showPrompt() {
    console.log();
    rl.question(c('> ', 'green'), handleInput);
}

function handleInput(input) {
    const message = input.trim();
    
    if (!message) {
        showPrompt();
        return;
    }
    
    // 命令处理
    switch (message.toLowerCase()) {
        case '/exit':
        case '/quit':
        case '/q':
            console.log(c('\n👋 再见！\n', 'green'));
            process.exit(0);
            
        case '/clear':
        case '/cls':
            clear();
            printLogo();
            printStatusPanel();
            console.log();
            printTeamPanel();
            showPrompt();
            
        case '/team':
            console.log();
            printTeamPanel();
            showPrompt();
            
        case '/status':
            console.log();
            printStatusPanel();
            showPrompt();
            
        case '/logs':
            printLogs();
            showPrompt();
            
        case '/help':
            console.log(`
${c('可用命令:', 'cyan')}
  ${c('/team', 'white')}   - 查看团队状态
  ${c('/status', 'white')}  - 查看任务进度
  ${c('/logs', 'white')}    - 查看操作日志
  ${c('/clear', 'white')}   - 清屏
  ${c('/exit', 'white')}    - 退出
`);
            showPrompt();
            
        default:
            sendMessage(message);
    }
}

// ==================== 启动 ====================

async function start() {
    clear();
    printLogo();
    console.log(c('\n  正在连接...', 'gray'));
    
    try {
        await connectWebSocket();
        clear();
        printLogo();
        printStatusPanel();
        console.log();
        printTeamPanel();
        printSeparator();
        printMessage('输入你的需求，按 Enter 发送...\n使用 /help 查看更多命令', 'system');
    } catch (err) {
        console.log(c('\n❌ 无法连接到后端，请确保 server.py 正在运行', 'red'));
        console.log(c(`   地址: ${apiUrl}`, 'gray'));
    }
    
    showPrompt();
}

// ==================== 信号处理 ====================

process.on('SIGINT', () => {
    console.log(c('\n\n👋 再见！\n', 'green'));
    process.exit(0);
});

process.on('uncaughtException', (err) => {
    console.log(c(`\n❌ 错误: ${err.message}`, 'red'));
    process.exit(1);
});

// ==================== 运行 ====================

start();
