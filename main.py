from duckduckgo_search import DDGS

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit, QWidget, QScrollArea, QLabel
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt, Signal
from PySide6.QtWebEngineWidgets import QWebEngineView

from jsoncomment import JsonComment

import traceback
import os
import sys
from urllib.parse import urlparse

def load_sites() -> list[str]:
    """
    Load prioritized sites from a JSONC file.
    Returns:
        list: A list of prioritized sites.
    """
    try:
        with open('sites.jsonc', 'r') as file:
            content = file.read()
            return JsonComment().loads(content)
    except FileNotFoundError:
        print("Warning: sites.jsonc is empty.")
        return []

def load_settings() -> int:
    """
    Load settings from a JSONC file.
    Returns:
        int: The maximum number of results to display.
    """
    try:
        with open('settings.jsonc', 'r') as file:
            content = file.read()
            settings = JsonComment().loads(content)
            return settings.get('max_results', 5)
    except FileNotFoundError:
        print("Warning: settings.jsonc is empty.")
        return 5

MAX_RESULTS = load_settings()

class Style:
    """
    A class to define the style for the application.
    Attributes:
        BACKGROUND_COLOR (str): Background color of the main window.
        WIDGET_COLOR (str): Color of the widgets.
        WIDGET_COLOR_HOVER (str): Color of the widgets on hover.
        TEXT_COLOR (str): Color of the text.
    """
    def __init__(self, mode = 0) -> None:
        """
        Initializes the style with colors based on the mode.
        Args:
            mode (int): 0 for dark mode, 1 for light mode. Default is 0.
        """
        if mode == 0:
            (self.BACKGROUND_COLOR, self.WIDGET_COLOR, self.WIDGET_COLOR_HOVER, self.TEXT_COLOR) = (
                "#212529", "#343A40", "#495057", "#FFFFFF"
            )
        else:
            (self.BACKGROUND_COLOR, self.WIDGET_COLOR, self.WIDGET_COLOR_HOVER, self.TEXT_COLOR) = (
                "#dedad6", "#cbc5bf", "#b6afa8", "#000000"
            )
    def style_sheet(self) -> str:
        """
        Returns the style sheet for the application.
        Returns:
            str: The style sheet as a string.
        """
        return f"""
        QMainWindow {{
            background-color: {self.BACKGROUND_COLOR};
        }}
        QWidget {{
            background-color: {self.WIDGET_COLOR};
            color: {self.TEXT_COLOR};
            border-radius: 5px;
        }}
        QLineEdit {{
            background-color: {self.WIDGET_COLOR};
            color: {self.TEXT_COLOR};
            border: 1px solid {self.WIDGET_COLOR_HOVER};
            padding: 5px;
            border-radius: 5px;
        }}
        QLineEdit:hover {{
            background-color: {self.WIDGET_COLOR_HOVER};
        }}
        QScrollArea {{
            background-color: {self.WIDGET_COLOR};
            border-radius: 5px;
        }}
        QLabel {{
            color: {self.TEXT_COLOR};
            font-size: 14px;
        }}
        QLabel:hover {{
            background-color: rgba(255, 255, 255, 0.05);
        }}
        QScrollBar:vertical {{
            border: 1px solid {self.WIDGET_COLOR_HOVER};
            background: {self.WIDGET_COLOR};
            width: 12px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical {{
            background: {self.WIDGET_COLOR_HOVER};
            min-height: 20px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: rgba(255, 255, 255, 0.2);
            border-radius: 5px;
        }}
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar::add-line:vertical {{
            height: 0px;
        }}
        """


class ClickableLabel(QLabel):
    """
    A QLabel that emits a signal when clicked.
    Inherits from QLabel.
    Attributes:
        clicked (Signal): A signal emitted when the label is clicked.
    Methods:
        mousePressEvent(event): Overrides the mouse press event to emit the clicked signal.
    """
    clicked = Signal()

    def mousePressEvent(self, event) -> None:
        """
        Overrides the mouse press event to emit the clicked signal.
        Args:
            event (QMouseEvent): The mouse event that triggered the press.
        Emits the clicked signal when the label is pressed.
        """
        self.clicked.emit()
        super().mousePressEvent(event)

class BrowserWindow(QMainWindow):
    """
    Browser window class for displaying web content.
    Inherits from QMainWindow.
    Attributes:
        web_view (QWebEngineView): The web view for displaying web content.
    Methods:
        __init__(url, parent): Initializes the browser window with a given URL.
    Args:
        url (str): The URL to load in the browser window.
        parent (QMainWindow, optional): The parent window for this browser window.
    Initializes the browser window with a specified URL and sets up the web view.
    Sets the window title, geometry, and central widget to the web view.
    Inherits from QMainWindow to provide a standard window interface.
    """
    def __init__(self, url: str, parent=None) -> None:
        from PySide6.QtCore import QUrl
        super().__init__(parent)
        self.setWindowTitle("Browser")
        self.setGeometry(200, 200, 1000, 700)
        
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl(url))
        self.setCentralWidget(self.web_view)

