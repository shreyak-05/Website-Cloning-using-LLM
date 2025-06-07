# # # hello.py
# # #working code
# # from fastapi import FastAPI, HTTPException
# # from fastapi.middleware.cors import CORSMiddleware
# # from pydantic import BaseModel, HttpUrl
# # import uvicorn

# # import httpx
# # from bs4 import BeautifulSoup
# # import anthropic
# # import os
# # # from hyperbrowser import Hyperbrowser  

# # app = FastAPI(
# #     title="Orchids Cloner via Claude 4 Sonnet",
# #     description="FastAPI backend using Anthropic Claude 4 Sonnet",
# #     version="1.0.0"
# # )

# # # 1) Allow CORS so your Next.js frontend can call /api/clone
# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["*"],  # In production, restrict to your frontend’s domain
# #     allow_credentials=True,
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )

# # # 2) Pydantic models for request/response
# # class CloneRequest(BaseModel):
# #     url: HttpUrl

# # class CloneResponse(BaseModel):
# #     html: str

# # # 3) Initialize the Claude client
# # claude_api_key = os.getenv("CLAUDE_API_KEY")
# # if not claude_api_key:
# #     raise RuntimeError("CLAUDE_API_KEY environment variable is not set")

# # # For recent versions of anthropic-python, you use “Anthropic” class
# # client = anthropic.Anthropic(api_key=claude_api_key)

# # # Anthropic’s prompt markers
# # HUMAN_PROMPT = anthropic.HUMAN_PROMPT
# # AI_PROMPT    = anthropic.AI_PROMPT

# # @app.post("/api/clone", response_model=CloneResponse)
# # async def clone_website(request: CloneRequest):
# #     target_url = str(request.url)

# #     # 4) Fetch raw HTML
# #     try:
# #         async with httpx.AsyncClient(timeout=30.0) as http_client:
# #             resp = await http_client.get(target_url)
# #             resp.raise_for_status()
# #             raw_html = resp.text
# #     except Exception as e:
# #         raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}")

# #     # 5) Parse & extract CSS context
# #     soup = BeautifulSoup(raw_html, "html.parser")

# #     # Inline <style> blocks
# #     style_blocks = soup.find_all("style")
# #     inline_css = "\n".join(block.get_text() for block in style_blocks)

# #     # Fetch first-party linked CSS
# #     linked_css = []
# #     for link_tag in soup.find_all("link", rel="stylesheet"):
# #         href = link_tag.get("href")
# #         if not href:
# #             continue
# #         full_href = href if href.startswith("http") else httpx.URL(target_url).join(href)
# #         try:
# #             async with httpx.AsyncClient(timeout=10.0) as http_client:
# #                 css_resp = await http_client.get(str(full_href))
# #                 if (
# #                     css_resp.status_code == 200
# #                     and "text/css" in css_resp.headers.get("content-type", "")
# #                 ):
# #                     linked_css.append(css_resp.text)
# #         except:
# #             pass

# #     combined_css = inline_css + "\n" + "\n".join(linked_css)

# #     # Extract up to 5 color tokens and 3 font-family lines
# #     colors = set()
# #     fonts  = set()
# #     for line in combined_css.splitlines():
# #         if "font-family" in line:
# #             fonts.add(line.strip())
# #         for token in line.split():
# #             if token.startswith("#") and len(token) in (4, 7):
# #                 colors.add(token)
# #             if token.startswith("rgb("):
# #                 colors.add(token.strip(";"))
# #     colors_list = ", ".join(list(colors)[:10])
# #     fonts_list  = ", ".join(list(fonts)[:10]) or "system default"

# #     # Detect nav, footer, title, and hero image
# #     has_nav    = bool(soup.find("nav"))
# #     has_footer = bool(soup.find("footer"))
# #     title_tag  = soup.title.string if soup.title else "No Title"

