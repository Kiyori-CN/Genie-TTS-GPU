# Genie-TTS-GPU

**面向本机与局域网的 Windows 语音合成工作台。** 基于 Genie-TTS／GPT-SoVITS，将 CPU/CUDA 推理、WebUI、HTTP API、长文本作业与阅读器接入组织为可检查的本地服务。

[简体中文](README.md) · [English](README.en.md) · [环境准备](Docs/Quickstart.md) · [API 文档](Docs/API-Service.md)

## 可以用来做什么

| 场景 | 使用方式 |
| --- | --- |
| 在浏览器里测试声音 | WebUI 加载角色、设置参考音频和文本，生成并试听 |
| 为小说、文档准备长音频 | 作业接口提交长文本，查询进度、取消任务、下载最终 WAV |
| 接入 Android 阅读器 | 优先使用 Legado buffered 完整 WAV 示例，客户端单独验证 |
| 为自己的程序提供语音 | HTTP API 区分 raw PCM、分块 WAV 和完整 WAV |
| 检查计算设备与服务状态 | 查看 `/runtime` 的实际模型提供方，以及 `/status` 的任务状态 |

![本地 CPU 模式下的真实 WebUI，未加载模型](Docs/assets/showcase/webui-desktop.png)

截图来自 2026-10-17 的本地 CPU 界面，未加载角色；它展示界面与状态，不代表 GPU 性能或音质验收。[更多界面和代表流程](Docs/Showcase.md)。

## 开始之前

**源码仓库不包含可直接运行的完整整合包。** 下载 ZIP 或 clone 后仍需准备包内 Python、依赖、共享资源、角色模型和参考音频；这些不进入 Git。

当前脚本面向 Windows，目录示例为 `E:\Genie-TTS`：

| 目录 | 内容 |
| --- | --- |
| `Runtime/Python`、`Runtime/.venv` | 包内 Python 与依赖；CPU 依赖和 CUDA overlay 分别维护 |
| `GenieData` | G2P、HuBERT、说话人编码等共享资源 |
| `CharacterModels` | 自行准备且有权使用的角色 ONNX 模型与参考音频 |
| `UserData` | 本地状态及任务音频输出 |

GPU 模式还需要兼容的 NVIDIA 驱动及包内 CUDA/cuDNN 依赖。完整路径和准备条件见[首次合成指南](Docs/Quickstart.md)；不要把系统 Python、全局 CUDA 或修改机器 PATH 当作正常运行前提。

## 先完成一次本机合成

准备好上述环境后，从只监听本机的 CPU 模式开始：

```cmd
E:\Genie-TTS\go-webui.bat --host 127.0.0.1 --runtime cpu
```

1. 按启动器打印的本机地址打开 `/ui`，确认运行模式。
2. 填写角色名、模型目录、语言、参考音频与对应原文，完成加载与参考设置。
3. 输入一段自己的文本，选择完整 WAV，生成后试听并检查内容是否完整。
4. 需要 GPU 时，按[运行指南](Docs/Quickstart.md)选择 CUDA，再加载模型并检查实际 session providers。

不带参数双击启动器默认请求 CUDA、监听 `0.0.0.0`；端口占用时可能选择空闲端口，以打印地址为准。上面的命令显式选择本机 CPU，不会更改启动器默认值。

## 接入方式怎么选

| 需求 | 推荐入口 | 需要留意 |
| --- | --- | --- |
| 普通播放器或文件下载 | `/tts/wav` | 等待合成完成后返回完整 WAV |
| Android/Legado 阅读 | `/tts/legado.wav?mode=buffered` | 当前推荐兼容路径，仍需实际手机验收 |
| 较长文本与后台任务 | `/jobs/tts` | 提交、轮询，再下载完成任务的 WAV |
| 低延迟自定义客户端 | `/tts/raw` 或 stream WAV | PCM 与分块 WAV 有格式、长度和客户端兼容差异 |

复制请求和加载参考示例见[首次合成](Docs/Quickstart.md)，字段、错误与并发语义以 [API 合同](Docs/API-Service.md)为准。[阅读器模板](Examples/legado_http_tts_buffered.json)中的地址需要替换成手机可达的电脑地址；手机的 `127.0.0.1` 指手机自身。

## 文档导航

| 你要做什么 | 阅读入口 |
| --- | --- |
| 准备环境、加载模型、首次合成 | [中文步骤](Docs/Quickstart.md) · [English steps](Docs/Quickstart.en.md) |
| 无法启动、没有声音、GPU 或阅读器异常 | [故障排查](Docs/Troubleshooting.md) |
| 编写客户端、提交作业 | [API 合同](Docs/API-Service.md) · [直接调用示例](Examples/api_client.py) · [作业示例](Examples/api_job_client.py) |
| 了解模块和个人增量工作 | [架构](Docs/Architecture.md) · [项目展示](Docs/Showcase.md) |
| 维护环境、检查运行与音频 | [维护和验证](Docs/Maintenance.md) |

## 使用边界与来源

- 服务不自带公网身份与访问控制；局域网接入按实际网络边界配置，不直接暴露到不可信网络。
- API 正常、WAV 结构正确、GPU session 创建和中文内容正确是不同验收项。音频需要试听，不宣称未经测量的加速倍数。
- 推理与模型基础来自 [Genie-TTS](https://github.com/High-Logic/Genie-TTS)／[GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)。本仓库主要维护 Windows 运行整合、服务、WebUI、任务与客户端兼容，不把上游模型与算法写作个人原创。
- 源码许可见 [LICENSE](LICENSE)。模型、参考声音、上游组件和生成音频的使用条件需分别核对；仓库不授予第三方声音或素材的额外权利。
