"""Main PyQt6 GUI application for ArtForge Publisher."""

import sys
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox,
    QTextEdit, QFormLayout, QLineEdit, QFileDialog, QSplitter,
    QProgressBar, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QImage, QFont, QPalette, QColor, QGuiApplication


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
        self.counter_label.setStyleSheet("color: #666; font-size: 10px;")
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.counter_label)
        
        self.setLayout(layout)
    
    def update_counter(self):
        """Update the character counter."""
        text = self.text_edit.toPlainText()
        count = len(text)
        
        if self.max_chars:
            remaining = self.max_chars - count
            if remaining < 0:
                self.counter_label.setText(f"{count}/{self.max_chars} characters ({abs(remaining)} over limit!)")
                self.counter_label.setStyleSheet("color: #f44336; font-size: 10px; font-weight: bold;")
            elif remaining < 20:
                self.counter_label.setText(f"{count}/{self.max_chars} characters ({remaining} remaining)")
                self.counter_label.setStyleSheet("color: #ff9800; font-size: 10px;")
            else:
                self.counter_label.setText(f"{count}/{self.max_chars} characters")
                self.counter_label.setStyleSheet("color: #666; font-size: 10px;")
        else:
            self.counter_label.setText(f"{count} characters")
    
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
        self.counter_label.setStyleSheet("color: #666; font-size: 10px;")
        
        # Copy button
        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 4px 12px;
                font-size: 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
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
        
        if self.max_chars:
            remaining = self.max_chars - count
            if remaining < 0:
                self.counter_label.setText(f"{count}/{self.max_chars} characters ({abs(remaining)} over limit!)")
                self.counter_label.setStyleSheet("color: #f44336; font-size: 10px; font-weight: bold;")
            elif remaining < 20:
                self.counter_label.setText(f"{count}/{self.max_chars} characters ({remaining} remaining)")
                self.counter_label.setStyleSheet("color: #ff9800; font-size: 10px;")
            else:
                self.counter_label.setText(f"{count}/{self.max_chars} characters")
                self.counter_label.setStyleSheet("color: #666; font-size: 10px;")
        else:
            self.counter_label.setText(f"{count} characters")
    
    def copy_to_clipboard(self):
        """Copy text to clipboard."""
        text = self.text_edit.toPlainText()
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        # Visual feedback
        self.copy_btn.setText("✓ Copied!")
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 4px 12px;
                font-size: 10px;
                border-radius: 3px;
            }
        """)
        # Reset button after 2 seconds
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2000, self.reset_copy_button)
    
    def reset_copy_button(self):
        """Reset copy button to original state."""
        self.copy_btn.setText("📋 Copy")
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 4px 12px;
                font-size: 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
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
        self.setAcceptDrops(True)  # Enable drag-and-drop
        self.init_ui()
        self.load_images()
    
    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.accept()
            self.drop_zone.setStyleSheet("""
                QFrame {
                    border: 3px dashed #4CAF50;
                    border-radius: 10px;
                    background-color: #e8f5e9;
                }
                QLabel {
                    color: #2e7d32;
                    font-size: 14px;
                    font-weight: bold;
                }
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
        self.drop_zone.setStyleSheet("""
            QFrame {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
            }
            QLabel {
                color: #666;
                font-size: 14px;
            }
        """)
    
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Image Management")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Status and progress
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(20)
        layout.addWidget(self.progress_bar)
        
        # Drag-and-drop zone
        self.drop_zone = QFrame()
        self.drop_zone.setStyleSheet("""
            QFrame {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
            }
            QLabel {
                color: #666;
                font-size: 14px;
            }
        """)
        drop_zone_layout = QVBoxLayout()
        drop_zone_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_zone_label = QLabel("📁 Drag & Drop Images Here\nor click Upload below")
        drop_zone_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_zone_layout.addWidget(drop_zone_label)
        self.drop_zone.setLayout(drop_zone_layout)
        self.drop_zone.setMinimumHeight(100)
        layout.addWidget(self.drop_zone)
        
        # Upload button
        self.upload_btn = QPushButton("📤 Upload Image")
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.upload_btn.clicked.connect(self.upload_image)
        layout.addWidget(self.upload_btn)
        
        # Image list
        list_group = QGroupBox("Uploaded Images")
        list_layout = QVBoxLayout()
        self.image_list = QListWidget()
        self.image_list.itemClicked.connect(self.on_image_selected)
        self.image_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
        """)
        list_layout.addWidget(self.image_list)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        # Delete button
        self.delete_btn = QPushButton("🗑️ Delete Selected Image")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_image)
        self.delete_btn.setEnabled(False)
        layout.addWidget(self.delete_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
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
        else:
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(1)
            self.status_label.setText("Ready")
    
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
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Image Analysis")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Instructions
        self.instruction_label = QLabel("Select an image from the Upload tab to view/edit analysis")
        self.instruction_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.instruction_label)
        
        # Status and progress
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(20)
        layout.addWidget(self.progress_bar)
        
        # Analysis form
        form_group = QGroupBox("Analysis Details")
        form_layout = QFormLayout()
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Image title")
        self.subject_edit = TextEditWithCounter(placeholder="Subject description")
        self.subject_edit.setMaximumHeight(100)
        self.character_edit = TextEditWithCounter(placeholder="Character description")
        self.character_edit.setMaximumHeight(100)
        self.environment_edit = TextEditWithCounter(placeholder="Environment description")
        self.environment_edit.setMaximumHeight(100)
        self.art_style_edit = QLineEdit()
        self.art_style_edit.setPlaceholderText("Art style")
        self.mood_edit = QLineEdit()
        self.mood_edit.setPlaceholderText("Mood")
        self.genre_edit = QLineEdit()
        self.genre_edit.setPlaceholderText("Genre")
        self.technical_edit = TextEditWithCounter(placeholder="Technical details")
        self.technical_edit.setMaximumHeight(100)
        
        # Set all fields to read-only by default
        self.title_edit.setReadOnly(True)
        self.subject_edit.setReadOnly(True)
        self.character_edit.setReadOnly(True)
        self.environment_edit.setReadOnly(True)
        self.art_style_edit.setReadOnly(True)
        self.mood_edit.setReadOnly(True)
        self.genre_edit.setReadOnly(True)
        self.technical_edit.setReadOnly(True)
        
        # Apply styling to form widgets
        for widget in [self.title_edit, self.art_style_edit, self.mood_edit, self.genre_edit]:
            widget.setStyleSheet("""
                QLineEdit {
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: #f5f5f5;
                }
                QLineEdit[readOnly="true"] {
                    background-color: #e8e8e8;
                    color: #666;
                }
            """)
        
        for widget in [self.subject_edit, self.character_edit, self.environment_edit, self.technical_edit]:
            widget.text_edit.setStyleSheet("""
                QTextEdit {
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: #f5f5f5;
                }
            """)
        
        form_layout.addRow("Title:", self.title_edit)
        form_layout.addRow("Subject:", self.subject_edit)
        form_layout.addRow("Character:", self.character_edit)
        form_layout.addRow("Environment:", self.environment_edit)
        form_layout.addRow("Art Style:", self.art_style_edit)
        form_layout.addRow("Mood:", self.mood_edit)
        form_layout.addRow("Genre:", self.genre_edit)
        form_layout.addRow("Technical:", self.technical_edit)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 10px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        self.edit_btn.setEnabled(False)
        
        self.analyze_btn = QPushButton("🔍 Analyze Image")
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.analyze_btn.clicked.connect(self.analyze_image)
        self.save_btn = QPushButton("💾 Save Analysis")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.save_btn.clicked.connect(self.save_analysis)
        self.save_btn.setEnabled(False)
        
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.analyze_btn)
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def set_image(self, image_id):
        """Set the current image."""
        self.current_image_id = image_id
        self.instruction_label.setText(f"Editing analysis for image: {image_id[:8]}...")
        self.edit_btn.setEnabled(True)
        self.load_analysis()
        self.save_btn.setEnabled(True)
    
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
        else:
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(1)
            self.status_label.setText("Ready")
    
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
        if editable:
            self.edit_btn.setText("✖️ Cancel Edit")
            self.edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #9E9E9E;
                    color: white;
                    border: none;
                    padding: 10px;
                    font-size: 12px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #757575;
                }
            """)
            # Update field backgrounds for edit mode
            for widget in [self.title_edit, self.art_style_edit, self.mood_edit, self.genre_edit]:
                widget.setStyleSheet("""
                    QLineEdit {
                        padding: 8px;
                        border: 1px solid #2196F3;
                        border-radius: 4px;
                        background-color: white;
                    }
                """)
            for widget in [self.subject_edit, self.character_edit, self.environment_edit, self.technical_edit]:
                widget.text_edit.setStyleSheet("""
                    QTextEdit {
                        padding: 8px;
                        border: 1px solid #2196F3;
                        border-radius: 4px;
                        background-color: white;
                    }
                """)
        else:
            self.edit_btn.setText("✏️ Edit")
            self.edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    padding: 10px;
                    font-size: 12px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #e68900;
                }
            """)
            # Update field backgrounds for read-only mode
            for widget in [self.title_edit, self.art_style_edit, self.mood_edit, self.genre_edit]:
                widget.setStyleSheet("""
                    QLineEdit {
                        padding: 8px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        background-color: #f5f5f5;
                    }
                    QLineEdit[readOnly="true"] {
                        background-color: #e8e8e8;
                        color: #666;
                    }
                """)
            for widget in [self.subject_edit, self.character_edit, self.environment_edit, self.technical_edit]:
                widget.text_edit.setStyleSheet("""
                    QTextEdit {
                        padding: 8px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        background-color: #f5f5f5;
                    }
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
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Content Generation")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Instructions
        self.instruction_label = QLabel("Select an image from the Upload tab to generate content")
        self.instruction_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.instruction_label)
        
        # Status and progress
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(20)
        layout.addWidget(self.progress_bar)
        
        # Platform tabs
        self.platform_tabs = QTabWidget()
        self.platform_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 8px 16px;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
        """)
        
        # Create tabs for each platform with specific fields
        self.content_edits = {}  # Will store dicts of fields per platform
        
        # X/Twitter tab - 3 fields
        twitter_tab = QWidget()
        twitter_layout = QVBoxLayout()
        twitter_layout.addWidget(QLabel("<b>Short Version</b>"))
        twitter_short = TextEditWithCounterAndCopy(max_chars=280, placeholder="Short tweet (under 280 chars)")
        twitter_short.setReadOnly(True)
        twitter_short.setMaximumHeight(100)
        twitter_layout.addWidget(twitter_short)
        
        twitter_layout.addWidget(QLabel("<b>Medium Version</b>"))
        twitter_medium = TextEditWithCounterAndCopy(max_chars=280, placeholder="Medium-length tweet")
        twitter_medium.setReadOnly(True)
        twitter_medium.setMaximumHeight(120)
        twitter_layout.addWidget(twitter_medium)
        
        twitter_layout.addWidget(QLabel("<b>Engagement Version</b>"))
        twitter_engagement = TextEditWithCounterAndCopy(max_chars=280, placeholder="Engagement-focused tweet with hashtags")
        twitter_engagement.setReadOnly(True)
        twitter_layout.addWidget(twitter_engagement)
        
        twitter_tab.setLayout(twitter_layout)
        self.platform_tabs.addTab(twitter_tab, "X/Twitter")
        self.content_edits["X/Twitter"] = {
            "short": twitter_short,
            "medium": twitter_medium,
            "engagement": twitter_engagement
        }
        
        # Instagram tab - 2 fields
        instagram_tab = QWidget()
        instagram_layout = QVBoxLayout()
        instagram_layout.addWidget(QLabel("<b>Caption</b>"))
        instagram_caption = TextEditWithCounterAndCopy(placeholder="Instagram caption")
        instagram_caption.setReadOnly(True)
        instagram_layout.addWidget(instagram_caption)
        
        instagram_layout.addWidget(QLabel("<b>Hashtags</b>"))
        instagram_hashtags = TextEditWithCounterAndCopy(placeholder="Hashtags (comma-separated)")
        instagram_hashtags.setReadOnly(True)
        instagram_hashtags.setMaximumHeight(100)
        instagram_layout.addWidget(instagram_hashtags)
        
        instagram_tab.setLayout(instagram_layout)
        self.platform_tabs.addTab(instagram_tab, "Instagram")
        self.content_edits["Instagram"] = {
            "caption": instagram_caption,
            "hashtags": instagram_hashtags
        }
        
        # Reddit tab - 2 fields
        reddit_tab = QWidget()
        reddit_layout = QVBoxLayout()
        reddit_layout.addWidget(QLabel("<b>Title</b>"))
        reddit_title = TextEditWithCounterAndCopy(max_chars=300, placeholder="Post title")
        reddit_title.setReadOnly(True)
        reddit_title.setMaximumHeight(80)
        reddit_layout.addWidget(reddit_title)
        
        reddit_layout.addWidget(QLabel("<b>Body</b>"))
        reddit_body = TextEditWithCounterAndCopy(placeholder="Post body content")
        reddit_body.setReadOnly(True)
        reddit_layout.addWidget(reddit_body)
        
        reddit_tab.setLayout(reddit_layout)
        self.platform_tabs.addTab(reddit_tab, "Reddit")
        self.content_edits["Reddit"] = {
            "title": reddit_title,
            "body": reddit_body
        }
        
        # ArtStation tab - 3 fields
        artstation_tab = QWidget()
        artstation_layout = QVBoxLayout()
        artstation_layout.addWidget(QLabel("<b>Title</b>"))
        artstation_title = TextEditWithCounterAndCopy(placeholder="Artwork title")
        artstation_title.setReadOnly(True)
        artstation_title.setMaximumHeight(80)
        artstation_layout.addWidget(artstation_title)
        
        artstation_layout.addWidget(QLabel("<b>Description</b>"))
        artstation_description = TextEditWithCounterAndCopy(placeholder="Artwork description")
        artstation_description.setReadOnly(True)
        artstation_layout.addWidget(artstation_description)
        
        artstation_layout.addWidget(QLabel("<b>Tags</b>"))
        artstation_tags = TextEditWithCounterAndCopy(placeholder="SEO tags")
        artstation_tags.setReadOnly(True)
        artstation_tags.setMaximumHeight(100)
        artstation_layout.addWidget(artstation_tags)
        
        artstation_tab.setLayout(artstation_layout)
        self.platform_tabs.addTab(artstation_tab, "ArtStation")
        self.content_edits["ArtStation"] = {
            "title": artstation_title,
            "description": artstation_description,
            "tags": artstation_tags
        }
        
        # DeviantArt tab - 3 fields
        deviantart_tab = QWidget()
        deviantart_layout = QVBoxLayout()
        deviantart_layout.addWidget(QLabel("<b>Title</b>"))
        deviantart_title = TextEditWithCounterAndCopy(placeholder="Artwork title")
        deviantart_title.setReadOnly(True)
        deviantart_title.setMaximumHeight(80)
        deviantart_layout.addWidget(deviantart_title)
        
        deviantart_layout.addWidget(QLabel("<b>Description</b>"))
        deviantart_description = TextEditWithCounterAndCopy(placeholder="Artwork description")
        deviantart_description.setReadOnly(True)
        deviantart_layout.addWidget(deviantart_description)
        
        deviantart_layout.addWidget(QLabel("<b>Tags</b>"))
        deviantart_tags = TextEditWithCounterAndCopy(placeholder="SEO tags")
        deviantart_tags.setReadOnly(True)
        deviantart_tags.setMaximumHeight(100)
        deviantart_layout.addWidget(deviantart_tags)
        
        deviantart_tab.setLayout(deviantart_layout)
        self.platform_tabs.addTab(deviantart_tab, "DeviantArt")
        self.content_edits["DeviantArt"] = {
            "title": deviantart_title,
            "description": deviantart_description,
            "tags": deviantart_tags
        }
        
        # Apply consistent styling to all fields
        for platform, fields in self.content_edits.items():
            for field_name, field_edit in fields.items():
                field_edit.text_edit.setStyleSheet("""
                    QTextEdit {
                        padding: 12px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        background-color: #f5f5f5;
                        font-size: 11px;
                    }
                """)
        
        layout.addWidget(self.platform_tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.edit_content_btn = QPushButton("✏️ Edit Content")
        self.edit_content_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 10px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.edit_content_btn.clicked.connect(self.toggle_content_edit_mode)
        self.edit_content_btn.setEnabled(False)
        
        self.generate_btn = QPushButton("✨ Generate Content")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 12px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7b1fa2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_content)
        self.generate_btn.setEnabled(False)
        
        button_layout.addWidget(self.edit_content_btn)
        button_layout.addWidget(self.generate_btn)
        layout.addLayout(button_layout)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def set_image(self, image_id):
        """Set the current image."""
        self.current_image_id = image_id
        self.instruction_label.setText(f"Generating content for image: {image_id[:8]}...")
        self.edit_content_btn.setEnabled(True)
        self.load_content()
        self.generate_btn.setEnabled(True)
    
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
        else:
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(1)
            self.status_label.setText("Ready")
    
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
        if editable:
            self.edit_content_btn.setText("✖️ Cancel Edit")
            self.edit_content_btn.setStyleSheet("""
                QPushButton {
                    background-color: #9E9E9E;
                    color: white;
                    border: none;
                    padding: 10px;
                    font-size: 12px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #757575;
                }
            """)
            # Update field backgrounds for edit mode
            for platform, fields in self.content_edits.items():
                for field_name, field_edit in fields.items():
                    field_edit.text_edit.setStyleSheet("""
                        QTextEdit {
                            padding: 12px;
                            border: 1px solid #9C27B0;
                            border-radius: 4px;
                            background-color: white;
                            font-size: 11px;
                        }
                    """)
        else:
            self.edit_content_btn.setText("✏️ Edit Content")
            self.edit_content_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    padding: 10px;
                    font-size: 12px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #e68900;
                }
            """)
            # Update field backgrounds for read-only mode
            for platform, fields in self.content_edits.items():
                for field_name, field_edit in fields.items():
                    field_edit.text_edit.setStyleSheet("""
                        QTextEdit {
                            padding: 12px;
                            border: 1px solid #ddd;
                            border-radius: 4px;
                            background-color: #f5f5f5;
                            font-size: 11px;
                        }
                    """)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("ArtForge Publisher")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.upload_tab = ImageUploadTab(self)
        self.analysis_tab = AnalysisTab(self)
        self.content_tab = ContentTab(self)
        
        # Connect image selection signal to clear forms
        self.upload_tab.image_selected.connect(self.on_image_selected)
        
        # Add tabs
        self.tabs.addTab(self.upload_tab, "Upload")
        self.tabs.addTab(self.analysis_tab, "Analysis")
        self.tabs.addTab(self.content_tab, "Content")
        
        # Connect tab change to update current image
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        self.setCentralWidget(self.tabs)
    
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


if __name__ == "__main__":
    main()
