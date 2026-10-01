# 🐈‍⬛ PaperSort Desktop

<p align="center">
  <strong>把乱糟糟的论文 PDF，整理成真正找得到的文献库。</strong>
</p>

<p align="center">
  Local-first · Open source · Windows · Preview before changes
</p>

<p align="center">
  <a href="https://github.com/coocoomaomao/PaperSort-Desktop/releases/tag/v0.2.0"><img src="https://img.shields.io/badge/Release-v0.2.0-1F3A5F?style=flat-square" alt="Release v0.2.0"></a>
  <a href="https://github.com/coocoomaomao/PaperSort-Desktop/releases/download/v0.2.0/PaperSort-Desktop-v0.2.0-Setup.exe"><img src="https://img.shields.io/badge/Windows-Download-2CB1A1?style=flat-square&logo=windows" alt="Windows Download"></a>
  <a href="https://github.com/coocoomaomao/PaperSort-Desktop/actions/workflows/ci.yml"><img src="https://github.com/coocoomaomao/PaperSort-Desktop/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT License"></a>
</p>

---

## ✨ PaperSort 是做什么的？

论文越下越多，最后经常会变成这样：

`download (17).pdf` · `S0925231223001234-main.pdf` · `paper_final_v2.pdf` …

PaperSort Desktop 会在 **本地** 扫描你的 PDF 文件夹，尽可能识别论文标题、作者、年份与 DOI，找出疑似重复项，并先生成整理预览。

**你确认以后，它才会真正修改文件。**

> **产品原则：能确定的问题才做，不能确定的就让用户确认。**

## 🚀 30 秒开始使用

### 1. 下载 Windows 安装包

**[⬇️ 下载 PaperSort Desktop v0.2.0](https://github.com/coocoomaomao/PaperSort-Desktop/releases/download/v0.2.0/PaperSort-Desktop-v0.2.0-Setup.exe)**

也可以前往 [Releases](https://github.com/coocoomaomao/PaperSort-Desktop/releases) 查看版本记录。

### 2. 安装并打开 PaperSort

把你的论文文件夹直接拖进窗口，或者点击选择文件夹。

### 3. 检查预览，再决定是否应用

PaperSort 不会自动删除重复文件，也不会在你确认前直接重命名。

## 🧩 v0.2.0 功能

| 功能 | 说明 |
| --- | --- |
| 📁 递归扫描 PDF | 一次扫描整个论文文件夹 |
| 🏷️ 本地元数据识别 | 提取标题、作者、年份、DOI |
| ♻️ 重复论文检测 | SHA-256 完全重复 + 同 DOI 检测 |
| 👀 左右对比重复项 | 对比文件名、大小、页数、标题、作者、年份、DOI、路径 |
| ✍️ 自定义命名模板 | 支持 `{year}` `{author}` `{title}` `{doi}` |
| 🧾 修改前预览 | 每个文件先显示建议结果 |
| 🗂️ 年份子文件夹 | 可选按年份整理 |
| 📤 CSV / BibTeX 导出 | 导出扫描后的文献清单 |
| ↩️ 撤销 | 保存本地 undo manifest，可撤销上一次整理 |
| 🔒 Local only | PDF 不上传，不自动删除 |

示例命名：

```text
2026_Smith_Clean_Research_Title.pdf
```

也可以改成：

```text
{author}_{year}_{title}
{year}-{doi}
{title}
```

## 🔒 隐私与安全

PaperSort v0.2.0 的论文扫描与整理在本地完成：

- 不上传 PDF 内容
- 不自动删除重复文件
- 疑似重复项默认不选中
- 修改前必须预览
- 真正应用修改前再次确认
- 整理记录保存在所选文献库的 `.papersort/history`
- 批量重命名中途失败时会尽力回滚

更多说明见 [Privacy Notes](docs/PRIVACY.md)。

## 🛠️ 从源码运行

需要 Python 3.11+。

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
papersort
```

开发环境：

```bash
pip install -e ".[dev]"
pytest
```

## 📦 Windows 构建

Windows 版本通过 GitHub Actions 自动完成：

`pytest → PyInstaller → EXE smoke test → Inno Setup → Installer`

也就是说，安装包不仅要“能打出来”，打包后的 EXE 还必须实际通过启动自检。

## 🗺️ 下一步

- 更强的作者识别
- 元数据置信度提示
- 更多导出格式
- 可选在线元数据补全
- 全文搜索与标签

完整计划见 [Roadmap](docs/ROADMAP.md)。

## 🤝 Contributing

欢迎提交 Issue 和 Pull Request。较大的改动请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 📄 License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  <strong>MeowBuild Lab</strong><br>
  一只猫，认真造点有用的。 🐈
</p>
