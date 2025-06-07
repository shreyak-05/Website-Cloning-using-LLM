# hello.py — Improved Web Cloner with Fixed Session Management
import os
import asyncio
import json
import logging
import time
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
import uvicorn
from bs4 import BeautifulSoup
import anthropic
from hyperbrowser import AsyncHyperbrowser
from pyppeteer import connect
import pyppeteer.errors

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Orchids Cloner", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CloneRequest(BaseModel):
    url: HttpUrl
    max_input_tokens: Optional[int] = Field(default=3000, ge=500, le=4000, description="Maximum tokens for input prompt")
    max_output_tokens: Optional[int] = Field(default=3000, ge=500, le=3000, description="Maximum tokens for Claude's response")
    include_responsive: bool = Field(default=True)
    css_framework: str = Field(default="tailwind", pattern="^(tailwind|bootstrap|custom)$")

class CloneResponse(BaseModel):
    html: str
    processing_time: float
    token_usage: Dict[str, int]
    warnings: List[str] = []

class CloneStatus(BaseModel):
    status: str
    progress: int
    message: str

# Environment variables
claude_api_key = os.getenv("CLAUDE_API_KEY")
hyper_api_key = os.getenv("HYPERBROWSER_API_KEY")

if not claude_api_key:
    raise RuntimeError("CLAUDE_API_KEY environment variable is not set")
if not hyper_api_key:
    raise RuntimeError("HYPERBROWSER_API_KEY environment variable is not set")

client = anthropic.Anthropic(api_key=claude_api_key)

# Global cache for common patterns
layout_cache = {}
style_patterns = {}

class WebCloner:
    def __init__(self):
        self.session = None
        self.browser = None
        self.hb = None
        self.page = None
        self._cleanup_tasks = []
        
    async def __aenter__(self):
        try:
            logger.info("Initializing WebCloner session...")
            self.hb = AsyncHyperbrowser(api_key=hyper_api_key)
            self.session = await self.hb.sessions.create()
            logger.info(f"Created session: {self.session.id}")
            
            # Connect with timeout and proper error handling
            self.browser = await asyncio.wait_for(
                connect(
                    browserWSEndpoint=self.session.ws_endpoint, 
                    defaultViewport=None,
                    autoClose=False  # Don't auto-close
                ),
                timeout=30
            )
            logger.info("Browser connected successfully")
            return self
        except Exception as e:
            logger.error(f"Failed to initialize WebCloner: {e}")
            await self.cleanup()
            raise e
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
    
    async def cleanup(self):
        """Proper cleanup of resources with error handling"""
        cleanup_errors = []
        
        # Close page first
        if self.page:
            try:
                if not self.page.isClosed():
                    await asyncio.wait_for(self.page.close(), timeout=5)
                    logger.info("Page closed successfully")
            except Exception as e:
                cleanup_errors.append(f"Error closing page: {e}")
                logger.warning(f"Error closing page: {e}")
        
        # Close browser
    # 3) Tear down Puppeteer client
        if self.browser:
            try:
                # try disconnect first (won’t work on some pyppeteer builds)
                if hasattr(self.browser, "disconnect"):
                    await self.browser.disconnect()
                    logger.info("Browser.disconnect() succeeded")
                # if disconnect isn’t there or failed, try the normal close()
                elif hasattr(self.browser, "close"):
                    await asyncio.wait_for(self.browser.close(), timeout=10)
                    logger.info("Browser.close() succeeded")
                else:
                    logger.debug("No disconnect/close on browser, skipping")
            except AttributeError as e:
                # e.g. 'Browser' object has no attribute 'connection'
                logger.debug(f"Ignoring missing‐attribute in browser teardown: {e}")
            except Exception as e:
                cleanup_errors.append(f"Error tearing down browser: {e}")
                logger.warning(f"Error tearing down browser: {e}")


        # Stop hyperbrowser session
        if self.session and self.hb:
            try:
                await asyncio.wait_for(self.hb.sessions.stop(self.session.id), timeout=10)
                logger.info(f"Session {self.session.id} stopped successfully")
            except Exception as e:
                cleanup_errors.append(f"Error stopping session: {e}")
                logger.warning(f"Error stopping session: {e}")
        
        # Close hyperbrowser client
        if self.hb:
            try:
                await self.hb.close()
                logger.info("Hyperbrowser client closed")
            except Exception as e:
                cleanup_errors.append(f"Error closing hyperbrowser: {e}")
                logger.warning(f"Error closing hyperbrowser: {e}")
        
        if cleanup_errors:
            logger.warning(f"Cleanup completed with {len(cleanup_errors)} errors")

    async def is_session_alive(self) -> bool:
        """Check if the browser session is still alive"""
        try:
            if not self.browser or self.browser.connection.closed:
                return False
            
            # Try a simple operation to test connection
            pages = await asyncio.wait_for(self.browser.pages(), timeout=5)
            return True
        except Exception as e:
            logger.warning(f"Session health check failed: {e}")
            return False

