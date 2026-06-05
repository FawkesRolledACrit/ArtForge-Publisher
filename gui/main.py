"""Main PyQt6 GUI application for ArtForge Publisher."""

import sys
import requests
import json
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox,
    QTextEdit, QFormLayout, QLineEdit, QFileDialog, QSplitter,
    QProgressBar, QGroupBox, QFrame, QScrollArea, QToolButton,
    QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData, QTimer, QPropertyAnimation, QEasingCurve, QRect, QUrl, QBuffer, QIODevice
from PyQt6.QtGui import QPixmap, QImage, QFont, QPalette, QColor, QGuiApplication, QFontDatabase, QPainter, QPen, QBrush, QLinearGradient
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


class StreamingWorker(QThread):
    """Worker for handling SSE streaming from backend."""
    
    received_chunk = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.running = True
    
    def run(self):
        """Run the streaming worker."""
        try:
            response = requests.get(self.url, stream=True, timeout=600)  # Increased timeout
            response.raise_for_status()
            
            buffer = ""
            for line in response.iter_lines():
                if not self.running:
                    break
                    
                if line:
                    line_str = line.decode('utf-8')
                    buffer += line_str
                    # Process complete messages
                    while '\n\n' in buffer:
                        message, buffer = buffer.split('\n\n', 1)
                        if message.startswith('data: '):
                            data_str = message[6:]  # Remove 'data: ' prefix
                            try:
                                data = json.loads(data_str)
                                if 'content' in data:
                                    self.received_chunk.emit(data['content'])
                                elif 'error' in data:
                                    self.error.emit(data['error'])
                                elif 'done' in data and data['done']:
                                    self.finished.emit()
                                    break
                            except json.JSONDecodeError:
                                pass
                                    
        except requests.RequestException as e:
            self.error.emit(f"Request error: {str(e)}")
        except Exception as e:
            self.error.emit(f"Streaming error: {str(e)}")
    
    def stop(self):
        """Stop the streaming worker."""
        self.running = False
        self.quit()
        self.wait()


class ThemeManager:
    """Manages application themes and color schemes."""
    
    # Font families (platform-specific)
    FONT_FAMILY = "Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    FONT_FAMILY_MONOSPACE = "Consolas, Monaco, Courier New, monospace"
    
    # Retro Y2K Theme (based on user's website)
    RETRO_THEME = {
        "background": "#000000",
        "surface": "#0a0a0a",
        "border": "#00FF00",
        "text_primary": "#00FF00",
        "text_secondary": "#00FF00",  # Made brighter for readability
        "primary": "#00FFFF",
        "primary_hover": "#008800",  # Darker green for hover states
        "success": "#006600",  # Very dark matrix green
        "success_hover": "#004400",  # Even darker for hover
        "warning": "#666600",  # Very muted yellow
        "warning_hover": "#444400",  # Darker yellow for hover
        "danger": "#660066",  # Very muted magenta
        "danger_hover": "#440044",  # Darker magenta for hover
        "purple": "#660066",  # Same as danger for consistency
        "purple_hover": "#440044",
        "input_bg": "#111111",
        "input_border": "#00FF00",
        "input_focus": "#00FFFF",
        "card_bg": "#0a0a0a",
        "card_border": "#FF00FF",
        "scroll_bg": "#050505",
    }
    
    LIGHT_THEME = {
        "background": "#ffffff",
        "surface": "#f8f9fa",
        "border": "#e0e0e0",
        "text_primary": "#333333",
        "text_secondary": "#666666",
        "primary": "#2196F3",
        "primary_hover": "#0b7dda",
        "success": "#4CAF50",
        "success_hover": "#45a049",
        "warning": "#FF9800",
        "warning_hover": "#e68900",
        "danger": "#f44336",
        "danger_hover": "#da190b",
        "purple": "#9C27B0",
        "purple_hover": "#7b1fa2",
        "input_bg": "#f8f9fa",
        "input_border": "#e0e0e0",
        "input_focus": "#2196F3",
        "card_bg": "#ffffff",
        "card_border": "#e0e0e0",
        "scroll_bg": "#f8f9fa",
    }
    
    DARK_THEME = {
        "background": "#0a0a0a",
        "surface": "#151515",
        "border": "#333333",
        "text_primary": "#ffffff",  # Changed from #e0e0e0 to pure white
        "text_secondary": "#e0e0e0",  # Changed from #b0b0b0 to brighter
        "primary": "#64B5F6",
        "primary_hover": "#42A5F5",
        "success": "#81C784",
        "success_hover": "#66BB6A",
        "warning": "#FFB74D",
        "warning_hover": "#FFA726",
        "danger": "#E57373",
        "danger_hover": "#EF5350",
        "purple": "#BA68C8",
        "purple_hover": "#AB47BC",
        "input_bg": "#1a1a1a",
        "input_border": "#404040",
        "input_focus": "#64B5F6",
        "card_bg": "#151515",
        "card_border": "#333333",
        "scroll_bg": "#0a0a0a",
    }
    
    def __init__(self):
        self.current_theme = "retro"  # Default to retro theme
        self.config_path = Path.home() / ".artforge_publisher" / "config.json"
        self.load_theme()
        # Disable custom font loading temporarily - causes GUI crash
        # self.load_custom_font()
    
    def load_custom_font(self):
        """Load the custom RetroByte font."""
        try:
            font_path = Path("C:/Users/Fawke/Downloads/Fonts/RetroByte.ttf")
            if font_path.exists():
                font_id = QFontDatabase.addApplicationFont(str(font_path))
                if font_id >= 0:
                    print(f"Successfully loaded RetroByte font from {font_path}")
                else:
                    print(f"Failed to load RetroByte font from {font_path}")
            else:
                print(f"RetroByte font not found at {font_path}")
        except Exception as e:
            print(f"Error loading RetroByte font: {e}")
            # Continue without the font if loading fails
    
    def load_theme(self):
        """Load theme preference from config file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.current_theme = config.get("theme", "retro")
        except Exception:
            self.current_theme = "retro"
    
    def save_theme(self):
        """Save theme preference to config file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            config = {"theme": self.current_theme}
            with open(self.config_path, 'w') as f:
                json.dump(config, f)
        except Exception:
            pass
    
    def get_color(self, color_name):
        """Get color from current theme."""
        if self.current_theme == "retro":
            theme = self.RETRO_THEME
        elif self.current_theme == "dark":
            theme = self.DARK_THEME
        else:
            theme = self.LIGHT_THEME
        return theme.get(color_name, "#000000")
    
    def toggle_theme(self):
        """Toggle between light, dark, and retro theme."""
        themes = ["light", "dark", "retro"]
        current_index = themes.index(self.current_theme) if self.current_theme in themes else 0
        self.current_theme = themes[(current_index + 1) % len(themes)]
        self.save_theme()
        return self.current_theme
    
    def get_stylesheet(self):
        """Get stylesheet for current theme."""
        if self.current_theme == "retro":
            colors = self.RETRO_THEME
        elif self.current_theme == "dark":
            colors = self.DARK_THEME
        else:
            colors = self.LIGHT_THEME
        return f"""
            QMainWindow {{
                background-color: {colors['background']};
                font-family: {self.FONT_FAMILY};
            }}
            QWidget {{
                background-color: {colors['background']};
                color: {colors['text_primary']};
                font-family: {self.FONT_FAMILY};
            }}
            QLabel {{
                color: {colors['text_primary']};
                font-family: {self.FONT_FAMILY};
            }}
            QLineEdit {{
                background-color: {colors['input_bg']};
                border: 1px solid {colors['input_border']};
                border-radius: 8px;
                padding: 10px 12px;
                color: {colors['text_primary']};
                font-size: 13px;
                font-family: {self.FONT_FAMILY};
            }}
            QLineEdit:focus {{
                border: 2px solid {colors['input_focus']};
                background-color: {colors['background']};
            }}
            QLineEdit[readOnly="true"] {{
                background-color: {colors['surface']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
            }}
            QTextEdit {{
                background-color: {colors['input_bg']};
                border: 1px solid {colors['input_border']};
                border-radius: 8px;
                padding: 10px 12px;
                color: {colors['text_primary']};
                font-size: 13px;
                font-family: {self.FONT_FAMILY};
            }}
            QTextEdit:focus {{
                border: 2px solid {colors['input_focus']};
                background-color: {colors['background']};
            }}
            QTextEdit[readOnly="true"] {{
                background-color: {colors['surface']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
            }}
            QGroupBox {{
                border: 1px solid {colors['card_border']};
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 18px;
                font-weight: bold;
                font-size: 13px;
                color: {colors['text_primary']};
                background-color: {colors['card_bg']};
                font-family: {self.FONT_FAMILY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px 0 5px;
            }}
            QScrollArea {{
                background-color: {colors['scroll_bg']};
                border: none;
            }}
            QListWidget {{
                border: none;
                border-radius: 8px;
                padding: 8px;
                background-color: {colors['surface']};
                font-family: {self.FONT_FAMILY};
            }}
            QListWidget::item {{
                padding: 12px;
                border-radius: 6px;
                border: none;
                background-color: {colors['card_bg']};
                color: {colors['text_primary']};
                font-family: {self.FONT_FAMILY};
            }}
            QListWidget::item:hover {{
                background-color: {colors['primary_hover']};
                color: white;
            }}
            QListWidget::item:selected {{
                background-color: {colors['primary']};
                color: white;
            }}
            QTabWidget::pane {{
                border: 1px solid {colors['card_border']};
                border-radius: 12px;
                background-color: {colors['card_bg']};
                padding: 8px;
            }}
            QTabBar::tab {{
                background-color: {colors['surface']};
                padding: 10px 20px;
                border: 1px solid {colors['card_border']};
                border-bottom: none;
                border-radius: 8px 8px 0 0;
                margin-right: 4px;
                font-size: 13px;
                font-weight: bold;
                color: {colors['text_primary']};
                font-family: {self.FONT_FAMILY};
            }}
            QTabBar::tab:hover {{
                background-color: {colors['primary_hover']};
                color: white;
            }}
            QTabBar::tab:selected {{
                background-color: {colors['card_bg']};
                border-bottom: 2px solid {colors['primary']};
                color: {colors['primary']};
            }}
            QProgressBar {{
                border: 1px solid {colors['border']};
                border-radius: 4px;
                background-color: {colors['surface']};
                text-align: center;
                color: {colors['text_primary']};
                font-family: {self.FONT_FAMILY};
            }}
            QProgressBar::chunk {{
                background-color: {colors['primary']};
                border-radius: 3px;
            }}
            QPushButton {{
                font-family: {self.FONT_FAMILY};
            }}
        """
    
    def get_theme_colors(self):
        """Get current theme colors dictionary."""
        if self.current_theme == "retro":
            return self.RETRO_THEME
        elif self.current_theme == "dark":
            return self.DARK_THEME
        else:
            return self.LIGHT_THEME


# Global theme manager instance
theme_manager = ThemeManager()


