"""HTML → Markdown 转换器，支持微信公众号格式输出"""
import re
from bs4 import BeautifulSoup


def html_to_markdown(html: str) -> str:
    """将 HTML 转为干净的 Markdown"""
    soup = BeautifulSoup(html, "lxml")

    # 预处理：代码块（必须在 code 处理之前，且用 replace_with 移除整个 pre）
    for pre in soup.find_all("pre"):
        code = pre.get_text()
        lang = ""
        code_el = pre.find("code")
        if code_el and code_el.get("class"):
            for c in code_el.get("class"):
                if c.startswith("language-") or c.startswith("lang-"):
                    lang = c.split("-", 1)[1]
                    break
        pre.replace_with(f"\n```{lang}\n{code}\n```\n")

    # 预处理：行内代码（跳过 pre 的子孙 — 已被 replace_with 移除，但以防万一）
    for code in soup.find_all("code"):
        if code.find_parent("pre") is None:
            code.replace_with(f"`{code.get_text()}`")

    # 预处理：图片
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original") or ""
        alt = img.get("alt", "图片")
        if src and not src.startswith("data:"):
            img.replace_with(f"\n![{alt}]({src})\n")
        else:
            img.replace_with(f"[{alt}]")

    # 预处理：链接（过滤 javascript: 和无意义的 # 锚点，但保留 #section 类有效锚点）
    for a in soup.find_all("a"):
        href = a.get("href", "")
        text = a.get_text(strip=True)
        if href and text and href != "#" and not href.startswith("javascript:") and href != text:
            a.replace_with(f"[{text}]({href})")

    # 预处理：标题
    for level in range(6, 0, -1):
        for h in soup.find_all(f"h{level}"):
            text = h.get_text(strip=True)
            if text:
                h.replace_with(f"\n{'#' * level} {text}\n")

    # 预处理：粗体/斜体
    for b in soup.find_all(["b", "strong"]):
        b.replace_with(f"**{b.get_text()}**")
    for i in soup.find_all(["i", "em"]):
        i.replace_with(f"*{i.get_text()}*")

    # 预处理：列表
    for li in soup.find_all("li"):
        li.replace_with(f"- {li.get_text(strip=True)}")

    # 预处理：段落/换行
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all(["p", "div"]):
        text = p.get_text(strip=True)
        if text:
            p.replace_with(f"\n{text}\n")

    # 获取纯文本
    text = soup.get_text()

    # 清理多余空白
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()

    return text


def markdown_to_wechat(md: str) -> str:
    """
    将 Markdown 转为微信公众号兼容格式
    微信公众号不支持标准 Markdown，需要特殊处理：
    - 标题加粗显示
    - 代码块转为引用块
    - 链接保留文本形式
    """
    lines = md.split("\n")
    result = []
    in_code = False

    for line in lines:
        # 代码块处理
        if line.startswith("```"):
            in_code = not in_code
            if in_code:
                result.append("\n【代码】")
            continue
        if in_code:
            result.append(f"  {line}")
            continue

        # 标题处理
        if line.startswith("# "):
            result.append(f"\n【{line[2:]}】\n")
        elif line.startswith("## "):
            result.append(f"\n▎{line[3:]}\n")
        elif line.startswith("### "):
            result.append(f"\n▶ {line[4:]}\n")
        # 列表
        elif line.startswith("- "):
            result.append(f"  • {line[2:]}")
        # 引用
        elif line.startswith("> "):
            result.append(f"  ❝ {line[2:]}")
        # 普通行
        else:
            result.append(line)

    text = "\n".join(result)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