# #     hero_img_url = ""
# #     hero_tag = soup.find("img", {"class": lambda c: c and "hero" in c})
# #     if not hero_tag:
# #         hero_tag = soup.find("img", {"id": lambda c: c and "hero" in c})
# #     if hero_tag and hero_tag.get("src"):
# #         raw_src = hero_tag["src"]
# #         hero_img_url = (
# #             raw_src
# #             if raw_src.startswith("http")
# #             else str(httpx.URL(target_url).join(raw_src))
# #         )

# #     # Truncate CSS snippet to ~3000 characters
# #     snippet = combined_css[:5000]

# #     # 6) Build the Anthropic-style prompt
# #     prompt = (
# #         f"{HUMAN_PROMPT}"
# #         f"You are a web-design AI. Below is the design context of a target website:\n\n"
# #         f"URL: {target_url}\n"
# #         f"Title: {title_tag}\n"
# #         f"Has navigation: {has_nav}\n"
# #         f"Has footer: {has_footer}\n"
# #         f"Hero image URL: {hero_img_url or 'none'}\n"
# #         f"Color tokens: {colors_list}\n"
# #         f"Font lines: {fonts_list}\n\n"
# #         f"Here is a snippet of the site’s CSS (trimmed to 3000 chars):\n"
# #         f"```\n{snippet}\n```\n\n"
# #         f"Generate a complete HTML5 document that:\n"
# #         f"  - Inlines all CSS in one <style> block in the <head>.\n"
# #         f"  - Uses the provided color palette (hex or rgb values).\n"
# #         f"  - Applies the main font families (from the CSS snippet).\n"
# #         f"  - Includes a responsive <nav> if “Has navigation” is true (with a minimal burger toggle).\n"
# #         f"  - Includes a hero/banner section—use the actual hero_img_url if provided, otherwise use a placeholder (https://via.placeholder.com/600x400).\n"
# #         f"  - Includes a <footer>.\n\n"
# #         f"Return only the raw HTML (no Markdown, no code fences).\n"
# #         f"{AI_PROMPT}"
# #     )

# #     # 7) Call Claude 4 Sonnet via the “completions” endpoint
   
# #     try:
# #         response = client.messages.create(
# #             model="claude-opus-4-20250514",   # or opus if you want opus
# #             max_tokens=2000,
# #             temperature=0.3,
# #             messages=[
# #                 {"role": "user", "content": prompt}
# #             ],
# #         )
# #         # Claude’s Messages API returns .content as a list of message parts
# #         generated_html = response.content[0].text if hasattr(response.content[0], "text") else response.content[0]
# #         return CloneResponse(html=generated_html)
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=f"Claude API error: {e}")

# # def main():
# #     uvicorn.run("hello:app", host="127.0.0.1", port=8002, reload=True)

# # if __name__ == "__main__":
# #     main()


# # hello.py — Final Working Web Cloner (Layout + Spacing Focused)
# import os
# import asyncio
# import json
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel, HttpUrl
# import uvicorn
# from bs4 import BeautifulSoup
# import anthropic
# from hyperbrowser import AsyncHyperbrowser
# from pyppeteer import connect

# app = FastAPI(title="Orchids Cloner", version="1.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class CloneRequest(BaseModel):
#     url: HttpUrl

# class CloneResponse(BaseModel):
#     html: str

# claude_api_key = os.getenv("CLAUDE_API_KEY")
# hyper_api_key = os.getenv("HYPERBROWSER_API_KEY")

# client = anthropic.Anthropic(api_key=claude_api_key)
# HUMAN_PROMPT = anthropic.HUMAN_PROMPT
# AI_PROMPT = anthropic.AI_PROMPT

# @app.post("/api/clone", response_model=CloneResponse)
# async def clone_website(request: CloneRequest):
#     target_url = str(request.url)

#     try:
#         hb = AsyncHyperbrowser(api_key=hyper_api_key)
#         session = await hb.sessions.create()
#         browser = await connect(browserWSEndpoint=session.ws_endpoint, defaultViewport=None)
#         page = await browser.newPage()

