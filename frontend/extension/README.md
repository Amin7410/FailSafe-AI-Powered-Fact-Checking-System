# FailSafe Browser Extension

A Chrome extension that provides AI-powered fact-checking and misinformation analysis for web content.

## Features

- **Quick Analysis**: Analyze selected text or entire web pages
- **Claim Highlighting**: Automatically highlight potential claims on web pages
- **Real-time Fact Checking**: Get instant analysis results
- **Evidence Sources**: View supporting evidence and sources
- **Logical Fallacy Detection**: Identify common logical fallacies
- **AI Content Detection**: Detect AI-generated content
- **Keyboard Shortcuts**: Quick access via keyboard shortcuts
- **Settings Management**: Customizable settings and preferences

## Installation

### Development Installation

1. Clone the FailSafe repository
2. Navigate to the extension directory:
   ```bash
   cd frontend/extension
   ```

3. Open Chrome and go to `chrome://extensions/`
4. Enable "Developer mode" in the top right
5. Click "Load unpacked" and select the extension directory
6. The FailSafe extension should now appear in your extensions list

### Production Installation

1. Download the extension from the Chrome Web Store (when available)
2. Click "Add to Chrome" to install

## Usage

### Basic Usage

1. **Analyze Selected Text**:
   - Select any text on a webpage
   - Right-click and select "Fact Check with FailSafe" or use Ctrl+Shift+F
   - View the analysis results in the popup

2. **Analyze Entire Page**:
   - Click the FailSafe extension icon
   - Click "Analyze Page" to analyze the entire page content
   - View results in the popup

3. **Highlight Claims**:
   - Click the FailSafe extension icon
   - Click "Highlight Claims" to highlight potential claims on the page
   - Click on highlighted text to see more details

### Keyboard Shortcuts

- **Ctrl+Shift+F**: Analyze selected text
- **Ctrl+Shift+H**: Highlight claims on current page

### Settings

Click the extension icon and then "Advanced Settings" to configure:

- **API URL**: Set the FailSafe API server URL
- **Auto-highlight**: Automatically highlight claims on pages
- **Show Confidence**: Display confidence scores in results
- **Notifications**: Enable/disable desktop notifications
- **Privacy**: Anonymize data and manage history

## API Integration

The extension requires a running FailSafe API server. By default, it connects to `http://localhost:8000`.

### Configuration

1. Open the extension options page
2. Set the correct API URL
3. Test the connection to ensure it's working

### Required API Endpoints

The extension uses the following API endpoints:

- `POST /api/v1/analyze` - Analyze text content
- `GET /api/v1/health` - Health check

## Development

### Project Structure

```
extension/
├── manifest.json          # Extension manifest
├── popup.html            # Popup interface
├── popup.css             # Popup styles
├── popup.js              # Popup functionality
├── content.js            # Content script for page interaction
├── background.js         # Background service worker
├── options.html          # Settings page
├── options.js            # Settings functionality
├── content.css           # Content script styles
└── icons/                # Extension icons
    ├── icon16.png
    ├── icon32.png
    ├── icon48.png
    └── icon128.png
```

### Building

The extension is ready to use as-is for development. For production:

1. Update the version in `manifest.json`
2. Create icons in the `icons/` directory
3. Package the extension using Chrome's packaging tools

### Testing

1. Load the extension in Chrome
2. Test on various websites
3. Verify API connectivity
4. Test all features and settings

## Troubleshooting

### Common Issues

1. **"Analysis failed" error**:
   - Check that the FailSafe API server is running
   - Verify the API URL in settings
   - Check browser console for detailed error messages

2. **Extension not working on some sites**:
   - Some sites may block content scripts
   - Try refreshing the page
   - Check if the site has strict Content Security Policy

3. **Highlights not appearing**:
   - Ensure "Auto-highlight" is enabled in settings
   - Try manually clicking "Highlight Claims"
   - Check if the page has dynamic content loading

### Debug Mode

Enable debug mode by:

1. Open Chrome DevTools
2. Go to the Console tab
3. Look for FailSafe-related messages
4. Check the Network tab for API requests

## Privacy

The extension:

- Stores analysis history locally in your browser
- Can be configured to anonymize data
- Does not send personal information to the API
- Allows you to clear all stored data

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Open an issue on the GitHub repository
3. Contact the FailSafe team

## License

This extension is part of the FailSafe project and follows the same license terms.

