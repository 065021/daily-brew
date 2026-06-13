# 日知录

每天花 3 分钟，搞懂一个跨学科概念。哲学、科学、经济、文学、思想实验、认知偏误——轮流来。

所有文章由 GitHub Actions 每天自动生成，部署到 GitHub Pages，完全免费运行。

## 领域轮值

| 星期 | 领域 |
|------|------|
| 周一 | 哲学 |
| 周二 | 科学 |
| 周三 | 经济/社会 |
| 周四 | 文学/艺术 |
| 周五 | 思想实验 |
| 周六 | 认知偏误 |
| 周日 | 休息 |

## 本地使用

```bash
# 1. 安装依赖
pip install openai

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key

# 3. 手动生成一篇文章
python scripts/generate.py --category 哲学 --dry-run   # 预览 prompt
python scripts/generate.py --category 哲学              # 实际生成

# 4. 构建索引
python scripts/build.py

# 5. 预览前端
cd web && python -m http.server 8080
# 浏览器打开 http://localhost:8080
```

## 部署到 GitHub

1. Fork 或推送此仓库到 GitHub
2. 在 Settings → Secrets and variables → Actions 中添加：
   - `DEEPSEEK_API_KEY`：你的 DeepSeek API Key
3. 在 Settings → Pages 中，Source 设为 "Deploy from a branch"，分支选 `main`，目录选 `/web`
4. 手动触发一次 Actions（Actions → 每日生成 → Run workflow）
5. 几分钟后访问 `https://你的用户名.github.io/仓库名/`

## 成本

- GitHub Pages & Actions：公开仓库免费
- DeepSeek API：约 ¥0.02/篇，月均不到 ¥1
