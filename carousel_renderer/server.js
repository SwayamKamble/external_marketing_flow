require('dotenv').config({ path: '../.env' }); // Load from root
const express = require("express");
const cors = require("cors");
const puppeteer = require("puppeteer");
const path = require("path");
const fs = require("fs");

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 4000;
const EXPORTS_DIR = path.join(__dirname, "..", "data", "exports");

// Ensure exports dir exists
if (!fs.existsSync(EXPORTS_DIR)) {
  fs.mkdirSync(EXPORTS_DIR, { recursive: true });
}

app.post("/render", async (req, res) => {
  let { jsx_code, theme, topic_id, slides } = req.body;

  if (!jsx_code || !topic_id) {
    return res.status(400).json({ error: "Missing jsx_code or topic_id" });
  }

  // Load additional fonts dynamically if custom slide typography is used
  const allFonts = new Set();
  allFonts.add(theme?.font_heading || "Inter");
  allFonts.add(theme?.font_body || "Inter");
  if (Array.isArray(slides)) {
    for (const slide of slides) {
      if (slide.heading_font) allFonts.add(slide.heading_font);
      if (slide.body_font) allFonts.add(slide.body_font);
    }
  }
  
  const fontImportRules = Array.from(allFonts)
    .map(f => `@import url('https://fonts.googleapis.com/css2?family=${f.trim().replace(/\s+/g, "+")}:wght@400;700;900&display=swap');`)
  const isFullHtml = jsx_code && (jsx_code.includes("<!DOCTYPE") || jsx_code.includes("<html"));

  if (!isFullHtml && (jsx_code === "FRONTEND_RENDERED" || jsx_code)) {
    const slidesData = Array.isArray(slides) ? slides : [];
    
    const slidesHtml = slidesData.map((slide, idx) => {
      const isLast = idx === slidesData.length - 1;
      const st = slide.slide_theme || slide.theme || {};
      const placement = (st?.layout?.image_position || st?.image?.placement || slide.image_placement || "").toLowerCase();
      const isSplitLeft = placement.includes("left");
      const isSplitRight = placement.includes("right");
      const isSplit = isSplitLeft || isSplitRight;

      const headingFont = slide.heading_font ? `"${slide.heading_font}"` : `"${theme?.font_heading || "Inter"}"`;
      const bodyFont = slide.body_font ? `"${slide.body_font}"` : `"${theme?.font_body || "Inter"}"`;
      
      // Font Weight Overrides
      const customHeadingWeight = st?.visual_hierarchy?.headline_weight;
      let headingWeight = slide.heading_font_weight || '900';
      if (customHeadingWeight === "bold" || customHeadingWeight === "900") headingWeight = '900';
      else if (customHeadingWeight === "semibold" || customHeadingWeight === "600") headingWeight = '600';
      else if (customHeadingWeight === "normal" || customHeadingWeight === "regular" || customHeadingWeight === "400") headingWeight = '400';
      else if (customHeadingWeight === "light" || customHeadingWeight === "300") headingWeight = '300';

      const bodyWeight = slide.body_font_weight || '400';
      
      const headingEsc = (slide.heading || "").replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
      const bodyEsc = (slide.body_text || "").replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
      const visualConcept = (st?.image?.description || slide.visual_concept || slide.image_description || "").replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
      
      const isFullImage = placement.includes("background") || placement.includes("full") || placement.includes("whole");
      const hasImage = Boolean((st?.image?.description || slide.image_description || "").trim());

      // Keyword highlighting in Heading
      const highlightWords = Array.isArray(st?.visual_hierarchy?.highlight_words) ? st.visual_hierarchy.highlight_words : [];
      const highlightColor = st?.visual_hierarchy?.highlight_color || theme?.accent_color || "#eab308";
      
      let renderedHeading = headingEsc;
      if (highlightWords.length > 0) {
        const escapedWords = highlightWords
          .map(w => String(w || "").trim())
          .filter(Boolean)
          .map(w => w.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&'));
        if (escapedWords.length > 0) {
          const pattern = escapedWords.join("|");
          const regex = new RegExp(`\\b(${pattern})\\b`, "gi");
          renderedHeading = headingEsc.replace(regex, `<span style="color: ${highlightColor}; font-weight: 900;">$1</span>`);
        }
      }

      // Font Size Override
      const customHeadingSize = st?.visual_hierarchy?.headline_size;
      let slideHeadingFontSize = "54px";
      if (customHeadingSize === "large" || customHeadingSize === "h1") slideHeadingFontSize = "64px";
      else if (customHeadingSize === "medium" || customHeadingSize === "h2") slideHeadingFontSize = "54px";
      else if (customHeadingSize === "small" || customHeadingSize === "h3") slideHeadingFontSize = "42px";

      // Ordering
      let badgeOrder = 1;
      let headingOrder = 2;
      let dividerOrder = 3;
      let bodyOrder = 4;
      let imageOrder = 5;

      const headlinePos = st?.layout?.headline_position || st?.layout?.component_positions?.heading || "";
      if (headlinePos === "bottom") {
        headingOrder = 4;
        dividerOrder = 5;
        bodyOrder = 2;
      }
      if (placement.includes("top")) {
        imageOrder = 0;
      } else if (placement.includes("bottom")) {
        imageOrder = 6;
      }

      const elementPaddingX = isSplit ? "0" : "72px";

      const renderImageHtml = (isSplitImage) => {
        const widthStyle = isSplitImage ? "width: 45%; height: 100%; min-height: 100%; padding: 16px; display: flex; flex-direction: column; justify-content: center; box-sizing: border-box;" : `padding: 8px ${elementPaddingX} 0; height: ${isFullImage ? '34%' : '26%'}; min-height: ${isFullImage ? '160px' : '110px'}; flex: 1 1 auto;`;
        return `
          <div style="${widthStyle} z-index: 2; order: ${imageOrder};">
            <div style="
              border-radius: 16px;
              border: 2px dashed rgba(255, 255, 255, 0.2);
              background: rgba(255, 255, 255, 0.05);
              padding: 24px;
              text-align: center;
              height: 100%;
              box-sizing: border-box;
              display: flex;
              align-items: center;
              justify-content: center;
            ">
              <span style="font-size: 20px; opacity: 0.6; display: flex; flex-direction: column; align-items: center; gap: 10px;">
                <span style="font-size: 32px;">🖼️</span>
                <span>${visualConcept}</span>
              </span>
            </div>
          </div>
        `;
      };

      const renderBadgeHtml = () => `
        <div style="padding: 18px ${elementPaddingX} 0; z-index: 2; order: ${badgeOrder}; flex-shrink: 0;">
          <span style="
            font-size: 24px; font-weight: 900; text-transform: uppercase; letter-spacing: 2.5px;
            padding: 12px 32px; border-radius: 4px; background: var(--accent);
            color: var(--bg); display: inline-block;
          ">
            SLIDE ${slide.slide_number || (idx + 1)}
          </span>
        </div>
      `;

      const renderHeadingHtml = () => `
        <div style="padding: 16px ${elementPaddingX} 0; z-index: 2; order: ${headingOrder}; flex-shrink: 0;">
          <div style="
            font-size: ${slideHeadingFontSize};
            line-height: 1.12;
            font-weight: ${headingWeight};
            font-family: ${headingFont};
            color: var(--text);
            text-shadow: 0 2px 8px rgba(0,0,0,0.3);
            overflow-wrap: anywhere;
          ">
            ${renderedHeading}
          </div>
        </div>
      `;

      const renderDividerHtml = () => `
        <div style="padding: 12px ${elementPaddingX} 0; z-index: 2; order: ${dividerOrder}; flex-shrink: 0;">
          <div style="
            width: 180px; height: 10px; background: var(--accent); border-radius: 2px;
          "></div>
        </div>
      `;

      const renderBodyHtml = () => `
        <div style="padding: 12px ${elementPaddingX} 0; z-index: 2; order: ${bodyOrder}; flex: 0 0 auto; overflow: hidden;">
          <div style="
            font-size: 32px;
            line-height: 1.55;
            opacity: 0.92;
            overflow-wrap: anywhere;
            max-height: ${isFullImage ? '290px' : '490px'};
            overflow: hidden;
          ">
            ${bodyEsc}
          </div>
        </div>
      `;

      const insideContentHtml = isSplit ? `
        <div style="display: flex; flex-direction: row; flex: 1 1 auto; overflow: hidden; width: 100%; height: 100%; box-sizing: border-box;">
          ${isSplitLeft && hasImage ? renderImageHtml(true) : ''}
          <div style="display: flex; flex-direction: column; flex: 1; justify-content: center; padding: 16px 72px; z-index: 2; box-sizing: border-box;">
            ${renderBadgeHtml()}
            ${renderHeadingHtml()}
            ${renderDividerHtml()}
            ${renderBodyHtml()}
          </div>
          ${isSplitRight && hasImage ? renderImageHtml(true) : ''}
        </div>
      ` : `
        ${renderBadgeHtml()}
        ${renderHeadingHtml()}
        ${renderDividerHtml()}
        ${renderBodyHtml()}
        ${hasImage ? renderImageHtml(false) : ''}
      `;

      return `
        <div class="slide-container" style="
          width: 1080px;
          height: 1350px;
          background-color: var(--bg);
          color: var(--text);
          position: relative;
          padding: 80px 0 40px 0;
          box-sizing: border-box;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          font-family: ${bodyFont};
          font-weight: ${bodyWeight};
          margin-bottom: 20px;
        ">
          <!-- Top accent bar -->
          <div style="
            position: absolute; top: 0; left: 0; right: 0; height: 18px;
            background: linear-gradient(90deg, var(--accent), var(--primary), var(--accent));
            z-index: 5;
          "></div>
          
          <!-- Left accent stripe -->
          <div style="
            position: absolute; top: 0; left: 0; bottom: 0; width: 15px;
            background: var(--accent);
            z-index: 5;
          "></div>

          ${insideContentHtml}

          <!-- Decorative Glows -->
          <div style="
            position: absolute; top: -100px; right: -100px;
            width: 360px; height: 360px; border-radius: 50%;
            background: radial-gradient(circle, rgba(234, 179, 8, 0.15) 0%, transparent 70%);
            pointer-events: none; z-index: 1;
          "></div>
          <div style="
            position: absolute; bottom: -100px; left: -100px;
            width: 300px; height: 300px; border-radius: 50%;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%);
            pointer-events: none; z-index: 1;
          "></div>

          <!-- Brand/Footer -->
          <div style="
            display: flex; justify-content: space-between; align-items: center; margin-top: 20px; z-index: 2; padding: 0 72px;
          ">
            <!-- Slide arrow -->
            ${!isLast ? `
              <div style="
                width: 76px; height: 76px; border-radius: 50%;
                display: flex; align-items: center; justify-content: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.4);
                background: var(--accent);
              ">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--bg)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
              </div>
            ` : '<div style="width: 76px;"></div>'}
            <div style="font-size: 24px; font-weight: 700; opacity: 0.55;">@tech_by_pravesh</div>
          </div>
        </div>
      `;
    }).join("\n");

    jsx_code = slidesHtml;
  }

  // Generate a basic HTML container
  const htmlContent = isFullHtml ? jsx_code : `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      
      <!-- Theme variables -->
      <style>
         ${fontImportRules}
         
         body {
            margin: 0;
            padding: 0;
            overflow: hidden; /* Important for exact screenshotting */
            --primary: ${theme?.primary_color || "#3b82f6"};
            --secondary: ${theme?.secondary_color || "#10b981"};
            --accent: ${theme?.accent_color || "#eab308"};
            --bg: ${theme?.background_color || "#0f172a"};
            --text: ${theme?.text_color || "#f8fafc"};
         }
         
         .slide-container {
             width: 1080px;
             height: 1350px; /* Standard IG Carousel ratio 4:5 */
             position: relative;
             overflow: hidden;
         }
      </style>
    </head>
    <body>
      <div id="carousel-container" style="display: flex; flex-direction: column;">
        ${jsx_code}
      </div>
    </body>
    </html>
  `;

  let browser;
  try {
    const outputDir = path.join(EXPORTS_DIR, topic_id);
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }
    
    // Write slides.html file (no temp unlinking so users can edit it)
    const slidesHtmlPath = path.join(outputDir, "slides.html");
    fs.writeFileSync(slidesHtmlPath, htmlContent);

    // Using new syntax
    browser = await puppeteer.launch();
    
    const page = await browser.newPage();
    await page.setViewport({ width: 1080, height: 1350, deviceScaleFactor: 2 });
    
    // Navigate to slides html
    await page.goto(`file://${slidesHtmlPath}`, { waitUntil: 'networkidle0' });
    
    const slidesCount = await page.evaluate(() => {
        const totalHeight = document.body.scrollHeight;
        return Math.floor(totalHeight / 1350);
    });

    const savedFiles = [];
    
    for (let i = 0; i < slidesCount; i++) {
        await page.evaluate((index) => {
            window.scrollTo(0, index * 1350);
        }, i);
        
        await new Promise(r => setTimeout(r, 200));
        
        const filePath = path.join(outputDir, `slide_${String(i+1).padStart(2, '0')}.png`);
        await page.screenshot({ 
            path: filePath,
            clip: { x: 0, y: i * 1350, width: 1080, height: 1350 }
        });
        
        savedFiles.push(filePath);
    }

    await browser.close();

    res.json({ success: true, count: slidesCount, files: savedFiles });

  } catch (error) {
    if (browser) await browser.close();
    console.error(error);
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Carousel Renderer running on http://localhost:${PORT}`);
});
