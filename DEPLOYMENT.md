# ConferenceAssistant 部署指南

## 📋 部署方式概览

ConferenceAssistant 支持多种部署方式，可根据不同场景选择合适的部署方案：

| 部署方式 | 适用场景 | 复杂度 | 性能 | 扩展性 |
|---------|---------|-------|------|--------|
| 本地开发 | 开发测试 | 低 | 中 | 低 |
| Docker | 单机部署 | 中 | 高 | 中 |
| 云服务器 | 生产环境 | 中 | 高 | 高 |
| 容器编排 | 大规模部署 | 高 | 极高 | 极高 |

---

## 🔧 环境准备

### 系统要求
- **CPU**: 4核心+ (推荐8核心)
- **内存**: 8GB+ (推荐16GB+)
- **存储**: 20GB+ 可用空间
- **网络**: 稳定的互联网连接（用于API调用）

### GPU加速（可选但推荐）
- **NVIDIA GPU**: RTX 3060+ 或同等性能
- **显存**: 6GB+ VRAM
- **CUDA**: 11.8+
- **Docker GPU支持**: nvidia-docker2

---

## 🚀 快速部署

### 方式1: Docker部署（推荐）

#### 1. 准备配置文件
```bash
# 复制环境配置模板
cp .env.example .env

# 编辑配置文件
nano .env
```

#### 2. 启动服务
```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f conference-assistant

# 检查服务状态
curl http://localhost:8080/docs
```

#### 3. GPU支持（可选）
如果有NVIDIA GPU，修改 `docker-compose.yml`:
```yaml
services:
  conference-assistant:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - WHISPER_DEVICE=cuda
```

### 方式2: 直接部署

#### 1. 环境搭建
```bash
# 克隆项目
git clone <repository-url>
cd ConferenceAssistant

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 2. 配置环境
```bash
# 复制配置模板
cp .env.example .env

# 编辑配置
export DEEPSEEK_API_KEY="your-api-key-here"
```

#### 3. 启动服务
```bash
# 开发模式
uvicorn web_service:app --reload --host 0.0.0.0 --port 8080

# 生产模式
uvicorn web_service:app --host 0.0.0.0 --port 8080 --workers 4
```

---

## 🌐 生产环境部署

### 云服务器部署

#### 1. 服务器准备
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Docker和Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo pip install docker-compose

# 安装NVIDIA驱动（如果有GPU）
sudo apt install nvidia-driver-470
sudo systemctl reboot
```

#### 2. 安全配置
```bash
# 创建应用用户
sudo useradd -m -s /bin/bash conference
sudo usermod -aG docker conference

# 配置防火墙
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 8080  # API服务
```

#### 3. SSL证书配置
```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 申请证书
sudo certbot --nginx -d yourdomain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### 4. Nginx反向代理
创建 `/etc/nginx/sites-available/conference-assistant`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

---

## 📊 监控和日志

### 1. 服务监控
```bash
# 使用Docker Compose监控
docker-compose top

# 查看资源使用
docker stats conference-assistant

# 查看服务日志
docker-compose logs -f --tail=100 conference-assistant
```

### 2. 性能监控
```bash
# 系统资源监控
htop
nvidia-smi  # GPU监控

# API性能测试
ab -n 100 -c 10 http://localhost:8080/docs
```

### 3. 日志管理
```bash
# 配置日志轮转
sudo nano /etc/logrotate.d/conference-assistant

# 内容:
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size 50M
    missingok
    delaycompress
    copytruncate
}
```

---

## 🔄 自动化部署

### GitHub Actions CI/CD
创建 `.github/workflows/deploy.yml`:
```yaml
name: Deploy Conference Assistant

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.4
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /app/ConferenceAssistant
          git pull origin main
          docker-compose down
          docker-compose up -d --build
```

### 自动备份脚本
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/conference-assistant"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份配置文件
cp .env $BACKUP_DIR/.env.$DATE
cp docker-compose.yml $BACKUP_DIR/docker-compose.yml.$DATE

# 备份输出文件
tar -czf $BACKUP_DIR/outputs.$DATE.tar.gz outputs/

# 清理旧备份（保留7天）
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

---

## 🚨 故障排除

### 常见问题

#### 1. 服务无法启动
```bash
# 检查端口占用
netstat -tulpn | grep 8080
lsof -i :8080

# 检查Docker状态
docker-compose ps
docker-compose logs conference-assistant
```

#### 2. GPU不可用
```bash
# 检查NVIDIA驱动
nvidia-smi

# 检查Docker GPU支持
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# 检查容器GPU访问
docker-compose exec conference-assistant python -c "import torch; print(torch.cuda.is_available())"
```

#### 3. API调用失败
```bash
# 检查API密钥
echo $DEEPSEEK_API_KEY

# 测试API连接
curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
     "https://api.deepseek.com/v1/chat/completions" \
     -H "Content-Type: application/json" \
     -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"test"}]}'
```

#### 4. 内存不足
```bash
# 检查系统内存
free -h

# 检查Docker内存限制
docker-compose exec conference-assistant cat /proc/meminfo

# 调整Docker内存限制
# 在docker-compose.yml中添加:
# mem_limit: 8g
# memswap_limit: 8g
```

### 性能优化

#### 1. 模型缓存优化
```bash
# 预下载模型
python -c "from faster_whisper import WhisperModel; WhisperModel('large-v3')"

# 使用本地模型路径
export WHISPER_MODEL_PATH="/path/to/local/model"
```

#### 2. 并发处理优化
```yaml
# docker-compose.yml
services:
  conference-assistant:
    command: uvicorn web_service:app --host 0.0.0.0 --port 8080 --workers 4
```

#### 3. 存储优化
```bash
# 清理临时文件
find ./temp_output -name "*.tmp" -mtime +1 -delete

# 配置自动清理
crontab -e
# 添加: 0 2 * * * find /app/temp_output -name "*.tmp" -mtime +1 -delete
```

---

## 📈 扩展部署

### Kubernetes部署
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: conference-assistant
spec:
  replicas: 3
  selector:
    matchLabels:
      app: conference-assistant
  template:
    metadata:
      labels:
        app: conference-assistant
    spec:
      containers:
      - name: conference-assistant
        image: conference-assistant:latest
        ports:
        - containerPort: 8080
        env:
        - name: DEEPSEEK_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: deepseek
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
---
apiVersion: v1
kind: Service
metadata:
  name: conference-assistant-service
spec:
  selector:
    app: conference-assistant
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

### 负载均衡配置
```nginx
upstream conference_backend {
    server 127.0.0.1:8080;
    server 127.0.0.1:8081;
    server 127.0.0.1:8082;
}

server {
    listen 80;
    location / {
        proxy_pass http://conference_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📞 技术支持

### 获取帮助
- **文档**: 查看 [README.md](./README.md) 和 [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **Issues**: 提交问题到 [GitHub Issues](https://github.com/your-repo/ConferenceAssistant/issues)
- **讨论**: 参与 [GitHub Discussions](https://github.com/your-repo/ConferenceAssistant/discussions)

### 部署检查清单
- [ ] 系统要求确认
- [ ] 依赖安装完成
- [ ] API密钥配置正确
- [ ] 网络防火墙设置
- [ ] SSL证书配置（生产环境）
- [ ] 监控和日志设置
- [ ] 备份策略制定
- [ ] 故障恢复计划

---

**生产部署建议**: 建议在部署到生产环境前，先在测试环境中充分验证所有功能和性能指标。