#         await page.goto(target_url, {"waitUntil": "domcontentloaded", "timeout": 90000})
#         await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
#         await asyncio.sleep(4)
#         layout_blocks = await page.evaluate("""() => {
#         const blocks = Array.from(document.querySelectorAll("header, nav, main, section, footer, div"));
#         return blocks.map(el => {
#             const rect = el.getBoundingClientRect();
#             const cs = window.getComputedStyle(el);
#             return {
#                 tag: el.tagName.toLowerCase(),
#                 is_link: el.tagName.toLowerCase() === "a",
#                 is_button: el.tagName.toLowerCase() === "button" || el.className.toLowerCase().includes("btn"),
#                 text: (
#                     el.innerText ||
#                     el.getAttribute("alt") ||
#                     el.getAttribute("aria-label") ||
#                     el.getAttribute("title") ||
#                     ""
#                 ).slice(0, 100).trim(),
#                 width: Math.round(rect.width),
#                 height: Math.round(rect.height),
#                 styles: {
#                     disp: cs.display,
#                     pos: cs.position,
#                     pad: cs.padding,
#                     mar: cs.margin,
#                     gap: cs.gap,
#                     justify: cs.justifyContent,
#                     align: cs.alignItems,
#                     txtAlign: cs.textAlign,
#                     bg: cs.backgroundColor,
#                     color: cs.color
#                 }
#             };
#         }).filter(b =>
#             b.height > 40 &&
#             b.width > 150 &&
#             b.text.length >= 4 &&
#             b.styles.disp !== "none"
#         ).slice(0, 10);  // reduced from 12 to 10
#         }""")

#         raw_html = await page.content()
#         await browser.close()
#         await hb.sessions.stop(session.id)
#         await hb.close()

#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Hyperbrowser error: {e}")

#     soup = BeautifulSoup(raw_html, "html.parser")
#     has_nav = bool(soup.find("nav"))
#     has_footer = bool(soup.find("footer"))
#     title_tag = soup.title.string if soup.title else "No Title"
#     hero_img_url = ""
#     hero = soup.select_one("img.hero") or soup.select_one("img#hero")
#     if hero and hero.get("src"):
#         raw_src = hero["src"]
#         hero_img_url = raw_src if raw_src.startswith("http") else str(request.url.join(raw_src))

#     # Extract inline styles only from layout blocks
#     extracted_styles = {
#         f"{block['tag']}#{block['id']}" if block['id'] else f"{block['tag']}.{block['class']}" if block['class'] else block['tag']: block["styles"]
#         for block in layout_blocks
#     }
#     styles_json = json.dumps(extracted_styles, separators=(',', ':'))


#     def extract_colors_and_fonts(blocks):
#         colors = set()
#         fonts = set()
#         for block in blocks:
#             styles = block.get("styles", {})
#             fg = styles.get("fg", "").strip()
#             bg = styles.get("bg", "").strip()
#             font = styles.get("font", "").strip()

#             if fg and fg != "inherit":
#                 colors.add(fg)
#             if bg and bg != "inherit":
#                 colors.add(bg)
#             if font and font.lower() not in ("", "inherit", "initial"):
#                 fonts.add(font)

#         color_palette = ", ".join(list(colors)[:6]) or "black, white"
#         typography_info = ", ".join(list(fonts)[:3]) or "sans-serif"
#         return color_palette, typography_info
#     color_palette, typography_info = extract_colors_and_fonts(layout_blocks)


#     def extract_brand_elements(soup):
#         logos = []
#         for img in soup.find_all("img"):
#             src = img.get("src", "")
#             alt = img.get("alt", "").lower()
#             if any(keyword in alt for keyword in ["logo", "brand", "icon"]) or "logo" in src.lower():
#                 logos.append(src)

#         return ", ".join(logos) if logos else "No logo or brand icons found"
#     brand_elements = extract_brand_elements(soup)