def prioritize_blocks(blocks: List[Dict]) -> List[Dict]:
    """Intelligently prioritize layout blocks by importance"""
    scored = []
    for block in blocks:
        score = 0
        
        # Semantic importance
        tag = block.get('tag', '').lower()
        if tag in ['header', 'nav', 'main', 'section', 'footer']:
            score += 20
        elif tag in ['div', 'article', 'aside']:
            score += 10
        
        # Interactive elements
        if block.get('is_button') or block.get('is_link'):
            score += 15
        
        # Size importance (larger elements are often more important)
        width = block.get('width', 0)
        height = block.get('height', 0)
        if width * height > 50000:  # Large elements
            score += 10
        elif width * height > 10000:  # Medium elements
            score += 5
        
        # Text content richness
        text_len = len(block.get('text', ''))
        score += min(text_len * 0.1, 20)
        
        # Visual prominence (positioned elements often important)
        styles = block.get('styles', {})
        if styles.get('pos') in ['fixed', 'sticky', 'absolute']:
            score += 10
        
        scored.append((score, block))
    
    # Return top blocks sorted by score
    return [block for score, block in sorted(scored, key=lambda x: x[0], reverse=True)[:20]]

def create_smart_summary(blocks: List[Dict], max_chars: int = 1500) -> str:
    """Create intelligent summary that fits within character limits"""
    prioritized = prioritize_blocks(blocks)
    
    # Create compact representation
    compact_blocks = []
    for block in prioritized:
        compact = {
            't': block['tag'],
            'w': block['width'],
            'h': block['height'],
            'txt': block['text'][:500],  # Truncate text
        }
        
        # Only include non-default styles
        styles = block.get('styles', {})
        important_styles = {}
        for key, value in styles.items():
            if value and value not in ['', 'initial', 'inherit', 'auto', 'none']:
                important_styles[key] = value
        
        if important_styles:
            compact['s'] = important_styles
            
        # Add interactive flags
        if block.get('is_button'): compact['btn'] = 1
        if block.get('is_link'): compact['lnk'] = 1
        if block.get('is_image'): compact['img'] = 1
        
        compact_blocks.append(compact)
        
        # Check if we're approaching the limit
        current_size = len(json.dumps(compact_blocks, separators=(',', ':')))
        if current_size > max_chars:
            break
    
    return json.dumps(compact_blocks, separators=(',', ':'))

def build_enhanced_prompt(url: str, layout_summary: str, colors: str, fonts: str, 
                         framework: str = "tailwind", responsive: bool = True) -> str:
    """Build an optimized prompt for Claude"""
    
    framework_instructions = {
        "tailwind": "Use Tailwind CSS classes exclusively. Include responsive classes (sm:, md:, lg:).",
        "bootstrap": "Use Bootstrap 5 classes. Include responsive grid system.",
        "custom": "Write custom CSS with modern flexbox/grid layouts."
    }
    
    responsive_note = " Make it fully responsive with mobile-first design." if responsive else ""
    
    prompt = f"""Clone this website layout: {url}

Layout data (compact): {layout_summary}

Colors: {colors}
Fonts: {fonts}

Requirements:
- {framework_instructions[framework]}
- Clean, modern design{responsive_note}
- Preserve visual hierarchy and spacing
- Include proper semantic HTML5 elements
- Make interactive elements functional (buttons, links)

Output only the complete HTML with inline CSS/classes. No explanations."""

    return prompt

