# Screenshot Guide for ccpeek

If you're contributing screenshots for the README, please follow these guidelines:

## Required Screenshots

1. **Main Interface** (`screenshots/main.png`)
   - Show the default view with sidebar and a conversation loaded
   - Include both light and dark avatars visible
   - Ensure the logo is clearly visible

2. **Search Functionality** (`screenshots/search.png`)
   - Show active search with highlighted results
   - Include the search counter (e.g., "3/15")
   - Show the clear button (✕)
   - Display sidebar with match counts

3. **Tool Filtering** (`screenshots/filtering.png`)
   - Before: Show conversation with tools visible
   - After: Same conversation with tools hidden
   - Highlight the "Show/Hide Tools" button

4. **Export Options** (`screenshots/export.png`)
   - Show the Export button active
   - If possible, show the download dialog

## How to Take Screenshots

### Linux (Your System)
```bash
# Full application window
gnome-screenshot -w

# Specific area
gnome-screenshot -a

# Or use your compositor's built-in screenshot tool
```

### Creating the screenshots directory
```bash
mkdir -p ~/ccpeek/screenshots
```

## Image Requirements
- Format: PNG preferred
- Resolution: At least 1280px wide
- Clean: Hide any sensitive information
- Consistent: Use the same conversation if possible

## Example Commands for Demo Data
If you want to create demo conversations for screenshots, ensure they don't contain sensitive information.