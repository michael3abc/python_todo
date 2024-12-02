# 先在terminal打 pip install PySide6
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QTableWidget, 
                             QTableWidgetItem, QVBoxLayout, QHBoxLayout, QSizePolicy, 
                             QHeaderView, QPushButton, QLabel, QTimeEdit, QSpinBox,
                             QLineEdit, QFrame, QMenu)
from PySide6.QtCore import Qt, QTime, QMimeData
from PySide6.QtGui import QDrag
from datetime import datetime, timedelta

class DraggableButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.course_name = text
        self.setMouseTracking(True)
        self.setAcceptDrops(False)
        self.setMinimumHeight(30)
        self.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.course_name)
            drag.setMimeData(mime_data)
            drag.exec_(Qt.CopyAction | Qt.MoveAction)

class CourseButtonWidget(QWidget):
    def __init__(self, course_name, delete_callback, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 創建課程按鈕
        self.course_button = DraggableButton(course_name)
        
        # 創建刪除按鈕
        delete_button = QPushButton("×")
        delete_button.setFixedSize(20, 20)
        delete_button.clicked.connect(lambda: delete_callback(self))
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        """)
        
        layout.addWidget(self.course_button)
        layout.addWidget(delete_button)

class ScheduleWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("課表")
        self.resize(800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)
        
        # 左側容器
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 左側表格
        self.schedule_table = QTableWidget()
        self.schedule_table.setAcceptDrops(True)
        self.schedule_table.dragEnterEvent = self.table_drag_enter
        self.schedule_table.dragMoveEvent = self.table_drag_move
        self.schedule_table.dropEvent = self.table_drop
        self.schedule_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 啟用右鍵選單
        self.schedule_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.schedule_table.customContextMenuRequested.connect(self.show_context_menu)
        
        left_layout.addWidget(self.schedule_table)
        main_layout.addWidget(left_container)
        
        # 右側容器
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 50, 0)
        right_layout.setSpacing(0)
        
        # 時間設定區域
        time_settings = QWidget()
        time_layout = QVBoxLayout(time_settings)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(15)
        
        # 開始時間設定
        start_time_container = QWidget()
        start_time_layout = QHBoxLayout(start_time_container)
        start_time_layout.setContentsMargins(0, 0, 0, 0)
        start_time_label = QLabel("開始時間:")
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setTime(QTime(8, 0))
        start_time_layout.addWidget(start_time_label)
        start_time_layout.addWidget(self.start_time_edit)
        
        # 結束時間設定
        end_time_container = QWidget()
        end_time_layout = QHBoxLayout(end_time_container)
        end_time_layout.setContentsMargins(0, 0, 0, 0)
        end_time_label = QLabel("結束時間:")
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setTime(QTime(17, 0))
        end_time_layout.addWidget(end_time_label)
        end_time_layout.addWidget(self.end_time_edit)
        
        # 時間間隔設定
        interval_container = QWidget()
        interval_layout = QHBoxLayout(interval_container)
        interval_layout.setContentsMargins(0, 0, 0, 0)
        interval_label = QLabel("時間間隔(分鐘):")
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(5, 60)
        self.interval_spinbox.setValue(30)
        self.interval_spinbox.setSingleStep(5)
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spinbox)
        
        # 更新按鈕
        update_button = QPushButton("更新課表")
        update_button.clicked.connect(self.update_schedule)
        
        # 將時間設定元件加入布局
        time_layout.addWidget(start_time_container)
        time_layout.addWidget(end_time_container)
        time_layout.addWidget(interval_container)
        time_layout.addWidget(update_button)
        
        right_layout.addWidget(time_settings)
        
        # 添加間距來上下移動
        right_layout.addSpacing(30)
        
        # 分隔線
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setMaximumHeight(5)
        right_layout.addWidget(separator)
        
        # 課程設定區域
        course_settings = QWidget()
        course_layout = QVBoxLayout(course_settings)
        course_layout.setContentsMargins(0, 0, 0, 0)
        course_layout.setSpacing(5)

        # 課程輸入
        course_input_container = QWidget()
        course_input_layout = QHBoxLayout(course_input_container)
        course_input_layout.setContentsMargins(0, 0, 0, 0)

        self.course_input = QLineEdit()
        self.course_input.setPlaceholderText("輸入課程名稱")
        add_course_button = QPushButton("添加課程")
        add_course_button.clicked.connect(self.add_course)

        course_input_layout.addWidget(self.course_input)
        course_input_layout.addWidget(add_course_button)

        # 課程按鈕區域
        self.course_buttons_container = QWidget()
        self.course_buttons_layout = QVBoxLayout(self.course_buttons_container)
        self.course_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.course_buttons_layout.addStretch()

        # 將課程設定元件加入布局
        course_layout.addWidget(course_input_container)
        course_layout.addWidget(self.course_buttons_container)

        right_layout.addWidget(course_settings)
        main_layout.addWidget(right_container)
        
        # 初始設定表格
        self.setup_table()
        
    def add_course(self):
        course_name = self.course_input.text().strip()
        if course_name:
            course_widget = CourseButtonWidget(course_name, self.delete_course)
            self.course_buttons_layout.insertWidget(
                self.course_buttons_layout.count() - 1, 
                course_widget
            )
            self.course_input.clear()

    def delete_course(self, widget):
        self.course_buttons_layout.removeWidget(widget)
        widget.deleteLater()
    def table_drag_enter(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def table_drag_move(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def table_drop(self, event):
        pos = event.pos()
        row = self.schedule_table.rowAt(pos.y())
        col = self.schedule_table.columnAt(pos.x())
        
        if row >= 0 and col >= 0:
            if event.mimeData().hasText():
                course_name = event.mimeData().text()
                new_item = QTableWidgetItem(course_name)
                self.schedule_table.setItem(row, col, new_item)
                event.acceptProposedAction()

    def show_context_menu(self, position):
        # 建立右鍵選單
        menu = QMenu()
        delete_action = menu.addAction("刪除課程")
        
        # 獲取右鍵點擊的位置對應的儲存格
        item = self.schedule_table.itemAt(position)
        
        if item and item.text():  # 只有在儲存格有課程時才顯示選單
            action = menu.exec_(self.schedule_table.viewport().mapToGlobal(position))
            if action == delete_action:
                self.schedule_table.setItem(self.schedule_table.row(item), 
                                          self.schedule_table.column(item), 
                                          QTableWidgetItem(""))

    def table_key_press(self, event):
        # 處理鍵盤刪除事件
        if event.key() == Qt.Key_Delete:
            self.delete_selected_course()
        else:
            # 保持原有的鍵盤事件處理
            QTableWidget.keyPressEvent(self.schedule_table, event)

    def delete_selected_course(self):
        # 刪除選中的課程
        for item in self.schedule_table.selectedItems():
            if item.text():  # 只有在儲存格有課程時才刪除
                self.schedule_table.setItem(self.schedule_table.row(item),
                                          self.schedule_table.column(item),
                                          QTableWidgetItem(""))

    def update_schedule(self):
        start_time = self.start_time_edit.time().toString("HH:mm")
        end_time = self.end_time_edit.time().toString("HH:mm")
        interval = self.interval_spinbox.value()
        
        self.setup_table(interval_minutes=interval, 
                        start_time_str=start_time, 
                        end_time_str=end_time)
        
    def setup_table(self, interval_minutes=30, start_time_str="08:00", end_time_str="17:00"):
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        self.schedule_table.setColumnCount(len(weekdays))
        self.schedule_table.setHorizontalHeaderLabels(weekdays)
        
        # 啟用右鍵選單和鍵盤刪除功能
        self.schedule_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.schedule_table.customContextMenuRequested.connect(self.show_context_menu)
        self.schedule_table.keyPressEvent = self.table_key_press
        
        start_time = datetime.strptime(start_time_str, "%H:%M")
        end_time = datetime.strptime(end_time_str, "%H:%M")
        total_intervals = int((end_time - start_time).total_seconds() / (interval_minutes * 60)) + 1
        
        self.schedule_table.setRowCount(total_intervals)
        
        time_labels = []
        current_time = start_time
        for i in range(total_intervals):
            time_str = current_time.strftime("%H:%M")
            time_labels.append(time_str)
            current_time += timedelta(minutes=interval_minutes)
            
        self.schedule_table.setVerticalHeaderLabels(time_labels)
        
        for row in range(total_intervals):
            for col in range(len(weekdays)):
                item = QTableWidgetItem("")
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.schedule_table.setItem(row, col, item)
        
        self.schedule_table.setFixedWidth(450)
        header = self.schedule_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        
        self.schedule_table.horizontalHeader().setDefaultSectionSize(55)
        self.schedule_table.verticalHeader().setDefaultSectionSize(30)
        
        self.schedule_table.setGridStyle(Qt.PenStyle.SolidLine)
        self.schedule_table.setShowGrid(True)
        self.schedule_table.setAlternatingRowColors(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScheduleWindow()
    window.show()
    sys.exit(app.exec())