from duckduckgo_search import DDGS

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit, QWidget, QScrollArea, QLabel
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt

from jsoncomment import JsonComment
import traceback
from urllib.parse import urlparse

def load_sites():
    try:
        with open('sites.jsonc', 'r') as file:
            content = file.read()
            return JsonComment().loads(content)
    except FileNotFoundError:
        print("Warning: sites.jsonc is empty.")
        return []

MAX_RESULTS = 5  # <-- Adjustable

class Style:
    def __init__(self, mode = 0):
        if mode == 0:
            (self.BACKGROUND_COLOR, self.WIDGET_COLOR, self.WIDGET_COLOR_HOVER, self.TEXT_COLOR) = (
                "#212529", "#343A40", "#495057", "#FFFFFF"
            )
        else:
            (self.BACKGROUND_COLOR, self.WIDGET_COLOR, self.WIDGET_COLOR_HOVER, self.TEXT_COLOR) = (
                "#dedad6", "#cbc5bf", "#b6afa8", "#000000"
            )
    def style_sheet(self):
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

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.prioritized_sites = load_sites()

        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle("Programmer Search")
        self.setStyleSheet(Style().style_sheet())
        self.setFont(QFont("Arial", 12))
        self.setWindowIcon(QIcon("icon.png"))
        self.setup_ui()

    def setup_ui(self):
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

    def search(self):
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

    def is_prioritized(self, url):
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


    def display_results(self, results):
        for result in results:
            href = result.get('href', '')
            title = result.get('title', 'No title')
            body = result.get('body', 'No description available')

            is_priority = self.is_prioritized(href)

            result_label = QLabel()
            result_label.setWordWrap(True)
            result_label.setTextFormat(Qt.TextFormat.RichText)
            result_label.setOpenExternalLinks(True)

            priority_star = '<span style="color: #28a745; font-weight: bold;"></span>' if is_priority else ''

            html_content = f"""
            <div style="margin: 0; padding: 0;">
                <h3 style="margin: 0 0 5px 0; padding: 0;">
                    {priority_star}<a href="{href}" style="color: #0066cc; text-decoration: none;">{title}</a>
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

def main():
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()

if __name__ == '__main__':
    main()