class TextEditWithCounter(QWidget):
    """QTextEdit with character counter label."""
    
    def __init__(self, max_chars=None, placeholder="", parent=None):
        super().__init__(parent)
        self.max_chars = max_chars
        self.init_ui(placeholder)
    
    def init_ui(self, placeholder):
        """Initialize the UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Text edit
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(placeholder)
        self.text_edit.textChanged.connect(self.update_counter)
        layout.addWidget(self.text_edit)
        
        # Counter label
        self.counter_label = QLabel("0 characters")
        self.counter_label.setStyleSheet(f"color: {theme_manager.get_theme_colors()['text_secondary']}; font-size: 10px;")
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.counter_label)
        
        self.setLayout(layout)
    
    def update_counter(self):
        """Update the character counter."""
        text = self.text_edit.toPlainText()
        count = len(text)
        
        colors = theme_manager.get_theme_colors()
        
        if self.max_chars:
            remaining = self.max_chars - count
            if remaining < 0:
                self.counter_label.setText(f"{count}/{self.max_chars} characters ({abs(remaining)} over limit!)")
                self.counter_label.setStyleSheet(f"color: {colors['danger']}; font-size: 10px; font-weight: bold;")
            elif remaining < 20:
                self.counter_label.setText(f"{count}/{self.max_chars} characters ({remaining} remaining)")
                self.counter_label.setStyleSheet(f"color: {colors['warning']}; font-size: 10px;")
            else:
                self.counter_label.setText(f"{count}/{self.max_chars} characters")
                self.counter_label.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 10px;")
        else:
            self.counter_label.setText(f"{count} characters")
            self.counter_label.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 10px;")
    
    def setPlainText(self, text):
        """Set text and update counter."""
        self.text_edit.setPlainText(text)
        self.update_counter()
    
    def toPlainText(self):
        """Get text from text edit."""
        return self.text_edit.toPlainText()
    
    def clear(self):
        """Clear text and update counter."""
        self.text_edit.clear()
        self.update_counter()
    
    def setReadOnly(self, readonly):
        """Set read-only state."""
        self.text_edit.setReadOnly(readonly)
    
    def isReadOnly(self):
        """Check if read-only."""
        return self.text_edit.isReadOnly()
    
    def setPlaceholderText(self, text):
        """Set placeholder text."""
        self.text_edit.setPlaceholderText(text)
    
    def setStyleSheet(self, style):
        """Set style sheet for text edit."""
        self.text_edit.setStyleSheet(style)
    
    def setMaximumHeight(self, height):
        """Set maximum height for text edit."""
        self.text_edit.setMaximumHeight(height)


class TextEditWithCounterAndCopy(QWidget):
    """QTextEdit with character counter and copy button."""
    
    def __init__(self, max_chars=None, placeholder="", parent=None):
        super().__init__(parent)
        self.max_chars = max_chars
        self.init_ui(placeholder)
    
    def init_ui(self, placeholder):
        """Initialize the UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Header with label and copy button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)
        
        # Text edit
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(placeholder)
        self.text_edit.textChanged.connect(self.update_counter)
        layout.addWidget(self.text_edit)
        
        # Footer with counter and copy button
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(5)
        
        # Counter label
        self.counter_label = QLabel("0 characters")
        self.counter_label.setStyleSheet(f"color: {theme_manager.get_theme_colors()['text_secondary']}; font-size: 10px;")
        
        # Copy button
        self.copy_btn = QPushButton("📋 Copy")
        colors = theme_manager.get_theme_colors()
        text_color = "black" if theme_manager.current_theme in ["retro", "light"] else "white"
        self.copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['success']};
                color: {text_color};
                border: none;
                padding: 4px 12px;
                font-size: 10px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {colors['success_hover']};
            }}
        """)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        
        footer_layout.addWidget(self.counter_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.copy_btn)
        layout.addLayout(footer_layout)
        
        self.setLayout(layout)
    
    def update_counter(self):
        """Update the character counter."""
        text = self.text_edit.toPlainText()
        count = len(text)
        
        colors = theme_manager.get_theme_colors()
        
        if self.max_chars:
            remaining = self.max_chars - count
            if remaining < 0:
                self.counter_label.setText(f"{count}/{self.max_chars} characters ({abs(remaining)} over limit!)")
                self.counter_label.setStyleSheet(f"color: {colors['danger']}; font-size: 10px; font-weight: bold;")
            elif remaining < 20:
                self.counter_label.setText(f"{count}/{self.max_chars} characters ({remaining} remaining)")
                self.counter_label.setStyleSheet(f"color: {colors['warning']}; font-size: 10px;")
            else:
                self.counter_label.setText(f"{count}/{self.max_chars} characters")
                self.counter_label.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 10px;")
        else:
            self.counter_label.setText(f"{count} characters")
            self.counter_label.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 10px;")
    
    def copy_to_clipboard(self):
        """Copy text to clipboard."""
        text = self.text_edit.toPlainText()
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        # Visual feedback
        self.copy_btn.setText("✓ Copied!")
        colors = theme_manager.get_theme_colors()
        text_color = "black" if theme_manager.current_theme in ["retro", "light"] else "white"
        self.copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['primary']};
                color: {text_color};
                border: none;
                padding: 4px 12px;
                font-size: 10px;
                border-radius: 3px;
            }}
        """)
        # Reset button after 2 seconds
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2000, self.reset_copy_button)
    
    def reset_copy_button(self):
        """Reset copy button to original state."""
        self.copy_btn.setText("📋 Copy")
        colors = theme_manager.get_theme_colors()
        text_color = "black" if theme_manager.current_theme in ["retro", "light"] else "white"
        self.copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['success']};
                color: {text_color};
                border: none;
                padding: 4px 12px;
                font-size: 10px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {colors['success_hover']};
            }}
        """)
    
    def setPlainText(self, text):
        """Set text and update counter."""
        self.text_edit.setPlainText(text)
        self.update_counter()
    
    def toPlainText(self):
        """Get text from text edit."""
        return self.text_edit.toPlainText()
    
    def clear(self):
        """Clear text and update counter."""
        self.text_edit.clear()
        self.update_counter()
    
    def setReadOnly(self, readonly):
        """Set read-only state."""
        self.text_edit.setReadOnly(readonly)
        self.copy_btn.setEnabled(not readonly)
    
    def isReadOnly(self):
        """Check if read-only."""
        return self.text_edit.isReadOnly()
    
    def setPlaceholderText(self, text):
        """Set placeholder text."""
        self.text_edit.setPlaceholderText(text)
    
    def setStyleSheet(self, style):
        """Set style sheet for text edit."""
        self.text_edit.setStyleSheet(style)
    
    def setMaximumHeight(self, height):
        """Set maximum height for text edit."""
        self.text_edit.setMaximumHeight(height)


class ToastNotification(QWidget):
    """Toast notification widget for success/error messages."""
    
    def __init__(self, message, message_type="success", parent=None):
        super().__init__(parent)
        self.message = message
        self.message_type = message_type
        self.init_ui()
        self.animate_in()
    
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Set style based on message type
        if self.message_type == "success":
            bg_color = "#4CAF50"
            icon = "✓"
        elif self.message_type == "error":
            bg_color = "#f44336"
            icon = "✕"
        elif self.message_type == "warning":
            bg_color = "#ff9800"
            icon = "⚠"
        else:
            bg_color = "#2196F3"
            icon = "ℹ"
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 8px;
                padding: 12px 16px;
            }}
            QLabel {{
                color: white;
                font-size: 12px;
                font-weight: bold;
            }}
        """)
        
        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 18px;")
        content_layout.addWidget(icon_label)
        
        # Message
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        content_layout.addWidget(message_label)
        
        layout.addLayout(content_layout)
        self.setLayout(layout)
        
        # Set fixed size
        self.setFixedWidth(350)
        self.adjustSize()
    
    def animate_in(self):
        """Animate the toast in from the top."""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Position at top-right of parent
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.width() - self.width() - 20
            y = 20
            self.move(x, y)
        
        # Fade in animation
        self.setWindowOpacity(0)
        self.show()
        
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(300)
        self.opacity_animation.setStartValue(0)
        self.opacity_animation.setEndValue(1)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.opacity_animation.start()
        
        # Auto-dismiss after 3 seconds
        QTimer.singleShot(3000, self.animate_out)
    
    def animate_out(self):
        """Animate the toast out."""
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(300)
        self.opacity_animation.setStartValue(1)
        self.opacity_animation.setEndValue(0)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.opacity_animation.finished.connect(self.close)
        self.opacity_animation.start()


class SpinnerWidget(QWidget):
    """Animated spinner widget for loading states."""
    
    def __init__(self, size=40, parent=None):
        super().__init__(parent)
        self.size = size
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_rotation)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        self.setFixedSize(self.size, self.size)
    
    def start(self):
        """Start the spinner animation."""
        self.timer.start(50)  # Update every 50ms
    
    def stop(self):
        """Stop the spinner animation."""
        self.timer.stop()
    
    def update_rotation(self):
        """Update the rotation angle."""
        self.angle = (self.angle + 15) % 360
        self.update()
    
    def paintEvent(self, event):
        """Paint the spinner."""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Get theme colors
            primary_color = QColor(theme_manager.get_color('primary'))
            
            # Draw spinner arc
            center_x = self.width() // 2
            center_y = self.height() // 2
            radius = min(center_x, center_y) - 4
            
            pen = QPen(primary_color, 3)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            
            # Draw arc with current rotation
            rect = QRect(center_x - radius, center_y - radius, radius * 2, radius * 2)
            start_angle = self.angle * 16  # Qt uses 1/16th degrees
            span_angle = 270 * 16  # Draw 270 degrees
            painter.drawArc(rect, start_angle, span_angle)
        except Exception as e:
            print(f"SpinnerWidget paintEvent error: {e}")


class SkeletonWidget(QWidget):
    """Skeleton loading widget for placeholder content."""
    
    def __init__(self, height=40, width=None, parent=None):
        super().__init__(parent)
        self.height = height
        self.width = width
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        if self.width:
            self.setFixedSize(self.width, self.height)
        else:
            self.setFixedHeight(self.height)
        
        # Animation for shimmer effect
        self.shimmer_offset = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_shimmer)
    
    def start(self):
        """Start the shimmer animation."""
        self.timer.start(50)
    
    def stop(self):
        """Stop the shimmer animation."""
        self.timer.stop()
    
    def update_shimmer(self):
        """Update the shimmer offset."""
        self.shimmer_offset = (self.shimmer_offset + 5) % 200
        self.update()
    
    def paintEvent(self, event):
        """Paint the skeleton."""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Get theme colors
            bg_color = QColor(theme_manager.get_color('surface'))
            shimmer_color = QColor(theme_manager.get_color('border'))
            
            # Draw background
            painter.fillRect(self.rect(), bg_color)
            
            # Draw shimmer gradient
            gradient = QLinearGradient(self.shimmer_offset - 100, 0, self.shimmer_offset + 100, 0)
            gradient.setColorAt(0, bg_color)
            gradient.setColorAt(0.5, shimmer_color)
            gradient.setColorAt(1, bg_color)
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.rect(), 4, 4)
        except Exception as e:
            print(f"SkeletonWidget paintEvent error: {e}")