#     def summarize_component_styles(blocks):
#         summary = {"buttons": 0, "links": 0, "images": 0}
#         for b in blocks:
#             if b.get("is_button"):
#                 summary["buttons"] += 1
#             if b.get("is_link"):
#                 summary["links"] += 1
#             if b.get("is_image"):
#                 summary["images"] += 1

#         parts = []
#         for k, v in summary.items():
#             if v:
#                 parts.append(f"{v} {k}")
#         return ", ".join(parts) or "No key components detected"
#     component_styles = summarize_component_styles(layout_blocks)



#     layout_json = json.dumps(layout_blocks, separators=(',', ':'))
#     # prompt = (
#     #     f"{HUMAN_PROMPT}"
#     #     f"You are a frontend layout cloning AI.\n"
#     #     f"Reconstruct the HTML layout using the blocks below.\n\n"
#     #     f"URL: {target_url}\n"
#     #     f"Title: {title_tag}\n"
#     #     f"Has navigation: {has_nav}\n"
#     #     f"Has footer: {has_footer}\n"
#     #     f"Hero image: {hero_img_url or 'none'}\n\n"
#     #     f"Layout blocks (JSON):\n{layout_json}\n\n"
#     #     f"Rules:\n"
#     #     f"• Output only raw valid HTML5\n"
#     #     f"• Inline all styles inside <style> tag in <head>\n"
#     #     f"• Use spacing/layout styles: display, position, padding, margin, gap, alignItems, justifyContent, textAlign\n"
#     #     f"• If bgImg exists, use it with background-size: cover\n"
#     #     f"• If is_button: use <button>, if is_link: use <a>\n"
#     #     f"• Use semantic tags like <header>, <main>, <section>, <footer>\n"
#     #     f"• Do not explain anything. Return only the HTML document\n"
#     #     f"{AI_PROMPT}"
#     # )
#     prompt = (
#         f"{HUMAN_PROMPT}"
#         f"You are a frontend website cloning AI that recreates visually identical websites.\n"
#         f"Recreate the complete visual design using the provided data and styling information.\n\n"
#         f"URL: {target_url}\n"
#         f"Title: {title_tag}\n"
#         f"Has navigation: {has_nav}\n" 
#         f"Has footer: {has_footer}\n"
#         f"Hero image: {hero_img_url or 'none'}\n"
#         f"Color palette: {color_palette}\n"
#         f"Typography: {typography_info}\n"
#         f"Layout blocks (JSON): {layout_json}\n"
#         f"CSS styles (JSON): {extracted_styles}\n"
#         f"Component styles: {component_styles}\n"
#         f"Brand elements: {brand_elements}\n\n"
#         f"Visual Requirements:\n"
#         f"• Match exact colors and visual hierarchy\n"
#         f"• Reproduce spacing, borders, shadows, and effects\n"
#         f"• Maintain original typography (font families, sizes, weights)\n"
#         f"• Preserve button styles, hover states, and interactions\n"
#         f"• Match background colors, gradients, and textures\n"
#         f"• Replicate image styling and positioning\n"
#         f"• Maintain brand consistency (logos, icons, color scheme)\n\n"
#         f"Layout Instructions:\n"
#         f"• Reproduce exact spacing and alignment\n"
#         f"• Use comprehensive CSS including: display, position, padding, margin, gap, width, height, \n"
#         f"  justifyContent, alignItems, textAlign, backgroundColor, color, fontSize, fontFamily, \n"
#         f"  fontWeight, border, borderRadius, boxShadow, lineHeight, letterSpacing\n"
#         f"• For side-by-side elements, use flexbox/grid with proper gaps\n"
#         f"• Wrap overflowing content appropriately\n\n"
#         f"Output Requirements:\n"
#         f"• Generate complete HTML5 with embedded CSS\n"
#         f"• Include all visual styling to match original design\n"
#         f"• Add placeholder content that matches original tone/style\n"
#         f"{AI_PROMPT}"
#     )


