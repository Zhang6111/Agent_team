#!/usr/bin/env node

/**
 * Multi-Agent Team CLI - 简洁版
 * 参考 Claude Code CLI 和 Qwen Code CLI 风格
 */

const blessed = require('blessed');
const WebSocket = require('ws');
const axios = require('axios');

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
  --host <hostname>     指定后端 API 地址 (默认：localhost)
  --workdir <directory> 指定工作目录 (默认：当前目录)
  --help, -h            显示帮助
`);
        process.exit(0);
    }
}

// ==================== 创建屏幕 ====================

const screen = blessed.screen({
    smartCSR: true,
    title: 'Agent Team',
    fullUnicode: true,
});

// ==================== 主布局 ====================

// 主内容区（对话历史）
const mainBox = blessed.box({
    top: 0,
    left: 0,
    width: '100%',
    height: '100%-3',
    style: {
        fg: 'white',
        bg: 'black',
    },
    scrollable: true,
    alwaysScroll: true,
    scrollbar: {
        ch: ' ',
        track: {
            bg: 'gray',
        },
        style: {
            inverse: true,
        },
    },
    keys: true,
    vi: true,
});

// 底部输入区
const inputLayout = blessed.box({
    bottom: 0,
    left: 0,
    width: '100%',
    height: 3,
    style: {
        bg: 'black',
    },
});

// 提示符
const promptLabel = blessed.text({
    parent: inputLayout,
    top: 0,
    left: 0,
    width: 6,
    content: '👤 你：',
    style: {
        fg: 'green',
        bold: true,
    },
});

// 输入框
const inputBox = blessed.textbox({
    parent: inputLayout,
    top: 0,
    left: 6,
    width: '100%-6',
    style: {
        fg: 'white',
    },
    inputOnFocus: true,
});

// 状态栏
const statusBar = blessed.box({
    top: '100%-3',
    left: 0,
    width: '100%',
    height: 1,
    style: {
        bg: 'blue',
        fg: 'white',
    },
    content: '  按 Ctrl+C 退出 | 输入 /help 查看命令',
});

// 添加元素
screen.append(mainBox);
screen.append(inputLayout);
screen.append(statusBar);

// ==================== 对话历史 ====================

const messages = [];

function addMessage(role, content) {
    const timestamp = new Date().toLocaleTimeString();
    let prefix = '';
    let color = 'white';
    
    switch (role) {
        case 'user':
            prefix = '👤 你：';
            color = 'green';
            break;
        case 'assistant':
            prefix = '🤖 Agent:';
            color = 'cyan';
            break;
        case 'system':
            prefix = 'ℹ️ ';
            color = 'gray';
            break;
        case 'agent:ProductManager':
            prefix = '🟢 产品：';
            color = 'yellow';
            break;
        case 'agent:Architect':
            prefix = '🔵 架构：';
            color = 'blue';
            break;
        case 'agent:Developer':
            prefix = '🟡 开发：';
            color = 'green';
            break;
        case 'agent:Tester':
            prefix = '🔴 测试：';
            color = 'red';
            break;
        default:
            prefix = `🤖 ${role}:`;
            color = 'cyan';
    }
    
    const lines = content.split('\n');
    const formattedLines = lines.map((line, i) => {
        if (i === 0) {
            return `{${color} bold}${prefix}{/${color} bold} ${line}`;
        }
        return `  ${line}`;
    });
    
    messages.push(...formattedLines);
    
    // 保持最近 100 行
    if (messages.length > 100) {
        messages.splice(0, messages.length - 100);
    }
    
    mainBox.setContent(messages.join('\n'));
    screen.render();
    
    // 滚动到底部
    mainBox.setScrollPerc(100);
}

function clearMessages() {
    messages.length = 0;
    mainBox.setContent('');
    screen.render();
}

// ==================== WebSocket 连接 ====================

let ws = null;
let isConnected = false;

function connectWebSocket() {
    ws = new WebSocket(wsUrl);
    
    ws.on('open', () => {
        isConnected = true;
        addMessage('system', `已连接到 ${apiUrl}`);
        statusBar.setContent(`  已连接 | 工作目录：${workDir} | Ctrl+C 退出`);
        screen.render();
        
        // 心跳
        setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send('ping');
            }
        }, 30000);
    });
    
    ws.on('message', (data) => {
        try {
            const message = JSON.parse(data.toString());
            
            if (message.type === 'status_update') {
                // 更新 Agent 状态（可以在状态栏显示）
                const workingAgents = message.agents.filter(a => a.status === 'working');
                if (workingAgents.length > 0) {
                    const names = workingAgents.map(a => a.name).join(', ');
                    statusBar.setContent(`  工作中：${names} | Ctrl+C 退出`);
                    screen.render();
                }
            }
        } catch (e) {
            // 忽略
        }
    });
    
    ws.on('close', () => {
        isConnected = false;
        addMessage('system', '连接已断开，尝试重连...');
        statusBar.setContent(`  未连接 | Ctrl+C 退出`);
        screen.render();
        
        setTimeout(connectWebSocket, 3000);
    });
    
    ws.on('error', () => {
        // 静默错误
    });
}

// ==================== HTTP API 调用 ====================

let isWaiting = false;

async function sendMessage(message) {
    if (isWaiting) return;
    isWaiting = true;
    
    try {
        addMessage('user', message);
        
        const response = await axios.post(`${apiUrl}/chat`, {
            message: message,
            work_dir: workDir,
        });
        
        const { message: reply, actions } = response.data;
        
        // 逐行显示响应（打字机效果）
        await typeWriterEffect(reply);
        
        if (actions && actions.length > 0) {
            addMessage('system', `收到 ${actions.length} 个操作指令`);
        }
        
    } catch (error) {
        if (error.response) {
            addMessage('system', `API 错误：${error.response.status}`);
        } else if (error.request) {
            addMessage('system', '无法连接到后端 API');
        } else {
            addMessage('system', `错误：${error.message}`);
        }
    } finally {
        isWaiting = false;
        inputBox.focus();
        screen.render();
    }
}

// 打字机效果
async function typeWriterEffect(text) {
    const lines = text.split('\n');
    let currentText = '';
    
    for (let i = 0; i < lines.length; i++) {
        currentText += (i > 0 ? '\n' : '') + lines[i];
        addMessage('assistant', currentText + '▌');
        await sleep(30); // 每行 30ms
    }
    
    // 移除光标
    addMessage('assistant', text);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ==================== 键盘事件 ====================

inputBox.on('submit', (value) => {
    const message = value.trim();
    
    if (message) {
        // 处理命令
        if (message === '/clear' || message === '/cls') {
            clearMessages();
            addMessage('system', '屏幕已清空');
        } else if (message === '/help') {
            addMessage('system', '可用命令：/clear (清屏), /exit (退出), /status (状态)');
        } else if (message === '/exit' || message === '/quit') {
            process.exit(0);
        } else if (message === '/status') {
            addMessage('system', `工作目录：${workDir}`);
        } else {
            sendMessage(message);
        }
    }
    
    inputBox.clearValue();
    screen.render();
});

// 全局键盘事件
screen.key(['C-c'], () => {
    process.exit(0);
});

screen.key(['C-l'], () => {
    clearMessages();
    addMessage('system', '屏幕已清空');
});

// ==================== 启动 ====================

addMessage('system', `Multi-Agent Team CLI`);
addMessage('system', `工作目录：${workDir}`);
addMessage('system', `连接地址：${apiUrl}`);
addMessage('system', '');
addMessage('system', '输入你的需求，按 Enter 发送...');
addMessage('system', '');

connectWebSocket();

inputBox.focus();
screen.render();

// 错误处理
process.on('SIGINT', () => {
    screen.destroy();
    console.log('\n👋 再见！');
    process.exit(0);
});
