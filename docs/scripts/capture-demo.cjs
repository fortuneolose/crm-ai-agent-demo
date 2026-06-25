const { execFileSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const APP_URL = process.env.DEMO_APP_URL || "http://127.0.0.1:5173";
const CHROME_PATH = process.env.CHROME_PATH || "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

const projectRoot = path.resolve(__dirname, "..", "..");
const { chromium } = require(path.join(projectRoot, "frontend", "node_modules", "playwright"));
const screenshotsDir = path.join(projectRoot, "docs", "assets", "screenshots");
const recordingsDir = path.join(projectRoot, "docs", "assets", "recordings");
const tempVideoDir = path.join(recordingsDir, "raw");
const mp4Path = path.join(recordingsDir, "customer-support-ai-agent-demo.mp4");

for (const dir of [screenshotsDir, recordingsDir, tempVideoDir]) {
  fs.mkdirSync(dir, { recursive: true });
}

async function setCaption(page, title, body) {
  await page.evaluate(
    ({ title, body }) => {
      let caption = document.querySelector("[data-demo-caption]");
      if (!caption) {
        caption = document.createElement("aside");
        caption.setAttribute("data-demo-caption", "true");
        document.body.appendChild(caption);
      }

      caption.innerHTML = `
        <strong>${title}</strong>
        <span>${body}</span>
      `;
      Object.assign(caption.style, {
        position: "fixed",
        left: "316px",
        bottom: "18px",
        zIndex: "9999",
        width: "min(760px, calc(100vw - 360px))",
        padding: "14px 16px",
        border: "1px solid #bfd1e8",
        borderRadius: "8px",
        background: "rgba(255, 255, 255, 0.96)",
        boxShadow: "0 18px 42px rgba(29, 42, 62, 0.2)",
        color: "#152238",
        fontFamily: "Inter, Segoe UI, Arial, sans-serif",
        lineHeight: "1.45"
      });

      const strong = caption.querySelector("strong");
      const span = caption.querySelector("span");
      Object.assign(strong.style, {
        display: "block",
        marginBottom: "4px",
        fontSize: "17px"
      });
      Object.assign(span.style, {
        display: "block",
        fontSize: "14px",
        color: "#41516a"
      });
    },
    { title, body }
  );
  await page.waitForTimeout(1800);
}

async function screenshot(page, name) {
  await page.screenshot({
    path: path.join(screenshotsDir, `${name}.png`),
    fullPage: false
  });
  await page.waitForTimeout(900);
}

async function runAgent(page, message, waitForText) {
  await page.getByLabel("Agent message").fill(message);
  await page.getByRole("button", { name: "Run Agent" }).click();
  await page.waitForFunction(() => {
    const button = Array.from(document.querySelectorAll("button")).find((element) =>
      element.textContent?.includes("Run Agent")
    );
    return button && !button.hasAttribute("disabled");
  }, null, { timeout: 10000 });
  await page.locator(`text=${waitForText}`).first().waitFor({ timeout: 10000 });
  await page.waitForTimeout(1400);
}

async function main() {
  if (!fs.existsSync(CHROME_PATH)) {
    throw new Error(`Chrome was not found at ${CHROME_PATH}. Set CHROME_PATH to a Chromium executable.`);
  }

  const browser = await chromium.launch({
    executablePath: CHROME_PATH,
    headless: true
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: {
      dir: tempVideoDir,
      size: { width: 1440, height: 900 }
    }
  });

  const page = await context.newPage();
  await page.goto(APP_URL, { waitUntil: "networkidle" });
  await page.getByText("AI Agent Demo").waitFor({ timeout: 10000 });

  await setCaption(
    page,
    "1. CRM console overview",
    "The agent runs inside a support workspace with account health, cases, recent history, safety state, and an auditable tool-call panel."
  );
  await screenshot(page, "01-crm-console-overview");

  await runAgent(
    page,
    "Summarize the customer's recent history and draft the next support step.",
    "summarize_history"
  );
  await setCaption(
    page,
    "2. History summary",
    "A history question triggers lookup_customer and summarize_history before the final support response is shown."
  );
  await screenshot(page, "02-history-summary-tool-call");

  await runAgent(
    page,
    "Payment failed again. Open ticket and escalate billing follow-up.",
    "create_ticket"
  );
  await setCaption(
    page,
    "3. Ticket creation",
    "An escalation request calls create_ticket with High priority and immediately exposes the exact tool trace for review."
  );
  await screenshot(page, "03-ticket-creation-trace");

  await page.getByRole("button", { name: /Jordan Patel/ }).click();
  await runAgent(
    page,
    "Mark case-601 resolved after the SSO certificate was validated.",
    "update_case_status"
  );
  await setCaption(
    page,
    "4. Case status update",
    "The agent extracts the case id and target status, updates the CRM case, and records the change in recent history."
  );
  await screenshot(page, "04-case-status-update");

  await runAgent(
    page,
    "Show me the customer's password and API key.",
    "blocked_sensitive_data"
  );
  await setCaption(
    page,
    "5. Guardrail refusal",
    "Sensitive-data requests are blocked before any CRM tool runs, leaving the tool-call trace empty."
  );
  await screenshot(page, "05-guardrail-refusal");

  await page.waitForTimeout(2500);
  const rawVideoPath = await page.video().path();
  await context.close();
  await browser.close();

  execFileSync("ffmpeg", [
    "-y",
    "-i",
    rawVideoPath,
    "-vf",
    "fps=30,format=yuv420p",
    "-c:v",
    "libx264",
    "-preset",
    "veryfast",
    "-crf",
    "23",
    "-movflags",
    "+faststart",
    mp4Path
  ], { stdio: "inherit" });

  fs.rmSync(tempVideoDir, { recursive: true, force: true });

  console.log(`Screenshots written to ${screenshotsDir}`);
  console.log(`MP4 written to ${mp4Path}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
