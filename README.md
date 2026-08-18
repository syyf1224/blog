# Undefined Field

这个仓库包含一个独立的 Obsidian vault 和一个静态博客。它不会改动你原来用于普通本地笔记的 Obsidian vault。

## 开始写作

1. 在 Obsidian 中只打开 `obsidian/blog-vault/` 这个目录。
2. 进入 `obsidian/blog-vault/_templates/Article.md`，复制一份到 `obsidian/blog-vault/`、`obsidian/blog-vault/Tools/` 或 `obsidian/blog-vault/Projects/`。
3. 修改文章的标题、日期和正文，并把 `draft: false` 后保存。
4. 将改动提交并推送到 GitHub。GitHub Actions 会自动生成网页并发布到 GitHub Pages。

`obsidian/blog-vault/Index.md` 是首页；普通文章会自动出现在首页的文章列表里。带有 `draft: true` 的文章不会公开显示。

## Obsidian 自动同步

在 Obsidian 的 Community plugins 中安装 `Obsidian Git`，然后打开它的设置：

- `Vault backup interval`：设置为 5 分钟或 10 分钟
- `Auto pull interval`：设置为 10 分钟
- 打开自动提交和自动推送

第一次使用时，需要先在 Terminal 中完成一次 GitHub 登录或凭据配置。之后 Obsidian Git 会把你的笔记推送到这个仓库，GitHub Actions 再自动更新网页。

## 本地预览

```sh
python3 scripts/build_site.py
python3 -m http.server 8000 --directory _site
```
