"""HTML → Markdown + 公众号格式"""
import re
from bs4 import BeautifulSoup

_NBSP   = re.compile(r"\xa0+")
_SPACES = re.compile(r"[ \t]+")
_NL     = re.compile(r"\n{3,}")


def html_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    # pre → code fence
    for pre in soup.find_all("pre"):
        txt = pre.get_text()
        lang = ""
        ce = pre.find("code")
        if ce and ce.get("class"):
            for c in ce.get("class"):
                if c.startswith(("language-", "lang-")):
                    lang = c.split("-", 1)[1]; break
        pre.replace_with(f"\n```{lang}\n{txt}\n```\n")

    # inline code (skip inside pre)
    for c in soup.find_all("code"):
        if c.find_parent("pre") is None:
            c.replace_with(f"`{c.get_text()}`")

    # img
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original") or ""
        alt = img.get("alt", "图片")
        img.replace_with(f"\n![{alt}]({src})\n" if src and not src.startswith("data:") else f"[{alt}]")

    # a (skip javascript:, bare #)
    for a in soup.find_all("a"):
        h = a.get("href", "")
        t = a.get_text(strip=True)
        if h and t and h != "#" and not h.startswith("javascript:") and h != t:
            a.replace_with(f"[{t}]({h})")

    # headings (h6→h1 order to avoid nested conflicts)
    for lv in range(6, 0, -1):
        for h in soup.find_all(f"h{lv}"):
            t = h.get_text(strip=True)
            if t:
                h.replace_with(f"\n{'#' * lv} {t}\n")

    # bold / italic
    for b in soup.find_all(["b", "strong"]):
        b.replace_with(f"**{b.get_text()}**")
    for i in soup.find_all(["i", "em"]):
        i.replace_with(f"*{i.get_text()}*")

    # li
    for li in soup.find_all("li"):
        li.replace_with(f"- {li.get_text(strip=True)}")

    # br → nl
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # p / div
    for el in soup.find_all(["p", "div"]):
        t = el.get_text(strip=True)
        if t:
            el.replace_with(f"\n{t}\n")

    text = soup.get_text()
    text = _NBSP.sub(" ", text)
    text = _SPACES.sub(" ", text)
    text = _NL.sub("\n\n", text)
    return text.strip()


def markdown_to_wechat(md: str) -> str:
    lines = md.split("\n")
    out = []
    in_code = False

    for ln in lines:
        if ln.startswith("```"):
            in_code = not in_code
            if in_code:
                out.append("\n【代码】")
            continue
        if in_code:
            out.append(f"  {ln}")
            continue

        if ln.startswith("# "):     out.append(f"\n【{ln[2:]}】\n")
        elif ln.startswith("## "):  out.append(f"\n▎{ln[3:]}\n")
        elif ln.startswith("### "): out.append(f"\n▶ {ln[4:]}\n")
        elif ln.startswith("- "):   out.append(f"  • {ln[2:]}")
        elif ln.startswith("> "):   out.append(f"  ❝ {ln[2:]}")
        else:                       out.append(ln)

    text = "\n".join(out)
    return _NL.sub("\n\n", text).strip()