class ProgressOverlay(QWidget):
    """Progress overlay widget for long-running operations with real-time streaming log display."""
    
    def __init__(self, message="Loading...", parent=None):
        super().__init__(parent)
        self.message = message
        self.ollama_host = "http://localhost:11434"
        self.log_timer = None
        self.streaming_worker = None
        self.backend_log_reader = None
        self.backend_log_path = Path(__file__).parent.parent / "backend.log"
        self.ollama_log_path = Path(__file__).parent.parent / "ollama.log"
        self.last_backend_log_position = 0
        self.last_ollama_log_position = 0
        self.status_timer = None
        self.status_phrases = [
            "Yapping with AI",
            "Talking to AI",
            "Conversing with AI",
            "Chatting with AI",
            "Discussing with AI",
            "Banter with AI",
            "Gossiping with AI",
            "Conferring with AI",
            "Consulting AI",
            "Interacting with AI",
            "Engaging with AI",
            "Communicating with AI",
            "Exchanging with AI",
            "Dialoguing with AI",
            "Schmoozing with AI",
            "Jawing with AI",
            "Nattering with AI",
            "Prattling with AI",
            "Rambling with AI",
            "Waffling with AI"
        ]
        self.current_phrase_index = 0
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Background container
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 200);
                border-radius: 12px;
                border: 2px solid #00FF00;
            }
        """)
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(30, 30, 30, 30)
        container_layout.setSpacing(15)
        
        # Animated spinner
        self.spinner = SpinnerWidget(size=48)
        container_layout.addWidget(self.spinner, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Message
        self.message_label = QLabel(self.message)
        self.message_label.setStyleSheet("color: #00FF00; font-size: 16px; font-weight: bold;")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.message_label)
        
        # Log display area for streaming tokens
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(250)
        self.log_display.setMinimumHeight(150)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 180);
                color: #00FF00;
                border: 1px solid #00FF00;
                border-radius: 8px;
                padding: 10px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """)
        container_layout.addWidget(self.log_display)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("color: #00FFFF; font-size: 12px; font-style: italic;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.status_label)
        
        container.setLayout(container_layout)
        layout.addWidget(container)
        self.setLayout(layout)
    
    def show_overlay(self, parent_widget):
        """Show the overlay over the parent widget."""
        if parent_widget:
            self.setParent(parent_widget)
            self.setGeometry(parent_widget.rect())
        self.spinner.start()
        self.show()
        self.raise_()
        self.activateWindow()
    
    def hide(self):
        """Hide the overlay and stop spinner and streaming."""
        self.spinner.stop()
        if self.streaming_worker:
            self.streaming_worker.stop()
            self.streaming_worker = None
        if self.log_timer:
            self.log_timer.stop()
            self.log_timer = None
        if self.status_timer:
            self.status_timer.stop()
            self.status_timer = None
        super().hide()
    
    def closeEvent(self, event):
        """Handle window close event properly."""
        self.spinner.stop()
        if self.streaming_worker:
            self.streaming_worker.stop()
            self.streaming_worker = None
        if self.log_timer:
            self.log_timer.stop()
            self.log_timer = None
        if self.status_timer:
            self.status_timer.stop()
            self.status_timer = None
        super().closeEvent(event)
    
    def set_message(self, message):
        """Update the progress message."""
        self.message = message
        self.message_label.setText(message)
    
    def set_streaming_url(self, url):
        """Set the streaming URL for real-time token display."""
        self.streaming_url = url
    
    def start_streaming_worker(self):
        """Start the streaming worker for real-time token display."""
        self.log_display.clear()
        self.status_label.setText("Connecting to AI...")
        
        # Start backend log reader
        self.start_backend_log_reader()
        
        if hasattr(self, 'streaming_url') and self.streaming_url:
            self.streaming_worker = StreamingWorker(self.streaming_url)
            self.streaming_worker.received_chunk.connect(self.append_streaming_chunk)
            self.streaming_worker.finished.connect(self.on_streaming_finished)
            self.streaming_worker.error.connect(self.on_streaming_error)
            self.streaming_worker.start()
    
    def start_backend_log_reader(self):
        """Start reading backend and Ollama logs in real-time."""
        self.last_backend_log_position = 0
        self.last_ollama_log_position = 0
        
        # Initialize backend log position
        if self.backend_log_path.exists():
            try:
                with open(self.backend_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(0, 2)  # Seek to end
                    self.last_backend_log_position = f.tell()
            except:
                self.last_backend_log_position = 0
        
        # Initialize Ollama log position
        if self.ollama_log_path.exists():
            try:
                with open(self.ollama_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(0, 2)  # Seek to end
                    self.last_ollama_log_position = f.tell()
            except:
                self.last_ollama_log_position = 0
        
        # Start timer to check for new log entries
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.read_backend_logs)
        self.log_timer.start(500)  # Check every 500ms
    
    def read_backend_logs(self):
        """Read new entries from backend and Ollama log files."""
        has_new_logs = False
        
        # Read backend logs
        if self.backend_log_path.exists():
            try:
                with open(self.backend_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(self.last_backend_log_position)
                    new_logs = f.read()
                    if new_logs:
                        self.last_backend_log_position = f.tell()
                        has_new_logs = True
                        # Append new logs with [Backend] prefix
                        for line in new_logs.split('\n'):
                            if line.strip():
                                self.log_display.insertPlainText(f"[Backend] {line}\n")
            except Exception as e:
                pass  # Silently ignore read errors
        
        # Read Ollama logs
        if self.ollama_log_path.exists():
            try:
                with open(self.ollama_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(self.last_ollama_log_position)
                    new_logs = f.read()
                    if new_logs:
                        self.last_ollama_log_position = f.tell()
                        has_new_logs = True
                        # Append new logs with [Ollama] prefix
                        for line in new_logs.split('\n'):
                            if line.strip():
                                self.log_display.insertPlainText(f"[Ollama] {line}\n")
            except Exception as e:
                pass  # Silently ignore read errors
        
        # Start status cycling when we see any log activity
        if has_new_logs and not self.status_timer:
            self.start_status_cycling()
        
        # Auto-scroll to bottom
        cursor = self.log_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_display.setTextCursor(cursor)
    
    def append_streaming_chunk(self, chunk):
        """Append a streaming chunk to the display."""
        self.log_display.insertPlainText(chunk)
        # Auto-scroll to bottom
        cursor = self.log_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_display.setTextCursor(cursor)
        
        # Start status cycling on first chunk
        if not self.status_timer:
            self.start_status_cycling()
    
    def start_status_cycling(self):
        """Start cycling through status phrases."""
        import random
        # Shuffle phrases for randomness
        random.shuffle(self.status_phrases)
        self.current_phrase_index = 0
        
        # Set initial phrase
        self.status_label.setText(self.status_phrases[0])
        
        # Start timer to cycle phrases every 2 seconds
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.cycle_status_phrase)
        self.status_timer.start(2000)
    
    def cycle_status_phrase(self):
        """Cycle to the next status phrase."""
        self.current_phrase_index = (self.current_phrase_index + 1) % len(self.status_phrases)
        self.status_label.setText(self.status_phrases[self.current_phrase_index])
    
    def stop_status_cycling(self):
        """Stop cycling status phrases."""
        if self.status_timer:
            self.status_timer.stop()
            self.status_timer = None
    
    def on_streaming_finished(self):
        """Handle streaming completion."""
        self.stop_status_cycling()
        self.status_label.setText("✓ Analysis complete!")
        self.log_display.append("\n[COMPLETE] Finished successfully")
    
    def on_streaming_error(self, error):
        """Handle streaming error."""
        self.stop_status_cycling()
        self.status_label.setText("✗ Error occurred")
        self.log_display.append(f"\n[ERROR] {error}")


class CollapsibleGroupBox(QGroupBox):
    """QGroupBox with collapsible functionality."""
    
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(True)
        self.toggled.connect(self.on_toggled)
        # Apply theme-aware styling
        self.apply_theme_style()
    
    def apply_theme_style(self):
        """Apply theme-aware styling to the group box."""
        colors = theme_manager.get_theme_colors()
        self.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {colors['card_border']};
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 18px;
                font-weight: bold;
                font-size: 13px;
                color: {colors['text_primary']};
                background-color: {colors['card_bg']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px 0 5px;
                color: {colors['text_primary']};
            }}
            QGroupBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            QGroupBox::indicator:unchecked {{
                image: url(none);
                border: 2px solid {colors['border']};
                border-radius: 3px;
                background-color: {colors['surface']};
            }}
            QGroupBox::indicator:checked {{
                image: url(none);
                border: 2px solid {colors['primary']};
                border-radius: 3px;
                background-color: {colors['primary']};
            }}
        """)
    
    def on_toggled(self, checked):
        """Handle collapse/expand toggle."""
        # Find the content layout and toggle visibility
        for child in self.children():
            if isinstance(child, QFormLayout) or isinstance(child, QVBoxLayout) or isinstance(child, QHBoxLayout):
                for i in range(child.count()):
                    item = child.itemAt(i)
                    if item and item.widget():
                        item.widget().setVisible(checked)


class APIWorker(QThread):
    """Worker thread for API calls."""
    
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)  # Progress message
    
    def __init__(self, url, method="GET", data=None):
        super().__init__()
        self.url = url
        self.method = method
        self.data = data
    
    def run(self):
        """Execute the API call."""
        try:
            self.progress.emit("Connecting to server...")
            if self.method == "GET":
                self.progress.emit("Fetching data...")
                response = requests.get(self.url, timeout=30)
            elif self.method == "POST":
                self.progress.emit("Sending request...")
                # Use longer timeout for AI operations
                timeout = 300 if "analyze" in self.url or "generate" in self.url else 120
                response = requests.post(self.url, json=self.data, timeout=timeout)
            elif self.method == "DELETE":
                self.progress.emit("Deleting...")
                response = requests.delete(self.url, timeout=30)
            
            self.progress.emit("Processing response...")
            if response.status_code in [200, 201]:
                try:
                    self.finished.emit(response.json())
                except:
                    self.finished.emit({"success": True})
            else:
                self.error.emit(f"API Error: {response.status_code} - {response.text}")
        except Exception as e:
            self.progress.emit("Error occurred")
            self.error.emit(str(e))


class ImageUploadTab(QWidget):
    """Tab for uploading and managing images."""
    
    image_selected = pyqtSignal(str)  # Signal emitted when image is selected
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.images = {}  # Store image data
        self.selected_image_id = None
        self.workers = []  # Track workers for cleanup
        self.network_managers = []  # Track network managers for cleanup
        self.setAcceptDrops(True)  # Enable drag-and-drop
        self.progress_overlay = ProgressOverlay(parent=self)
        self.init_ui()
        self.load_images()
    
    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.accept()
            colors = theme_manager.get_theme_colors()
            self.drop_zone.setStyleSheet(f"""
                QFrame {{
                    border: 3px dashed {colors['success']};
                    border-radius: 10px;
                    background-color: {colors['surface']};
                }}
                QLabel {{
                    color: {colors['text_primary']};
                    font-size: 14px;
                    font-weight: bold;
                }}
            """)
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        self.reset_drop_zone_style()
    
    def dropEvent(self, event):
        """Handle drop event."""
        self.reset_drop_zone_style()
        if event.mimeData().hasUrls():
            files = [u.toLocalFile() for u in event.mimeData().urls()]
            image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'))]
            if image_files:
                for file_path in image_files:
                    self.upload_image_file(file_path)
            event.accept()
        else:
            event.ignore()
    
    def reset_drop_zone_style(self):
        """Reset drop zone to default style."""
        colors = theme_manager.get_theme_colors()
        self.drop_zone.setStyleSheet(f"""
            QFrame {{
                border: 2px dashed {colors['border']};
                border-radius: 10px;
                background-color: {colors['surface']};
            }}
            QLabel {{
                color: {colors['text_secondary']};
                font-size: 14px;
            }}
        """)
    
    def init_ui(self):
        """Initialize the UI."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget
        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Image Management")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Status and progress
        self.status_label = QLabel("Ready")
        colors = theme_manager.get_theme_colors()
        self.status_label.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(20)
        layout.addWidget(self.progress_bar)
        
        # Drag-and-drop zone
        self.drop_zone = QFrame()
        colors = theme_manager.get_theme_colors()
        self.drop_zone.setStyleSheet(f"""
            QFrame {{
                border: 2px dashed {colors['border']};
                border-radius: 12px;
                background-color: {colors['surface']};
            }}
            QLabel {{
                color: {colors['text_secondary']};
                font-size: 14px;
            }}
        """)
        drop_zone_layout = QVBoxLayout()
        drop_zone_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_zone_label = QLabel("📁 Drag & Drop Images Here\nor click Upload below")
        drop_zone_label.setToolTip("Drag and drop image files here to upload them automatically")
        drop_zone_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_zone_layout.addWidget(drop_zone_label)
        self.drop_zone.setLayout(drop_zone_layout)
        self.drop_zone.setMinimumHeight(100)
        layout.addWidget(self.drop_zone)
        
        # Upload button
        colors = theme_manager.get_theme_colors()
        text_color = "black" if theme_manager.current_theme in ["retro", "light"] else "white"
        self.upload_btn = QPushButton("📤 Upload Image")
        self.upload_btn.setToolTip("Upload a new image file to the database")
        self.upload_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['success']};
                color: {text_color};
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 8px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors['success_hover']};
            }}
            QPushButton:disabled {{
                background-color: {colors['border']};
            }}
        """)
        self.upload_btn.clicked.connect(self.upload_image)
        layout.addWidget(self.upload_btn)
        
        # Image list
        list_group = CollapsibleGroupBox("Uploaded Images")
        list_group.setToolTip("List of all uploaded images. Click to select, hover to preview.")
        list_layout = QVBoxLayout()
        self.image_list = QListWidget()
        self.image_list.setToolTip("Click an image to select it for analysis and content generation")
        self.image_list.setMouseTracking(True)  # Enable mouse tracking for hover events
        self.image_list.itemEntered.connect(self.on_image_hover)
        self.image_list.itemClicked.connect(self.on_image_selected)
        list_layout.addWidget(self.image_list)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        # Delete button
        self.delete_btn = QPushButton("🗑️ Delete Selected Image")
        self.delete_btn.setToolTip("Delete the selected image from the database (cannot be undone)")
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['danger']};
                color: {text_color};
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 8px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors['danger_hover']};
            }}
            QPushButton:disabled {{
                background-color: {colors['border']};
            }}
        """)
        self.delete_btn.clicked.connect(self.delete_image)
        self.delete_btn.setEnabled(False)
        layout.addWidget(self.delete_btn)
        
        layout.addStretch()
        content_widget.setLayout(layout)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
    
    def load_images(self):
        """Load images from the backend."""
        self.set_loading(True, "Loading images...")
        worker = APIWorker("http://localhost:8000/api/v1/images")
        worker.finished.connect(self.on_images_loaded)
        worker.error.connect(self.on_error)
        worker.progress.connect(self.on_progress)
        self.workers.append(worker)
        worker.start()
    
    def on_progress(self, message):
        """Handle progress updates."""
        self.status_label.setText(message)
    
    def set_loading(self, loading, message="Loading..."):
        """Set loading state."""
        self.progress_bar.setVisible(loading)
        self.upload_btn.setEnabled(not loading)
        self.delete_btn.setEnabled(not loading and self.selected_image_id is not None)
        if loading:
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.status_label.setText(message)
            self.progress_overlay.set_message(message)
            self.progress_overlay.show_overlay(self)
            # Show skeleton items in list
            self.image_list.clear()
            for i in range(5):
                self.image_list.addItem("Loading...")
        else:
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(1)
            self.status_label.setText("Ready")
            self.progress_overlay.hide()
    
    def on_images_loaded(self, data):
        """Handle loaded images."""
        self.set_loading(False)
        self.image_list.clear()
        self.images = {}
        for image in data.get("images", []):
            image_id = image.get('id', '')
            filename = image.get('filename', 'Unknown')
            self.images[image_id] = image
            self.image_list.addItem(f"{filename} - {image_id}")
    
    def on_image_hover(self, item):
        """Handle image hover event to show thumbnail."""
        text = item.text()
        # Extract image_id from the text (format: "filename - image_id")
        if ' - ' in text:
            image_id = text.split(' - ')[-1]
            if image_id in self.images:
                # Get image path
                image_info = self.images[image_id]
                thumbnail_path = image_info.get('thumbnail_path') or image_info.get('original_path')
                if thumbnail_path and thumbnail_path != "null":
                    # Convert file path to HTTP URL
                    # Paths are like "storage\thumbnails\thumb_xxx.jpg" or "storage\images\xxx.png"
                    # Convert to HTTP URL: http://localhost:8000/storage/thumbnails/thumb_xxx.jpg
                    http_path = thumbnail_path.replace("\\", "/")
                    image_url = f"http://localhost:8000/{http_path}"
                    
                    # Use QNetworkAccessManager to fetch image
                    manager = QNetworkAccessManager()
                    self.network_managers.append(manager)  # Keep reference to prevent garbage collection
                    request = QNetworkRequest(QUrl(image_url))
                    
                    def on_reply_finished(reply):
                        if reply.error() == QNetworkReply.NetworkError.NoError:
                            image_data = reply.readAll()
                            pixmap = QPixmap()
                            if pixmap.loadFromData(image_data):
                                # Scale to reasonable thumbnail size
                                scaled_pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                # Convert to HTML for tooltip
                                buffer = QBuffer()
                                buffer.open(QIODevice.OpenModeFlag.ReadWrite)
                                scaled_pixmap.save(buffer, "PNG")
                                image_html = buffer.data().toBase64().data().decode()
                                item.setToolTip(f'<img src="data:image/png;base64,{image_html}" />')
                        reply.deleteLater()
                        # Remove manager from list after request completes
                        if manager in self.network_managers:
                            self.network_managers.remove(manager)
                    
                    manager.finished.connect(on_reply_finished)
                    manager.get(request)
    
    def upload_image(self):
        """Upload an image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.webp *.bmp *.tiff)"
        )
        if file_path:
            self.upload_image_file(file_path)
    
    def upload_image_file(self, file_path):
        """Upload an image from a given file path."""
        self.set_loading(True, "Uploading image...")
        # Read file and upload to backend
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.split('\\')[-1], f, 'image/png')}
                response = requests.post(
                    "http://localhost:8000/api/v1/images/upload",
                    files=files,
                    timeout=30
                )
            
            self.set_loading(False)
            if response.status_code == 201:
                if self.main_window:
                    self.main_window.show_toast("Image uploaded successfully!", "success")
                self.load_images()
            else:
                if self.main_window:
                    self.main_window.show_toast(f"Upload failed: {response.text}", "error")
        except Exception as e:
            self.set_loading(False)
            if self.main_window:
                self.main_window.show_toast(f"Upload error: {str(e)}", "error")
    
    def delete_image(self):
        """Delete selected image."""
        if not self.selected_image_id:
            return
        
        reply = QMessageBox.question(
            self, 'Confirm Delete',
            'Are you sure you want to delete this image?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.set_loading(True, "Deleting image...")
            try:
                response = requests.delete(
                    f"http://localhost:8000/api/v1/images/{self.selected_image_id}",
                    timeout=30
                )
                
                self.set_loading(False)
                if response.status_code in [200, 204]:
                    if self.main_window:
                        self.main_window.show_toast("Image deleted successfully!", "success")
                    self.load_images()
                    self.selected_image_id = None
                    self.delete_btn.setEnabled(False)
                else:
                    if self.main_window:
                        self.main_window.show_toast(f"Delete failed: {response.text}", "error")
            except Exception as e:
                self.set_loading(False)
                if self.main_window:
                    self.main_window.show_toast(f"Delete error: {str(e)}", "error")
    
    def on_image_selected(self, item):
        """Handle image selection."""
        # Extract image ID from the item text
        text = item.text()
        if ' - ' in text:
            self.selected_image_id = text.split(' - ')[-1]
            self.delete_btn.setEnabled(True)
            # Emit signal to notify other tabs
            self.image_selected.emit(self.selected_image_id)
    
    def on_error(self, error_msg):
        """Handle errors."""
        self.set_loading(False)
        if self.main_window:
            self.main_window.show_toast(error_msg, "error")
    
    def cleanup_workers(self):
        """Clean up running workers."""
        for worker in self.workers:
            if worker.isRunning():
                worker.terminate()
                worker.wait()
        self.workers.clear()


class AnalysisTab(QWidget):
    """Tab for viewing and editing image analysis."""
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.current_image_id = None
        self.workers = []  # Track workers for cleanup
        self.network_managers = []  # Track network managers for cleanup
        self.progress_overlay = ProgressOverlay(parent=self)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget
        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Image Analysis")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Instructions
        self.instruction_label = QLabel("Select an image from the Upload tab to view/edit analysis")
        layout.addWidget(self.instruction_label)
        
        # Image preview box
        self.image_preview_label = QLabel()
        self.image_preview_label.setMinimumSize(200, 200)
        self.image_preview_label.setMaximumSize(400, 400)
        self.image_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview_label.setToolTip("Preview of the currently selected image for analysis")
        colors = theme_manager.get_theme_colors()
        self.image_preview_label.setStyleSheet(f"""
            QLabel {{
                border: 2px solid {colors['border']};
                border-radius: 8px;
                background-color: {colors['surface']};
            }}
        """)
        self.image_preview_label.setText("No image selected")
        layout.addWidget(self.image_preview_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Status and progress
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(20)
        layout.addWidget(self.progress_bar)
        
        # Analysis form - individual collapsible sections
        layout.addWidget(QLabel("<b>Analysis Details</b>"))
        
        # Title section
        title_group = CollapsibleGroupBox("Title")
        title_group.setToolTip("The main title or subject of the image")
        title_layout = QVBoxLayout()
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Image title")
        self.title_edit.setToolTip("Enter a descriptive title for the image")
        self.title_edit.setReadOnly(True)
        title_layout.addWidget(self.title_edit)
        title_group.setLayout(title_layout)
        layout.addWidget(title_group)
        
        # Subject section
        subject_group = CollapsibleGroupBox("Subject")
        subject_group.setToolTip("Detailed description of the main subject or focal point")
        subject_layout = QVBoxLayout()
        self.subject_edit = TextEditWithCounter(placeholder="Subject description")
        self.subject_edit.setToolTip("Describe the main subject or focal point of the image in detail")
        self.subject_edit.setMaximumHeight(100)
        self.subject_edit.setReadOnly(True)
        subject_layout.addWidget(self.subject_edit)
        subject_group.setLayout(subject_layout)
        layout.addWidget(subject_group)
        
        # Character section
        character_group = CollapsibleGroupBox("Character")
        character_group.setToolTip("Description of any characters present in the image")
        character_layout = QVBoxLayout()
        self.character_edit = TextEditWithCounter(placeholder="Character description")
        self.character_edit.setToolTip("Describe any characters, people, or figures in the image")
        self.character_edit.setMaximumHeight(100)
        self.character_edit.setReadOnly(True)
        character_layout.addWidget(self.character_edit)
        character_group.setLayout(character_layout)
        layout.addWidget(character_group)
        
        # Environment section
        environment_group = CollapsibleGroupBox("Environment")
        environment_group.setToolTip("Description of the setting, background, and surroundings")
        environment_layout = QVBoxLayout()
        self.environment_edit = TextEditWithCounter(placeholder="Environment description")
        self.environment_edit.setToolTip("Describe the setting, background, and environmental elements")
        self.environment_edit.setMaximumHeight(100)
        self.environment_edit.setReadOnly(True)
        environment_layout.addWidget(self.environment_edit)
        environment_group.setLayout(environment_layout)
        layout.addWidget(environment_group)
        
        # Art Style section
        art_style_group = CollapsibleGroupBox("Art Style")
        art_style_group.setToolTip("The artistic style, medium, or technique used")
        art_style_layout = QVBoxLayout()
        self.art_style_edit = QLineEdit()
        self.art_style_edit.setPlaceholderText("Art style")
        self.art_style_edit.setToolTip("Enter the art style (e.g., digital painting, watercolor, pixel art)")
        self.art_style_edit.setReadOnly(True)
        art_style_layout.addWidget(self.art_style_edit)
        art_style_group.setLayout(art_style_layout)
        layout.addWidget(art_style_group)
        
        # Mood section
        mood_group = CollapsibleGroupBox("Mood")
        mood_group.setToolTip("The emotional tone or atmosphere of the image")
        mood_layout = QVBoxLayout()
        self.mood_edit = QLineEdit()
        self.mood_edit.setPlaceholderText("Mood")
        self.mood_edit.setToolTip("Enter the mood or emotional atmosphere (e.g., peaceful, dark, energetic)")
        self.mood_edit.setReadOnly(True)
        mood_layout.addWidget(self.mood_edit)
        mood_group.setLayout(mood_layout)
        layout.addWidget(mood_group)
        
        # Genre section
        genre_group = CollapsibleGroupBox("Genre")
        genre_group.setToolTip("The category or genre of the artwork")
        genre_layout = QVBoxLayout()
        self.genre_edit = QLineEdit()
        self.genre_edit.setPlaceholderText("Genre")
        self.genre_edit.setToolTip("Enter the genre (e.g., fantasy, sci-fi, portrait, landscape)")
        self.genre_edit.setReadOnly(True)
        genre_layout.addWidget(self.genre_edit)
        genre_group.setLayout(genre_layout)
        layout.addWidget(genre_group)
        
        # Technical section
        technical_group = CollapsibleGroupBox("Technical Details")
        technical_group.setToolTip("Technical aspects like composition, lighting, and technique")
        technical_layout = QVBoxLayout()
        self.technical_edit = TextEditWithCounter(placeholder="Technical details")
        self.technical_edit.setToolTip("Describe technical details like composition, lighting, color palette, and techniques used")
        self.technical_edit.setMaximumHeight(100)
        self.technical_edit.setReadOnly(True)
        technical_layout.addWidget(self.technical_edit)
        technical_group.setLayout(technical_layout)
        layout.addWidget(technical_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        colors = theme_manager.get_theme_colors()
        text_color = "black" if theme_manager.current_theme in ["retro", "light"] else "white"
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setToolTip("Toggle edit mode to manually enter or modify analysis data")
        self.edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['warning']};
                color: {text_color};
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 8px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors['warning_hover']};
            }}
            QPushButton:disabled {{
                background-color: {colors['border']};
            }}
        """)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        self.edit_btn.setEnabled(False)
        
        self.analyze_btn = QPushButton("🔍 Analyze Image")
        self.analyze_btn.setToolTip("Analyze the selected image using AI to extract visual details")
        self.analyze_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['primary']};
                color: {text_color};
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 8px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors['primary_hover']};
            }}
            QPushButton:disabled {{
                background-color: {colors['border']};
            }}
        """)
        self.analyze_btn.clicked.connect(self.analyze_image)
        self.save_btn = QPushButton("💾 Save Analysis")
        self.save_btn.setToolTip("Save the current analysis data to the database")
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['success']};
                color: {text_color};
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 8px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors['success_hover']};
            }}
            QPushButton:disabled {{
                background-color: {colors['border']};
            }}
        """)
        self.save_btn.clicked.connect(self.save_analysis)
        self.save_btn.setEnabled(False)
        
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.analyze_btn)
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)
        
        layout.addStretch()
        content_widget.setLayout(layout)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
    
    def set_image(self, image_id):
        """Set the current image."""
        self.current_image_id = image_id
        self.instruction_label.setText(f"Editing analysis for image: {image_id[:8]}...")
        self.edit_btn.setEnabled(True)
        self.load_analysis()
        self.save_btn.setEnabled(True)
        self.load_image_preview(image_id)
    
    def load_image_preview(self, image_id):
        """Load and display image preview."""
        self.set_loading(True, "Loading image preview...")
        worker = APIWorker(f"http://localhost:8000/api/v1/images/{image_id}")
        worker.finished.connect(self.on_image_preview_loaded)
        worker.error.connect(self.on_image_preview_error)
        worker.progress.connect(self.on_progress)
        self.workers.append(worker)
        worker.start()
    
    def on_image_preview_loaded(self, data):
        """Handle loaded image preview."""
        self.set_loading(False)
        # Get image path from API response
        thumbnail_path = data.get('thumbnail_path') or data.get('original_path')
        if thumbnail_path and thumbnail_path != "null":
            # Convert file path to HTTP URL
            http_path = thumbnail_path.replace("\\", "/")
            image_url = f"http://localhost:8000/{http_path}"
            
            # Use QNetworkAccessManager to fetch image
            manager = QNetworkAccessManager()
            self.network_managers.append(manager)  # Keep reference to prevent garbage collection
            request = QNetworkRequest(QUrl(image_url))
            
            def on_reply_finished(reply):
                if reply.error() == QNetworkReply.NetworkError.NoError:
                    image_data = reply.readAll()
                    pixmap = QPixmap()
                    if pixmap.loadFromData(image_data):
                        # Scale to fit the available space while maintaining aspect ratio
                        label_size = self.image_preview_label.size()
                        scaled_pixmap = pixmap.scaled(label_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        self.image_preview_label.setPixmap(scaled_pixmap)
                        self.image_preview_label.setText("")
                    else:
                        self.image_preview_label.setText("Failed to load image")
                else:
                    self.image_preview_label.setText("Failed to load image")
                reply.deleteLater()
                # Remove manager from list after request completes
                if manager in self.network_managers:
                    self.network_managers.remove(manager)
            
            manager.finished.connect(on_reply_finished)
            manager.get(request)
        else:
            self.image_preview_label.setText("No image path")
    
    def on_image_preview_error(self, error_msg):
        """Handle image preview load error."""
        self.set_loading(False)
        self.image_preview_label.setText("Failed to load preview")
    
    def load_analysis(self):
        """Load analysis for current image."""
        if not self.current_image_id:
            return
        
        self.set_loading(True, "Loading existing analysis...")
        worker = APIWorker(f"http://localhost:8000/api/v1/analysis/{self.current_image_id}")
        worker.finished.connect(self.on_analysis_loaded)
        worker.error.connect(self.on_analysis_load_error)  # Handle 404 separately
        worker.progress.connect(self.on_progress)
        self.workers.append(worker)
        worker.start()
    
    def on_analysis_load_error(self, error_msg):
        """Handle analysis load error (e.g., 404 not found)."""
        self.set_loading(False)
        # If analysis doesn't exist (404), enable manual entry
        if "404" in error_msg or "not found" in error_msg.lower():
            self.instruction_label.setText("No analysis found. Click 'Edit' to manually enter analysis.")
            # Clear fields and keep them in read-only mode
            self.title_edit.clear()
            self.subject_edit.clear()
            self.character_edit.clear()
            self.environment_edit.clear()
            self.art_style_edit.clear()
            self.mood_edit.clear()
            self.genre_edit.clear()
            self.technical_edit.clear()
            # Ensure fields are in read-only mode
            self.set_edit_mode(False)
            # Enable edit button for manual entry
            self.edit_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
        else:
            self.on_error(error_msg)
    
    def on_progress(self, message):
        """Handle progress updates."""
        self.status_label.setText(message)
    
    def set_loading(self, loading, message="Loading..."):
        """Set loading state."""
        self.progress_bar.setVisible(loading)
        self.analyze_btn.setEnabled(not loading and self.current_image_id is not None)
        self.save_btn.setEnabled(not loading and self.current_image_id is not None)
        if loading:
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.status_label.setText(message)
            self.progress_overlay.set_message(message)
            self.progress_overlay.show_overlay(self)
        else:
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(1)
            self.status_label.setText("Ready")
            self.progress_overlay.hide()
    
    def on_analysis_loaded(self, data):
        """Handle loaded analysis."""
        self.set_loading(False)
        self.title_edit.setText(data.get("title", ""))
        self.subject_edit.setPlainText(data.get("subject", ""))
        self.character_edit.setPlainText(data.get("character_description", ""))
        self.environment_edit.setPlainText(data.get("environment", ""))
        self.art_style_edit.setText(data.get("art_style", ""))
        self.mood_edit.setText(data.get("mood", ""))
        self.genre_edit.setText(data.get("genre", ""))
        self.technical_edit.setPlainText(data.get("technical_details", ""))
        # Ensure fields are in read-only mode after loading
        self.set_edit_mode(False)
    
    def analyze_image(self):
        """Analyze the current image."""
        if not self.current_image_id:
            if self.main_window:
                self.main_window.show_toast("Please select an image first", "warning")
            return
        
        self.set_loading(True, "Analyzing image with AI...")
        
        # Configure streaming URL for the progress overlay (GET with query param)
        streaming_url = f"http://localhost:8000/api/v1/analysis/analyze/stream?image_id={self.current_image_id}"
        self.progress_overlay.set_streaming_url(streaming_url)
        self.progress_overlay.start_streaming_worker()
        
        # Also call the non-streaming endpoint for the final result
        worker = APIWorker(
            "http://localhost:8000/api/v1/analysis/analyze",
            method="POST",
            data={"image_id": self.current_image_id}
        )
        worker.finished.connect(self.on_analysis_loaded)
        worker.error.connect(self.on_error)
        worker.progress.connect(self.on_progress)
        self.workers.append(worker)
        worker.start()
    
    def save_analysis(self):
        """Save the analysis (create new or update existing)."""
        if not self.current_image_id:
            return
        
        self.set_loading(True, "Saving analysis...")
        # Prepare update data
        update_data = {
            "title": self.title_edit.text(),
            "subject": self.subject_edit.toPlainText(),
            "character_description": self.character_edit.toPlainText(),
            "environment": self.environment_edit.toPlainText(),
            "art_style": self.art_style_edit.text(),
            "mood": self.mood_edit.text(),
            "genre": self.genre_edit.text(),
            "technical_details": self.technical_edit.toPlainText()
        }
        
        try:
            # First try to check if analysis exists
            check_response = requests.get(
                f"http://localhost:8000/api/v1/analysis/{self.current_image_id}",
                timeout=10
            )
            
            if check_response.status_code == 200:
                # Analysis exists, update it (exclude image_id from update_data)
                response = requests.put(
                    f"http://localhost:8000/api/v1/analysis/{self.current_image_id}",
                    json=update_data,
                    timeout=30
                )
            else:
                # Analysis doesn't exist, create it with manual data (include image_id)
                create_data = update_data.copy()
                create_data["image_id"] = self.current_image_id
                response = requests.post(
                    f"http://localhost:8000/api/v1/analysis/",
                    json=create_data,
                    timeout=30
                )
            
            self.set_loading(False)
            if response.status_code in [200, 201]:
                if self.main_window:
                    self.main_window.show_toast("Analysis saved successfully!", "success")
                # Exit edit mode after saving
                self.set_edit_mode(False)
            else:
                if self.main_window:
                    self.main_window.show_toast(f"Save failed: {response.text}", "error")
        except Exception as e:
            self.set_loading(False)
            if self.main_window:
                self.main_window.show_toast(f"Save error: {str(e)}", "error")
    
    def toggle_edit_mode(self):
        """Toggle between read-only and edit mode."""
        current_readonly = self.title_edit.isReadOnly()
        # If currently read-only, we want to make it editable (True)
        # If currently editable, we want to make it read-only (False)
        new_editable = current_readonly  # Toggle: if readonly is True, editable should be True
        self.set_edit_mode(new_editable)
    
    def set_edit_mode(self, editable):
        """Set edit mode for all fields."""
        # Toggle read-only state
        self.title_edit.setReadOnly(not editable)
        self.subject_edit.setReadOnly(not editable)
        self.character_edit.setReadOnly(not editable)
        self.environment_edit.setReadOnly(not editable)
        self.art_style_edit.setReadOnly(not editable)
        self.mood_edit.setReadOnly(not editable)
        self.genre_edit.setReadOnly(not editable)
        self.technical_edit.setReadOnly(not editable)
        
        # Update button text and styling
        colors = theme_manager.get_theme_colors()
        text_color = "black" if theme_manager.current_theme in ["retro", "light"] else "white"
        if editable:
            self.edit_btn.setText("✖️ Cancel Edit")
            self.edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['border']};
                    color: {colors['text_primary']};
                    border: none;
                    padding: 10px;
                    font-size: 12px;
                    border-radius: 5px;
                }}
                QPushButton:hover {{
                    background-color: {colors['text_secondary']};
                }}
            """)
            # Update field backgrounds for edit mode
            for widget in [self.title_edit, self.art_style_edit, self.mood_edit, self.genre_edit]:
                widget.setStyleSheet(f"""
                    QLineEdit {{
                        padding: 8px;
                        border: 1px solid {colors['input_focus']};
                        border-radius: 4px;
                        background-color: {colors['input_bg']};
                    }}
                """)
            for widget in [self.subject_edit, self.character_edit, self.environment_edit, self.technical_edit]:
                widget.text_edit.setStyleSheet(f"""
                    QTextEdit {{
                        padding: 8px;
                        border: 1px solid {colors['input_focus']};
                        border-radius: 4px;
                        background-color: {colors['input_bg']};
                    }}
                """)
        else:
            self.edit_btn.setText("✏️ Edit")
            self.edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['warning']};
                    color: {text_color};
                    border: none;
                    padding: 12px;
                    font-size: 13px;
                    border-radius: 8px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {colors['warning_hover']};
                }}
                QPushButton:disabled {{
                    background-color: {colors['border']};
                }}
            """)
            # Update field backgrounds for read-only mode
            for widget in [self.title_edit, self.art_style_edit, self.mood_edit, self.genre_edit]:
                widget.setStyleSheet(f"""
                    QLineEdit {{
                        padding: 8px;
                        border: 1px solid {colors['border']};
                        border-radius: 4px;
                        background-color: {colors['surface']};
                    }}
                    QLineEdit[readOnly="true"] {{
                        background-color: {colors['surface']};
                        color: {colors['text_secondary']};
                    }}
                """)
            for widget in [self.subject_edit, self.character_edit, self.environment_edit, self.technical_edit]:
                widget.text_edit.setStyleSheet(f"""
                    QTextEdit {{
                        padding: 8px;
                        border: 1px solid {colors['border']};
                        border-radius: 4px;
                        background-color: {colors['surface']};
                    }}
                """)
    
    def on_error(self, error_msg):
        """Handle errors."""
        self.set_loading(False)
        if self.main_window:
            self.main_window.show_toast(error_msg, "error")
    
    def cleanup_workers(self):
        """Clean up running workers."""
        for worker in self.workers:
            if worker.isRunning():
                worker.terminate()
                worker.wait()
        self.workers.clear()
    
    def clear_form(self):
        """Clear all form fields."""
        # Check if user has unsaved changes
        if not self.title_edit.isReadOnly():
            reply = QMessageBox.question(
                self, 'Confirm Clear',
                'You have unsaved changes. Are you sure you want to clear the form?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.title_edit.clear()
        self.subject_edit.clear()
        self.character_edit.clear()
        self.environment_edit.clear()
        self.art_style_edit.clear()
        self.mood_edit.clear()
        self.genre_edit.clear()
        self.technical_edit.clear()
        self.instruction_label.setText("Select an image from the Upload tab to view/edit analysis")
        self.current_image_id = None
        self.analyze_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.edit_btn.setEnabled(False)
        # Reset to read-only mode
        self.set_edit_mode(False)


class ContentTab(QWidget):
    """Tab for generating and editing platform-specific content."""
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.current_image_id = None
        self.content_edits = {}  # Store text edits for each platform
        self.workers = []  # Track workers for cleanup
        self.network_managers = []  # Track network managers for cleanup
        self.progress_overlay = ProgressOverlay(parent=self)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget
        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Content Generation")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Instructions
        self.instruction_label = QLabel("Select an image from the Upload tab to generate content")
        layout.addWidget(self.instruction_label)
        
        # Image preview box
        self.image_preview_label = QLabel()
        self.image_preview_label.setMinimumSize(200, 200)
        self.image_preview_label.setMaximumSize(400, 400)
        self.image_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview_label.setToolTip("Preview of the currently selected image for content generation")
        colors = theme_manager.get_theme_colors()
        self.image_preview_label.setStyleSheet(f"""
            QLabel {{
                border: 2px solid {colors['border']};
                border-radius: 8px;
                background-color: {colors['surface']};
            }}
        """)
        self.image_preview_label.setText("No image selected")
        layout.addWidget(self.image_preview_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Status and progress
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(20)
        layout.addWidget(self.progress_bar)
        
        # Platform tabs
        self.platform_tabs = QTabWidget()
        self.platform_tabs.setToolTip("Select a platform to view or generate content for that specific platform")
        colors = theme_manager.get_theme_colors()
        
        # Style the tab widget for better visibility in dark/retro modes
        if theme_manager.current_theme == "retro":
            # Use green for retro mode to match the theme
            selected_color = colors['success']  # Green
            selected_border = colors['success']
        elif theme_manager.current_theme == "dark":
            selected_color = colors['primary']  # Blue
            selected_border = colors['primary']
        else:
            selected_color = colors['primary']  # Blue
            selected_border = colors['primary']
        
        self.platform_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {colors['border']};
                background-color: {colors['surface']};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background-color: {colors['surface']};
                color: {colors['text_secondary']};
                padding: 10px 20px;
                border: 1px solid {colors['border']};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {selected_color};
                color: white;
                border: 2px solid {selected_border};
                border-bottom: 2px solid {selected_border};
                font-weight: bold;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {colors['border']};
            }}
        """)
        
        # Create tabs for each platform with specific fields
        self.content_edits = {}  # Will store dicts of fields per platform
        
        # X/Twitter tab - 3 collapsible fields
        twitter_tab = QWidget()
        twitter_layout = QVBoxLayout()
        
        twitter_short_group = CollapsibleGroupBox("Short Version")
        twitter_short_group.setToolTip("A concise tweet for quick engagement")
        twitter_short_layout = QVBoxLayout()
        twitter_short = TextEditWithCounterAndCopy(max_chars=280, placeholder="Short tweet (under 280 chars)")
        twitter_short.setToolTip("Write a short, punchy tweet (max 280 characters)")
        twitter_short.setReadOnly(True)
        twitter_short.setMaximumHeight(100)
        twitter_short_layout.addWidget(twitter_short)
        twitter_short_group.setLayout(twitter_short_layout)
        twitter_layout.addWidget(twitter_short_group)
        
        twitter_medium_group = CollapsibleGroupBox("Medium Version")
        twitter_medium_group.setToolTip("A more detailed tweet with additional context")
        twitter_medium_layout = QVBoxLayout()
        twitter_medium = TextEditWithCounterAndCopy(max_chars=280, placeholder="Medium-length tweet")
        twitter_medium.setToolTip("Write a medium-length tweet with more detail (max 280 characters)")
        twitter_medium.setReadOnly(True)
        twitter_medium.setMaximumHeight(120)
        twitter_medium_layout.addWidget(twitter_medium)
        twitter_medium_group.setLayout(twitter_medium_layout)
        twitter_layout.addWidget(twitter_medium_group)
        
        twitter_engagement_group = CollapsibleGroupBox("Engagement Version")
        twitter_engagement_group.setToolTip("An engagement-focused tweet with hashtags and call-to-action")
        twitter_engagement_layout = QVBoxLayout()
        twitter_engagement = TextEditWithCounterAndCopy(max_chars=280, placeholder="Engagement-focused tweet with hashtags")
        twitter_engagement.setToolTip("Write an engaging tweet with hashtags and a call-to-action (max 280 characters)")
        twitter_engagement.setReadOnly(True)
        twitter_engagement_layout.addWidget(twitter_engagement)
        twitter_engagement_group.setLayout(twitter_engagement_layout)
        twitter_layout.addWidget(twitter_engagement_group)
        
        twitter_tab.setLayout(twitter_layout)
        self.platform_tabs.addTab(twitter_tab, "𝕏 Twitter")
        self.content_edits["X/Twitter"] = {
            "short": twitter_short,
            "medium": twitter_medium,
            "engagement": twitter_engagement
        }
        
        # Instagram tab - 2 collapsible fields
        instagram_tab = QWidget()
        instagram_layout = QVBoxLayout()
        
        instagram_caption_group = CollapsibleGroupBox("Caption")
        instagram_caption_group.setToolTip("The main caption for the Instagram post")
        instagram_caption_layout = QVBoxLayout()
        instagram_caption = TextEditWithCounterAndCopy(placeholder="Instagram caption")
        instagram_caption.setToolTip("Write a descriptive caption for your Instagram post")
        instagram_caption.setReadOnly(True)
        instagram_caption_layout.addWidget(instagram_caption)
        instagram_caption_group.setLayout(instagram_caption_layout)
        instagram_layout.addWidget(instagram_caption_group)
        
        instagram_hashtags_group = CollapsibleGroupBox("Hashtags")
        instagram_hashtags_group.setToolTip("Relevant hashtags for discoverability")
        instagram_hashtags_layout = QVBoxLayout()
        instagram_hashtags = TextEditWithCounterAndCopy(placeholder="Hashtags (comma-separated)")
        instagram_hashtags.setToolTip("Add relevant hashtags separated by commas")
        instagram_hashtags.setReadOnly(True)
        instagram_hashtags.setMaximumHeight(100)
        instagram_hashtags_layout.addWidget(instagram_hashtags)
        instagram_hashtags_group.setLayout(instagram_hashtags_layout)
        instagram_layout.addWidget(instagram_hashtags_group)
        
        instagram_tab.setLayout(instagram_layout)
        self.platform_tabs.addTab(instagram_tab, "📷 Instagram")
        self.content_edits["Instagram"] = {
            "caption": instagram_caption,
            "hashtags": instagram_hashtags
        }
        
        # Reddit tab - 2 collapsible fields
        reddit_tab = QWidget()
        reddit_layout = QVBoxLayout()
        
        reddit_title_group = CollapsibleGroupBox("Title")
        reddit_title_group.setToolTip("The title for your Reddit post")
        reddit_title_layout = QVBoxLayout()
        reddit_title = TextEditWithCounterAndCopy(max_chars=300, placeholder="Post title")
        reddit_title.setToolTip("Write a catchy title for your Reddit post (max 300 characters)")
        reddit_title.setReadOnly(True)
        reddit_title.setMaximumHeight(80)
        reddit_title_layout.addWidget(reddit_title)
        reddit_title_group.setLayout(reddit_title_layout)
        reddit_layout.addWidget(reddit_title_group)
        
        reddit_body_group = CollapsibleGroupBox("Body")
        reddit_body_group.setToolTip("The main content of your Reddit post")
        reddit_body_layout = QVBoxLayout()
        reddit_body = TextEditWithCounterAndCopy(placeholder="Post body content")
        reddit_body.setToolTip("Write the main content for your Reddit post")
        reddit_body.setReadOnly(True)
        reddit_body_layout.addWidget(reddit_body)
        reddit_body_group.setLayout(reddit_body_layout)
        reddit_layout.addWidget(reddit_body_group)
        
        reddit_tab.setLayout(reddit_layout)
        self.platform_tabs.addTab(reddit_tab, "📱 Reddit")
        self.content_edits["Reddit"] = {
            "title": reddit_title,
            "body": reddit_body
        }
        
        # ArtStation tab - 3 collapsible fields
        artstation_tab = QWidget()
        artstation_layout = QVBoxLayout()
        
        artstation_title_group = CollapsibleGroupBox("Title")
        artstation_title_group.setToolTip("The title for your ArtStation artwork")
        artstation_title_layout = QVBoxLayout()
        artstation_title = TextEditWithCounterAndCopy(placeholder="Artwork title")
        artstation_title.setToolTip("Enter the title for your ArtStation artwork")
        artstation_title.setReadOnly(True)
        artstation_title.setMaximumHeight(80)
        artstation_title_layout.addWidget(artstation_title)
        artstation_title_group.setLayout(artstation_title_layout)
        artstation_layout.addWidget(artstation_title_group)
        
        artstation_description_group = CollapsibleGroupBox("Description")
        artstation_description_group.setToolTip("Detailed description of your artwork")
        artstation_description_layout = QVBoxLayout()
        artstation_description = TextEditWithCounterAndCopy(placeholder="Artwork description")
        artstation_description.setToolTip("Write a detailed description of your artwork")
        artstation_description.setReadOnly(True)
        artstation_description_layout.addWidget(artstation_description)
        artstation_description_group.setLayout(artstation_description_layout)
        artstation_layout.addWidget(artstation_description_group)
        
        artstation_tags_group = CollapsibleGroupBox("Tags")
        artstation_tags_group.setToolTip("SEO tags for discoverability")
        artstation_tags_layout = QVBoxLayout()
        artstation_tags = TextEditWithCounterAndCopy(placeholder="SEO tags")
        artstation_tags.setToolTip("Add relevant tags for SEO and discoverability")
        artstation_tags.setReadOnly(True)
        artstation_tags.setMaximumHeight(100)
        artstation_tags_layout.addWidget(artstation_tags)
        artstation_tags_group.setLayout(artstation_tags_layout)
        artstation_layout.addWidget(artstation_tags_group)
        
        artstation_tab.setLayout(artstation_layout)
        self.platform_tabs.addTab(artstation_tab, "🎨 ArtStation")
        self.content_edits["ArtStation"] = {
            "title": artstation_title,
            "description": artstation_description,
            "tags": artstation_tags
        }
        
        # DeviantArt tab - 3 collapsible fields
        deviantart_tab = QWidget()
        deviantart_layout = QVBoxLayout()
        
        deviantart_title_group = CollapsibleGroupBox("Title")
        deviantart_title_group.setToolTip("The title for your DeviantArt artwork")
        deviantart_title_layout = QVBoxLayout()
        deviantart_title = TextEditWithCounterAndCopy(placeholder="Artwork title")
        deviantart_title.setToolTip("Enter the title for your DeviantArt artwork")
        deviantart_title.setReadOnly(True)
        deviantart_title.setMaximumHeight(80)
        deviantart_title_layout.addWidget(deviantart_title)
        deviantart_title_group.setLayout(deviantart_title_layout)
        deviantart_layout.addWidget(deviantart_title_group)
        
        deviantart_description_group = CollapsibleGroupBox("Description")
        deviantart_description_group.setToolTip("Detailed description of your artwork")
        deviantart_description_layout = QVBoxLayout()
        deviantart_description = TextEditWithCounterAndCopy(placeholder="Artwork description")
        deviantart_description.setToolTip("Write a detailed description of your artwork")
        deviantart_description.setReadOnly(True)
        deviantart_description_layout.addWidget(deviantart_description)
        deviantart_description_group.setLayout(deviantart_description_layout)
        deviantart_layout.addWidget(deviantart_description_group)
        
        deviantart_tags_group = CollapsibleGroupBox("Tags")
        deviantart_tags_group.setToolTip("SEO tags for discoverability")
        deviantart_tags_layout = QVBoxLayout()
        deviantart_tags = TextEditWithCounterAndCopy(placeholder="SEO tags")
        deviantart_tags.setToolTip("Add relevant tags for SEO and discoverability")
        deviantart_tags.setReadOnly(True)
        deviantart_tags.setMaximumHeight(100)
        deviantart_tags_layout.addWidget(deviantart_tags)
        deviantart_tags_group.setLayout(deviantart_tags_layout)
        deviantart_layout.addWidget(deviantart_tags_group)
        
        deviantart_tab.setLayout(deviantart_layout)
        self.platform_tabs.addTab(deviantart_tab, "🖌️ DeviantArt")
        self.content_edits["DeviantArt"] = {
            "title": deviantart_title,
            "description": deviantart_description,
            "tags": deviantart_tags
        }
        
        # Apply consistent styling to all content fields
        colors = theme_manager.get_theme_colors()
        for platform, fields in self.content_edits.items():
            for field_name, field_edit in fields.items():
                field_edit.text_edit.setStyleSheet(f"""
                    QTextEdit {{
                        padding: 12px;
                        border: 1px solid {colors['input_border']};
                        border-radius: 8px;
                        background-color: {colors['input_bg']};
                        font-size: 13px;
                    }}
                    QTextEdit:focus {{
                        border: 2px solid {colors['input_focus']};
                        background-color: {colors['background']};
                    }}
                """)
        
        layout.addWidget(self.platform_tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        colors = theme_manager.get_theme_colors()
        text_color = "black" if theme_manager.current_theme in ["retro", "light"] else "white"
        self.edit_content_btn = QPushButton("✏️ Edit Content")
        self.edit_content_btn.setToolTip("Toggle edit mode to manually enter or modify generated content")
        self.edit_content_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['warning']};
                color: {text_color};
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 8px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors['warning_hover']};
            }}
            QPushButton:disabled {{
                background-color: {colors['border']};
            }}
        """)
        self.edit_content_btn.clicked.connect(self.toggle_content_edit_mode)
        self.edit_content_btn.setEnabled(False)
        
        self.generate_btn = QPushButton("✨ Generate Content")
        self.generate_btn.setToolTip("Generate platform-specific content using AI based on the image analysis")
        self.generate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['purple']};
                color: {text_color};
                border: none;
                padding: 14px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {colors['purple_hover']};
            }}
            QPushButton:disabled {{
                background-color: {colors['border']};
            }}
        """)
        self.generate_btn.clicked.connect(self.generate_content)
        self.generate_btn.setEnabled(False)
        
        button_layout.addWidget(self.edit_content_btn)
        button_layout.addWidget(self.generate_btn)
        layout.addLayout(button_layout)
        
        layout.addStretch()
        content_widget.setLayout(layout)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
    
    def set_image(self, image_id):
        """Set the current image."""
        self.current_image_id = image_id
        self.instruction_label.setText(f"Generating content for image: {image_id[:8]}...")
        self.edit_content_btn.setEnabled(True)
        self.load_content()
        self.generate_btn.setEnabled(True)
        self.load_image_preview(image_id)
    
    def load_image_preview(self, image_id):
        """Load and display image preview."""
        self.set_loading(True, "Loading image preview...")
        worker = APIWorker(f"http://localhost:8000/api/v1/images/{image_id}")
        worker.finished.connect(self.on_image_preview_loaded)
        worker.error.connect(self.on_image_preview_error)
        worker.progress.connect(self.on_progress)
        self.workers.append(worker)
        worker.start()
    
    def on_image_preview_loaded(self, data):
        """Handle loaded image preview."""
        self.set_loading(False)
        # Get image path from API response
        thumbnail_path = data.get('thumbnail_path') or data.get('original_path')
        if thumbnail_path and thumbnail_path != "null":
            # Convert file path to HTTP URL
            http_path = thumbnail_path.replace("\\", "/")
            image_url = f"http://localhost:8000/{http_path}"
            
            # Use QNetworkAccessManager to fetch image
            manager = QNetworkAccessManager()
            self.network_managers.append(manager)  # Keep reference to prevent garbage collection
            request = QNetworkRequest(QUrl(image_url))
            
            def on_reply_finished(reply):
                if reply.error() == QNetworkReply.NetworkError.NoError:
                    image_data = reply.readAll()
                    pixmap = QPixmap()
                    if pixmap.loadFromData(image_data):
                        # Scale to fit the available space while maintaining aspect ratio
                        label_size = self.image_preview_label.size()
                        scaled_pixmap = pixmap.scaled(label_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        self.image_preview_label.setPixmap(scaled_pixmap)
                        self.image_preview_label.setText("")
                    else:
                        self.image_preview_label.setText("Failed to load image")
                else:
                    self.image_preview_label.setText("Failed to load image")
                reply.deleteLater()
                # Remove manager from list after request completes
                if manager in self.network_managers:
                    self.network_managers.remove(manager)
            
            manager.finished.connect(on_reply_finished)
            manager.get(request)
        else:
            self.image_preview_label.setText("No image path")
    
    def on_image_preview_error(self, error_msg):
        """Handle image preview load error."""
        self.set_loading(False)
        self.image_preview_label.setText("Failed to load preview")
    
    def load_content(self):
        """Load content for current image."""
        if not self.current_image_id:
            return
        
        self.set_loading(True, "Loading existing content...")
        worker = APIWorker(f"http://localhost:8000/api/v1/content/{self.current_image_id}")
        worker.finished.connect(self.on_content_loaded)
        worker.error.connect(self.on_content_load_error)  # Handle 404 separately
        worker.progress.connect(self.on_progress)
        self.workers.append(worker)
        worker.start()
    
    def on_content_load_error(self, error_msg):
        """Handle content load error (e.g., 404 not found)."""
        self.set_loading(False)
        # If content doesn't exist (404), enable manual entry
        if "404" in error_msg or "not found" in error_msg.lower():
            self.instruction_label.setText("No content found. Click 'Generate Content' to create posts.")
            # Clear all content fields
            for platform, fields in self.content_edits.items():
                for field_name, field_edit in fields.items():
                    field_edit.clear()
            # Enable edit and generate buttons
            self.edit_content_btn.setEnabled(True)
            self.generate_btn.setEnabled(True)
        else:
            self.on_error(error_msg)
    
    def on_progress(self, message):
        """Handle progress updates."""
        self.status_label.setText(message)
    
    def set_loading(self, loading, message="Loading..."):
        """Set loading state."""
        self.progress_bar.setVisible(loading)
        self.generate_btn.setEnabled(not loading and self.current_image_id is not None)
        if loading:
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.status_label.setText(message)
            self.progress_overlay.set_message(message)
            self.progress_overlay.show_overlay(self)
        else:
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(1)
            self.status_label.setText("Ready")
            self.progress_overlay.hide()
    
    def on_content_loaded(self, data):
        """Handle loaded content."""
        self.set_loading(False)
        
        # The backend returns AllContentResponse with a platforms dict
        # Extract the platforms dict if it exists, otherwise treat as flat list
        if isinstance(data, dict) and "platforms" in data:
            platforms_dict = data["platforms"]
            # Convert dict to flat list
            content_items = []
            for platform, items in platforms_dict.items():
                content_items.extend(items)
        else:
            content_items = data if isinstance(data, list) else []
        
        # Clear all content edits first
        for platform, fields in self.content_edits.items():
            for field_name, field_edit in fields.items():
                field_edit.clear()
        
        # Map platform names and content types to field names
        platform_map = {
            "artstation": "ArtStation",
            "x": "X/Twitter",
            "instagram": "Instagram",
            "reddit": "Reddit",
            "deviantart": "DeviantArt"
        }
        
        # Map content types to field names for each platform
        content_type_map = {
            "X/Twitter": {
                "post": "all"  # Special handling needed
            },
            "Instagram": {
                "post": "caption",
                "hashtags": "hashtags"
            },
            "Reddit": {
                "title": "title",
                "description": "body"
            },
            "ArtStation": {
                "title": "title",
                "description": "description",
                "hashtags": "tags"
            },
            "DeviantArt": {
                "title": "title",
                "description": "description",
                "hashtags": "tags"
            }
        }
        
        # Populate content for each platform
        for item in content_items:
            platform = item.get("platform", "")
            content = item.get("content", "")
            content_type = item.get("content_type", "")
            
            display_platform = platform_map.get(platform.lower(), platform)
            
            if display_platform in self.content_edits:
                # Map content_type to field name
                if display_platform in content_type_map:
                    field_name = content_type_map[display_platform].get(content_type)
                    
                    # Special handling for X/Twitter posts
                    if display_platform == "X/Twitter" and content_type == "post":
                        # Content format: "[short] content", "[medium] content", "[engagement] content
                        if content.startswith("[short]"):
                            self.content_edits[display_platform]["short"].setPlainText(content.replace("[short] ", "").strip())
                        elif content.startswith("[medium]"):
                            self.content_edits[display_platform]["medium"].setPlainText(content.replace("[medium] ", "").strip())
                        elif content.startswith("[engagement]"):
                            self.content_edits[display_platform]["engagement"].setPlainText(content.replace("[engagement] ", "").strip())
                    
                    # Special handling for Instagram post (caption)
                    elif display_platform == "Instagram" and content_type == "post" and field_name == "caption":
                        self.content_edits[display_platform][field_name].setPlainText(content)
                    
                    # Special handling for Reddit description (body)
                    elif display_platform == "Reddit" and content_type == "description" and field_name == "body":
                        self.content_edits[display_platform][field_name].setPlainText(content)
                    
                    # Special handling for hashtags (already joined by backend)
                    elif content_type == "hashtags" and field_name:
                        if field_name in self.content_edits[display_platform]:
                            self.content_edits[display_platform][field_name].setPlainText(content)
                    
                    # Regular handling for title, description, etc.
                    elif field_name and field_name in self.content_edits[display_platform]:
                        self.content_edits[display_platform][field_name].setPlainText(content)
        
        # Ensure fields are in read-only mode after loading
        self.set_content_edit_mode(False)
        self.status_label.setText(f"Loaded content for {len(content_items)} items")
    
    def generate_content(self):
        """Generate content for current image."""
        if not self.current_image_id:
            if self.main_window:
                self.main_window.show_toast("Please select an image first", "warning")
            return
        
        self.set_loading(True, "Generating content with AI...")
        
        # Configure streaming URL for the progress overlay (GET with query params)
        platforms = "Instagram,Twitter,X,Facebook,TikTok,LinkedIn,Reddit,YouTube,Blog,Email"
        streaming_url = f"http://localhost:8000/api/v1/content/generate/stream?image_id={self.current_image_id}&platforms={platforms}"
        self.progress_overlay.set_streaming_url(streaming_url)
        self.progress_overlay.start_streaming_worker()
        
        # Also call the non-streaming endpoint for the final result
        worker = APIWorker(
            "http://localhost:8000/api/v1/content/generate",
            method="POST",
            data={"image_id": self.current_image_id}
        )
        worker.finished.connect(self.on_content_generated)
        worker.error.connect(self.on_error)
        worker.progress.connect(self.on_progress)
        self.workers.append(worker)
        worker.start()
    
    def on_content_generated(self, data):
        """Handle content generation completion."""
        # After generation, reload the content from the database
        if self.main_window:
            self.main_window.show_toast("Content generated successfully!", "success")
        self.load_content()
    
    def on_error(self, error_msg):
        """Handle errors."""
        self.set_loading(False)
        if self.main_window:
            self.main_window.show_toast(error_msg, "error")
    
    def cleanup_workers(self):
        """Clean up running workers."""
        for worker in self.workers:
            if worker.isRunning():
                worker.terminate()
                worker.wait()
        self.workers.clear()
    
    def clear_form(self):
        """Clear all content fields."""
        # Check if user has unsaved changes
        first_platform = list(self.content_edits.values())[0]
        first_field = list(first_platform.values())[0]
        if not first_field.isReadOnly():
            reply = QMessageBox.question(
                self, 'Confirm Clear',
                'You have unsaved changes. Are you sure you want to clear the form?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        for platform, fields in self.content_edits.items():
            for field_name, field_edit in fields.items():
                field_edit.clear()
        self.instruction_label.setText("Select an image from the Upload tab to generate/edit content")
        self.current_image_id = None
        self.generate_btn.setEnabled(False)
        self.edit_content_btn.setEnabled(False)
        # Reset to read-only mode
        self.set_content_edit_mode(False)
    
    def toggle_content_edit_mode(self):
        """Toggle between read-only and edit mode for content."""
        # Get the first field from the first platform to check current state
        first_platform = list(self.content_edits.values())[0]
        first_field = list(first_platform.values())[0]
        current_readonly = first_field.isReadOnly()
        # If currently read-only, we want to make it editable (True)
        # If currently editable, we want to make it read-only (False)
        new_editable = current_readonly  # Toggle: if readonly is True, editable should be True
        self.set_content_edit_mode(new_editable)
    
    def set_content_edit_mode(self, editable):
        """Set edit mode for all content fields."""
        # Toggle read-only state for all platform fields
        for platform, fields in self.content_edits.items():
            for field_name, field_edit in fields.items():
                field_edit.setReadOnly(not editable)
        
        # Update button text and styling
        colors = theme_manager.get_theme_colors()
        text_color = "black" if theme_manager.current_theme in ["retro", "light"] else "white"
        if editable:
            self.edit_content_btn.setText("✖️ Cancel Edit")
            self.edit_content_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['border']};
                    color: {colors['text_primary']};
                    border: none;
                    padding: 10px;
                    font-size: 12px;
                    border-radius: 5px;
                }}
                QPushButton:hover {{
                    background-color: {colors['text_secondary']};
                }}
            """)
            # Update field backgrounds for edit mode
            for platform, fields in self.content_edits.items():
                for field_name, field_edit in fields.items():
                    field_edit.text_edit.setStyleSheet(f"""
                        QTextEdit {{
                            padding: 12px;
                            border: 1px solid {colors['purple']};
                            border-radius: 4px;
                            background-color: {colors['input_bg']};
                            font-size: 11px;
                        }}
                    """)
        else:
            self.edit_content_btn.setText("✏️ Edit Content")
            self.edit_content_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['warning']};
                    color: {text_color};
                    border: none;
                    padding: 12px;
                    font-size: 13px;
                    border-radius: 8px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {colors['warning_hover']};
                }}
                QPushButton:disabled {{
                    background-color: {colors['border']};
                }}
            """)
            # Update field backgrounds for read-only mode
            for platform, fields in self.content_edits.items():
                for field_name, field_edit in fields.items():
                    field_edit.text_edit.setStyleSheet(f"""
                        QTextEdit {{
                            padding: 12px;
                            border: 1px solid {colors['border']};
                            border-radius: 4px;
                            background-color: {colors['surface']};
                            font-size: 11px;
                        }}
                    """)


class LogsTab(QWidget):
    """Tab for viewing application logs from Ollama, Backend, and GUI."""
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.log_files = {
            "Ollama": Path(__file__).parent.parent / "ollama.log",
            "Backend": Path(__file__).parent.parent / "backend.log",
            "GUI": Path(__file__).parent.parent / "gui.log"
        }
        self.log_watchers = {}  # Store file watchers
        self.ollama_host = "http://localhost:11434"
        self.init_ui()
        self.start_log_watching()
    
    def init_ui(self):
        """Initialize the UI."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title = QLabel("Application Logs")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        main_layout.addWidget(title)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Source filter
        filter_layout.addWidget(QLabel("Source:"))
        self.source_filter = QComboBox()
        self.source_filter.addItems(["All", "Ollama", "Backend", "GUI"])
        self.source_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.source_filter)
        
        filter_layout.addSpacing(20)
        
        # Level filter
        filter_layout.addWidget(QLabel("Level:"))
        self.level_filter = QComboBox()
        self.level_filter.addItems(["All", "INFO", "WARNING", "ERROR"])
        self.level_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.level_filter)
        
        filter_layout.addStretch()
        
        # Auto-scroll checkbox
        self.auto_scroll = QCheckBox("Auto-scroll")
        self.auto_scroll.setChecked(True)
        filter_layout.addWidget(self.auto_scroll)
        
        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_logs)
        filter_layout.addWidget(self.clear_btn)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_logs)
        filter_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(filter_layout)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 9))
        colors = theme_manager.get_theme_colors()
        self.log_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors['surface']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        main_layout.addWidget(self.log_display)
        
        # Status bar
        self.status_label = QLabel("Monitoring log files...")
        main_layout.addWidget(self.status_label)
        
        self.setLayout(main_layout)
        
        # Load initial logs
        self.refresh_logs()
    
    def start_log_watching(self):
        """Start watching log files for changes."""
        # For now, we'll use a timer to periodically check for updates
        # In a more sophisticated implementation, we could use QFileSystemWatcher
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.refresh_logs)
        self.log_timer.start(2000)  # Check every 2 seconds
    
    def get_ollama_status(self):
        """Fetch Ollama status from the API."""
        try:
            import requests
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                if models:
                    model_names = [m.get("name") for m in models]
                    return f"Ollama is running. Available models: {', '.join(model_names)}"
                else:
                    return "Ollama is running but no models found"
            else:
                return f"Ollama API returned status: {response.status_code}"
        except Exception as e:
            return f"Failed to connect to Ollama API: {e}"
    
    def refresh_logs(self):
        """Refresh logs from all log files."""
        all_logs = []
        
        for source, log_file in self.log_files.items():
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        logs = f.readlines()
                        for log in logs:
                            all_logs.append((source, log.strip()))
                except Exception as e:
                    all_logs.append((source, f"ERROR: Failed to read log file: {e}"))
            else:
                if source == "Ollama":
                    all_logs.append((source, "INFO: No log file found (Ollama may be running externally)"))
                else:
                    all_logs.append((source, "INFO: No log file found"))
        
        self.all_logs = all_logs
        self.apply_filters()
    
    def apply_filters(self):
        """Apply source and level filters to logs."""
        source_filter = self.source_filter.currentText()
        level_filter = self.level_filter.currentText()
        
        filtered_logs = []
        for source, log in self.all_logs:
            # Apply source filter
            if source_filter != "All" and source != source_filter:
                continue
            
            # Apply level filter
            if level_filter != "All":
                log_upper = log.upper()
                if level_filter == "INFO" and not ("INFO" in log_upper or log_upper.startswith("[") or not any(l in log_upper for l in ["WARNING", "ERROR"])):
                    pass  # Include non-labeled logs as INFO
                elif level_filter == "WARNING" and "WARNING" not in log_upper:
                    continue
                elif level_filter == "ERROR" and "ERROR" not in log_upper:
                    continue
            
            filtered_logs.append((source, log))
        
        # Display filtered logs
        self.display_logs(filtered_logs)
    
    def display_logs(self, logs):
        """Display logs in the text widget."""
        colors = theme_manager.get_theme_colors()
        
        html = f'<body style="background-color: {colors["surface"]}; color: {colors["text_primary"]}; margin: 0; padding: 10px;">'
        for source, log in logs:
            # Color code by source
            if source == "Ollama":
                color = colors['primary']  # Blue
            elif source == "Backend":
                color = colors['success']  # Green
            else:  # GUI
                color = colors['warning']  # Orange
            
            # Color code by level
            log_upper = log.upper()
            if "ERROR" in log_upper:
                text_color = colors['danger']  # Red
            elif "WARNING" in log_upper:
                text_color = colors['warning']  # Orange
            else:
                text_color = colors['text_primary']
            
            # Escape HTML special characters
            log_escaped = log.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            html += f'<span style="color: {color}; font-weight: bold;">[{source}]</span> '
            html += f'<span style="color: {text_color};">{log_escaped}</span><br>'
        html += '</body>'
        
        cursor = self.log_display.textCursor()
        
        # Store current scroll position if auto-scroll is disabled
        if not self.auto_scroll.isChecked():
            scroll_bar = self.log_display.verticalScrollBar()
            scroll_pos = scroll_bar.value()
            was_at_bottom = scroll_bar.value() == scroll_bar.maximum()
        
        self.log_display.setHtml(html)
        
        # Restore scroll position or auto-scroll
        if self.auto_scroll.isChecked():
            cursor.movePosition(cursor.MoveOperation.End)
            self.log_display.setTextCursor(cursor)
        else:
            scroll_bar = self.log_display.verticalScrollBar()
            if was_at_bottom:
                scroll_bar.setValue(scroll_bar.maximum())
            else:
                scroll_bar.setValue(scroll_pos)
        
        # Update status
        self.status_label.setText(f"Showing {len(logs)} log entries")
    
    def clear_logs(self):
        """Clear the log display."""
        self.log_display.clear()
        self.status_label.setText("Logs cleared")
    
    def closeEvent(self, event):
        """Handle close event."""
        if hasattr(self, 'log_timer'):
            self.log_timer.stop()
        event.accept()


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("ArtForge Publisher")
        self.setGeometry(100, 100, 1200, 800)
        
        # Apply theme stylesheet
        self.setStyleSheet(theme_manager.get_stylesheet())
        
        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create header with theme toggle
        colors = theme_manager.get_theme_colors()
        self.header = QWidget()
        self.header.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['surface']};
                border-bottom: 1px solid {colors['border']};
                padding: 8px;
            }}
        """)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        self.title_label = QLabel("ArtForge Publisher")
        self.title_label.setFont(QFont(theme_manager.FONT_FAMILY, 16, QFont.Weight.Bold))
        self.title_label.setStyleSheet(f"color: {colors['text_primary']};")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Theme toggle button
        theme_icon = "🕹️" if theme_manager.current_theme == "retro" else ("🌙" if theme_manager.current_theme == "light" else "☀️")
        self.theme_btn = QPushButton(theme_icon)
        self.theme_btn.setFixedSize(40, 40)
        self.theme_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {colors['primary_hover']};
                color: white;
            }}
        """)
        self.theme_btn.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_btn)
        
        self.header.setLayout(header_layout)
        main_layout.addWidget(self.header)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.upload_tab = ImageUploadTab(self)
        self.analysis_tab = AnalysisTab(self)
        self.content_tab = ContentTab(self)
        self.logs_tab = LogsTab(self)
        
        # Connect image selection signal to clear forms
        self.upload_tab.image_selected.connect(self.on_image_selected)
        
        # Add tabs
        self.tabs.addTab(self.upload_tab, "Upload")
        self.tabs.addTab(self.analysis_tab, "Analysis")
        self.tabs.addTab(self.content_tab, "Content")
        self.tabs.addTab(self.logs_tab, "Logs")
        
        # Connect tab change to update current image
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        main_layout.addWidget(self.tabs)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def toggle_theme(self):
        """Toggle between light, dark, and retro theme."""
        new_theme = theme_manager.toggle_theme()
        theme_icon = "🕹️" if new_theme == "retro" else ("🌙" if new_theme == "light" else "☀️")
        self.theme_btn.setText(theme_icon)
        self.setStyleSheet(theme_manager.get_stylesheet())
        
        # Update all CollapsibleGroupBox widgets
        for widget in self.findChildren(CollapsibleGroupBox):
            widget.apply_theme_style()
        
        # Update header styling
        colors = theme_manager.get_theme_colors()
        self.header.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['surface']};
                border-bottom: 1px solid {colors['border']};
                padding: 8px;
            }}
        """)
        
        # Update title label color
        self.title_label.setStyleSheet(f"color: {colors['text_primary']}; font-weight: bold; font-size: 16px;")
        
        # Update theme button styling
        colors = theme_manager.get_theme_colors()
        self.theme_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {colors['primary_hover']};
                color: white;
            }}
        """)
        
        # Update drop zone styling
        self.upload_tab.reset_drop_zone_style()
        
        # Update status label styling
        colors = theme_manager.get_theme_colors()
        self.upload_tab.status_label.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 11px;")
        
        # Update button styling in all tabs
        self.update_tab_button_styles()
    
    def update_tab_button_styles(self):
        """Update button styles when theme changes."""
        colors = theme_manager.get_theme_colors()
        
        # Determine text color based on theme - use black for retro and light, white for dark
        text_color = "black" if theme_manager.current_theme in ["retro", "light"] else "white"
        
        # Update AnalysisTab buttons
        self.analysis_tab.edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['warning']};
                color: {text_color};
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 8px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors['warning_hover']};
            }}
            QPushButton:disabled {{
                background-color: {colors['border']};
            }}
        """)
        self.analysis_tab.analyze_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['primary']};
                color: {text_color};
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 8px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors['primary_hover']};
            }}
            QPushButton:disabled {{
                background-color: {colors['border']};
            }}
        """)
        self.analysis_tab.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['success']};
                color: {text_color};
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 8px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors['success_hover']};
            }}
            QPushButton:disabled {{
                background-color: {colors['border']};
            }}
        """)
        
        # Update ContentTab buttons
        self.content_tab.edit_content_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['warning']};
                color: {text_color};
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 8px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors['warning_hover']};
            }}
            QPushButton:disabled {{
                background-color: {colors['border']};
            }}
        """)
        self.content_tab.generate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['purple']};
                color: {text_color};
                border: none;
                padding: 14px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {colors['purple_hover']};
            }}
            QPushButton:disabled {{
                background-color: {colors['border']};
            }}
        """)
        
        # Update ImageUploadTab buttons
        self.upload_tab.upload_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['success']};
                color: {text_color};
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 8px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors['success_hover']};
            }}
            QPushButton:disabled {{
                background-color: {colors['border']};
            }}
        """)
        self.upload_tab.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['danger']};
                color: {text_color};
                border: none;
                padding: 12px;
                font-size: 13px;
                border-radius: 8px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors['danger_hover']};
            }}
            QPushButton:disabled {{
                background-color: {colors['border']};
            }}
        """)
        
        # Update content field styling
        for platform, fields in self.content_tab.content_edits.items():
            for field_name, field_edit in fields.items():
                field_edit.text_edit.setStyleSheet(f"""
                    QTextEdit {{
                        padding: 12px;
                        border: 1px solid {colors['input_border']};
                        border-radius: 8px;
                        background-color: {colors['input_bg']};
                        font-size: 13px;
                    }}
                    QTextEdit:focus {{
                        border: 2px solid {colors['input_focus']};
                        background-color: {colors['background']};
                    }}
                """)
        
        # Update image preview styling
        self.analysis_tab.image_preview_label.setStyleSheet(f"""
            QLabel {{
                border: 2px solid {colors['border']};
                border-radius: 8px;
                background-color: {colors['surface']};
            }}
        """)
        self.content_tab.image_preview_label.setStyleSheet(f"""
            QLabel {{
                border: 2px solid {colors['border']};
                border-radius: 8px;
                background-color: {colors['surface']};
            }}
        """)
        
        # Update platform tabs styling
        if theme_manager.current_theme == "retro":
            # Use green for retro mode to match the theme
            selected_color = colors['success']  # Green
            selected_border = colors['success']
        elif theme_manager.current_theme == "dark":
            selected_color = colors['primary']  # Blue
            selected_border = colors['primary']
        else:
            selected_color = colors['primary']  # Blue
            selected_border = colors['primary']
        
        self.content_tab.platform_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {colors['border']};
                background-color: {colors['surface']};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background-color: {colors['surface']};
                color: {colors['text_secondary']};
                padding: 10px 20px;
                border: 1px solid {colors['border']};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {selected_color};
                color: white;
                border: 2px solid {selected_border};
                border-bottom: 2px solid {selected_border};
                font-weight: bold;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {colors['border']};
            }}
        """)
    
    def on_image_selected(self, image_id):
        """Handle image selection - clear forms when new image is selected."""
        # Clear analysis and content forms when a new image is selected
        self.analysis_tab.clear_form()
        self.content_tab.clear_form()
    
    def on_tab_changed(self, index):
        """Handle tab change."""
        # Pass selected image to analysis/content tabs
        if index > 0:  # Not the upload tab
            selected_image_id = self.upload_tab.selected_image_id
            if selected_image_id:
                if index == 1:  # Analysis tab
                    self.analysis_tab.set_image(selected_image_id)
                elif index == 2:  # Content tab
                    self.content_tab.set_image(selected_image_id)
    
    def show_toast(self, message, message_type="success"):
        """Show a toast notification."""
        toast = ToastNotification(message, message_type, self)
        toast.show()
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Clean up workers in all tabs
        self.upload_tab.cleanup_workers()
        self.analysis_tab.cleanup_workers()
        self.content_tab.cleanup_workers()
        event.accept()


def main():
    """Main entry point."""
    try:
        app = QApplication(sys.argv)
        
        # Set application style
        app.setStyle("Fusion")
        
        # Set dark/light theme palette
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(76, 175, 80))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        app.setPalette(palette)
        
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error starting GUI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
