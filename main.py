from duckduckgo_search import DDGS

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit, QWidget, QScrollArea, QLabel
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt

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
        query = self.search_input.text()
        if not query:
            return

        priority_sites = [
            "stackoverflow.com",
            "geeksforgeeks.org",
            "reddit.com/r/programming",
            "reddit.com/r/learnprogramming",
            "reddit.com/r/AskProgramming",
            "tutorialspoint.com",
            "w3schools.com",
            "medium.com/topic/programming",
            "dev.to",
            "github.com",
            "devdocs.io",
            "youtube.com",
            "developer.mozilla.org",
        ]

        site_query = " OR ".join([f"site:{site}" for site in priority_sites])
        prioritized_query = f"{site_query} {query}"

        for i in reversed(range(self.results_layout.count())):
            child = self.results_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        results = []

        with DDGS() as ddgs:
            priority_results = ddgs.text(prioritized_query, max_results=20)

            general_results = ddgs.text(query, max_results=20)

        seen = set()
        for result in priority_results + general_results:
            href = result.get('href')
            if href and href not in seen:
                seen.add(href)
                results.append(result)

        if results:
            for result in results:
                result_label = QLabel()
                result_label.setWordWrap(True)
                result_label.setTextFormat(Qt.TextFormat.RichText)
                result_label.setOpenExternalLinks(True)

                title = result.get('title', 'No title')
                href = result.get('href', '#')
                body = result.get('body', 'No description available')

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
                result_label.setStyleSheet("""
                    QLabel {
                        padding: 10px;
                        border-bottom: 1px solid #444;
                        margin: 0px;
                        background-color: transparent;
                    }
                    QLabel:hover {
                        background-color: rgba(255, 255, 255, 0.05);
                    }
                """)

                self.results_layout.addWidget(result_label)
        else:
            no_results = QLabel("No results found.")
            no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_results.setStyleSheet(
                "color: #999; font-size: 16px; padding: 30px; background-color: transparent;")
            self.results_layout.addWidget(no_results)

        
def main():
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()

if __name__ == '__main__':
    main()