#     try:
#         count = client.beta.messages.count_tokens(
#             model="claude-3-5-sonnet-20240620",
#             messages=[{"role": "user", "content": prompt}]
#         )
#         #print number of tokens

#         # Safe access (no .get())
#         token_count = count.input_tokens  # it's a proper attribute
#         print(f"🔢 Estimated input tokens: {token_count}")

#         if token_count > 1000:
#             raise HTTPException(status_code=400, detail=f"Too many tokens: {token_count}")

#         response = client.messages.create(
#             model="claude-3-5-sonnet-20240620",
#             max_tokens=1700,
#             temperature=0.2,
#             messages=[{"role": "user", "content": prompt}],
#         )
#         generated_html = (
#             response.content[0].text if hasattr(response.content[0], "text") else response.content[0]
#         )
#         return CloneResponse(html=generated_html)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Claude API error: {e}")

# def main():
#     uvicorn.run("hello:app", host="127.0.0.1", port=8002, reload=True, timeout_keep_alive=60)

# if __name__ == "__main__":
#     main()

# hello.py

# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel, HttpUrl
# import uvicorn

# import httpx
# from bs4 import BeautifulSoup
# import anthropic
# import os
# # from hyperbrowser import Hyperbrowser  

# app = FastAPI(
#     title="Orchids Cloner via Claude 4 Sonnet",
#     description="FastAPI backend using Anthropic Claude 4 Sonnet",
#     version="1.0.0"
# )

# # 1) Allow CORS so your Next.js frontend can call /api/clone
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # In production, restrict to your frontend’s domain
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # 2) Pydantic models for request/response
# class CloneRequest(BaseModel):
#     url: HttpUrl

# class CloneResponse(BaseModel):
#     html: str

# # 3) Initialize the Claude client
# claude_api_key = os.getenv("CLAUDE_API_KEY")
# if not claude_api_key:
#     raise RuntimeError("CLAUDE_API_KEY environment variable is not set")

# # For recent versions of anthropic-python, you use “Anthropic” class
# client = anthropic.Anthropic(api_key=claude_api_key)

# # Anthropic’s prompt markers
# HUMAN_PROMPT = anthropic.HUMAN_PROMPT
# AI_PROMPT    = anthropic.AI_PROMPT

# @app.post("/api/clone", response_model=CloneResponse)
# async def clone_website(request: CloneRequest):
#     target_url = str(request.url)

#     # 4) Fetch raw HTML
#     try:
#         async with httpx.AsyncClient(timeout=30.0) as http_client:
#             resp = await http_client.get(target_url)
#             resp.raise_for_status()
#             raw_html = resp.text
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}")

#     # 5) Parse & extract CSS context
#     soup = BeautifulSoup(raw_html, "html.parser")

#     # Inline <style> blocks
#     style_blocks = soup.find_all("style")
#     inline_css = "\n".join(block.get_text() for block in style_blocks)

#     # Fetch first-party linked CSS
#     linked_css = []
#     for link_tag in soup.find_all("link", rel="stylesheet"):
#         href = link_tag.get("href")
#         if not href:
#             continue
#         full_href = href if href.startswith("http") else httpx.URL(target_url).join(href)
#         try:
#             async with httpx.AsyncClient(timeout=10.0) as http_client:
#                 css_resp = await http_client.get(str(full_href))
#                 if (
#                     css_resp.status_code == 200
#                     and "text/css" in css_resp.headers.get("content-type", "")
#                 ):
#                     linked_css.append(css_resp.text)
#         except:
#             pass

#     combined_css = inline_css + "\n" + "\n".join(linked_css)

