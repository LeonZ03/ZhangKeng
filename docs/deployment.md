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

站点将 Three.js r180 随源码保存在 `site/vendor/`，正式发布使用预先导出的 `site/assets/zhangkeng.glb`。构建生成按内容哈希命名的 gzip 下载包，并在 `dist/version.json` 记录提交与下载地址。原始 GLB 保留供浏览器兼容使用。原始图纸、照片及完整 Blender 工程保存在本地。用 `npm run preview` 检查发布产物。 [模型重建方法](reconstruction.md#重建-blender-工程和网页资产)

推送 `main` 后，在 Pages 的生产部署记录确认提交和构建状态。首次发布还需核对自定义域的 HTTPS。访问线上 `version.json` 可确认域名正在提供的提交。
