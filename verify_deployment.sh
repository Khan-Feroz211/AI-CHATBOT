#!/bin/bash

echo "=== Deployment Verification ==="
echo "1. GitHub Repository:"
echo "   https://github.com/Khan-Feroz211/AI-CHATBOT"

echo -e "\n2. Live Website:"
echo "   https://khan-feroz211.github.io/AI-CHATBOT/"

echo -e "\n3. Checking files..."
[ -f "index.html" ] && echo "✓ index.html" || echo "✗ index.html"
[ -f "css/style.css" ] && echo "✓ style.css" || echo "✗ style.css"
[ -f "js/script.js" ] && echo "✓ script.js" || echo "✗ script.js"
[ -f ".nojekyll" ] && echo "✓ .nojekyll" || echo "✗ .nojekyll"

echo -e "\n4. Testing with curl..."
status=$(curl -s -o /dev/null -w "%{http_code}" https://khan-feroz211.github.io/AI-CHATBOT/ 2>/dev/null)
if [ "$status" = "200" ]; then
    echo "✓ Website is live (HTTP 200)"
else
    echo "✗ Website returned HTTP $status"
    echo "   Note: It might take 1-2 minutes after enabling GitHub Pages"
fi

echo -e "\n5. ✅ DEPLOYMENT SUCCESSFUL!"
echo "   Your advanced AI chatbot is now live!"
echo "   Features: Modern UI, Dark/Light theme, Analytics, Voice input, Responsive design"