#     # Extract up to 5 color tokens and 3 font-family lines
#     colors = set()
#     fonts  = set()
#     for line in combined_css.splitlines():
#         if "font-family" in line:
#             fonts.add(line.strip())
#         for token in line.split():
#             if token.startswith("#") and len(token) in (4, 7):
#                 colors.add(token)
#             if token.startswith("rgb("):
#                 colors.add(token.strip(";"))
#     colors_list = ", ".join(list(colors)[:10])
#     fonts_list  = ", ".join(list(fonts)[:10]) or "system default"

#     # Detect nav, footer, title, and hero image
#     has_nav    = bool(soup.find("nav"))
#     has_footer = bool(soup.find("footer"))
#     title_tag  = soup.title.string if soup.title else "No Title"

#     hero_img_url = ""
#     hero_tag = soup.find("img", {"class": lambda c: c and "hero" in c})
#     if not hero_tag:
#         hero_tag = soup.find("img", {"id": lambda c: c and "hero" in c})
#     if hero_tag and hero_tag.get("src"):
#         raw_src = hero_tag["src"]
#         hero_img_url = (
#             raw_src
#             if raw_src.startswith("http")
#             else str(httpx.URL(target_url).join(raw_src))
#         )

#     # Truncate CSS snippet to ~3000 characters
#     snippet = combined_css[:5000]

#     # 6) Build the Anthropic-style prompt
#     prompt = (
#         f"{HUMAN_PROMPT}"
#         f"You are a web-design AI. Below is the design context of a target website:\n\n"
#         f"URL: {target_url}\n"
#         f"Title: {title_tag}\n"
#         f"Has navigation: {has_nav}\n"
#         f"Has footer: {has_footer}\n"
#         f"Hero image URL: {hero_img_url or 'none'}\n"
#         f"Color tokens: {colors_list}\n"
#         f"Font lines: {fonts_list}\n\n"
#         f"Here is a snippet of the site’s CSS (trimmed to 3000 chars):\n"
#         f"```\n{snippet}\n```\n\n"
#         f"Generate a complete HTML5 document that:\n"
#         f"  - Inlines all CSS in one <style> block in the <head>.\n"
#         f"  - Uses the provided color palette (hex or rgb values).\n"
#         f"  - Applies the main font families (from the CSS snippet).\n"
#         f"  - Includes a responsive <nav> if “Has navigation” is true (with a minimal burger toggle).\n"
#         f"  - Includes a hero/banner section—use the actual hero_img_url if provided, otherwise use a placeholder (https://via.placeholder.com/600x400).\n"
#         f"  - Includes a <footer>.\n\n"
#         f"Return only the raw HTML (no Markdown, no code fences).\n"
#         f"{AI_PROMPT}"
#     )

#     # 7) Call Claude 4 Sonnet via the “completions” endpoint
   
#     try:
#         response = client.messages.create(
#             model="claude-opus-4-20250514",   # or opus if you want opus
#             max_tokens=2000,
#             temperature=0.3,
#             messages=[
#                 {"role": "user", "content": prompt}
#             ],
#         )
#         # Claude’s Messages API returns .content as a list of message parts
#         generated_html = response.content[0].text if hasattr(response.content[0], "text") else response.content[0]
#         return CloneResponse(html=generated_html)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Claude API error: {e}")

# def main():
#     uvicorn.run("hello:app", host="127.0.0.1", port=8001, reload=True)

# if __name__ == "__main__":
#     main()




# hello.py
# hello.py

import re
import os
import httpx
import asyncio
import pyppeteer
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import anthropic
import uvicorn
from contextlib import asynccontextmanager

