const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'money_magnet_dashboard.html');
let content = fs.readFileSync(filePath, 'utf-8');

// 1. Fix the Pretendard link issue (remove as="style")
content = content.replace(
    '<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />',
    '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />'
);

// 2. Update font stack globally
content = content.replace(
    "font-family: 'Pretendard', 'Outfit', sans-serif;",
    "font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;"
);

// 3. Make the UI more "comfortable"
// Update CSS root variables
const oldVars = `--primary: #10b981;
            --primary-light: #d1fae5;
            --primary-dark: #059669;
            --bg-dark: #f9fafb; /* Off-white background */
            --sidebar-bg: #ffffff;
            --card-bg: #ffffff;
            --card-border: #e5e7eb;
            --text-main: #111827;
            --text-muted: #6b7280;`;
const newVars = `--primary: #10b981;
            --primary-light: #d1fae5;
            --primary-dark: #059669;
            --bg-dark: #f3f4f6; /* Softer gray background to contrast white cards */
            --sidebar-bg: #ffffff;
            --card-bg: #ffffff;
            --card-border: #f3f4f6; /* Very soft border */
            --text-main: #1f2937;
            --text-muted: #6b7280;`;
content = content.replace(oldVars, newVars);

// Add soft shadow and more padding to panels for "comfortable UI"
content = content.replace(/box-shadow: none;/g, "box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);");
content = content.replace(/border-radius:\s*12px;/g, "border-radius: 16px;");

// Fix any leftover outfit fonts on header titles
content = content.replace(/font-family:\s*'Outfit',\s*sans-serif;/g, "");

// Add a script at the bottom to force cache refresh by appending a timestamp to CSS, though it's in the same file.
// The user is likely seeing a cached version of the HTML. We can't clear their cache, but we can instruct them.

fs.writeFileSync(filePath, content, 'utf-8');
console.log("Comfortable UI refinements applied.");
