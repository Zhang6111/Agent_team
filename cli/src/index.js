#!/usr/bin/env node

/**
 * Multi-Agent Team CLI
 * 
 * 使用方法：
 *   node src/index.js              # 连接默认地址 http://localhost:8000
 *   node src/index.js --host xxx   # 连接指定地址
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

for (let i = 0; i < args.length; i++) {
    if (args[i] === '--host' && args[i + 1]) {
        apiUrl = `http://${args[i + 1]}:8000`;
        wsUrl = `ws://${args[i + 1]}:8000/ws`;
        i++;
    } else if (args[i] === '--help' || args[i] === '-h') {
        console.log(`
Multi-Agent Team CLI

用法:
  node src/index.js [选项]

选项:
  --host <hostname>  指定后端 API 地址 (默认：localhost)
  --help, -h         显示帮助

示例:
  node src/index.js                          # 本地连接
  node src/index.js --host 192.168.1.100     # 连接远程服务器
        `);
        process.exit(0);
    }
}

// ==================== 创建屏幕 ====================

const screen = blessed.screen({
    smartCSR: true,
    title: 'Multi-Agent Team CLI',
    fullUnicode: true,
});

// ==================== 创建布局 ====================

// 标题栏
const header = blessed.box({
    top: 0,
    left: 0,
    width: '100%',
    height: 3,
    content: '{center}🤖 Multi-Agent Team CLI{/center}',
    tags: true,
    style: {
        fg: 'cyan',
        bg: 'black',
        bold: true,
    },
    border: {
        type: 'line',
        fg: 'cyan',
    },
});

// Agent 状态面板
const agentPanel = blessed.box({
    top: 3,
    left: 0,
    width: '40%',
    height: '60%',
    label: ' Agent 状态 ',
    tags: true,
    style: {
        fg: 'white',
        border: {
            fg: 'green',
        },
    },
    border: {
        type: 'line',
        fg: 'green',
    },
    content: '正在连接...',
});

// 日志面板
const logPanel = blessed.box({
    top: 3,
    left: '40%',
    width: '60%',
    height: '60%',
    label: ' 实时日志 ',
    tags: true,
    style: {
        fg: 'white',
        border: {
            fg: 'blue',
        },
    },
    border: {
        type: 'line',
        fg: 'blue',
    },
    content: '',
});

// 日志行集合
const logLines = [];
const MAX_LOG_LINES = 100;

function addLog(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    let color = 'white';
    
    switch (type) {
        case 'error': color = 'red'; break;
        case 'success': color = 'green'; break;
        case 'warning': color = 'yellow'; break;
        case 'agent': color = 'cyan'; break;
    }
    
    const line = `{gray}[${timestamp}]{/gray} {${color}}${message}{/${color}}`;
    logLines.push(line);
    
    if (logLines.length > MAX_LOG_LINES) {
        logLines.shift();
    }
    
    logPanel.setContent(logLines.join('\n'));
    screen.render();
}

// 输入框
const inputBox = blessed.textbox({
    bottom: 0,
    left: 0,
    width: '80%',
    height: 3,
    label: ' 输入消息 (Enter 发送): ',
    tags: true,
    style: {
        fg: 'white',
        label: {
            fg: 'yellow',
            bold: true,
        },
    },
    border: {
        type: 'line',
        fg: 'yellow',
    },
    inputOnFocus: true,
});

// 状态栏
const statusBar = blessed.box({
    bottom: 0,
    left: '80%',
    width: '20%',
    height: 3,
    content: '{center}状态：{green}已连接{/green}{/center}',
    tags: true,
    style: {
        fg: 'white',
        bg: 'black',
    },
    border: {
        type: 'line',
        fg: 'gray',
    },
});

// 帮助提示
const helpBox = blessed.box({
    bottom: 3,
    left: 0,
    width: '100%',
    height: 1,
    content: '{center}Ctrl+C 退出 | Ctrl+L 清屏 | /help 查看命令{/center}',
    tags: true,
    style: {
        fg: 'gray',
        bg: 'black',
    },
});

// 添加元素到屏幕
screen.append(header);
screen.append(agentPanel);
screen.append(logPanel);
screen.append(helpBox);
screen.append(inputBox);
screen.append(statusBar);

// ==================== WebSocket 连接 ====================

let ws = null;
let agents = [];

function connectWebSocket() {
    addLog(`正在连接 ${wsUrl}...`, 'info');
    
    ws = new WebSocket(wsUrl);
    
    ws.on('open', () => {
        addLog('已连接到后端 API', 'success');
        statusBar.setContent('{center}状态：{green}已连接{/green}{/center}');
        screen.render();
        
        // 发送心跳
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
                agents = message.agents || [];
                updateAgentPanel();
            } else if (message.type === 'connected') {
                agents = message.agents || [];
                updateAgentPanel();
            }
        } catch (e) {
            // 忽略解析错误
        }
    });
    
    ws.on('close', () => {
        addLog('连接已断开，尝试重连...', 'warning');
        statusBar.setContent('{center}状态：{red}断开{/red}{/center}');
        screen.render();
        
        setTimeout(connectWebSocket, 3000);
    });
    
    ws.on('error', (error) => {
        addLog(`WebSocket 错误：${error.message}`, 'error');
    });
}

function updateAgentPanel() {
    if (agents.length === 0) {
        agentPanel.setContent('没有可用的 Agent');
        screen.render();
        return;
    }
    
    const content = agents.map(agent => {
        let statusIcon = '⚪';
        let statusColor = 'gray';
        
        switch (agent.status) {
            case 'working':
                statusIcon = '🟢';
                statusColor = 'green';
                break;
            case 'done':
                statusIcon = '✅';
                statusColor = 'green';
                break;
            case 'error':
                statusIcon = '❌';
                statusColor = 'red';
                break;
        }
        
        const task = agent.current_task ? ` - ${agent.current_task.substring(0, 20)}...` : '';
        return `{${statusColor}}${statusIcon} ${agent.name}{/${statusColor}}${task}`;
    }).join('\n');
    
    agentPanel.setContent(content);
    screen.render();
}

// ==================== HTTP API 调用 ====================

async function sendMessage(message) {
    try {
        addLog(`发送：${message}`, 'info');
        
        const response = await axios.post(`${apiUrl}/chat`, {
            message: message,
        });
        
        const { message: reply, actions } = response.data;
        
        addLog(reply, 'agent');
        
        // 如果有操作指令，显示确认
        if (actions && actions.length > 0) {
            addLog(`收到 ${actions.length} 个操作指令`, 'warning');
            // 这里可以添加确认逻辑
        }
        
    } catch (error) {
        if (error.response) {
            addLog(`API 错误：${error.response.status}`, 'error');
        } else if (error.request) {
            addLog('无法连接到后端 API', 'error');
        } else {
            addLog(`错误：${error.message}`, 'error');
        }
    }
}

// ==================== 键盘事件 ====================

inputBox.on('submit', (value) => {
    const message = value.trim();
    
    if (message) {
        // 处理命令
        if (message === '/clear' || message === '/cls') {
            logLines.length = 0;
            logPanel.setContent('');
            addLog('屏幕已清空', 'success');
        } else if (message === '/help') {
            addLog('可用命令：/clear (清屏), /exit (退出), /status (状态)', 'info');
        } else if (message === '/exit' || message === '/quit') {
            process.exit(0);
        } else if (message === '/status') {
            addLog(`当前有 ${agents.length} 个 Agent 在线`, 'info');
        } else {
            // 发送消息
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
    logLines.length = 0;
    logPanel.setContent('');
    addLog('屏幕已清空', 'success');
});

// ==================== 启动 ====================

addLog('正在启动 Multi-Agent Team CLI...');
addLog(`连接地址：${apiUrl}`);
connectWebSocket();

// 聚焦输入框
inputBox.focus();

// 渲染屏幕
screen.render();

// 错误处理
process.on('uncaughtException', (err) => {
    addLog(`未捕获异常：${err.message}`, 'error');
});

process.on('SIGINT', () => {
    screen.destroy();
    console.log('\n👋 再见！');
    process.exit(0);
});
