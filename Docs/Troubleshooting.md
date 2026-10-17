# Genie-TTS-GPU 故障排查

先按症状定位，保留原始模型、参考音频和已有输出。以下只读检查不会安装依赖、加载模型或证明语音内容正确。

## 服务是否已启动

使用启动器实际打印的端口；端口占用时它可能另选空闲端口。假设端口为 8000：

```powershell
$base = 'http://127.0.0.1:8000'
Invoke-RestMethod "$base/health"
Invoke-RestMethod "$base/runtime"
Invoke-RestMethod "$base/status"
```

`/health` 成功只说明进程可响应。合成需要模型加载成功、参考音频可读取且对应文本正确。

## 按症状检查

| 现象 | 先检查 | 下一步 |
| --- | --- | --- |
| 提示缺少 Internal Python | `Runtime/.venv/Scripts/python.exe` 及包内 Python 基础库 | 回到[准备说明](Quickstart.md)，源码 ZIP 本身不含运行环境 |
| 浏览器打不开 | 启动终端是否仍运行、打印地址与端口是否一致 | 先在电脑访问 `127.0.0.1`；手机访问需使用电脑可达地址 |
| CPU 可运行，CUDA 失败 | 驱动、包内 NVIDIA 依赖、实际 session provider | 按[维护链](Maintenance.md)定位，不以 available providers 为成功证据 |
| 切换模式后旧角色仍用原设备 | 运行时配置针对后续加载 session | 核对加载顺序；按 API 合同卸载并重新加载对应模型 |
| 模型或参考加载失败 | 模型目录、语言、文件存在性及参考原文 | 路径是服务电脑上的路径，手机本地路径不能直接传给电脑读取 |
| 阅读器无声，电脑能播放 | 示例 IP、监听地址、同网连通与 WAV 模式 | 优先 buffered 模板；stream WAV 的未知最终长度并非所有 Android 播放器都支持 |
| WAV 有内容但漏字或错读 | 参考文本匹配、语言、输入分句与音频实际内容 | 用较长自写文本、`split_sentence=true` 对照试听，格式通过不等于内容正确 |
| 长文本未立即出现完整音频 | 作业状态、失败原因、是否取消或仍在排队 | 根据[作业 API](API-Service.md)轮询终态，仅完成后下载 WAV |

## 反馈前记录

提供源码提交、启动参数、Python/ONNX Runtime 版本、实际 providers、所选接口与模式、最短复现步骤及脱敏错误。可分享有权公开的最小文本和音频样本；不要上传私人参考音频、模型资源、局域网账户或整份运行目录。

返回[中文首页](../README.md) · [首次合成](Quickstart.md) · [API 合同](API-Service.md)。
