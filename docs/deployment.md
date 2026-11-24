# Cloudflare Pages 发布

参考 BeiPiao 使用 Cloudflare Pages 的 GitHub 集成。

| Pages 设置 | 值 |
| --- | --- |
| GitHub 仓库 | `LeonZ03/ZhangKeng` |
| 生产分支 | `main` |
| 框架预设 | None |
| 构建命令 | `npm run build:pages` |
| 输出目录 | `dist` |
| 自定义域名 | `zhangkeng.leonz03.dpdns.org` |

站点将 Three.js r180 随源码保存在 `site/vendor/`。构建只从 `site/` 复制发布资源，并写入 `dist/version.json`。原始图纸和照片留在本机 `references/`。用 `npm run preview` 检查发布产物。

推送 `main` 后，在 Pages 的生产部署记录确认提交和构建状态。首次发布还需核对自定义域的 HTTPS。访问线上 `version.json` 可确认域名正在提供的提交。
