# 搜索引擎收录提交指引（GSC / Bing / 百度站长）

> 站点已具备：sitemap.xml（448 URL，含 server/skill 详情页）、robots.txt、canonical、hreflang、og 标签、结构化数据。
> 目标：提交 sitemap + 验证站点 + 提交页面。约 1–3 周开始收录，需持续提交。

## 0. 前置确认

- [ ] `curl -s https://trustlens.icodestar.net/sitemap.xml | head` 能正常返回 XML
- [ ] `curl -s https://trustlens.icodestar.net/robots.txt` 返回 Sitemap 声明
- [ ] 首页与详情页都能正常访问（无 404/5xx）

## 1. Google Search Console（最高优先级，海外）

1. 打开 https://search.google.com/search-console ，用 Google 账号登录（**需用户本人 Google 账号**）
2. 添加资源 → 选"网域" → 输入 `icodestar.net`（网域验证，需在 DNS 加 TXT 记录）
   - 备用：选"网址前缀" → `https://trustlens.icodestar.net/` → 用 HTML 文件或 meta 标签验证（需要能往 Aliyun 站点根目录放文件，可用 ssh 上传）
3. 验证通过后：左侧「Sitemap」→ 提交 `sitemap.xml`
4. 「性能」标签：3–6 个月后看收录与点击
5. 用「网址检查」工具对首页 + 一个 server 详情页 + 一个 skill 详情页做"请求编制索引"

**结构化数据验证**：用「富媒体搜索结果」检查 server 详情页的 SoftwareApplication/评分富摘要是否被识别（若报错按提示修）。

## 2. Bing Webmaster（可一键导入 GSC）

1. 打开 https://www.bing.com/webmasters ，微软/Microsoft 账号登录
2. 添加网站 → 选"从 Google 导入"（若已配置 GSC）→ 授权后自动带入
3. 提交 sitemap：`https://trustlens.icodestar.net/sitemap.xml`
4. Bing 会自动同步 GSC 的验证

## 3. 百度站长（国内）

1. 打开 https://ziyuan.baidu.com/ ，用百度账号登录（**需用户本人百度账号**）
2. 添加站点：`https://trustlens.icodestar.net/`
3. 验证方式（三选一，任选可行）：
   - DNS 验证：加一条 TXT 记录（推荐，可复用）
   - HTML 文件验证：上传到站点根目录（ssh 操作）
   - CNAME 验证
4. 提交 sitemap：`https://trustlens.icodestar.net/sitemap.xml`
5. 「普通收录」可手动提交首页 + 常用页；「快速收录」对新闻/博客类，暂无则先普通收录
6. 百度抓取频控低，前 2 周可每周手动提交一次

## 4. 360 搜索 / 搜狗（可选）

- 360 站长平台（zhanzhang.so.com）、搜狗站长（zhanzhang.sogou.com）做同样操作，优先级低于前三者

## 5. 后续维护

- **每周一次**：`curl -sI https://trustlens.icodestar.net/sitemap.xml` 确认 200
- **每次周更后**：GSC「网址检查」把新出现的 server 详情页批量请求索引（周更产生的新页面）
- 3 个月后复盘：GSC 查询词里排名靠前的是哪些 → 反哺内容（如"filesystem mcp score"这类词）
- 中文内容主要吃百度 + 微信内搜索，英文吃 Google——双语架构已就绪，靠持续周更喂
