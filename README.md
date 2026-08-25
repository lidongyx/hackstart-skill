# HackStart Skills

HackStart 官方 Codex skills 集合。每个 skill 独立放在 `skills/<skill-name>/`，可通过
Codex 的 `$skill-installer` 从 GitHub 安装。

## Skills

| Skill | 用途 | 安装提示词 |
| --- | --- | --- |
| `imagegen-gateway` | 通过用户当前配置的 HackStart provider 调用官方图片 CLI，自动准备环境并进行零计费诊断 | [打开安装文档](docs/IMAGEGEN_GATEWAY_INSTALL_PROMPT.md) |

## 推荐安装方式

打开 [一键安装提示词](docs/IMAGEGEN_GATEWAY_INSTALL_PROMPT.md)，把“安装指令”全文复制到
一个新的 Codex 任务中。Codex 会自动安装、配置和验收环境，用户不需要粘贴 API Key。

也可以直接对 Codex 说：

```text
请使用 $skill-installer 安装以下 skill：
- repo: lidongyx/hackstart-skill
- ref: main
- path: skills/imagegen-gateway
```

如果默认下载方式遇到 TLS 或本机 CA 证书错误，让 `$skill-installer` 使用
`method=git` 重试；不要关闭证书校验。

安装后新建 Codex 任务，直接输入：

```text
生成一张万里长城的科幻海报
```

## 安全边界

- 仓库不包含任何 API Key、provider token、`config.toml` 或 `auth.json`。
- 用户凭据只从其本机 Codex provider 配置解析，不写入 skill 文件。
- 安装验收只读取模型列表，不生成测试图片，不产生图片生成费用。
- `.venv` 是每位用户本机生成的运行环境，不进入 Git。
