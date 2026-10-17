# Genie-TTS-GPU 中文文档入口

中文默认首页已迁至 [README.md](README.md)，英文为 [README.en.md](README.en.md)。
本页仅保留历史链接与章节锚点，具体步骤和协议通过下列入口维护，避免两份中文正文漂移。

## 先看什么

[中文首页](README.md)提供定位、功能和文档导航；[English](README.en.md)提供对应英文入口。

## 获取与准备

源码不包含运行时或模型。准备条件见[中文首页](README.md#开始之前)与[环境准备](Docs/Quickstart.md#获取与准备)。

## 包内运行规则

包内 Python、依赖与模型边界见[运行规则](Docs/Quickstart.md#包内运行规则)。

## 快速开始

加载模型、设置参考、生成 WAV 与阅读器步骤见[首次合成](Docs/Quickstart.md#快速开始)。

## 主要端点

完整字段、响应及错误语义统一见 [API 合同](Docs/API-Service.md)。

## 音频格式

完整 WAV、buffered、stream 和 PCM 的选择见[接入方式](README.md#接入方式怎么选)，协议以 [API 合同](Docs/API-Service.md)为准。

## 验证命令

开发者验证与运行检查统一见[维护指南](Docs/Maintenance.md)。音频内容仍需试听。

## 示例

[直接调用](Examples/api_client.py) · [长文本作业](Examples/api_job_client.py) · [阅读器 buffered 模板](Examples/legado_http_tts_buffered.json)。

## 文档地图

统一见[中文首页文档导航](README.md#文档导航)。

## 开发注意事项

维护要求见 [AGENTS](AGENTS.md) 与[维护指南](Docs/Maintenance.md)，运行边界以正式合同为准。

## 上游来源

项目来源和源码许可见[中文首页](README.md#使用边界与来源)，第三方模型与声音资源分别核对使用条件。
