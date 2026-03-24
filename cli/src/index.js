#!/usr/bin/env node

/**
 * Multi-Agent Team CLI
 * 纯文本简洁风格 - 使用 readline
 */

const WebSocket = require('ws');
const axios = require('axios');
const readline = require('readline');

// ANSI 颜色代码
const ESC = '\x1b[';
const colors = {
    reset: `${ESC}0m`,
    bold: `${ESC}1m`,
    cyan: `${ESC}96m`,
    green: `${ESC}92m`,
    yellow: `${ESC}93m`,
    white: `${ESC}97m`,
    gray: `${ESC}90m`,
    red: `${ESC}91m`,
};

function c(text, color) {
    return `${colors[color]}${text}${colors.reset}`;
}

// ==================== 配置 ====================

const DEFAULT_API_URL = 'http://localhost:8000';
const DEFAULT_WS_URL = 'ws://localhost:8000/ws';

// 解析命令行参数
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
Multi-Agent Team CLI

用法:
  agent-team [选项]

选项:
  --host <hostname>     指定后端 API 地址
  --workdir <directory> 指定工作目录
  --help, -h            显示帮助
`);
        process.exit(0);
    }
}

// ==================== 清屏 ====================

function clear() {
    readline.cursorTo(process.stdout, 0, 0);
    readline.clearScreenDown(process.stdout);
}

// ==================== 打印 Logo ====================

function printLogo() {
    const logo = `
${c('  ███╗   ███╗ █████╗  ██████╗██████╗ ██╗██████╗ ', 'cyan')}
${c('  ████╗ ████║██╔══██╗██╔════╝██╔══██╗██║██╔══██╗', 'cyan')}
${c('  ██╔████╔██║███████║██║     ██████╔╝██║██║  ██║', 'cyan')}
${c('  ██║╚██╔╝██║██╔══██║██║     ██╔══██╗██║██║  ██║', 'cyan')}
${c('  ██║ ╚═╝ ██║██║  ██║╚██████╗██║  ██║██║██████╔╝', 'cyan')}
${c('  ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═════╝ ', 'cyan')}
`;
    console.log(logo);
}

// ==================== 打印信息 ====================

function printInfo(connected) {
    const status = connected ? c('● 已连接', 'green') : c('○ 连接中...', 'yellow');
    console.log(c('  Multi-Agent Team CLI', 'white') + c('  v1.0.0', 'gray'));
    console.log(c('  工作目录:', 'white') + ` ${workDir}`);
    console.log(c('  后端地址:', 'white') + ` ${apiUrl}`);
    console.log(`  ${status}`);
    console.log();
}

// ==================== 打印分隔线 ====================

function printSeparator() {
    console.log(c('────────────────────────────────────────────────────────────────────────', 'gray'));
}

// ==================== 打印消息 ====================

function printMessage(role, content) {
    let prefix = '';
    let color = 'white';
    
    switch (role) {
        case 'user':
            prefix = c('> ', 'green');
            break;
        case 'assistant':
            prefix = c('🤖 ', 'cyan');
            break;
        case 'system':
            prefix = c('ℹ️  ', 'gray');
            break;
        case 'action':
            prefix = c('📋 ', 'yellow');
            break;
        case 'success':
            prefix = c('✅ ', 'green');
            break;
        case 'error':
            prefix = c('❌ ', 'red');
            break;
    }
    
    const lines = content.split('\n');
    lines.forEach((line, i) => {
        if (i === 0) {
            console.log(`${prefix}${line}`);
        } else {
            console.log(`  ${line}`);
        }
    });
}

// ==================== WebSocket 连接 ====================

let ws = null;
let isConnected = false;

function connectWebSocket() {
    return new Promise((resolve, reject) => {
        ws = new WebSocket(wsUrl);
        
        ws.on('open', () => {
            isConnected = true;
            resolve();
        });
        
        ws.on('close', () => {
            isConnected = false;
        });
        
        ws.on('error', (err) => {
            reject(err);
        });
    });
}

// ==================== HTTP API 调用 ====================

let isWaiting = false;
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
});

async function sendMessage(message) {
    if (isWaiting) return;
    isWaiting = true;
    
    try {
        printMessage('user', message);
        
        const response = await axios.post(`${apiUrl}/chat`, {
            message: message,
            work_dir: workDir,
        });
        
        const { message: reply, actions } = response.data;
        
        if (actions && actions.length > 0) {
            actions.forEach(action => {
                if (action.type === 'create_file') {
                    printMessage('action', `创建文件：${action.path}`);
                    printMessage('success', `已创建 ${action.path}`);
                } else if (action.type === 'run_command') {
                    printMessage('action', `运行命令：${action.command}`);
                }
            });
        }
        
        if (reply) {
            printMessage('assistant', reply);
        }
        
    } catch (error) {
        if (error.code === 'ECONNREFUSED') {
            printMessage('error', '无法连接到后端 API');
        } else {
            printMessage('error', `错误：${error.message}`);
        }
    } finally {
        isWaiting = false;
        showPrompt();
    }
}

// ==================== 显示输入提示 ====================

function showPrompt() {
    rl.question(c('> ', 'green'), handleInput);
}

function handleInput(input) {
    const message = input.trim();
    
    if (message) {
        if (message === '/exit' || message === '/quit' || message === '/q') {
            console.log(c('\n👋 再见！\n', 'green'));
            process.exit(0);
        } else if (message === '/clear' || message === '/cls') {
            clear();
            printLogo();
            printInfo(isConnected);
            printSeparator();
            showPrompt();
        } else if (message === '/help') {
            printMessage('system', '可用命令：/exit (退出), /clear (清屏)');
            showPrompt();
        } else {
            sendMessage(message);
        }
    } else {
        showPrompt();
    }
}

// ==================== 启动 ====================

async function start() {
    clear();
    printLogo();
    printInfo(false);
    printSeparator();
    
    try {
        await connectWebSocket();
        printInfo(true);
        printSeparator();
        printMessage('system', '输入你的需求，按 Enter 发送...');
        console.log();
    } catch (err) {
        printMessage('error', '无法连接到后端，请确保 server.py 正在运行');
        console.log();
    }
    
    showPrompt();
}

// 处理 Ctrl+C
process.on('SIGINT', () => {
    console.log(c('\n\n👋 再见！\n', 'green'));
    process.exit(0);
});

start();
