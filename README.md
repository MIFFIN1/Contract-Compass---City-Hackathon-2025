# Compact Compass
### HackMemphis 2025 - Challenge #3

> **Tagline:**  AI-powered gateway to City of Memphis codes and contracts.

---

## The Problem
Memphis has over 130,000 local businesses, but becoming a City vendor is a bureaucratic nightmare. To receive contract alerts, a small business owner—often an expert in their trade, not in government procurement—must categorize themselves using **NIGP Commodity Codes**.

This is a **225+ page PDF** of complex government jargon. It is a massive technical barrier that disproportionately filters out the very Minority and Women-owned Business Enterprises (M/WBEs) the City wants to hire.

## The Solution: Compact Compass
Compact Compass replaces clunky government forms with an intelligent, conversational experience. It uses a **Triple-AI Pipeline** to translate a user's plain-English business description into official government data and instantly matches them with live contract opportunities.

We turn a 3-day headache into a 60-second "luxury" onboarding experience.

### Key Features
* **Conversational Smart Form:** A guided, step-by-step UI that feels like a modern consumer app, not a government portal.
* **AI Agent #1 (The Translator):** Instantly analyzes a business description and identifies the correct official NIGP Commodity Codes from a database of 1,800+ entries.
* **Live Portal Scraper:** Uses **Selenium** to bypass complex JavaScript on the City's procurement portal (`beaconbid.com`) and scrape real-time, active RFP data.
* **AI Agent #2 (The Matchmaker):** Intelligently compares the user's new codes against live contracts to find high-confidence matches instantly.
* **AI Agent #3 (The Profile Builder):** Generates a polished, professional 3-sentence business capability statement that users can copy-paste directly into their official City vendor application.

---

## Tech Stack
* **Frontend:** Vanilla HTML5, Modern CSS3 (Animations, Flexbox), Vanilla JavaScript. Designed for a premium, "Apple-like" user experience with zero external framework dependencies for maximum speed.
* **Backend:** Python (Flask) serving as a lightweight API.
* **AI Engine:** Google Gemini Pro (via `google-generativeai` API).
* **Data Pipeline:** Selenium WebDriver (Chrome Headless) for real-time, dynamic web scraping.

---
