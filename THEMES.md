# 🎨 Theme Guide - WebDev IDE

## Built-in Themes

Your IDE now comes with **6 beautiful color themes** inspired by popular IDEs:

### 1. VS Code Dark+ (Default)

Classic Visual Studio Code dark theme with purple keywords and cyan functions.

### 2. Monokai

The legendary Sublime Text theme - vibrant pink, yellow, and green.

### 3. Dracula

Dark purple theme with neon accents - easy on the eyes for long coding sessions.

### 4. One Dark

Atom's popular theme with soft purple, blue, and orange.

### 5. GitHub Dark

GitHub's official dark theme with modern, balanced colors.

### 6. Tokyo Night

Inspired by Tokyo's neon nights - deep blues and purples.

---

## How to Change Theme

### Method 1: Menu Bar (Easiest)

1. Go to **View** → **🎨 Editor Theme**
2. Click on any theme name
3. All open files instantly update!

### Method 2: Keyboard

1. Press `Alt` to show menu
2. Navigate with arrow keys
3. Press `Enter` to apply

---

## Import Themes from VS Code

Want to use your favorite VS Code theme? Here's how:

### Step 1: Find VS Code Theme File

1. Open VS Code
2. Press `Ctrl+Shift+P`
3. Type "Developer: Generate Color Theme"
4. Copy the JSON output

### Step 2: Convert to WebDev IDE Format

Add this structure to `WebDevelopmentIDE.py` in the `THEMES` dictionary:

```python
"Your Theme Name": {
    "keyword": "#C586C0",      # if, else, const, let, var
    "string": "#CE9178",       # "text", 'text', `text`
    "comment": "#6A9955",      # // comments, /* comments */
    "number": "#B5CEA8",       # 123, 45.6
    "function": "#DCDCAA",     # functionName()
    "class": "#4EC9B0",        # ClassName
    "tag": "#569CD6",          # <html>, <div>
    "attribute": "#9CDCFE",    # id="", class=""
    "operator": "#D4D4D4",     # +, -, *, /
    "variable": "#9CDCFE",     # variableName
    "constant": "#4FC1FF",     # CONSTANT_NAME
    "decorator": "#C586C0",    # @decorator
},
```

### Step 3: Map VS Code Colors

VS Code uses these color keys → WebDev IDE mapping:

| VS Code Key                   | WebDev IDE Key | Used For                   |
| ----------------------------- | -------------- | -------------------------- |
| `keyword`                     | `keyword`      | Keywords (if, else, const) |
| `string`                      | `string`       | String literals            |
| `comment`                     | `comment`      | Comments                   |
| `number`                      | `number`       | Numbers                    |
| `function`                    | `function`     | Function names             |
| `type`                        | `class`        | Class/Type names           |
| `keyword.control`             | `keyword`      | Control keywords           |
| `variable`                    | `variable`     | Variables                  |
| `constant`                    | `constant`     | Constants                  |
| `entity.name.tag`             | `tag`          | HTML tags                  |
| `entity.other.attribute-name` | `attribute`    | HTML attributes            |

---

## Import Themes from Other IDEs

### From Sublime Text

Sublime uses `.tmTheme` (XML) format. Convert using:

1. Open theme file in Sublime
2. View → Scope for each color
3. Map to WebDev IDE format manually

### From JetBrains (IntelliJ/PyCharm/WebStorm)

JetBrains uses `.icls` (XML) format:

1. Settings → Editor → Color Scheme
2. Export scheme
3. Extract color values from XML
4. Add to `THEMES` dictionary

### Quick Color Extraction Tool

Use this Python snippet to extract colors from any theme file:

```python
import re

# Paste your theme JSON/XML here
theme_text = """..."""

# Find all hex colors
colors = re.findall(r'#[0-9A-Fa-f]{6}', theme_text)
print("Found colors:", set(colors))
```

---

## Creating Custom Themes

### Example: "Midnight Blue"

```python
"Midnight Blue": {
    "keyword": "#88C0D0",      # Soft cyan
    "string": "#A3BE8C",       # Soft green
    "comment": "#616E88",      # Gray blue
    "number": "#B48EAD",       # Purple
    "function": "#81A1C1",     # Blue
    "class": "#88C0D0",        # Cyan
    "tag": "#5E81AC",          # Dark blue
    "attribute": "#D08770",    # Orange
    "operator": "#ECEFF4",     # White
    "variable": "#D8DEE9",     # Light gray
    "constant": "#EBCB8B",     # Yellow
    "decorator": "#B48EAD",    # Purple
},
```

### Color Guidelines

- **Background**: Keep editor background at `#1e1e1e` (dark) or `#ffffff` (light)
- **Contrast**: Ensure minimum 4.5:1 contrast ratio for readability
- **Consistency**: Use similar hues for related concepts
- **Accessibility**: Test with colorblindness simulators

---

## Tips for Theme Selection

### For JavaScript/React Development

- **Recommended**: Monokai or One Dark
- **Why**: Excellent contrast for JSX syntax

### For HTML/CSS

- **Recommended**: VS Code Dark+ or GitHub Dark
- **Why**: Clear distinction between tags and attributes

### For Long Coding Sessions

- **Recommended**: Dracula or Tokyo Night
- **Why**: Reduced eye strain with muted colors

### For Dark Rooms

- **Recommended**: Tokyo Night or Dracula
- **Why**: Lower overall brightness

### For Bright Environments

- **Recommended**: GitHub Dark or One Dark
- **Why**: Better contrast in ambient light

---

## Troubleshooting

### Theme doesn't change?

- Close and reopen the file
- Or: Edit → Undo/Redo to force refresh

### Colors look wrong?

- Check if file extension is correct (.html, .css, .js)
- Syntax highlighter depends on file type

### Want more themes?

- Check out: https://vscodethemes.com/
- Download JSON, convert to dictionary format
- Add to `THEMES` in `WebDevelopmentIDE.py`

---

## Contributing Themes

Have a beautiful theme? Share it!

1. Add your theme to `THEMES` dictionary
2. Test with HTML, CSS, and JavaScript
3. Take a screenshot
4. Submit!

---

**Happy Coding!** 🎨✨