async def extract_website_data_with_retry(cloner: WebCloner, url: str, max_retries: int = 2) -> tuple:
    """Extract website data with retry logic for session failures"""
    for attempt in range(max_retries + 1):
        try:
            return await extract_website_data(cloner, url)
        except pyppeteer.errors.NetworkError as e:
            if "Target closed" in str(e) and attempt < max_retries:
                logger.warning(f"Session failed on attempt {attempt + 1}, retrying...")
                await asyncio.sleep(2)
                
                # Check if we need to reinitialize the session
                if not await cloner.is_session_alive():
                    logger.info("Reinitializing browser session...")
                    await cloner.cleanup()
                    
                    # Reinitialize
                    cloner.hb = AsyncHyperbrowser(api_key=hyper_api_key)
                    cloner.session = await cloner.hb.sessions.create()
                    cloner.browser = await connect(
                        browserWSEndpoint=cloner.session.ws_endpoint, 
                        defaultViewport=None,
                        autoClose=False
                    )
                continue
            raise
        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"Extraction failed on attempt {attempt + 1}: {e}")
                await asyncio.sleep(2)
                continue
            raise

async def extract_website_data(cloner: WebCloner, url: str) -> tuple:
    """Extract comprehensive website data (handles dynamic sites like Pinterest)"""
    try:
        # Create a new page
        cloner.page = await cloner.browser.newPage()
        
        # Set reasonable timeouts
        if hasattr(cloner.page, "setDefaultNavigationTimeout"):
            cloner.page.setDefaultNavigationTimeout(60000)

        # Spoof a real browser and disable webdriver flag
        await cloner.page.setUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        await cloner.page.evaluateOnNewDocument("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
        """)

        logger.info(f"Navigating to: {url}")
        
        # Navigate with proper error handling
        try:
            await cloner.page.goto(url, {
                "waitUntil": "networkidle2", 
                "timeout": 60000
            })
        except Exception as e:
            logger.warning(f"Navigation timeout or error: {e}, trying with domcontentloaded")
            await cloner.page.goto(url, {
                "waitUntil": "domcontentloaded", 
                "timeout": 30000
            })

        # 1) Scroll to the bottom in N “page downs”
        max_scrolls = 5
        for _ in range(max_scrolls):
            await cloner.page.evaluate("""
                () => {
                    const sc = document.scrollingElement || document.body;
                    sc.scrollBy({ top: window.innerHeight, behavior: 'smooth' });
                }
            """)
            await asyncio.sleep(1)   # let the scroll start

        # 2) Wait for the scroll to actually reach bottom (or 5s max)
        try:
            await cloner.page.waitForFunction(
                """() => {
                    const sc = document.scrollingElement || document.body;
                    return sc.scrollTop + window.innerHeight >= sc.scrollHeight;
                }""",
                timeout=5000
            )
        except Exception:
            # timed out—still okay, we’ll proceed
            pass

        # 3) Give the page a moment to fire any XHRs / render new nodes
        await asyncio.sleep(2)

        logger.info("Finished scrolling and waiting, now extracting blocks")


            # Extract layout blocks with enhanced data
        logger.info("Extracting layout blocks...")
        layout_blocks = await cloner.page.evaluate("""() => {
            const blocks = Array.from(document.body.querySelectorAll(
                "header, nav, main, section, footer, div, article, aside"
            )).filter(el => {
                const r = el.getBoundingClientRect();
                return r.width > 50 && r.height > 20;
            });
            
            return blocks.slice(0, 100).map((el) => {
                const rect = el.getBoundingClientRect();
                const cs = window.getComputedStyle(el);
                const tag = el.tagName.toLowerCase();
                
                return {
                    tag,
                    id: el.id || "",
                    class: el.className || "",
                    is_link: tag === "a",
                    is_button: tag === "button" || el.className.toLowerCase().includes("btn"),
                    is_image: tag === "img",
                    text: (el.innerText || el.getAttribute("alt") || "").trim().substring(0, 200),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    styles: {
                        disp: cs.display,
                        pos: cs.position,
                        bg: cs.backgroundColor,
                        color: cs.color,
                        font: cs.fontFamily,
                        pad: cs.padding,
                        mar: cs.margin,
                        justify: cs.justifyContent,
                        align: cs.alignItems,
                        txtAlign: cs.textAlign
                    }
                };
            }).filter(b => b && b.text.length > 0);
        }""")

        # Get page HTML and metadata
        raw_html = await cloner.page.content()
        page_title = await cloner.page.title()
        
        logger.info(f"Extracted {len(layout_blocks)} layout blocks")
        return layout_blocks, raw_html, page_title

    except Exception as e:
        logger.error(f"Error extracting website data: {e}")
        raise
    finally:
        # Clean up the page
        if cloner.page and not cloner.page.isClosed():
            try:
                await cloner.page.close()
                cloner.page = None
            except Exception as e:
                logger.warning(f"Error closing page: {e}")

def extract_design_tokens(blocks: List[Dict], soup: BeautifulSoup) -> tuple:
    """Extract colors, fonts, and other design tokens"""
    colors = set()
    fonts = set()
    
    for block in blocks:
        styles = block.get("styles", {})
        
        # Extract colors
        for color_prop in ['color', 'bg']:
            color = styles.get(color_prop, "").strip()
            if color and color not in ("", "rgba(0, 0, 0, 0)", "transparent", "inherit"):
                colors.add(color)
        
        # Extract fonts
        font = styles.get("font", "").strip()
        if font and font not in ("", "inherit", "initial"):
            # Clean up font family string
            font_clean = font.split(',')[0].strip().strip('"\'')
            if font_clean:
                fonts.add(font_clean)
    
    # Limit and format
    color_palette = ", ".join(list(colors)[:8]) or "black, white, #f3f4f6"
    typography = ", ".join(list(fonts)[:4]) or "system-ui, sans-serif"
    
    return color_palette, typography

@app.post("/api/clone", response_model=CloneResponse)
async def clone_website(request: CloneRequest):
    start_time = time.time()
    target_url = str(request.url)
    warnings = []
    
    logger.info(f"Starting clone for: {target_url}")
    
    try:
        async with WebCloner() as cloner:
            # Extract website data with retry
            layout_blocks, raw_html, page_title = await extract_website_data_with_retry(cloner, target_url)
            
            if not layout_blocks:
                raise HTTPException(status_code=400, detail="Could not extract layout data")
            
            # Process design tokens
            soup = BeautifulSoup(raw_html, "html.parser")
            colors, fonts = extract_design_tokens(layout_blocks, soup)
            
            # Create smart summary
            layout_summary = create_smart_summary(layout_blocks, max_chars=2000)
            
            # Build prompt
            prompt = build_enhanced_prompt(
                target_url, layout_summary, colors, fonts,
                request.css_framework, request.include_responsive
            )
            
            # Count tokens
            token_count_response = client.beta.messages.count_tokens(
                model="claude-3-5-sonnet-20241022",
                messages=[{"role": "user", "content": prompt}]
            )
            input_tokens = token_count_response.input_tokens
            
            logger.info(f"Input tokens: {input_tokens}")
            # Generate with Claude
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=request.max_output_tokens,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
            )

            # Pull out the raw HTML
            html = response.content[0].text

            # Compute timings & usage
            processing_time = time.time() - start_time
            usage = getattr(response, "usage", None) or type("u", (), {"input_tokens":0,"output_tokens":0})
            token_usage = {
                "input": usage.input_tokens,
                "output": usage.output_tokens,
                "total": usage.input_tokens + usage.output_tokens,
            }

            # Return immediately
            return CloneResponse(
                html=html,
                processing_time=processing_time,
                token_usage=token_usage,
                warnings=[],
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clone failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cloning failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "2.0"
    }

@app.get("/api/stats")
async def get_stats():
    """Get cloning statistics"""
    return {
        "cache_size": len(layout_cache),
        "patterns": len(style_patterns),
        "uptime": time.time()
    }

def main():
    uvicorn.run(
        "hello:app", 
        host="127.0.0.1", 
        port=8002, 
        reload=False, 
        timeout_keep_alive=120,
        access_log=True
    )

if __name__ == "__main__":
    main()