class Window(QMainWindow):
    """
    A class for the main application window.
    Inherits from QMainWindow.
    Attributes:
        prioritized_sites (list): A list of prioritized sites loaded from a JSONC file.
    """
    def __init__(self) -> None:
        """
        Inherits from QMainWindow and initializes the main window.
        Loads prioritized sites from a JSONC file and sets up the UI.
        """
        super().__init__()
        self.prioritized_sites = load_sites()
        self.browser_windows = []

        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle("Programmer Search")
        self.setStyleSheet(Style().style_sheet())
        self.setFont(QFont("Arial", 12))
        self.setWindowIcon(QIcon("icon.png"))
        self.setup_ui()

    def setup_ui(self) -> None:
        """
        Sets up the user interface for the main window.
        Creates a vertical layout with a search input field and a scroll area for displaying results.
        """
        layout = QVBoxLayout()
        search_layout = QHBoxLayout()
        search_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Enter your search query...")
        self.search_input.returnPressed.connect(self.search)

        search_layout.addWidget(self.search_input)

        layout.addLayout(search_layout)

        self.results_scroll = QScrollArea()
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_layout.setSpacing(0)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_scroll.setWidget(self.results_widget)
        self.results_scroll.setWidgetResizable(True)

        layout.addWidget(self.results_scroll)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

    def search(self) -> None:
        """
        Performs a search using the DuckDuckGo Search API.
        Clears previous results and displays new results based on the search query.        
        """
        query = self.search_input.text().strip()
        if not query:
            return

        for i in reversed(range(self.results_layout.count())):
            child = self.results_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        results = []
        with DDGS() as ddgs:
            try:
                results = ddgs.text(query, max_results=MAX_RESULTS)
            except Exception as e:
                print(f"Error searching: {e}")
                traceback.print_exc()

        self.display_results(results)

    def is_prioritized(self, url) -> bool:
        """
        Checks if the given URL matches any of the prioritized sites.
        Args:
            url (str): The URL to check.
        Returns:
            bool: True if the URL matches a prioritized site, False otherwise.
        """
        parsed_url = urlparse(url)
        result_domain = parsed_url.netloc.lower().lstrip('www.')

        for site in self.prioritized_sites:
            site_parsed = urlparse(site)
            site_domain = site_parsed.netloc.lower().lstrip('www.')

            if not site_domain:
                site_domain = site.replace('http://', '').replace('https://', '').split('/')[0].lower().lstrip('www.')

            if result_domain.endswith(site_domain):
                return True

        return False

    def open_browser_window(self, url: str) -> None:
        """
        Opens a new browser window with the specified URL.
        Args:
            url (str): The URL to open in the browser window.
        """
        browser_window = BrowserWindow(url, self)
        browser_window.show()
        self.browser_windows.append(browser_window)

    def display_results(self, results) -> None:
        """
        Displays the search results in the results layout.
        Args:
            results (list): A list of search results to display.
        Iterates through the results and creates clickable labels for each result.
        Each label contains the title, URL, and description of the result.
        Each label is clickable and opens the corresponding URL in a new browser window.
        Highlights prioritized results with special styling.
        If no results are found, it displays a message indicating that no results were found.
        """
        for result in results:
            href = result.get('href', '')
            title = result.get('title', 'No title')
            body = result.get('body', 'No description available')

            is_priority = self.is_prioritized(href)

            result_label = ClickableLabel()
            result_label.setWordWrap(True)
            result_label.setTextFormat(Qt.TextFormat.RichText)
            result_label.setOpenExternalLinks(False)
            result_label.clicked.connect(lambda url=href: self.open_browser_window(url))

            html_content = f"""
            <div style="margin: 0; padding: 0;">
                <h3 style="margin: 0 0 5px 0; padding: 0;">
                    <a href="{href}" style="color: #0066cc; text-decoration: none;">{title}</a>
                </h3>
                <p style="color: #666; font-size: 11px; margin: 0 0 3px 0; padding: 0;">{href}</p>
                <p style="margin: 0; padding: 0; font-size: 13px;">{body}</p>
            </div>
            """

            result_label.setText(html_content)

            if is_priority:
                result_label.setStyleSheet("""
                    QLabel {
                        padding: 10px;
                        border-bottom: 1px solid #444;
                        border-left: 3px solid #28a745;
                        background-color: rgba(40, 167, 69, 0.1);
                    }
                    QLabel:hover {
                        background-color: rgba(40, 167, 69, 0.2);
                    }
                """)
            else:
                result_label.setStyleSheet("""
                    QLabel {
                        padding: 10px;
                        border-bottom: 1px solid #444;
                    }
                    QLabel:hover {
                        background-color: rgba(255, 255, 255, 0.05);
                    }
                """)

            self.results_layout.addWidget(result_label)

if __name__ == '__main__':
    """
    Main entry point for the application.
    Initializes the QApplication, creates the main window, and starts the event loop.
    Sets environment variables for Qt and GPU settings to ensure compatibility with NVIDIA drivers.
    Ensures that the application runs with the correct display server and GPU settings.
    """
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    
    os.environ["__GLX_VENDOR_LIBRARY_NAME"] = "nvidia"
    os.environ["GBM_BACKEND"] = "nvidia-drm"
    
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--ignore-gpu-blacklist --disable-gpu-sandbox --use-gl=angle --enable-gpu-rasterization"
    
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()
