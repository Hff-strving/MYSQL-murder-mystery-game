# 剧本图片资源说明

## 📁 图片目录
`frontend-vue/public/assets/images/`

## 🎨 需要的图片文件

### 剧本封面图片（12张）
根据数据库中的剧本ID，需要以下图片：

1. `script_1001.jpg` - 年轮（情感还原）
2. `script_1002.jpg` - 云使（机制推理）
3. `script_1003.jpg` - 长安疑云（古风推理）
4. `script_1004.jpg` - 时空旅人（科幻硬核）
5. `script_1005.jpg` - 红蝶夫人（恐怖惊悚）
6. `script_1006.jpg` - 百变大侦探（欢乐推理）
7. `script_1007.jpg` - 迷雾庄园（本格推理）
8. `script_1008.jpg` - 民国往事（情感沉浸）
9. `script_1009.jpg` - 末日求生（机制阵营）
10. `script_1010.jpg` - 古董局中局（文化推理）
11. `script_1011.jpg` - 赛博追凶（科幻推理）
12. `script_1012.jpg` - 桃花源记（古风情感）

### 默认图片
- `default.jpg` - 默认占位图

## 🔧 临时解决方案

在没有实际图片的情况下，可以使用以下方法：

### 方法1：使用占位图服务（推荐）
修改 `detail.js` 和 `scripts.js`，使用在线占位图：
```javascript
const coverImage = `https://via.placeholder.com/400x500/1a1a2e/d4af37?text=${script.Title}`;
```

### 方法2：使用渐变色占位
创建简单的SVG占位图，每个剧本使用不同颜色。

### 方法3：使用AI生成
使用AI工具（如Midjourney、DALL-E）生成12张不同风格的剧本封面。

## ✅ 当前状态
- 数据库已配置 `Cover_Image` 字段
- 前端代码已支持图片显示
- 图片路径格式：`assets/images/script_{Script_ID}.jpg`

## 📝 下一步
1. 准备12张图片文件
2. 放入 `frontend-vue/public/assets/images/` 目录
3. 确保文件名与数据库中的 `Cover_Image` 字段匹配
