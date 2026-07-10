"""
Fixed CodeEditor with working QCompleter-based autocomplete
Replace the CodeEditor class in WebDevelopmentIDE.py with this implementation
"""

from PySide6.QtWidgets import QTextEdit, QCompleter
from PySide6.QtCore import Qt, QStringListModel
from PySide6.QtGui import QFont, QColor, QPalette, QTextCursor, QTextOption
import re


class CodeEditor(QTextEdit):
    """Code editor with Qt's built-in QCompleter autocomplete"""

    def __init__(self, parent=None, language="html"):
        super().__init__(parent)
        self.language = language

        # Auto-closing pairs
        self.auto_pairs = {
            "(": ")",
            "[": "]",
            "{": "}",
            '"': '"',
            "'": "'",
        }

        # Comprehensive keyword lists
        self.html_keywords = [
            # Tags
            "div",
            "span",
            "p",
            "a",
            "img",
            "input",
            "button",
            "form",
            "label",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "ul",
            "ol",
            "li",
            "table",
            "tr",
            "td",
            "th",
            "thead",
            "tbody",
            "tfoot",
            "nav",
            "header",
            "footer",
            "section",
            "article",
            "aside",
            "main",
            "figure",
            "figcaption",
            "video",
            "audio",
            "canvas",
            "svg",
            "iframe",
            "textarea",
            "select",
            "option",
            "fieldset",
            "legend",
            "details",
            "summary",
            "dialog",
            "menu",
            "menuitem",
            "strong",
            "em",
            "code",
            "pre",
            "br",
            "hr",
            # Common attributes
            "class=",
            "id=",
            "style=",
            "src=",
            "href=",
            "alt=",
            "title=",
            "width=",
            "height=",
            "type=",
            "value=",
            "name=",
            "placeholder=",
            "required",
            "disabled",
            "readonly",
            "checked",
            "selected",
            "data-",
            "aria-",
            "role=",
            "tabindex=",
        ]

        self.css_keywords = [
            # Properties with colons
            "color:",
            "background:",
            "background-color:",
            "background-image:",
            "background-size:",
            "font-size:",
            "font-family:",
            "font-weight:",
            "font-style:",
            "margin:",
            "margin-top:",
            "margin-right:",
            "margin-bottom:",
            "margin-left:",
            "padding:",
            "padding-top:",
            "padding-right:",
            "padding-bottom:",
            "padding-left:",
            "border:",
            "border-top:",
            "border-radius:",
            "width:",
            "height:",
            "max-width:",
            "min-width:",
            "display:",
            "position:",
            "top:",
            "left:",
            "right:",
            "bottom:",
            "flex:",
            "flex-direction:",
            "justify-content:",
            "align-items:",
            "grid:",
            "grid-template-columns:",
            "text-align:",
            "text-decoration:",
            "line-height:",
            "opacity:",
            "z-index:",
            "overflow:",
            "cursor:",
            "transition:",
            "transform:",
            "box-shadow:",
            "text-shadow:",
            # Common values
            "none",
            "block",
            "inline",
            "inline-block",
            "flex",
            "grid",
            "absolute",
            "relative",
            "fixed",
            "sticky",
            "center",
            "left",
            "right",
            "bold",
            "italic",
            "underline",
            "pointer",
            "hidden",
            "auto",
            "scroll",
        ]

        self.js_keywords = [
            # Keywords
            "const",
            "let",
            "var",
            "function",
            "return",
            "if",
            "else",
            "for",
            "while",
            "do",
            "switch",
            "case",
            "break",
            "continue",
            "class",
            "extends",
            "import",
            "export",
            "async",
            "await",
            "try",
            "catch",
            "finally",
            "throw",
            "new",
            "this",
            "typeof",
            # Common methods
            "console.log(",
            "console.error(",
            "console.warn(",
            "document.querySelector(",
            "document.getElementById(",
            "document.createElement(",
            "addEventListener(",
            "setTimeout(",
            "setInterval(",
            "fetch(",
            "then(",
            "catch(",
            "Promise",
            "JSON.parse(",
            "JSON.stringify(",
            "Math.random(",
            "Math.floor(",
            "Math.ceil(",
            "localStorage.getItem(",
            "localStorage.setItem(",
            "innerHTML",
            "textContent",
            "className",
            "classList",
            "style",
            "setAttribute(",
            "getAttribute(",
            "appendChild(",
            "removeChild(",
            "length",
            "push(",
            "pop(",
            "map(",
            "filter(",
            "forEach(",
            "find(",
            "includes(",
            "indexOf(",
            "split(",
            "join(",
        ]

        # Set up font
        font = QFont("Consolas", 11)
        font.setFixedPitch(True)
        self.setFont(font)

        # Appearance
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                padding: 0px;
            }
        """)

        # Syntax highlighter would go here (keep existing one)
        # self.highlighter = CodeHighlighter(self.document(), language)

        # Settings
        self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.setTabStopDistance(40)

        # Dark color scheme
        palette = self.palette()
        palette.setColor(QPalette.Base, QColor("#1e1e1e"))
        palette.setColor(QPalette.Text, QColor("#d4d4d4"))
        palette.setColor(QPalette.Highlight, QColor("#264f78"))
        self.setPalette(palette)

        # Set up autocomplete
        self.completer = None
        self.setup_completer()

    def setup_completer(self):
        """Set up QCompleter with keywords"""
        # Get keywords for current language
        if self.language == "html":
            keywords = self.html_keywords
        elif self.language == "css":
            keywords = self.css_keywords
        elif self.language == "javascript":
            keywords = self.js_keywords
        else:
            keywords = []

        # Create completer
        self.completer = QCompleter(keywords, self)
        self.completer.setWidget(self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setMaxVisibleItems(10)

        # Style popup
        popup = self.completer.popup()
        popup.setStyleSheet("""
            QListView {
                background-color: #252526;
                border: 1px solid #454545;
                color: #d4d4d4;
                font-family: Consolas;
                font-size: 11px;
                selection-background-color: #094771;
                outline: none;
            }
            QListView::item {
                padding: 4px 8px;
            }
            QListView::item:hover {
                background-color: #2a2d2e;
            }
        """)

        # Connect completion
        self.completer.activated.connect(self.insert_completion)

    def set_language(self, language):
        """Change language and update completer"""
        self.language = language
        # Update highlighter if you have one
        # self.highlighter = CodeHighlighter(self.document(), language)
        self.setup_completer()

    def insert_completion(self, completion):
        """Insert selected completion"""
        cursor = self.textCursor()
        prefix = self.completer.completionPrefix()
        extra = completion[len(prefix) :]
        cursor.insertText(extra)
        self.setTextCursor(cursor)

    def text_under_cursor(self):
        """Get word under cursor"""
        cursor = self.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        return cursor.selectedText()

    def keyPressEvent(self, event):
        """Handle keypresses for autocomplete and auto-closing"""
        key = event.key()
        text = event.text()

        # Handle completer popup
        if self.completer and self.completer.popup().isVisible():
            if key in [Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab, Qt.Key_Escape]:
                event.ignore()
                return

        # Auto-closing brackets
        if text in self.auto_pairs:
            cursor = self.textCursor()
            if text in ['"', "'"]:
                next_char = self.get_char_after_cursor()
                if next_char == text:
                    cursor.movePosition(QTextCursor.Right)
                    self.setTextCursor(cursor)
                    return
            cursor.insertText(text + self.auto_pairs[text])
            cursor.movePosition(QTextCursor.Left)
            self.setTextCursor(cursor)
            return

        # Skip closing brackets
        if text in self.auto_pairs.values():
            if self.get_char_after_cursor() == text:
                cursor = self.textCursor()
                cursor.movePosition(QTextCursor.Right)
                self.setTextCursor(cursor)
                return

        # HTML tag completion
        if key == Qt.Key_Return and self.language == "html":
            line = self.get_current_line()
            match = re.search(r"<(\w+)[^>]*>$", line.strip())
            if match:
                tag = match.group(1)
                if tag not in ["img", "br", "hr", "input", "meta", "link"]:
                    cursor = self.textCursor()
                    indent = self.get_current_indent()
                    cursor.insertText("\n" + indent + "  ")
                    pos = cursor.position()
                    cursor.insertText("\n" + indent + f"</{tag}>")
                    cursor.setPosition(pos)
                    self.setTextCursor(cursor)
                    return

        # Delete paired brackets
        if key == Qt.Key_Backspace:
            cursor = self.textCursor()
            if not cursor.hasSelection():
                prev = self.get_char_before_cursor()
                next_char = self.get_char_after_cursor()
                if prev in self.auto_pairs and self.auto_pairs[prev] == next_char:
                    cursor.deletePreviousChar()
                    cursor.deleteChar()
                    return

        # Ctrl+Space shortcut
        is_shortcut = event.modifiers() == Qt.ControlModifier and key == Qt.Key_Space

        if not self.completer or not is_shortcut:
            super().keyPressEvent(event)

        # Show completer
        if is_shortcut or (
            len(text) > 0 and (text.isalnum() or text in ["-", "_", ":"])
        ):
            prefix = self.text_under_cursor()

            if len(prefix) < 1 and not is_shortcut:
                self.completer.popup().hide()
                return

            if prefix != self.completer.completionPrefix():
                self.completer.setCompletionPrefix(prefix)
                self.completer.popup().setCurrentIndex(
                    self.completer.completionModel().index(0, 0)
                )

            # Show popup
            rect = self.cursorRect()
            rect.setWidth(
                self.completer.popup().sizeHintForColumn(0)
                + self.completer.popup().verticalScrollBar().sizeHint().width()
            )
            self.completer.complete(rect)

    def focusInEvent(self, event):
        """Handle focus"""
        if self.completer:
            self.completer.setWidget(self)
        super().focusInEvent(event)

    # Helper methods
    def get_current_line(self):
        cursor = self.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        return cursor.selectedText()

    def get_current_indent(self):
        line = self.get_current_line()
        indent = ""
        for char in line:
            if char in [" ", "\t"]:
                indent += char
            else:
                break
        return indent

    def get_char_before_cursor(self):
        pos = self.textCursor().position()
        if pos == 0:
            return ""
        text = self.toPlainText()
        return text[pos - 1] if pos <= len(text) else ""

    def get_char_after_cursor(self):
        pos = self.textCursor().position()
        text = self.toPlainText()
        return text[pos] if pos < len(text) else ""
