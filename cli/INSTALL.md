# 全局安装指南

## 本地开发安装

### Windows

```bash
# 1. 进入 cli 目录
cd D:\codes\python\Agent_team\cli

# 2. 安装依赖
npm install

# 3. 全局链接
npm link

# 4. 验证安装
agent-team --version
```

### macOS / Linux

```bash
# 1. 进入 cli 目录
cd /path/to/Agent_team/cli

# 2. 安装依赖
npm install

# 3. 全局链接
npm link

# 4. 验证安装
agent-team --version
```

## 使用方式

安装后，可以在**任何目录**下运行：

```bash
# 连接到本地后端（默认）
agent-team

# 连接到远程服务器
agent-team --host 192.168.1.100

# 指定工作目录
agent-team --workdir D:\projects\my-app

# 组合使用
agent-team --host 192.168.1.100 --workdir D:\projects\my-app
```

## 快捷命令

`at` 是 `agent-team` 的别名：

```bash
at              # 等同于 agent-team
at --help       # 查看帮助
```

## 卸载

```bash
npm uninstall -g agent-team-cli
```

## 发布到 npm（可选）

如果要发布到公共 npm 仓库：

```bash
# 1. 修改 package.json 中的 name, version, author 等

# 2. 登录 npm
npm login

# 3. 发布
npm publish

# 4. 全局安装（用户视角）
npm install -g agent-team-cli
```

## 故障排查

### 命令找不到

**Windows:**
```bash
# 检查 npm 全局目录
npm config get prefix

# 确保该目录在 PATH 中
# 通常是 C:\Users\你的用户名\AppData\Roaming\npm
```

**macOS/Linux:**
```bash
# 检查命令位置
which agent-team

# 如果没有，重新链接
npm link -g
```

### 权限错误

**macOS/Linux:** 可能需要 `sudo`
```bash
sudo npm link
```

**Windows:** 以管理员身份运行终端

### 版本冲突

```bash
# 查看已安装版本
npm list -g agent-team-cli

# 更新
npm update -g agent-team-cli
```
