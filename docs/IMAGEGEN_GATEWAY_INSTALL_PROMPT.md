# HackStart Imagegen Gateway 一键安装提示词

将下面“安装指令”中的全部内容复制到一个新的 Codex 任务中发送。Codex 会自动安装
`$imagegen-gateway`、读取你已经配置好的 HackStart provider、准备隔离的 Python
环境，并执行不计费的连通性检查。安装后默认使用 `gpt-image-2.5-flare` 生图。

安装过程不会要求你粘贴 API Key，也不会执行真实生图。不要把自己的 API Key 添加到这份 Markdown 中。

## 安装指令

```text
请为我安装并配置 HackStart Imagegen Gateway skill，完整执行以下步骤，不要只给出命令或教程：

来源：
- GitHub repository: lidongyx/hackstart-skill
- Git ref: main
- Skill path: skills/imagegen-gateway

要求：
1. 使用 Codex 官方的 $skill-installer 安装 skill。调用安装器时明确传递 repo=lidongyx/hackstart-skill、ref=main、path=skills/imagegen-gateway。目标为当前用户的 $CODEX_HOME/skills/imagegen-gateway；如果 CODEX_HOME 未设置，则使用 ~/.codex/skills/imagegen-gateway。如果默认 download/auto 方法因为 TLS、CA 证书或 ZIP 下载失败，立即使用同一个官方安装器并指定 method=git 重试，不要关闭证书校验。
2. 如果目标不存在，正常安装。如果已经存在，不要删除其中的 .venv，不要覆盖任何凭据；从来源下载最新版，只更新 SKILL.md、agents/、scripts/ 和 .gitignore 这些由 skill 管理的文件。
3. 不得读取后回显、记录或复制 API Key。不得把 ~/.codex/config.toml、~/.codex/auth.json、环境变量或 provider 认证命令产生的 token 内容显示在回答、日志、命令参数、临时文件或仓库中。
4. 检查 Python 3.11 或更高版本。依次尝试 python3、python、Windows 的 py -3，以及 Codex Desktop 提供的 bundled workspace Python。选择第一个满足版本要求的解释器。
5. 如果没有可用的 Python 3.11+，先检查系统平台和已有包管理器。仅在需要系统级安装时向我说明将执行的命令和影响并取得确认；不要静默使用 sudo，也不要修改无关系统配置。
6. 使用选中的 Python 运行已安装 skill 的 scripts/imagegen_gateway.py setup。setup 应自动：
   - 读取 ~/.codex/config.toml 中当前 model_provider 对应的 provider；
   - 从该 provider 的 env_key、experimental_bearer_token、command-backed auth 或 Codex auth store 中解析凭据；
   - 将 provider base_url 规范化为 OpenAI Images API 的 /v1 地址；
   - 创建 skill 私有的跨平台 .venv；
   - 安装或升级兼容的 OpenAI Python SDK；
   - 通过模型列表检查确认 gpt-image-2.5-flare 可用；
   - 在 ~/.codex/AGENTS.md 中以受管理、可重复执行的区块设置 $imagegen-gateway 为默认生图路线，并说明默认模型是 gpt-image-2.5-flare。
7. 如果 setup 失败，运行 scripts/imagegen_gateway.py doctor --repair，并根据其输出修复 Python、venv、SDK、provider、鉴权或网络问题。最多重复修复和检查两次；仍失败就停止，给我明确的失败项目和下一步，不要尝试真实生图。
8. 验收必须满足：doctor=ok、online_check=ok，并且 image_models 中包含 gpt-image-2.5-flare。安装期间不要调用 images.generate，不要生成测试图片，避免产生费用。
9. 完成后只报告：安装目录、Python 版本、OpenAI SDK 版本、provider 名称、规范化后的 base URL、可用图片模型，以及是否需要新建任务或重启 Codex。不要报告任何密钥内容。
10. 如果 skill 在当前任务中尚未出现在技能列表，说明这是任务启动时的技能发现缓存；完成安装和验收后告诉我新建一个 Codex 任务，或在仍未出现时重启 Codex。
```

## 安装后的使用方式

安装完成后，新建一个 Codex 任务，直接输入：

```text
生成一张万里长城的科幻海报
```

也可以显式指定：

```text
使用 $imagegen-gateway 生成一张万里长城的科幻海报
```

## 精简安装提示词

```text
请用 $skill-installer 安装并配置 GitHub 仓库 lidongyx/hackstart-skill 中的 skill：
skills/imagegen-gateway@main。安装后运行 setup/doctor 完成零计费验收，默认模型必须是
gpt-image-2.5-flare。直接读取本机 Codex 配置中的 API 地址和凭据，不要显示、复制或询问
API Key；完成后只报告安装目录、运行时版本、provider、可用图片模型和是否需要重启 Codex。
```

## 精简调用提示词

```text
使用 $imagegen-gateway 生成一张<描述你的图片>
```

需要排查环境时输入：

```text
使用 $imagegen-gateway 检查并修复生图环境，不要生成测试图片
```
