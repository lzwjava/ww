# ww

🌐 [English](README.md) | **中文**

---

跨平台命令行工具集，提升开发者生产力。涵盖 Git 工作流、GitHub 管理、笔记记录、截图捕获、图片处理（裁剪、压缩、去背景、EXIF 扫描）、PDF 转换（Markdown、LaTeX、代码转 PDF）、网页搜索（多引擎）、网络诊断（WiFi 扫描、IP/端口扫描、网络拓扑）、系统监控（macOS、Linux）、进程管理、Clash 代理控制、Java/Maven 分析、RAG 文档索引、LLM 模型对比、OpenRouter 账户管理、GitHub Actions 触发、语音转录（Whisper）、演示文稿生成（Marp）、Cloudflare 分析等 —— 多数命令内置 LLM 智能辅助。

## 安装

```bash
pip install -e .
```

## 用法

```bash
ww <命令组> [命令] [选项]
```

## 命令

### 笔记 (Note)

| 命令 | 说明 |
|------|------|
| `ww note` | 创建新笔记（集成 Git） |
| `ww note log` | 创建日志条目 |
| `ww note log-file` | 从文件创建日志条目 |
| `ww note obfuscate <file>` | 对文件中的敏感数据进行脱敏 |

### 截图 (Screenshot)

| 命令 | 说明 |
|------|------|
| `ww screenshot [DELAY]` | 截图（macOS，`--dir`） |
| `ww screenshot-linux` | 截图（Linux，保存到 SCREENSHOT_DIR，默认: assets/screenshots） |
| `ww screenshot note` | 从最新截图创建笔记（`-n`，`--prompt`） |
| `ww screenshot interact-note` | 交互式截图并创建笔记 |

### Git

| 命令 | 说明 |
|------|------|
| `ww git amend-push` | 修改上次提交并强制推送 |
| `ww git classify` | 分类 Git 提交 |
| `ww git find-commit` | 查找 Git 提交 |
| `ww git delete-commit` | 删除 Git 提交 |
| `ww git diff-tree` | 显示 Git 差异树 |
| `ww git check-filenames` | 检查 Git 文件名 |
| `ww git force-push` | 强制推送到远程 |
| `ww git show` | 显示 Git 提交详情 |
| `ww git squash` | 压缩 Git 提交 |
| `ww git gca` | AI 提交，不推送（gemini-flash） |
| `ww git gpa` | AI 提交并 pull+push（gemini-flash） |

### GitHub

| 命令 | 说明 |
|------|------|
| `ww github info` | 账户信息、套餐、速率限制 |
| `ww github repos` | 列出你的仓库（最近推送） |
| `ww github starred` | 列出星标仓库 |
| `ww github followers` | 列出关注者 |
| `ww github following` | 列出正在关注 |
| `ww github notifications` | 列出未读通知 |
| `ww github rate` | 显示速率限制详情 |
| `ww github gitmessageai` | 生成 AI 提交消息并提交 |

### 图片 (Image)

| 命令 | 说明 |
|------|------|
| `ww image avatar` | 处理头像图片 |
| `ww image crop` | 裁剪图片 |
| `ww image remove-bg` | 去除图片背景 |
| `ww image compress` | 压缩图片 |
| `ww image photo-compress` | 压缩照片 |
| `ww image exif` | 扫描图片 EXIF GPS 定位数据 |
| `ww image whatsapp` | 通过 Safari 从 WhatsApp Web 下载图片 |

### GIF

| 命令 | 说明 |
|------|------|
| `ww gif` | 从图片创建 GIF |

### PDF

| 命令 | 说明 |
|------|------|
| `ww pdf markdown-pdf` | 将 Markdown 文件转换为 PDF |
| `ww pdf pdf-pipeline` | 批量将 Markdown 文章转换为 PDF |
| `ww pdf update-pdf` | 转换上次提交中更改的 Markdown 文件 |
| `ww pdf code2pdf` | 将目录中的代码文件转换为 PDF |
| `ww pdf scale-pdf` | 使用 pdfjam 缩放 PDF |
| `ww pdf test-latex` | 测试 LaTeX/pandoc PDF 生成 |
| `ww pdf md2png` | 通过 HTML+PDF 将 Markdown 转换为 PNG（Chrome） |

### 搜索 (Search)

| 命令 | 说明 |
|------|------|
| `ww search` | 网页搜索（多引擎） |
| `ww search bing` | 使用 Bing 搜索 |
| `ww search code` | 代码搜索 |
| `ww search ddg` | 使用 DuckDuckGo 搜索 |
| `ww search ecosia` | 使用 Ecosia 搜索 |
| `ww search filename` | 按文件名搜索 |
| `ww search startpage` | 使用 StartPage 搜索 |
| `ww search tavily` | 使用 Tavily API 搜索 |
| `ww search web --json` | JSON 输出，供 LLM 工具调用 |

