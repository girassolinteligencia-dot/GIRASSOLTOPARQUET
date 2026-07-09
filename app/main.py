import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QPixmap, QPainter, QLinearGradient, QColor, QFont
from PySide6.QtCore import Qt, QRectF

# Add project root to path to ensure correct imports when running locally
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ui.main_window import MainWindow

def generate_default_icon():
    """
    Generates a high-quality icon.ico and icon.png programmatically
    using PySide6 QPainter, ensuring the application has beautiful assets offline.
    """
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    ico_path = os.path.join(assets_dir, "icon.ico")
    png_path = os.path.join(assets_dir, "icon.png")
    
    if os.path.exists(ico_path) and os.path.exists(png_path):
        return ico_path, png_path
        
    # Ensure QApplication is initialized for QPixmap/QPainter to work
    created_app = False
    app = QApplication.instance()
    if not app:
        app = QApplication([])
        created_app = True
        
    # Draw 256x256 premium logo with rounded corners & brand gradient
    pixmap = QPixmap(256, 256)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Brand orange gradient
    gradient = QLinearGradient(0, 0, 256, 256)
    gradient.setColorAt(0.0, QColor("#F36616"))  # GIRASSOLtoPARQUET orange
    gradient.setColorAt(1.0, QColor("#EA580C"))  # Darker orange
    
    painter.setBrush(gradient)
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(QRectF(16, 16, 224, 224), 48, 48)
    
    # Draw stylized 'P' and 'Q' (Parquet Converter)
    font = QFont("Georgia", 80)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor("#FFFFFF"))
    
    # Position letters centrally
    painter.drawText(QRectF(16, 50, 224, 150), Qt.AlignCenter, "PQ")
    painter.end()
    
    try:
        pixmap.save(png_path, "PNG")
        pixmap.save(ico_path, "ICO")
    except Exception as e:
        print(f"Erro ao salvar ícones programáticos: {e}")
        
    return ico_path, png_path

def main():
    app = QApplication(sys.argv)
    
    # 1. Generate assets programmatically if not present
    ico_path, _ = generate_default_icon()
    
    # 2. Set App Icon
    if os.path.exists(ico_path):
        app.setWindowIcon(QIcon(ico_path))
        
    # 3. Create and show MainWindow
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