# ─────────── Lifespan / App Initialization ─────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    1) On startup, launch a single headless browser and store it in app.state.browser.
    2) On shutdown, close that browser (so Ctrl+C cleans up properly).
    """
    print("[LIFESPAN] Starting up: launching headless browser...")
    browser = await pyppeteer.launch(
        headless=True,
        args=["--no-sandbox", "--disable-setuid-sandbox"]
    )
    app.state.browser = browser
    yield
    print("[LIFESPAN] Shutting down: closing headless browser...")
    try:
        await browser.close()
    except Exception as e:
        print("[LIFESPAN] Error closing browser:", e)
    finally:
        app.state.browser = None


app = FastAPI(
    title="Orchids Cloner via Claude 4 Sonnet",
    description="FastAPI backend using Anthropic Claude 4 Sonnet",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────── Anthropic (Claude) Setup ────────────────────────────────────────

claude_api_key = os.getenv("CLAUDE_API_KEY")
if not claude_api_key:
    raise RuntimeError("CLAUDE_API_KEY environment variable is not set")

client = anthropic.Anthropic(api_key=claude_api_key)
HUMAN_PROMPT = anthropic.HUMAN_PROMPT
AI_PROMPT    = anthropic.AI_PROMPT

# ─────────── Pydantic Models ─────────────────────────────────────────────────

class CloneRequest(BaseModel):
    url: HttpUrl

class CloneResponse(BaseModel):
    html: str

# ─────────── Browser Management ──────────────────────────────────────────────

async def get_browser():
    """
    Returns a connected Pyppeteer Browser. If it doesn't exist or is disconnected,
    launches a fresh one and stores it in app.state.browser.
    """
    browser = getattr(app.state, "browser", None)

    # If no browser is stored, or if that browser is not connected, re-launch:
    if browser is None:
        print("[get_browser] No browser in state → launching a new one.")
    else:
        try:
            # isConnected() returns False if browser has closed/crashed
            if not browser.isConnected():
                print("[get_browser] Existing browser is disconnected → closing and re-launching.")
                try:
                    await browser.close()
                except Exception as e:
                    print("[get_browser] Error closing old browser:", e)
                browser = None
            else:
                # Browser is alive; just return it
                return browser
        except Exception as e:
            print("[get_browser] Error checking .isConnected():", e)
            browser = None

    # Launch a new browser and store it
    try:
        new_browser = await pyppeteer.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        app.state.browser = new_browser
        print("[get_browser] Launched new headless browser.")
        return new_browser
    except Exception as e:
        print("[get_browser] Failed to launch new browser:", e)
        raise

async def fetch_with_pyppeteer(target_url: str) -> str:
    """
    Uses get_browser() to ensure we have a running headless browser,
    opens a new page, navigates to target_url, waits for 'networkidle2'
    then returns the HTML via page.content().
    """
    browser = await get_browser()
    page = await browser.newPage()

    # Spoof desktop UA (helps avoid basic bot detection)
    await page.setUserAgent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )

    try:
        await page.goto(target_url, {"waitUntil": "networkidle2", "timeout": 45000})
        # Ensure at least <body> has loaded
        await page.waitForSelector("body", {"timeout": 15000})
        content = await page.content()
    except Exception as e:
        # If anything goes wrong, close this page (to avoid leaks) and re-raise
        await page.close()
        raise
    finally:
        # Always close the page; we only keep the browser alive
        try:
            await page.close()
        except:
            pass

    return content

# ─────────── /api/clone Endpoint ─────────────────────────────────────────────

@app.post("/api/clone", response_model=CloneResponse)
async def clone_website(request: CloneRequest):
    target_url = str(request.url)

    # 1) Fetch the fully rendered HTML
    try:
        rendered_html = await fetch_with_pyppeteer(target_url)
    except Exception as e:
        # If fetch_with_pyppeteer raised “Connection is closed” or any other error,
        # return a 400‐level error to the client
        raise HTTPException(status_code=400, detail=f"Failed to render page: {e}")

    # 2) Parse & extract CSS, colors, fonts, nav/footer, title, hero image, etc.
    soup = BeautifulSoup(rendered_html, "html.parser")

    # Inline <style> blocks
    style_blocks = soup.find_all("style")
    inline_css = "\n".join(block.get_text() for block in style_blocks)

    # Fetch first-party linked CSS
    linked_css = []
    for link_tag in soup.find_all("link", rel="stylesheet"):
        href = link_tag.get("href")
        if not href:
            continue
        full_href = href if href.startswith("http") else httpx.URL(target_url).join(href)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client_http:
                css_resp = await client_http.get(str(full_href))
                if (
                    css_resp.status_code == 200
                    and "text/css" in css_resp.headers.get("content-type", "")
                ):
                    linked_css.append(css_resp.text)
        except:
            pass

    combined_css = inline_css + "\n" + "\n".join(linked_css)

    # Extract up to 3 color tokens and 2 font-family lines
    colors = set()
    fonts  = set()
    for line in combined_css.splitlines():
        if "font-family" in line:
            fonts.add(line.strip())
        for token in line.split():
            if token.startswith("#") and len(token) in (4, 7):
                colors.add(token)
            if token.startswith("rgb("):
                colors.add(token.strip(";"))
    colors_list = ", ".join(list(colors)[:3]) or "none"
    fonts_list  = ", ".join(list(fonts)[:2]) or "system default"

    # Detect nav, footer, title, and hero image
    has_nav    = bool(soup.find("nav"))
    has_footer = bool(soup.find("footer"))
    title_tag  = soup.title.string.strip() if soup.title and soup.title.string else "No Title"

    hero_img_url = ""
    hero_tag = soup.find("img", {"class": lambda c: c and "hero" in c})
    if not hero_tag:
        hero_tag = soup.find("img", {"id": lambda c: c and "hero" in c})
    if hero_tag and hero_tag.get("src"):
        raw_src = hero_tag["src"]
        hero_img_url = (
            raw_src
            if raw_src.startswith("http")
            else str(httpx.URL(target_url).join(raw_src))
        )

    # Truncate combined_css to ~800 characters (so we don’t send 3000 chars to Claude)
    snippet = combined_css[:800]

    # 3) Build a minimal Anthropic‐style prompt (no triple‐backticks on snippet)
    nav_line    = f"Nav: {has_nav}\n"    if has_nav    else ""
    footer_line = f"Footer: {has_footer}\n" if has_footer else ""
    prompt = (
        f"{HUMAN_PROMPT}"
        f"Clone this website:\n"
        f"URL: {target_url}\n"
        f"Title: {title_tag}\n"
        f"{nav_line}"
        f"{footer_line}"
        f"Hero: {hero_img_url or 'https://via.placeholder.com/600x400'}\n"
        f"Colors: {colors_list}\n"
        f"Fonts: {fonts_list}\n\n"
        f"CSS snippet:\n{snippet}\n\n"
        f"Create an HTML5 page that:\n"
        f"  • Inlines the above CSS in <head>.\n"
        f"  • Uses the listed colors and fonts.\n"
        f"  • Generates a responsive nav if needed.\n"
        f"  • Includes the hero image (or placeholder).\n"
        f"  • Includes a footer if needed.\n"
        f"Return only raw HTML (no Markdown nor commentary).\n"
        f"{AI_PROMPT}"
    )

    # 4) Call Claude 4 Sonnet
    try:
        response = client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=600,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = (
            response.content[0].text
            if hasattr(response.content[0], "text")
            else response.content[0]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claude API error: {e}")

    # 5) Strip any leftover triple‐backtick fences ('''…''')
    raw = raw.strip()
    cleaned = re.sub(r"```.*?```", "", raw, flags=re.DOTALL).strip()

    # 6) DEBUG: print + write the first/last 500 chars so you can confirm no fences
    print("====== BEGIN CLEANED HTML ======")
    print(cleaned[:500])
    print("…")
    print(cleaned[-500:])
    print("======= END CLEANED HTML =======")
    with open("/tmp/last_cloned.html", "w", encoding="utf-8") as f:
        f.write(cleaned)
    print("[DEBUG] Written /tmp/last_cloned.html")

    return CloneResponse(html=cleaned)

def main():
    uvicorn.run("hello:app", host="127.0.0.1", port=8002, reload=True)

if __name__ == "__main__":
    main()