### macOS

| 命令 | 说明 |
|------|------|
| `ww macos find-large-dirs` | 查找磁盘上最大的目录 |
| `ww macos system-info` | 显示系统信息 |
| `ww macos install` | 运行 macOS 安装任务 |
| `ww macos list-fonts` | 列出已安装字体 |
| `ww macos list-disks` | 列出便携磁盘 |
| `ww macos open-terminal` | 打开新终端窗口 |
| `ww macos toast` | 显示 macOS 通知 |
| `ww macos charge-watch` | 充电器已连接但未充电时提醒 |
| `ww macos process` | 分析运行中的进程并建议关闭 |
| `ww macos settings-proxy` | 设置系统代理（HTTP/HTTPS 7890，SOCKS 7891）含绕过列表 |
| `ww macos apps` | 审核已安装应用的大小和年龄（`--no-llm`，`--json`） |
| `ww macos dock` | 列出 Dock 中固定的应用（`--json`） |

### Linux

| 命令 | 说明 |
|------|------|
| `ww linux gpu` | 显示 GPU 和 CUDA 详情 |
| `ww linux system` | 综合系统概览 |
| `ww linux disk` | 显示磁盘使用情况 |
| `ww linux battery` | 显示电池状态 |
| `ww linux proxy-setup` | 交互式配置 APT 代理 |
| `ww linux wol` | 发送网络唤醒（WoL）数据包 |
| `ww linux terminal` | 打开全屏终端 |

### 网络 (Network)

| 命令 | 说明 |
|------|------|
| `ww network get-wifi-list` | 获取 WiFi 网络列表 |
| `ww network save-wifi-list` | 保存 WiFi 网络列表 |
| `ww network hack-wifi` | WiFi 密码工具 |
| `ww network wifi-gen-password` | 生成 WiFi 密码 |
| `ww network ip-scan` | 扫描网络 IP 地址 |
| `ww network port-scan` | 扫描开放端口 |
| `ww network wifi-scan` | 扫描 WiFi 网络 |
| `ww network wifi-util` | WiFi 实用工具 |
| `ww network network-plot` | 绘制网络拓扑图 |

### 进程 (Process)

| 命令 | 说明 |
|------|------|
| `ww proc kill-pattern` | 终止匹配模式的进程 |
| `ww proc kill-port` | 终止指定端口上的进程 |
| `ww proc kill-jekyll` | 终止 Jekyll 服务器 |
| `ww proc kill-proxy` | 终止 macOS 代理 |

### 工具 (Utils)

| 命令 | 说明 |
|------|------|
| `ww utils base64` | Base64 编码/解码 |
| `ww utils ccr` | CCR 工具 |
| `ww utils clean-zip` | 清理 zip 文件 |
| `ww utils decode-jwt` | 解码 JWT 令牌 |
| `ww utils py2txt` | 将 Python 文件转换为文本 |
| `ww utils request-proxy` | 通过代理发起 HTTP 请求 |
| `ww utils smart-unzip` | 智能解压归档文件 |
| `ww utils unzip` | 解压归档文件 |

### Java

| 命令 | 说明 |
|------|------|
| `ww java mvn` | Maven 项目工具 |
| `ww java analyze-deps` | 分析 Java 依赖 |
| `ww java analyze-packages` | 分析 Java 包 |
| `ww java analyze-poms` | 分析 Maven POM 文件 |
| `ww java analyze-spring` | 分析 Spring Boot 项目 |
| `ww java clean-log` | 清理 Java 日志文件 |

### Copilot

| 命令 | 说明 |
|------|------|
| `ww copilot auth` | 通过 GitHub OAuth 设备流程认证 |
| `ww copilot models` | 列出可用的 Copilot 模型 |
| `ww copilot chat` | 与 Copilot 模型对话 |

### 同步 (Sync)

| 命令 | 说明 |
|------|------|
| `ww sync claude` | 同步 Claude Code 设置（已脱敏） |
| `ww sync bashrc [back\|forth]` | 同步 .bashrc 文件 |
| `ww sync zprofile [back\|forth]` | 同步 .zprofile 文件 |
| `ww sync zed [back\|forth]` | 同步 ~/.config/zed/ 目录（Zed 配置） |
| `ww sync ssh [back\|forth]` | 同步 .ssh 目录 |
| `ww sync hermes [back\|forth]` | 同步 config.yaml、SOUL.md、hooks/、plugins/、agent-hooks/ |

