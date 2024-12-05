import sys
import os
import json
import copy
import csv
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QDialog, QFormLayout, QDialogButtonBox,
    QSpinBox, QComboBox, QTableWidget, QTableWidgetItem, QMessageBox,
    QTimeEdit, QHeaderView, QScrollArea, QFrame, QSpacerItem, QSizePolicy,
    QStackedWidget
)
from PyQt5.QtCore import Qt, QMimeData, QTime
from PyQt5.QtGui import QDrag, QPixmap, QPainter

# Constants
SETTINGS_FILE = "settings.json"
TASKS_FILE = "tasks.txt"
TAGSET_FILE = "tagset.csv"


class Scheduler:
    def __init__(self, start_time=9, end_time=17, interval_minutes=30, fatigue_calculation=None):
        """
        初始化排程器。

        :param start_time: 工作開始時間（24小時制），預設為9。
        :param end_time: 工作結束時間（24小時制），預設為17。
        :param interval_minutes: 每個時間區間的分鐘數，預設為30。
        :param fatigue_calculation: 用戶自定義的疲勞計算函數。
        """
        if not (0 <= start_time < 24) or not (0 < end_time <= 24):
            raise ValueError("工作時間必須在0到24之間。")
        if start_time >= end_time:
            raise ValueError("開始時間必須早於結束時間。")
        if 60 % interval_minutes != 0:
            raise ValueError("時間間隔必須能被60整除。")

        self.start_time = start_time
        self.end_time = end_time
        self.interval_minutes = interval_minutes
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.num_intervals_per_day = int((self.end_time - self.start_time) * 60 / self.interval_minutes)
        # Initialize schedule with None
        self.schedule = [[None for _ in range(self.num_intervals_per_day)] for _ in
                         range(7)]  # 0: Monday, ..., 6: Sunday
        self.tasks = []
        self.task_dict = {}  # 用於加速任務查找
        self.fatigue_calculation = fatigue_calculation or self.default_fatigue_calculation

    def default_fatigue_calculation(self, task):
        """
        默認的疲勞計算方式：difficulty * time

        :param task: 任務字典
        :return: 計算出的疲勞值
        """
        return task.get("difficulty", 1) * task.get("time", 1)

    def calculate_fatigue(self):
        total_fatigue = 0
        for day_tasks in self.schedule:
            daily_fatigue = 0
            daily_priority_sum = 0
            for task in day_tasks:
                if task:
                    task_fatigue = self.fatigue_calculation(task)
                    daily_fatigue += task_fatigue
                    daily_priority_sum += task.get("priority", 0)
            daily_fatigue *= (1 + daily_priority_sum)
            total_fatigue += daily_fatigue
        return total_fatigue

    def assign_task(self, task):
        """
        嘗試將任務分配到排程中。

        :param task: 任務字典
        :return: 是否成功分配
        """
        duration = int(task["time"])
        num_slots = duration * (60 // self.interval_minutes)

        if task.get("fixed_time"):
            day, start_hour, start_minute = task["fixed_time"]  # e.g., ('Monday', 9, 0)
            day_index = self.days.index(day)
            start_slot = int(
                (start_hour - self.start_time) * (60 // self.interval_minutes) + start_minute / self.interval_minutes)
            if start_slot < 0 or start_slot + num_slots > self.num_intervals_per_day:
                return False  # 固定時間超出範圍
            # 檢查是否有空閒
            for slot in range(start_slot, start_slot + num_slots):
                if self.schedule[day_index][slot]:
                    return False  # 時間區間已被佔用
            # 分配任務
            for slot in range(start_slot, start_slot + num_slots):
                self.schedule[day_index][slot] = task
            return True
        else:
            # 遍歷所有天和時間區間尋找空閒
            for day_index in range(7):
                for start_slot in range(self.num_intervals_per_day - num_slots + 1):
                    # 檢查區間是否空閒
                    occupied = False
                    for slot in range(start_slot, start_slot + num_slots):
                        if self.schedule[day_index][slot]:
                            occupied = True
                            break
                    if not occupied:
                        # 分配任務
                        for slot in range(start_slot, start_slot + num_slots):
                            self.schedule[day_index][slot] = task
                        return True
            return False  # 沒有可用的時間區間

    def minimize_total_fatigue(self):
        self.min_fatigue = float('inf')
        self.best_schedule = copy.deepcopy(self.schedule)
        self.backtrack(0)
        return self.best_schedule, self.min_fatigue

    def backtrack(self, index):
        if index >= len(self.tasks):
            fatigue = self.calculate_fatigue()
            if fatigue < self.min_fatigue:
                self.min_fatigue = fatigue
                self.best_schedule = copy.deepcopy(self.schedule)
            return

        task = self.tasks[index]
        possible_assignments = self.get_possible_assignments(task)
        for day_index, start_slot in possible_assignments:
            # 分配任務
            assigned = True
            for slot in range(start_slot, start_slot + int(task["time"] * (60 // self.interval_minutes))):
                if self.schedule[day_index][slot]:
                    assigned = False
                    break
            if not assigned:
                continue
            for slot in range(start_slot, start_slot + int(task["time"] * (60 // self.interval_minutes))):
                self.schedule[day_index][slot] = task
            # 繼續遞迴
            self.backtrack(index + 1)
            # 撤銷分配
            for slot in range(start_slot, start_slot + int(task["time"] * (60 // self.interval_minutes))):
                self.schedule[day_index][slot] = None

    def get_possible_assignments(self, task):
        """
        獲取任務可能的分配位置。

        :param task: 任務字典
        :return: 列表，包含 (day_index, start_slot) 的元組
        """
        assignments = []
        duration = int(task["time"])
        num_slots = duration * (60 // self.interval_minutes)

        if task.get("fixed_time"):
            day, start_hour, start_minute = task["fixed_time"]
            day_index = self.days.index(day)
            start_slot = int(
                (start_hour - self.start_time) * (60 // self.interval_minutes) + start_minute / self.interval_minutes)
            if 0 <= start_slot <= self.num_intervals_per_day - num_slots:
                # 檢查是否有空閒
                occupied = False
                for slot in range(start_slot, start_slot + num_slots):
                    if self.schedule[day_index][slot]:
                        occupied = True
                        break
                if not occupied:
                    assignments.append((day_index, start_slot))
        else:
            for day_index in range(7):
                for start_slot in range(self.num_intervals_per_day - num_slots + 1):
                    # 檢查是否有空閒
                    occupied = False
                    for slot in range(start_slot, start_slot + num_slots):
                        if self.schedule[day_index][slot]:
                            occupied = True
                            break
                    if not occupied:
                        assignments.append((day_index, start_slot))
        return assignments

    def add_tasks(self, tasks):
        self.tasks.extend(tasks)
        for task in tasks:
            self.task_dict[task["name"]] = task

    def generate_schedule_list(self):
        """
        將排程轉換為列表格式，便於 GUI 使用。

        :return: 二維列表，7天，每天 num_intervals_per_day 個時間區間
        """
        schedule_list = [[] for _ in range(7)]
        for day_index, day_slots in enumerate(self.schedule):
            for slot_index, task in enumerate(day_slots):
                if task:
                    schedule_list[day_index].append({
                        "name": task["name"],
                        "day": self.days[day_index],
                        "slot": slot_index
                    })
        return schedule_list


class TaskDetailsDialog(QDialog):
    def __init__(self, tags, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Task Details")
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        # Task Name
        self.task_name_input = QLineEdit()
        self.form_layout.addRow("Task Name:", self.task_name_input)

        # Difficulty
        self.difficulty_input = QSpinBox()
        self.difficulty_input.setRange(1, 10)
        self.form_layout.addRow("Difficulty:", self.difficulty_input)

        # Time
        self.time_input = QSpinBox()
        self.time_input.setRange(1, 24)
        self.form_layout.addRow("Time (hours):", self.time_input)

        # Priority
        self.priority_input = QSpinBox()
        self.priority_input.setRange(1, 5)
        self.form_layout.addRow("Priority:", self.priority_input)

        # Fixed Time
        self.fixed_time_checkbox = QComboBox()
        self.fixed_time_checkbox.addItems(["No Fixed Time", "Fixed Time"])
        self.fixed_time_checkbox.currentIndexChanged.connect(self.toggle_fixed_time_inputs)
        self.form_layout.addRow("Fixed Time:", self.fixed_time_checkbox)

        # Day for fixed time
        self.fixed_day_combo = QComboBox()
        self.fixed_day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        self.fixed_day_combo.setEnabled(False)
        self.form_layout.addRow("Day:", self.fixed_day_combo)

        # Start Time
        self.fixed_start_time = QTimeEdit()
        self.fixed_start_time.setDisplayFormat("HH:mm")
        self.fixed_start_time.setTime(QTime(9, 0))
        self.fixed_start_time.setEnabled(False)
        self.form_layout.addRow("Start Time:", self.fixed_start_time)

        # Dependencies
        self.dependencies_input = QLineEdit()
        self.dependencies_input.setPlaceholderText("Comma-separated task names")
        self.form_layout.addRow("Dependencies:", self.dependencies_input)

        # Dynamically create input fields for each tag
        self.tag_inputs = {}
        for tag in tags:
            tag_name = tag["name"]
            tag_type = tag["type"]

            if tag_type == "int":
                input_field = QSpinBox()
                input_field.setRange(-999999, 999999)
            elif tag_type == "float":
                input_field = QSpinBox()  # For simplicity, using QSpinBox. Can be replaced with QDoubleSpinBox.
            elif tag_type == "bool":
                input_field = QComboBox()
                input_field.addItems(["True", "False"])
            elif tag_type == "str":
                input_field = QLineEdit()
            else:
                input_field = QLineEdit()  # Default to QLineEdit for unsupported types

            self.form_layout.addRow(f"{tag_name}:", input_field)
            self.tag_inputs[tag_name] = input_field

        self.layout.addLayout(self.form_layout)

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addWidget(self.button_box)

    def toggle_fixed_time_inputs(self, index):
        """Enable or disable fixed time inputs based on the combo box selection."""
        if index == 1:  # Fixed Time selected
            self.fixed_day_combo.setEnabled(True)
            self.fixed_start_time.setEnabled(True)
        else:
            self.fixed_day_combo.setEnabled(False)
            self.fixed_start_time.setEnabled(False)

    def get_task_data(self):
        """Retrieve the task data entered by the user."""
        task_data = {
            "name": self.task_name_input.text(),
            "difficulty": self.difficulty_input.value(),
            "time": self.time_input.value(),
            "priority": self.priority_input.value(),
            "fixed_time": None,
            "dependencies": []
        }

        if self.fixed_time_checkbox.currentIndex() == 1:
            day = self.fixed_day_combo.currentText()
            start_time = self.fixed_start_time.time()
            task_data["fixed_time"] = (day, start_time.hour(), start_time.minute())

        dependencies_text = self.dependencies_input.text().strip()
        if dependencies_text:
            task_data["dependencies"] = [dep.strip() for dep in dependencies_text.split(",")]

        # Add other tags if necessary
        for tag_name, input_field in self.tag_inputs.items():
            if isinstance(input_field, QSpinBox):
                task_data[tag_name] = input_field.value()
            elif isinstance(input_field, QComboBox):
                task_data[tag_name] = input_field.currentText() == "True"
            elif isinstance(input_field, QLineEdit):
                task_data[tag_name] = input_field.text()
            # Add more types if necessary

        return task_data


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


class DraggableTask(QLabel):
    """A draggable QLabel representing a task."""

    def __init__(self, task_name, parent=None):
        super().__init__(task_name, parent)
        self.task_name = task_name
        self.setStyleSheet("background-color: lightblue; padding: 5px; border: 1px solid gray;")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(30)

    def mouseMoveEvent(self, event):
        """Handle the drag event when the task is dragged."""
        if event.buttons() & Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.task_name)  # Set the task name as drag data
            drag.setMimeData(mime_data)

            # Create a pixmap to use as a drag icon
            pixmap = QPixmap(self.size())  # Use the size of the widget
            pixmap.fill(Qt.transparent)  # Transparent background

            # Paint the task label onto the pixmap
            painter = QPainter(pixmap)
            painter.setOpacity(0.3)  # Set opacity to 30%

            painter.fillRect(self.rect(), self.palette().window())  # Fill with background color
            painter.drawText(self.rect(), Qt.AlignCenter, self.task_name)  # Draw task name
            painter.end()

            drag.setPixmap(pixmap)  # Set the pixmap as the drag icon
            drag.setHotSpot(event.pos())  # Set the hotspot to the cursor position

            drag.exec(Qt.CopyAction | Qt.MoveAction)


class HoverableBox(QFrame):
    """A custom frame that changes color when hovered and handles drops."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window  # Reference to the main window
        self.setFixedSize(50, 50)  # Smaller size for the box
        self.setStyleSheet("background-color: lightgray;")
        self.setAcceptDrops(True)  # Allow drop events

    def enterEvent(self, event):
        """Change color when mouse enters."""
        self.setStyleSheet("background-color: lightblue;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Revert color when mouse leaves."""
        self.setStyleSheet("background-color: lightgray;")
        super().leaveEvent(event)

    def dragEnterEvent(self, event):
        """Accept drag events if the data is text."""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Show a confirmation dialog when a task is dropped."""
        if event.mimeData().hasText():
            task_name = event.mimeData().text()
            dialog = QMessageBox()
            dialog.setIcon(QMessageBox.Question)
            dialog.setWindowTitle("Remove Task")
            dialog.setText(f"Are you sure you want to remove the task '{task_name}'?")
            dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            dialog.setDefaultButton(QMessageBox.No)
            choice = dialog.exec()

            if choice == QMessageBox.Yes:
                # Call the main window's remove_task method
                self.main_window.remove_task(task_name)


class ScheduleWidget(QWidget):
    def __init__(self, scheduler):
        super().__init__()
        self.scheduler = scheduler  # Reference to the Scheduler instance
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # Label to display minimum fatigue
        self.fatigue_label = QLabel("Minimum Fatigue: N/A")
        self.fatigue_label.setAlignment(Qt.AlignCenter)
        self.fatigue_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(self.fatigue_label)

        # Weekly schedule table
        self.schedule_table = QTableWidget()
        self.schedule_table.setAcceptDrops(True)  # Allow drop events
        self.schedule_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout.addWidget(self.schedule_table)

        self.setup_table()
        self.schedule_table.resizeEvent = lambda event: self.adjust_table_sizes()

    def setup_table(self, interval_minutes=30, start_time_str="09:00", end_time_str="17:00"):
        """Set up the schedule table with time intervals and days of the week."""
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        self.schedule_table.setColumnCount(len(weekdays))
        self.schedule_table.setHorizontalHeaderLabels(weekdays)

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
        self.schedule_table.verticalHeader().setDefaultSectionSize(30)  # Set the default row height

        # Initialize the table with empty cells
        for row in range(self.schedule_table.rowCount()):
            for col in range(self.schedule_table.columnCount()):
                self.schedule_table.setItem(row, col, QTableWidgetItem(""))

        # Set table properties for better UX
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.schedule_table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

    def dragEnterEvent(self, event):
        """Accept drag events if the data is text."""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle the drop event to set the task name in the dropped cell."""
        pos = event.pos()
        row = self.schedule_table.rowAt(pos.y())
        col = self.schedule_table.columnAt(pos.x())

        if row >= 0 and col >= 0 and event.mimeData().hasText():
            task_name = event.mimeData().text()
            item = QTableWidgetItem(task_name)
            item.setTextAlignment(Qt.AlignCenter)
            self.schedule_table.setItem(row, col, item)
            event.acceptProposedAction()

    def adjust_table_sizes(self):
        """Adjust the column widths and row heights to fit the table."""
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.schedule_table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

    def update_schedule_display(self, schedule_list, min_fatigue):
        """Update the schedule table and fatigue label with optimized schedule."""
        # Clear existing schedule
        for row in range(self.schedule_table.rowCount()):
            for col in range(self.schedule_table.columnCount()):
                self.schedule_table.setItem(row, col, QTableWidgetItem(""))

        # 填充排程資料
        for day_index, day_tasks in enumerate(schedule_list):
            for task in day_tasks:
                slot = task["slot"]
                task_name = task["name"]
                if 0 <= slot < self.schedule_table.rowCount():
                    self.schedule_table.setItem(slot, day_index, QTableWidgetItem(task_name))

        # 更新疲勞值標籤
        self.fatigue_label.setText(f"Minimum Fatigue: {min_fatigue}")


class CourseButtonWidget(QWidget):
    def __init__(self, course_name, delete_callback, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.course_button = DraggableButton(course_name)
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Schedule Manager")
        self.resize(1200, 800)
        self.move(300, 100)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Define the custom fatigue calculation function
        def custom_fatigue_calculation(task):
            """
            自定義疲勞計算方式：difficulty * spend_time * priority

            :param task: 任務字典
            :return: 計算出的疲勞值
            """
            difficulty = task.get("difficulty", 1)
            spend_time = task.get("time", 1)
            priority = task.get("priority", 1)  # 假設 priority 預設為1
            return difficulty * spend_time * priority

        # Initialize Scheduler with the custom fatigue calculation function
        self.scheduler = Scheduler(fatigue_calculation=custom_fatigue_calculation)

        # Weekly schedule
        self.schedule_widget = ScheduleWidget(self.scheduler)
        main_layout.addWidget(self.schedule_widget, stretch=3)

        # Right side navigation
        right_side = QWidget()
        right_layout = QVBoxLayout(right_side)

        button_layout = QHBoxLayout()
        self.tags_button = QPushButton("Tags")
        self.tasks_button = QPushButton("Tasks")
        self.optimize_button = QPushButton("Optimize")
        self.setting_button = QPushButton("Setting")
        button_layout.addWidget(self.tags_button)
        button_layout.addWidget(self.tasks_button)
        button_layout.addWidget(self.optimize_button)
        button_layout.addWidget(self.setting_button)

        self.page_stack = QStackedWidget()
        self.page_stack.addWidget(self.create_tags_page())
        self.page_stack.addWidget(self.create_tasks_page())
        self.page_stack.addWidget(self.create_page("Optimize Page"))
        self.settings_page = self.create_settings_page()
        self.page_stack.addWidget(self.settings_page)

        right_layout.addLayout(button_layout)
        right_layout.addWidget(self.page_stack)
        main_layout.addWidget(right_side, stretch=1)

        # Button connections
        self.tags_button.clicked.connect(lambda: self.page_stack.setCurrentIndex(0))
        self.tasks_button.clicked.connect(lambda: self.page_stack.setCurrentIndex(1))
        self.optimize_button.clicked.connect(self.optimize_schedule)
        self.setting_button.clicked.connect(lambda: self.page_stack.setCurrentIndex(3))

        # Initialize tasks list
        self.tasks = []

        # Load existing tasks
        self.load_tasks()

    def save_settings(self):
        """Save the current settings (start time, end time, time interval) to a JSON file."""
        settings = {
            "start_time": self.start_time_edit.time().toString("HH:mm"),
            "end_time": self.end_time_edit.time().toString("HH:mm"),
            "time_interval": self.interval_spinbox.value(),
        }
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
                json.dump(settings, file, ensure_ascii=False, indent=4)
            print(f"Settings saved to {SETTINGS_FILE}")
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_settings(self):
        """Load the settings from the JSON file and apply them to the widgets."""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
                    settings = json.load(file)
                    # Apply the settings to the widgets
                    self.start_time_edit.setTime(QTime.fromString(settings.get("start_time", "09:00"), "HH:mm"))
                    self.end_time_edit.setTime(QTime.fromString(settings.get("end_time", "17:00"), "HH:mm"))
                    self.interval_spinbox.setValue(settings.get("time_interval", 30))
                print(f"Settings loaded from {SETTINGS_FILE}")
            except Exception as e:
                print(f"Error loading settings: {e}")
        else:
            # If the file doesn't exist, set default values
            self.start_time_edit.setTime(QTime(9, 0))
            self.end_time_edit.setTime(QTime(17, 0))
            self.interval_spinbox.setValue(30)

    def create_tags_page(self):
        tags_page = QWidget()
        tags_layout = QVBoxLayout(tags_page)

        # Create a table to display data
        self.tags_table = QTableWidget()
        self.load_tags_data()
        tags_layout.addWidget(self.tags_table)

        # Add "Add" and "Save" buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add")
        save_button = QPushButton("Save")

        add_button.clicked.connect(self.add_tag_row)
        save_button.clicked.connect(self.save_tags_data)
        button_layout.addWidget(add_button)
        button_layout.addWidget(save_button)
        tags_layout.addLayout(button_layout)

        return tags_page

    def load_tags_data(self):
        """Load tags data from the CSV and display it in the table."""
        if not os.path.exists(TAGSET_FILE):
            # If the file doesn't exist, create it with headers
            with open(TAGSET_FILE, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["name", "type", "priority", "visibility"])  # Adjust headers as needed

        with open(TAGSET_FILE, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)

            try:
                headers = next(reader)
            except StopIteration:
                headers = ["name", "type", "priority", "visibility"]  # Default headers if file is empty
                with open(TAGSET_FILE, mode='w', newline='', encoding='utf-8') as fw:
                    writer = csv.writer(fw)
                    writer.writerow(headers)

            self.tags_table.setColumnCount(len(headers) + 1)  # +1 for the delete button column
            self.tags_table.setHorizontalHeaderLabels(headers + ["Delete"])

            for row_data in reader:
                row_position = self.tags_table.rowCount()
                self.tags_table.insertRow(row_position)

                for column, data in enumerate(row_data):
                    if column == 1:  # Type column
                        type_combo = QComboBox()
                        type_combo.addItems(["int", "float", "str", "list", "dict", "bool", "set"])
                        type_combo.setCurrentText(data)
                        self.tags_table.setCellWidget(row_position, column, type_combo)
                    elif column == 3:  # Visibility column
                        visibility_combo = QComboBox()
                        visibility_combo.addItems(["True", "False"])
                        visibility_combo.setCurrentText(data)
                        self.tags_table.setCellWidget(row_position, column, visibility_combo)
                    else:
                        item = QTableWidgetItem(data)
                        self.tags_table.setItem(row_position, column, item)

                # Add delete button
                delete_button = QPushButton("Delete")
                delete_button.clicked.connect(self.delete_row)
                self.tags_table.setCellWidget(row_position, len(headers), delete_button)

            self.evenly_distribute_column_widths()

    def evenly_distribute_column_widths(self):
        """Distribute the column widths evenly across the table."""
        total_width = self.tags_table.viewport().width()
        column_count = self.tags_table.columnCount()

        if column_count > 0:
            # Calculate the width for each column
            column_width = total_width / column_count

            for col in range(column_count):
                self.tags_table.setColumnWidth(col, int(column_width))

    def add_tag_row(self):
        """Add a new row to the tags table."""
        row_position = self.tags_table.rowCount()
        self.tags_table.insertRow(row_position)

        for column in range(self.tags_table.columnCount() - 1):  # Exclude the delete button column
            if column == 1:  # Type column
                type_combo = QComboBox()
                type_combo.addItems(["int", "float", "str", "list", "dict", "bool", "set"])
                self.tags_table.setCellWidget(row_position, column, type_combo)
            elif column == 3:  # Visibility column
                visibility_combo = QComboBox()
                visibility_combo.addItems(["True", "False"])
                self.tags_table.setCellWidget(row_position, column, visibility_combo)
            else:
                input_field = QLineEdit()
                input_field.setAlignment(Qt.AlignLeft)
                self.tags_table.setCellWidget(row_position, column, input_field)

        # Add delete button
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_row)
        self.tags_table.setCellWidget(row_position, self.tags_table.columnCount() - 1, delete_button)

    def delete_row(self):
        """Delete the row containing the clicked delete button."""
        button = self.sender()  # Get the button that was clicked
        if button:
            # Find the row containing this button
            for row in range(self.tags_table.rowCount()):
                if self.tags_table.cellWidget(row, self.tags_table.columnCount() - 1) == button:
                    self.tags_table.removeRow(row)
                    break

    def save_tags_data(self):
        """Save the tags data to a CSV file, excluding the last column (delete button)."""
        with open(TAGSET_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # Get the header
            headers = [self.tags_table.horizontalHeaderItem(col).text() for col in
                       range(self.tags_table.columnCount() - 1)]
            writer.writerow(headers)

            # Write rows
            for row in range(self.tags_table.rowCount()):
                row_data = []
                for column in range(self.tags_table.columnCount() - 1):  # Exclude the delete button column
                    widget = self.tags_table.cellWidget(row, column)
                    if isinstance(widget, QComboBox):  # For combo boxes
                        row_data.append(widget.currentText())
                    elif isinstance(widget, QLineEdit):  # For line edits
                        row_data.append(widget.text())
                    else:  # For standard table items
                        item = self.tags_table.item(row, column)
                        row_data.append(item.text() if item else "")
                writer.writerow(row_data)

    def create_tasks_page(self):
        """
        Create the Tasks Page with an "Add Task" button and a smaller hoverable box next to it.
        """
        tasks_page = QWidget()
        tasks_layout = QVBoxLayout(tasks_page)

        # Scroll area for tasks
        self.task_scroll_area = QScrollArea()
        self.task_scroll_area.setWidgetResizable(True)
        self.task_scroll_content = QWidget()
        self.task_scroll_layout = QVBoxLayout(self.task_scroll_content)
        self.task_scroll_layout.setAlignment(Qt.AlignTop)
        self.task_scroll_area.setWidget(self.task_scroll_content)

        # Add the scroll area to the tasks layout
        tasks_layout.addWidget(self.task_scroll_area)

        # Horizontal layout for the "Add Task" button and hoverable box
        action_layout = QHBoxLayout()

        # "Add Task" button
        add_task_button = QPushButton("Add Task")
        add_task_button.setStyleSheet("background-color: lightgray; font-size: 14px;")
        add_task_button.clicked.connect(self.open_task_dialog)
        action_layout.addWidget(add_task_button)

        # Hoverable Box (pass self as the main window reference)
        hoverable_box = HoverableBox(self)
        action_layout.addWidget(hoverable_box)

        # Add the action layout to the tasks layout
        tasks_layout.addLayout(action_layout)

        return tasks_page

    def create_page(self, text):
        """
        Create other simple pages.

        :param text: The text to display on the page.
        :return: QWidget object.
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 20px;")
        layout.addWidget(label)
        return page

    def open_task_dialog(self):
        """
        Open a new dialog for the user to input task details.
        """
        # Assuming tags are needed, load them from tags_table
        tags = self.get_tags()
        dialog = TaskDetailsDialog(tags, self)
        if dialog.exec():  # If the user pressed "OK" in the dialog
            task_data = dialog.get_task_data()
            if not task_data["name"]:
                QMessageBox.warning(self, "Error", "Task name cannot be empty.")
                return
            self.add_task(task_data)

    def add_task(self, task_data):
        """Add a draggable task to the Tasks Page and to the Scheduler."""
        task_name = task_data["name"]
        task = DraggableTask(task_name)
        self.task_scroll_layout.insertWidget(0, task)
        self.task_scroll_content.updateGeometry()

        # Add task to Scheduler
        self.scheduler.add_tasks([task_data])

        # Add to tasks list
        task_id = len(self.tasks) + 1
        timestamp = int(datetime.now().timestamp())
        task_entry = {
            "id": task_id,
            "name": task_name,
            "timestamp": timestamp,
            "data": task_data
        }
        self.tasks.append(task_entry)

        # Save to file
        self.save_tasks_to_txt(self.tasks, TASKS_FILE)

    def remove_task(self, task_name):
        """Remove a task by its name from the GUI and Scheduler."""
        # Remove from GUI
        for i in range(self.task_scroll_layout.count()):
            widget = self.task_scroll_layout.itemAt(i).widget()
            if isinstance(widget, DraggableTask) and widget.task_name == task_name:
                widget.deleteLater()
                break

        # Remove from Scheduler
        self.scheduler.tasks = [task for task in self.scheduler.tasks if task["name"] != task_name]
        if task_name in self.scheduler.task_dict:
            del self.scheduler.task_dict[task_name]

        # Remove from tasks list
        self.tasks = [task for task in self.tasks if task["name"] != task_name]

        # Save to file
        self.save_tasks_to_txt(self.tasks, TASKS_FILE)

    def edit_task(self, task_label):
        """
        Edit the task name.

        :param task_label: The QLabel of the task to edit.
        """
        tags = self.get_tags()
        dialog = TaskDetailsDialog(tags, self)
        if dialog.exec():  # If the user pressed "OK" in the dialog
            new_name = dialog.task_name_input.text()
            old_name = task_label.text()
            if not new_name:
                QMessageBox.warning(self, "Error", "Task name cannot be empty.")
                return
            task_label.setText(new_name)

            # Update Scheduler
            for task in self.scheduler.tasks:
                if task["name"] == old_name:
                    task["name"] = new_name
                    self.scheduler.task_dict[new_name] = task
                    del self.scheduler.task_dict[old_name]
                    break

            # Update tasks list
            for task in self.tasks:
                if task["name"] == old_name:
                    task["name"] = new_name
                    break

            # Save to file
            self.save_tasks_to_txt(self.tasks, TASKS_FILE)

    def get_tags(self):
        """Retrieve tags from the tags_table."""
        tags = []
        for row in range(self.tags_table.rowCount()):
            tag = {}
            name_widget = self.tags_table.cellWidget(row, 0)
            tag["name"] = name_widget.text() if isinstance(name_widget, QLineEdit) else ""
            type_widget = self.tags_table.cellWidget(row, 1)
            tag["type"] = type_widget.currentText() if isinstance(type_widget, QComboBox) else ""
            # Add more attributes if necessary
            tags.append(tag)
        return tags

    def optimize_schedule(self):
        """Handle the Optimize button click to perform schedule optimization."""
        # Gather tasks from Scheduler
        tasks = self.scheduler.tasks

        if not tasks:
            QMessageBox.warning(self, "Warning", "No tasks available to optimize. Please add tasks first.")
            return

        # Perform optimization
        schedule_list, min_fatigue = self.scheduler.minimize_total_fatigue()

        # Update the ScheduleWidget with the optimized schedule and fatigue value
        self.schedule_widget.update_schedule_display(schedule_list, min_fatigue)

    def save_tasks_to_txt(self, tasks, filename=TASKS_FILE):
        """
        Save task data to a .txt file using JSON format.

        :param tasks: List of task dictionaries.
        :param filename: Filename to save the tasks.
        """
        try:
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(tasks, file, ensure_ascii=False, indent=4)
            print(f"Successfully saved tasks to {filename}")
        except Exception as e:
            print(f"Error saving tasks: {e}")

    def load_tasks_from_txt(self, filename=TASKS_FILE):
        """
        Load task data from a .txt file assuming it's a JSON list.

        :param filename: Filename to load the tasks from.
        :return: List of task dictionaries.
        """
        tasks = []
        try:
            if os.path.exists(filename):
                with open(filename, "r", encoding="utf-8") as file:
                    tasks = json.load(file)
                print(f"Successfully loaded tasks from {filename}")
        except Exception as e:
            print(f"Error loading tasks: {e}")
        return tasks

    def load_tasks(self):
        """Load tasks from file and add them to the GUI and Scheduler."""
        if os.path.exists(TASKS_FILE):
            self.tasks = self.load_tasks_from_txt(TASKS_FILE)
            for task in self.tasks:
                self.add_task_to_gui(task)
                self.scheduler.add_tasks([task["data"]])
        else:
            self.tasks = []

    def add_task_to_gui(self, task):
        """Add a task to the GUI's task page."""
        task_name = task["name"]
        task_widget = DraggableTask(task_name)
        self.task_scroll_layout.insertWidget(0, task_widget)
        self.task_scroll_content.updateGeometry()

    def create_settings_page(self):
        # Create the main settings page widget and layout
        settings_page = QWidget()
        settings_layout = QVBoxLayout(settings_page)

        # Create the top section for time settings
        time_settings = QWidget()
        time_layout = QVBoxLayout()
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(15)

        # Start Time
        start_time_container = QWidget()
        start_time_layout = QHBoxLayout()
        start_time_layout.setContentsMargins(0, 0, 0, 0)
        start_time_label = QLabel("Start Time:")
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm")  # Set the time display format
        self.start_time_edit.setWrapping(True)  # Allow wrapping around limits
        start_time_layout.addWidget(start_time_label)
        start_time_layout.addWidget(self.start_time_edit)
        start_time_container.setLayout(start_time_layout)

        # End Time
        end_time_container = QWidget()
        end_time_layout = QHBoxLayout()
        end_time_layout.setContentsMargins(0, 0, 0, 0)
        end_time_label = QLabel("End Time:")
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm")  # Set the time display format
        self.end_time_edit.setWrapping(True)  # Allow wrapping around limits
        end_time_layout.addWidget(end_time_label)
        end_time_layout.addWidget(self.end_time_edit)
        end_time_container.setLayout(end_time_layout)

        # Time Interval
        interval_container = QWidget()
        interval_layout = QHBoxLayout()
        interval_layout.setContentsMargins(0, 0, 0, 0)
        interval_label = QLabel("Time Interval (minutes):")
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(5, 60)  # Allow intervals from 5 to 60 minutes
        self.interval_spinbox.setSingleStep(5)  # Adjust by 5 minutes per click
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spinbox)
        interval_container.setLayout(interval_layout)

        # Add start time, end time, and interval to the layout
        time_layout.addWidget(start_time_container)
        time_layout.addWidget(end_time_container)
        time_layout.addWidget(interval_container)
        time_settings.setLayout(time_layout)

        # Horizontal Line
        horizontal_line = QFrame()
        horizontal_line.setFrameShape(QFrame.HLine)
        horizontal_line.setFrameShadow(QFrame.Sunken)
        horizontal_line.setFixedHeight(2)  # Adjust line thickness

        # Spacer below the time settings to push the line higher
        spacer_below_settings = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)  # Fixed size spacer

        # Update Button
        update_button = QPushButton("Update Schedule")
        update_button.clicked.connect(self.update_schedule)  # Update the schedule
        update_button.clicked.connect(self.save_settings)  # Save settings to file

        # Spacer below the line
        spacer_below = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Layout for the line and update button
        line_and_button_layout = QVBoxLayout()
        line_and_button_layout.addSpacerItem(spacer_below_settings)  # Add spacer to push the line higher
        line_and_button_layout.addWidget(horizontal_line)
        line_and_button_layout.addSpacerItem(spacer_below)
        line_and_button_layout.addWidget(update_button)

        # Add everything to the main settings layout
        settings_layout.addWidget(time_settings)  # Add time settings above the line
        settings_layout.addLayout(line_and_button_layout)

        # Load settings on startup
        self.load_settings()

        return settings_page


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
