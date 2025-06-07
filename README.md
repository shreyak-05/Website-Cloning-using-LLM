# Orchids SWE Website Cloner

A minimal FastAPI + Pyppeteer backend for cloning websites by extracting design context and generating aesthetically similar HTML using Anthropic Claude.

---
## Background

This project implements a proof‑of‑concept for Orchids’ website cloning feature. It spins up a headless browser (via Hyperbrowser and Pyppeteer), scrapes layout blocks and design tokens (colors, fonts), and then prompts Anthropic Claude-3.5 Sonnet to generate a complete HTML clone with responsive CSS classes.

## Features

* Robust session management with retry logic and custom exception handler
* Headless‐detection bypass (`navigator.webdriver = false`) and realistic user‑agent
* Automatic scrolling and lazy‑load handling
* Prioritized layout block extraction (headers, nav, sections, etc.)
* Design token (color palette & typography) extraction
* Smart prompt engineering for concise Claude input
* Configurable CSS framework (Tailwind, Bootstrap, custom)
* FastAPI endpoints for cloning, health check, and stats


## Process Overview

* Start browserLaunch a Hyperbrowser session and connect Pyppeteer with a real User‑Agent and navigator.webdriver=false.
* Load & scrollNavigate to the target URL and auto‑scroll to surface any lazy‑loaded content.
* Grab layout blocksExtract headers, navs, sections, articles, etc., recording tag, size and element flags (link, button, image).
* Compress dataSummarize block information into a compact JSON snippet.
* Craft LLM promptCombine the JSON summary, extracted colors/fonts and chosen CSS framework into a tight instruction for Claude.
* Generate HTMLSend the prompt to Anthropic Claude-3.5 Sonnet and receive a complete, responsive HTML document.
* Configurable CSS framework (Tailwind, Bootstrap, custom)
* Cleanup & returnClose the page, browser connection and Hyperbrowser session, then return the generated HTML along with stats.

## Prerequisites

* Python 3.9+ (tested with 3.10)
* `npm` & Node.js (for Next.js frontend)
* Access tokens:

  * `CLAUDE_API_KEY` for Anthropic Claude
  * `HYPERBROWSER_API_KEY` for cloud browser sessions

## Installation

### Backend (Python)

1. **Clone the repository**

   ```bash
   git clone <REPO_URL>
   cd orchids-web-cloner
   ```

2. **Set up or activate the Python virtual environment** (for backend only)

   * If you haven’t created a venv yet, run:

     ```bash
     python3 -m venv .venv
     ```

   * **Activate the virtual environment**:

     ```bash
     source .venv/bin/activate
     ```

3. **Install dependencies:**

   ```bash
   pip install --upgrade pip
   pip install fastapi uvicorn[standard] beautifulsoup4 anthropic hyperbrowser pyppeteer pydantic
   ```

#### Alternative: UV Package Management

This project also supports `uv` for package management. You can install and run the backend using `uv` commands instead of pip + uvicorn.

* **Install dependencies**

  ```bash
  uv sync
  ```

* **Run the development server**

  ```bash
  uv run fastapi dev
  ```

### Frontend (Next.js) (Next.js)

1. **Navigate to the frontend directory**

   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**

   ```bash
   npm install
   ```

3. **Run the development server**

   ```bash
   npm run dev
   ```

## Configuration

Create a `.env` file in the project root with the following variables:

```ini
CLAUDE_API_KEY=your-anthropic-api-key
HYPERBROWSER_API_KEY=your-hyperbrowser-api-key
```

Or export them directly in your shell:

```bash
export CLAUDE_API_KEY=your-anthropic-api-key
export HYPERBROWSER_API_KEY=your-hyperbrowser-api-key
```

## Usage

### Running the Backend

From the project root (where `hello.py` lives):

   ```bash
   cd backend
   uvicorn hello:app --host 127.0.0.1 --port 8002 --reload
   ```


### Clone Endpoint

```http
POST /api/clone
Content-Type: application/json

{
  "url": "https://example.com",
  "max_input_tokens": 3000,
  "max_output_tokens": 3000,
  "include_responsive": true,
  "css_framework": "tailwind"
}
```

Response:

```json
{
  "html": "<html>...generated clone...</html>",
  "processing_time": 12.34,
  "token_usage": { "input": 1200, "output": 800, "total": 2000 },
  "warnings": []
}
```

## Customization

* **CSS framework**: set `css_framework` to `tailwind`, `bootstrap`, or `custom` in the clone request.
* **Responsive**: toggle `include_responsive` to enable/disable mobile-first instructions.
* **Model**: switch to a different Claude model by updating `build_enhanced_prompt` and API calls.

## Error Handling

* Network errors and headless‐detach errors are retried up to 5 times.
* Session health is checked before retry; sessions are reinitialized if needed.
* Uncaught exceptions return HTTP 500 with details in the response body.


## Troubleshooting & Known Limitations

* Retry Limit: I retried navigation 5 times (the default) and still couldn’t clone strict sites like Tesla.
* Anti‑bot Protections: I upped max_retries and scroll attempts, extended timeouts (waitUntil, navigation and network idle), randomized the User-Agent, added delays between scrolls, and even routed through a proxy—but Tesla’s bot defenses still blocked the clone.
* Dynamic Content Constraints: I observed heavy client-side frameworks and authentication tokens on Tesla’s pages that require login, making a full clone impossible without valid session credentials.


## Contributing

Contributions welcome! Please open an issue or submit a PR for:

* SPA & heavy‑JS support improvements
* Asset (images/fonts) inlining
* Multi‑model LLM workflows
* Frontend UX enhancements

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
