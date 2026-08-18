# SHUN Blog

这是一个独立的 Obsidian 博客 Vault，使用 Quartz 5 构建并由 GitHub Pages 发布。

## 写文章

1. 在 Obsidian 中单独打开 `content` 文件夹作为 Vault。
2. 普通文章直接新建在 `content`；工具文章放进 `content/Tools`；项目文章放进 `content/Projects`。
3. 可以复制 `content/templates/Article.md` 作为新文章模板。
4. 写作期间保留 `draft: true`；要发布时改成 `draft: false`。
5. Obsidian Git 会在停止编辑 5 分钟后自动提交并推送；GitHub Actions 随后自动更新网页。

这个 Vault 已在本机安装 Obsidian Git 2.39.0，并设置为启动时拉取、每 5 分钟检查远端、停止编辑 5 分钟后备份。插件和 Vault 界面设置保存在 `content/.obsidian`，已被 Git 忽略，不会污染网页或上传个人界面配置。

## 本地预览

```bash
npx quartz build --serve
```

浏览器打开终端显示的本地地址即可。

## 发布地址

https://syyf1224.github.io/blog/

## 结构

```text
content/
├── index.md              首页文案
├── Tools/                工具与环境文章
├── Projects/             项目文章
└── templates/Article.md  不会发布的文章模板
```

Quartz 配置在 `quartz.config.yaml`，视觉样式在 `quartz/styles/custom.scss`，自动发布流程在 `.github/workflows/deploy.yml`。

## 官方文档

- Quartz：https://quartz.jzhao.xyz/
- GitHub Pages 部署：https://quartz.jzhao.xyz/hosting
- Obsidian Git：https://github.com/Vinzent03/obsidian-git
