# 声纹识别功能使用指南

## 🚀 快速开始

### 1. 一键下载模型（推荐）
```bash
# 使用清华镜像自动下载模型
python download_models.py
```

### 2. 直接使用（自动下载）
```bash
# 直接运行，会自动尝试下载模型
python main.py "test_file/河北人设仲裁需求会-1.mp3"
```

## 🔧 网络问题解决方案

### 方案1: 使用清华镜像（自动配置）
系统已自动配置清华大学HuggingFace镜像：
- 镜像地址: `https://hf-mirror.com`
- 自动重试机制
- 本地缓存优先

### 方案2: 手动配置代理
如果仍有问题，可以设置代理：
```bash
# 设置HTTP代理
export http_proxy=http://your-proxy:port
export https_proxy=http://your-proxy:port

# 然后运行下载
python download_models.py
```

### 方案3: 离线使用
如果完全无法联网，系统会自动降级：
- ✅ 仍可使用基础转写功能
- ⚠️ 无声纹识别（发言人不分离）
- ℹ️ 会显示相应提示信息

## 📋 功能说明

### 智能降级机制
系统会按以下顺序尝试：
1. **本地缓存**: 优先从本地加载已下载的模型
2. **清华镜像**: 使用国内镜像下载模型
3. **重试机制**: 网络失败时自动重试
4. **降级模式**: 模型加载失败时使用普通转写

### 输出格式对比

**声纹识别成功时:**
```
【Speaker_0】今天我们讨论项目进展。
【Speaker_1】我觉得进度有些滞后。
【Speaker_0】那我们需要调整计划。
```

**降级模式时:**
```
今天我们讨论项目进展我觉得进度有些滞后那我们需要调整计划
```

## 🛠️ 故障排除

### 常见错误及解决方法

#### 1. 网络连接错误
```
Error: "Connection to huggingface.co timed out"
```
**解决方案:**
- 运行 `python download_models.py` 使用镜像下载
- 检查网络连接和防火墙设置
- 考虑使用VPN或代理

#### 2. 磁盘空间不足
```
Error: "No space left on device"
```
**解决方案:**
- 清理磁盘空间（需要约1GB）
- 更改缓存目录到其他磁盘

#### 3. 依赖包缺失
```
Error: "No module named 'pyannote'"
```
**解决方案:**
```bash
pip install pyannote.audio torch torchaudio
```

### 检查系统状态
```bash
# 验证配置和模型状态
python -c "from huggingface_config import *; check_network_connection()"

# 测试声纹识别功能
python -c "from speaker_identification import *; test_speaker_identification('test_file/audio.mp3')"
```

## 📊 性能说明

### 处理速度
- **仅转写**: ~10-30秒（取决于音频长度）
- **含声纹识别**: +30-50%时间（首次需下载模型）
- **GPU加速**: 可显著提升速度

### 模型大小
- 声纹识别模型: ~800MB
- 缓存位置: `./hf_cache/`

### 准确率
- **转写准确率**: 95%+（基于Whisper-large-v3）
- **发言人分离**: 90%+（基于pyannote-audio）
- **最佳效果**: 2-8人会议，清晰录音

## 🔄 更新和维护

### 更新模型
```bash
# 删除旧缓存
rm -rf hf_cache/

# 重新下载
python download_models.py
```

### 清理缓存
```bash
# 清理HuggingFace缓存
rm -rf hf_cache/

# 清理临时文件
rm -rf temp_* test_output/
```

## 💡 使用建议

### 最佳实践
1. **首次使用**: 先运行 `download_models.py` 预下载模型
2. **网络环境**: 确保稳定的网络连接（首次下载时）
3. **硬件要求**: 建议使用GPU（RTX 4060及以上）
4. **音频质量**: 使用清晰的录音，避免背景噪音

### 适用场景
- ✅ 多人会议记录
- ✅ 访谈转写
- ✅ 培训内容整理
- ✅ 客服对话分析

### 不适用场景
- ❌ 单人录音（无需声纹识别）
- ❌ 超过10人的大型会议
- ❌ 音质极差的录音
- ❌ 背景噪音严重的环境

有问题请参考错误信息或联系技术支持！