### 更新 (Update)

| 命令 | 说明 |
|------|------|
| `ww update [name...]` | 更新 Git 仓库（默认: updated_repos） |

### 最新 (Latest)

| 命令 | 说明 |
|------|------|
| `ww latest notes [N]` | 显示最新 N 条笔记的文件名和标题（默认 10） |

### 读取 / RAG (Read)

| 命令 | 说明 |
|------|------|
| `ww read index <dir>` | 索引目录中的文档（BGE + FAISS） |
| `ww read query <question>` | 对已索引文档提问 |
| `ww read query <q> --top-k N` | 使用 N 个检索片段（默认 5） |

### LLM

| 命令 | 说明 |
|------|------|
| `ww llm compare` | 比较 6 个模型对剪贴板提示的回答，评选最佳 |

### OpenRouter

| 命令 | 说明 |
|------|------|
| `ww openrouter info` | 账户摘要：额度、用量、密钥详情 |
| `ww openrouter credits` | 显示额度余额 |
| `ww openrouter activity` | 过去一周花费、请求数、Token 数（`--days N`） |
| `ww openrouter models` | 列出可用模型 |

### 环境 (Env)

| 命令 | 说明 |
|------|------|
| `ww env update` | 选取 Arena 排名靠前的模型并更新 .env 中的 MODEL= |

### 显示 (Display)

| 命令 | 说明 |
|------|------|
| `ww display <dark\|light\|auto\|show>` | 切换 macOS 外观或显示当前设置 |

### 图片生成 (Gen-image)

| 命令 | 说明 |
|------|------|
| `ww gen-image` | 从剪贴板文本生成图片（Imagen 3） |

### Action

| 命令 | 说明 |
|------|------|
| `ww action <workflow.yml>` | 通过 gh CLI 触发 GitHub Actions 工作流 |

### 学历 (Degree)

| 命令 | 说明 |
|------|------|
| `ww degree` | AI 分类最近的自学通知 |
| `ww degree practical` | 筛选关于实践考试/成绩的通知 |
| `ww degree list` | 原始抓取列表（无 AI） |
| `ww degree --pages N` | 抓取 N 个列表页（1-11，默认 1） |

### Marp

| 命令 | 说明 |
|------|------|
| `ww marp <file.md>` | 监听 Markdown 文件并通过 marp 重新生成 PDF |

### Whisper

| 命令 | 说明 |
|------|------|
| `ww whisper <file.mp4>` | 通过 whisper 转录（中文，large 模型，CUDA） |
| `ww whisper refine <file.txt>` | 通过 OpenRouter 将转录结果精炼为 .md |

### 主机 (Host)

| 命令 | 说明 |
|------|------|
| `ww host` | 显示所有主机 |
| `ww host local` | 本地机器 |
| `ww host workstation` | 工作站（RTX 4070） |
| `ww host dmit` | DMIT 服务器 |

### Cloudflare

| 命令 | 说明 |
|------|------|
| `ww cloudflare monthly-visit` | 来自 Web Analytics 的每月页面浏览和访问量 |
| `ww cloudflare zones` | 列出 Cloudflare 区域 |
| `ww cloudflare datasets` | 列出 Web Analytics 数据集 |
| `ww cloudflare schema` | 查看 GraphQL Account schema |
| `ww cloudflare pdf <file>` | 解析 Cloudflare Analytics PDF 导出 |

### Ghostty

| 命令 | 说明 |
|------|------|
| `ww ghostty` | 在随机位置打开 Ghostty 窗口 |
| `ww ghostty close` | 关闭所有 Ghostty 窗口 |

### Clash

| 命令 | 说明 |
|------|------|
| `ww clash select-provider` | 选择最佳代理提供商 |
| `ww clash speed` | 运行速度测试并选择最佳代理 |
| `ww clash run` | 完整的 Clash 管理（多轮迭代） |
| `ww clash top-proxies` | 打印前 5 个最快代理（单 URL） |
| `ww clash top-proxies-multi` | 打印前 10 个最快代理（多 URL） |
| `ww clash speed-tiktok` | 运行速度测试 + TikTok 加载时间 |
| `ww clash query-dns [host]` | 测试 AliDNS DoH 解析 |
| `ww clash gnome-proxy <set\|unset>` | 切换 GNOME 代理（Linux） |
| `ww clash macos-proxy <set\|unset>` | 切换 macOS 代理（networksetup） |
| `ww clash wifi <on\|off>` | 切换 macOS Wi-Fi |

## 依赖

- Python >= 3.8
- 完整依赖列表见 `pyproject.toml`
