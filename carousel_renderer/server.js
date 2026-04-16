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
  const { jsx_code, theme, topic_id } = req.body;

  if (!jsx_code || !topic_id) {
    return res.status(400).json({ error: "Missing jsx_code or topic_id" });
  }

  // Generate a basic HTML container that runs babel to render the JSX on the fly
  const htmlContent = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <script src="https://cdn.tailwindcss.com"></script>
      <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
      <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
      <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
      
      <!-- Theme variables -->
      <style>
         @import url('https://fonts.googleapis.com/css2?family=${(theme?.font_heading || "Inter").replace(" ", "+")}:wght@700&family=${(theme?.font_body || "Inter").replace(" ", "+")}:wght@400&display=swap');
         
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
      
      <script>
        tailwind.config = {
          theme: {
            extend: {
              colors: {
                primary: 'var(--primary)',
                secondary: 'var(--secondary)',
                accent: 'var(--accent)',
                bg: 'var(--bg)',
                text: 'var(--text)'
              },
              fontFamily: {
                heading: ['"${theme?.font_heading || "Inter"}"', 'sans-serif'],
                body: ['"${theme?.font_body || "Inter"}"', 'sans-serif'],
              }
            }
          }
        }
      </script>
    </head>
    <body class="bg-bg text-text font-body">
      <div id="root"></div>

      <script type="text/babel" data-type="module">
        ${jsx_code}
        
        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<Carousel />);
      </script>
    </body>
    </html>
  `;

  let browser;
  try {
    const outputDir = path.join(EXPORTS_DIR, topic_id);
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }
    
    // Write temporary HTML file
    const tempHtmlPath = path.join(outputDir, "temp_render.html");
    fs.writeFileSync(tempHtmlPath, htmlContent);

    // Using new syntax
    browser = await puppeteer.launch();
    
    const page = await browser.newPage();
    await page.setViewport({ width: 1080, height: 1350, deviceScaleFactor: 2 });
    
    // Navigate to temp html
    await page.goto(`file://${tempHtmlPath}`, { waitUntil: 'networkidle0' });
    
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

    fs.unlinkSync(tempHtmlPath);
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
