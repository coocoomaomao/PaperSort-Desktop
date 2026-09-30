from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QSize, Qt, QThread, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from .executor import apply_plan, latest_manifest, undo_manifest
from .exporter import export_bibtex, export_csv
from .metadata import DEFAULT_RENAME_TEMPLATE, validate_rename_template
from .models import PlanItem, ScanResult
from .planner import build_plan
from .scanner import scan_folder

INK = "#111820"
NAVY = "#1F3A5F"
TEAL = "#2CB1A1"
ORANGE = "#F4A261"
BG = "#F6F8FB"
MUTED = "#687386"
BORDER = "#DCE3EA"
RED = "#D95D5D"
YELLOW = "#C58B2B"


class BrandCat(QWidget):
    def __init__(self, size: int = 48, parent: QWidget | None = None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)

    def sizeHint(self) -> QSize:
        return QSize(self._size, self._size)

    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = min(self.width(), self.height())
        p.scale(s / 100.0, s / 100.0)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(INK))
        p.drawEllipse(18, 24, 64, 60)
        p.drawPolygon([(23, 34), (24, 8), (43, 27)])
        p.drawPolygon([(77, 34), (76, 8), (57, 27)])
        p.setBrush(QColor(TEAL))
        p.drawEllipse(34, 47, 9, 7)
        p.drawEllipse(57, 47, 9, 7)
        p.setPen(QPen(QColor(ORANGE), 7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawLine(39, 68, 48, 76)
        p.drawLine(48, 76, 65, 61)


class StatCard(QFrame):
    def __init__(self, title: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("statCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(1)
        self.value = QLabel("0")
        self.value.setObjectName("statValue")
        self.label = QLabel(title)
        self.label.setObjectName("statLabel")
        layout.addWidget(self.value)
        layout.addWidget(self.label)

    def set_value(self, value: int):
        self.value.setText(str(value))


class DropZone(QFrame):
    dropped = Signal(Path)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(20, 24, 20, 24)
        cat = BrandCat(64)
        cat_wrap = QHBoxLayout()
        cat_wrap.addStretch()
        cat_wrap.addWidget(cat)
        cat_wrap.addStretch()
        layout.addLayout(cat_wrap)
        title = QLabel("把文献文件夹拖到这里")
        title.setObjectName("dropTitle")
        title.setAlignment(Qt.AlignCenter)
        sub = QLabel("PDF · 本地扫描 · 不上传 · 不自动删除")
        sub.setObjectName("dropSub")
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(sub)

    def dragEnterEvent(self, event):  # noqa: N802
        urls = event.mimeData().urls()
        if any(Path(u.toLocalFile()).is_dir() for u in urls):
            event.acceptProposedAction()

    def dropEvent(self, event):  # noqa: N802
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_dir():
                self.dropped.emit(path)
                event.acceptProposedAction()
                return


class ScanWorker(QThread):
    progress = Signal(int, int, str)
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, root: Path):
        super().__init__()
        self.root = root

    def run(self):
        try:
            result = scan_folder(
                self.root,
                progress=lambda current, total, path: self.progress.emit(current, total, path.name),
            )
            self.completed.emit(result)
        except Exception as exc:  # pragma: no cover - GUI guard
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PaperSort Desktop — MeowBuild Lab")
        self.resize(1180, 780)
        self.setMinimumSize(980, 680)
        self._root: Path | None = None
        self._result: ScanResult | None = None
        self._plan: list[PlanItem] = []
        self._worker: ScanWorker | None = None
        self._settings = QSettings("MeowBuild Lab", "PaperSort Desktop")
        self._rename_template = self._settings.value("rename_template", DEFAULT_RENAME_TEMPLATE, type=str) or DEFAULT_RENAME_TEMPLATE
        self._build_ui()
        self._apply_styles()
        self._show_first_run_tip()

    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(15)
        self.setCentralWidget(central)

        header = QHBoxLayout()
        brand = QHBoxLayout()
        brand.addWidget(BrandCat(44))
        brand_text = QVBoxLayout()
        name = QLabel("PAPERSORT DESKTOP")
        name.setObjectName("brandName")
        tag = QLabel("把乱糟糟的论文 PDF，整理成真正找得到的文献库。")
        tag.setObjectName("brandTag")
        brand_text.addWidget(name)
        brand_text.addWidget(tag)
        brand.addLayout(brand_text)
        header.addLayout(brand)
        header.addStretch()
        badge = QLabel("OPEN SOURCE · v0.2.0")
        badge.setObjectName("versionBadge")
        header.addWidget(badge)
        root.addLayout(header)

        privacy = QFrame()
        privacy.setObjectName("privacy")
        privacy_layout = QHBoxLayout(privacy)
        privacy_layout.setContentsMargins(12, 8, 12, 8)
        chip = QLabel("LOCAL ONLY")
        chip.setObjectName("localChip")
        privacy_layout.addWidget(chip)
        privacy_layout.addWidget(QLabel("本地扫描 · 不上传论文 · 不自动删除重复文件 · 修改前先预览"))
        privacy_layout.addStretch()
        root.addWidget(privacy)

        self.drop = DropZone()
        self.drop.dropped.connect(self.scan_root)
        root.addWidget(self.drop)

        action_row = QHBoxLayout()
        self.pick_btn = QPushButton("救救我的下载文件夹")
        self.pick_btn.setObjectName("primary")
        self.pick_btn.clicked.connect(self.choose_folder)
        self.scan_btn = QPushButton("重新扫描")
        self.scan_btn.clicked.connect(self.rescan)
        self.scan_btn.setEnabled(False)
        self.organize = QCheckBox("按年份整理到子文件夹")
        self.organize.stateChanged.connect(self.rebuild_plan)
        self.apply_btn = QPushButton("应用选中的修改 →")
        self.apply_btn.setObjectName("primary")
        self.apply_btn.clicked.connect(self.apply_selected)
        self.apply_btn.setEnabled(False)
        self.export_btn = QPushButton("导出文献清单")
        self.export_btn.clicked.connect(self.export_library)
        self.export_btn.setEnabled(False)
        self.undo_btn = QPushButton("撤销上次操作")
        self.undo_btn.clicked.connect(self.undo_last)
        self.undo_btn.setEnabled(False)
        action_row.addWidget(self.pick_btn)
        action_row.addWidget(self.scan_btn)
        action_row.addWidget(self.organize)
        action_row.addStretch()
        action_row.addWidget(self.export_btn)
        action_row.addWidget(self.undo_btn)
        action_row.addWidget(self.apply_btn)
        root.addLayout(action_row)

        template_row = QHBoxLayout()
        template_label = QLabel("命名模板")
        template_label.setObjectName("templateLabel")
        self.template_input = QLineEdit(self._rename_template)
        self.template_input.setPlaceholderText(DEFAULT_RENAME_TEMPLATE)
        self.template_input.setToolTip("可用变量：{year} {author} {title} {doi}")
        self.template_input.editingFinished.connect(self.update_rename_template)
        template_reset = QPushButton("恢复默认")
        template_reset.clicked.connect(self.reset_rename_template)
        template_hint = QLabel("可用：{year} · {author} · {title} · {doi}")
        template_hint.setObjectName("templateHint")
        template_row.addWidget(template_label)
        template_row.addWidget(self.template_input, 1)
        template_row.addWidget(template_reset)
        template_row.addWidget(template_hint)
        root.addLayout(template_row)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setTextVisible(True)
        root.addWidget(self.progress)

        cards = QHBoxLayout()
        self.card_total = StatCard("全部文献")
        self.card_rename = StatCard("可重命名")
        self.card_dup = StatCard("疑似重复")
        self.card_missing = StatCard("元数据缺失")
        for card in (self.card_total, self.card_rename, self.card_dup, self.card_missing):
            cards.addWidget(card)
        root.addLayout(cards)

        self.status = QLabel("准备好了。选择一个文献文件夹，或者直接拖进来。")
        self.status.setObjectName("status")
        root.addWidget(self.status)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["处理", "状态", "当前文件", "建议文件名", "年份", "作者", "DOI", "备注"])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(2, QHeaderView.Stretch)
        header_view.setSectionResizeMode(3, QHeaderView.Stretch)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(7, QHeaderView.Stretch)
        root.addWidget(self.table, 1)

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background: {BG}; color: {INK}; font-size: 13px; }}
            QLabel {{ background: transparent; }}
            #brandName {{ font-size: 22px; font-weight: 800; color: {NAVY}; letter-spacing: 1px; }}
            #brandTag {{ color: {MUTED}; font-size: 13px; }}
            #versionBadge {{ background: #EAF0F6; color: {NAVY}; border-radius: 12px; padding: 6px 10px; font-weight: 700; }}
            #privacy {{ background: #EAF8F5; border: 1px solid #BFE7DF; border-radius: 10px; }}
            #localChip {{ background: {TEAL}; color: white; border-radius: 8px; padding: 4px 8px; font-weight: 800; }}
            #dropZone {{ background: white; border: 2px dashed #BBC8D4; border-radius: 16px; }}
            #dropZone:hover {{ border-color: {TEAL}; background: #FBFEFD; }}
            #dropTitle {{ font-size: 20px; font-weight: 800; color: {NAVY}; }}
            #dropSub {{ color: {MUTED}; }}
            QPushButton {{ background: white; border: 1px solid {BORDER}; border-radius: 9px; padding: 9px 14px; font-weight: 650; }}
            QPushButton:hover {{ border-color: {TEAL}; }}
            QPushButton:disabled {{ color: #A9B0B7; background: #F1F3F5; }}
            QPushButton#primary {{ background: {NAVY}; color: white; border: none; }}
            QPushButton#primary:hover {{ background: #274A76; }}
            QLineEdit {{ background: white; border: 1px solid {BORDER}; border-radius: 9px; padding: 8px 10px; }}
            QLineEdit:focus {{ border-color: {TEAL}; }}
            #templateLabel {{ color: {NAVY}; font-weight: 700; }}
            #templateHint {{ color: {MUTED}; }}
            QFrame#statCard {{ background: white; border: 1px solid {BORDER}; border-radius: 12px; }}
            #statValue {{ font-size: 23px; font-weight: 800; color: {NAVY}; }}
            #statLabel {{ color: {MUTED}; }}
            #status {{ color: {MUTED}; }}
            QTableWidget {{ background: white; border: 1px solid {BORDER}; border-radius: 10px; gridline-color: #EDF1F4; alternate-background-color: #FAFBFC; }}
            QHeaderView::section {{ background: #F0F4F7; color: {NAVY}; padding: 8px; border: none; border-bottom: 1px solid {BORDER}; font-weight: 700; }}
            QProgressBar {{ border: 1px solid {BORDER}; border-radius: 7px; background: white; text-align: center; }}
            QProgressBar::chunk {{ background: {TEAL}; border-radius: 6px; }}
        """)

    def _show_first_run_tip(self):
        if self._settings.value("first_run_shown", False, type=bool):
            return
        self._settings.setValue("first_run_shown", True)
        QMessageBox.information(
            self,
            "30 秒上手",
            "1. 选择或拖入一个论文 PDF 文件夹。\n"
            "2. PaperSort 只扫描并生成整理预览，不会自动删除文件。\n"
            "3. 疑似重复默认不勾选，请人工确认。\n"
            "4. 点击“应用选中的修改”后仍可撤销上一次操作。",
        )

    def update_rename_template(self):
        template = self.template_input.text().strip() or DEFAULT_RENAME_TEMPLATE
        try:
            validate_rename_template(template)
        except ValueError as exc:
            QMessageBox.warning(self, "命名模板不可用", str(exc))
            self.template_input.setText(self._rename_template)
            return
        self._rename_template = template
        self.template_input.setText(template)
        self._settings.setValue("rename_template", template)
        self.rebuild_plan()

    def reset_rename_template(self):
        self._rename_template = DEFAULT_RENAME_TEMPLATE
        self.template_input.setText(DEFAULT_RENAME_TEMPLATE)
        self._settings.setValue("rename_template", DEFAULT_RENAME_TEMPLATE)
        self.rebuild_plan()

    def choose_folder(self):
        selected = QFileDialog.getExistingDirectory(self, "选择论文 PDF 文件夹")
        if selected:
            self.scan_root(Path(selected))

    def rescan(self):
        if self._root:
            self.scan_root(self._root)

    def scan_root(self, root: Path):
        if self._worker and self._worker.isRunning():
            return
        self._root = Path(root).resolve()
        self.status.setText(f"正在扫描：{self._root}")
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.table.setRowCount(0)
        self.apply_btn.setEnabled(False)
        self.scan_btn.setEnabled(False)
        self.pick_btn.setEnabled(False)
        self._worker = ScanWorker(self._root)
        self._worker.progress.connect(self._on_progress)
        self._worker.completed.connect(self._on_scan_complete)
        self._worker.failed.connect(self._on_scan_failed)
        self._worker.start()

    def _on_progress(self, current: int, total: int, name: str):
        if total:
            self.progress.setRange(0, total)
            self.progress.setValue(current)
        self.progress.setFormat(f"{current}/{total} · {name}")

    def _on_scan_complete(self, result: ScanResult):
        self._result = result
        self._root = result.root
        self.progress.setVisible(False)
        self.scan_btn.setEnabled(True)
        self.pick_btn.setEnabled(True)
        self.undo_btn.setEnabled(bool(latest_manifest(result.root)))
        self.rebuild_plan()
        if result.total == 0:
            self.status.setText("这个文件夹里没有找到 PDF。")
        else:
            self.status.setText(
                f"扫描完成：{result.total} 篇 · {result.duplicates} 个疑似重复 · "
                f"{result.missing_metadata} 篇元数据不完整。修改前请先检查预览。"
            )

    def _on_scan_failed(self, message: str):
        self.progress.setVisible(False)
        self.scan_btn.setEnabled(bool(self._root))
        self.pick_btn.setEnabled(True)
        self.status.setText("扫描失败。")
        QMessageBox.critical(self, "扫描失败", message)

    def rebuild_plan(self):
        if not self._result:
            return
        self._plan = build_plan(
            self._result.records,
            organize_by_year=self.organize.isChecked(),
            root=self._result.root,
            rename_template=self._rename_template,
        )
        self.card_total.set_value(self._result.total)
        self.card_rename.set_value(sum(1 for p in self._plan if p.action == "rename"))
        self.card_dup.set_value(self._result.duplicates)
        self.card_missing.set_value(self._result.missing_metadata)
        self._populate_table()
        self.export_btn.setEnabled(bool(self._result.records))
        self.apply_btn.setEnabled(any(p.action == "rename" for p in self._plan))

    def _populate_table(self):
        assert self._result is not None
        self.table.setRowCount(len(self._result.records))
        for row, (record, plan) in enumerate(zip(self._result.records, self._plan, strict=True)):
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            checkbox.setCheckState(Qt.Checked if plan.selected else Qt.Unchecked)
            self.table.setItem(row, 0, checkbox)

            if record.duplicate_kind == "exact":
                status = "完全重复"
                color = RED
            elif record.duplicate_kind == "doi":
                status = "同 DOI"
                color = YELLOW
            elif record.warnings:
                status = "需确认"
                color = YELLOW
            else:
                status = "可整理"
                color = TEAL
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QBrush(QColor(color)))
            self.table.setItem(row, 1, status_item)
            self.table.setItem(row, 2, QTableWidgetItem(record.path.name))
            self.table.setItem(row, 3, QTableWidgetItem(plan.target.name if plan.action == "rename" else record.path.name))
            self.table.setItem(row, 4, QTableWidgetItem(record.year or "—"))
            self.table.setItem(row, 5, QTableWidgetItem(record.first_author or "—"))
            self.table.setItem(row, 6, QTableWidgetItem(record.doi or "—"))
            notes = list(record.warnings)
            if plan.reason:
                notes.insert(0, plan.reason)
            self.table.setItem(row, 7, QTableWidgetItem("；".join(dict.fromkeys(notes)) or "—"))

    def _sync_selection(self):
        for row, plan in enumerate(self._plan):
            item = self.table.item(row, 0)
            if item is not None:
                plan.selected = item.checkState() == Qt.Checked

    def export_library(self):
        if not self._result or not self._result.records:
            return
        default_path = (self._root or self._result.root) / "PaperSort-Library.csv"
        destination, selected_filter = QFileDialog.getSaveFileName(
            self,
            "导出文献清单",
            str(default_path),
            "CSV 文献清单 (*.csv);;BibTeX (*.bib)",
        )
        if not destination:
            return
        path = Path(destination)
        try:
            if selected_filter.startswith("BibTeX") or path.suffix.lower() == ".bib":
                if path.suffix.lower() != ".bib":
                    path = path.with_suffix(".bib")
                export_bibtex(self._result.records, path)
                kind = "BibTeX"
            else:
                if path.suffix.lower() != ".csv":
                    path = path.with_suffix(".csv")
                export_csv(self._result.records, path)
                kind = "CSV"
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", str(exc))
            return
        QMessageBox.information(self, "导出完成", f"已导出 {kind} 文献清单：\n{path}")

    def apply_selected(self):
        if not self._root or not self._plan:
            return
        self._sync_selection()
        selected = [p for p in self._plan if p.selected and p.action == "rename"]
        if not selected:
            QMessageBox.information(self, "没有选中修改", "至少勾选一项需要整理的文件。")
            return
        reply = QMessageBox.question(
            self,
            "确认应用修改",
            f"将重命名/移动 {len(selected)} 个 PDF。\n\nPaperSort 不会删除文件，并会保存撤销记录。继续吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            manifest = apply_plan(self._root, self._plan)
        except Exception as exc:
            QMessageBox.critical(self, "修改失败", str(exc))
            return
        QMessageBox.information(self, "整理完成", f"已处理 {len(selected)} 个文件。\n撤销记录：{manifest.name}")
        self.scan_root(self._root)

    def undo_last(self):
        if not self._root:
            return
        manifest = latest_manifest(self._root)
        if not manifest:
            QMessageBox.information(self, "没有可撤销操作", "未找到可撤销的整理记录。")
            return
        reply = QMessageBox.question(
            self,
            "撤销上次操作",
            "将尝试把上一次 PaperSort 修改的文件恢复到原路径。不会覆盖已存在文件。继续吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            restored = undo_manifest(manifest)
        except Exception as exc:
            QMessageBox.critical(self, "撤销失败", str(exc))
            return
        QMessageBox.information(self, "撤销完成", f"已恢复 {restored} 个文件。")
        self.scan_root(self._root)
