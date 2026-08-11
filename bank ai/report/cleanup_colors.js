const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'money_magnet_dashboard.html');
let content = fs.readFileSync(filePath, 'utf-8');

// Replace remaining primary color rgba values
content = content.split("0, 189, 167").join("0, 153, 143");

// Replace remaining white rgba values for borders/backgrounds to black
content = content.split("rgba(255, 255, 255, 0.08)").join("rgba(0, 0, 0, 0.08)");
content = content.split("rgba(255, 255, 255, 0.05)").join("rgba(0, 0, 0, 0.05)");
content = content.split("rgba(255, 255, 255, 0.1)").join("rgba(0, 0, 0, 0.1)");
content = content.split("rgba(255, 255, 255, 0.15)").join("rgba(0, 0, 0, 0.15)");
content = content.split("rgba(255, 255, 255, 0.03)").join("rgba(0, 0, 0, 0.03)");
content = content.split("rgba(255, 255, 255, 0.04)").join("rgba(0, 0, 0, 0.04)");

fs.writeFileSync(filePath, content, 'utf-8');
console.log("Cleanup completed.");
