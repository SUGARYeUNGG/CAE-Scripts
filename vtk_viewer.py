import vtk
import sys
import os
from pathlib import Path
from datetime import datetime
import numpy as np

# 添加必要的路径
if getattr(sys, 'frozen', False):
    # 如果是打包后的程序
    application_path = os.path.dirname(sys.executable)
else:
    # 如果是开发环境
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.append(r'C:\Users\Yang\AppData\Roaming\Python\Python313\site-packages')
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QPushButton, QFileDialog, QCheckBox, QSlider, QLabel,
                           QComboBox, QHBoxLayout, QGroupBox, QMessageBox)
from PyQt5.QtGui import QImage
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

class VTKViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        print("Initializing VTKViewer...")
        self.setWindowTitle("VTK 3D Viewer")
        self.setGeometry(100, 100, 400, 800)

        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # 创建 VTK 渲染窗口
        print("Creating VTK widget...")
        self.vtk_widget = QVTKRenderWindowInteractor()
        layout.addWidget(self.vtk_widget)

        # 创建 VTK 渲染器和场景
        print("Setting up renderer...")
        self.renderer = vtk.vtkRenderer()
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)
        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()

        # 设置交互器样式
        self.style = vtk.vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(self.style)
        
        # 设置旋转速度
        self.style.SetMotionFactor(10.0)  # 增加旋转速度

        # 创建控制面板
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        layout.addWidget(control_panel)

        # 创建文件操作按钮组
        file_group = QGroupBox("文件操作")
        file_layout = QHBoxLayout()
        
        # 创建打开文件按钮
        print("Creating open file button...")
        open_button = QPushButton("打开 VTK 文件")
        open_button.clicked.connect(self.open_file)
        file_layout.addWidget(open_button)
        
        # 创建删除模型按钮
        delete_button = QPushButton("删除模型")
        delete_button.clicked.connect(self.delete_model)
        file_layout.addWidget(delete_button)
        
        file_group.setLayout(file_layout)
        control_layout.addWidget(file_group)

        # 创建视图控制按钮组
        view_group = QGroupBox("视图控制")
        view_layout = QHBoxLayout()
        
        # 创建重置视角按钮
        reset_view_button = QPushButton("重置视角")
        reset_view_button.clicked.connect(self.reset_view)
        view_layout.addWidget(reset_view_button)
        
        # 创建截图按钮
        screenshot_button = QPushButton("截图")
        screenshot_button.clicked.connect(self.take_screenshot)
        view_layout.addWidget(screenshot_button)
        
        view_group.setLayout(view_layout)
        control_layout.addWidget(view_group)

        # 创建坐标轴显示开关
        self.axes_checkbox = QCheckBox("显示坐标轴")
        self.axes_checkbox.setChecked(True)
        self.axes_checkbox.stateChanged.connect(self.toggle_axes)
        control_layout.addWidget(self.axes_checkbox)

        # 创建颜色图例显示开关
        self.colorbar_checkbox = QCheckBox("显示颜色图例")
        self.colorbar_checkbox.setChecked(False)  # 初始状态未勾选
        self.colorbar_checkbox.stateChanged.connect(self.toggle_colorbar)
        control_layout.addWidget(self.colorbar_checkbox)

        # 创建显示模式控制
        display_mode_layout = QHBoxLayout()
        display_mode_label = QLabel("显示模式")
        display_mode_layout.addWidget(display_mode_label)
        self.display_mode = QComboBox()
        self.display_mode.addItems([
            "实体",           # Surface
            "线框",           # Wireframe
            "点云",           # Points
            "透明",           # Transparent
            "实体+线框",      # Surface with edges
            "实体+点",        # Surface with points
            "线框+点",        # Wireframe with points
            "实体+线框+点"    # Surface with edges and points
        ])
        self.display_mode.currentIndexChanged.connect(self.change_display_mode)
        display_mode_layout.addWidget(self.display_mode)
        control_layout.addLayout(display_mode_layout)

        # 创建切片控制组
        cutter_group = QGroupBox("切片控制")
        cutter_layout = QVBoxLayout()
        
        # 切片开关
        self.cutter_checkbox = QCheckBox("启用切片")
        self.cutter_checkbox.stateChanged.connect(self.toggle_cutter)
        cutter_layout.addWidget(self.cutter_checkbox)
        
        # 只显示切片开关
        self.show_only_slice_checkbox = QCheckBox("只显示切片")
        self.show_only_slice_checkbox.stateChanged.connect(self.toggle_show_only_slice)
        self.show_only_slice_checkbox.setEnabled(False)  # 初始状态禁用
        cutter_layout.addWidget(self.show_only_slice_checkbox)
        
        # 切片方向选择
        direction_layout = QHBoxLayout()
        direction_label = QLabel("切片方向:")
        direction_layout.addWidget(direction_label)
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["X轴", "Y轴", "Z轴"])
        self.direction_combo.currentIndexChanged.connect(self.update_cutter)
        direction_layout.addWidget(self.direction_combo)
        cutter_layout.addLayout(direction_layout)
        
        # 切片位置滑块
        position_layout = QVBoxLayout()
        self.position_label = QLabel("切片位置: 0.0")
        position_layout.addWidget(self.position_label)
        self.position_slider = QSlider()
        self.position_slider.setOrientation(1)  # 垂直方向
        self.position_slider.setMinimum(0)
        self.position_slider.setMaximum(100)
        self.position_slider.setValue(50)
        self.position_slider.valueChanged.connect(self.update_cutter_position)
        position_layout.addWidget(self.position_slider)
        cutter_layout.addLayout(position_layout)
        
        cutter_group.setLayout(cutter_layout)
        control_layout.addWidget(cutter_group)

        # 创建旋转速度控制
        speed_layout = QVBoxLayout()
        speed_label = QLabel("旋转速度")
        speed_layout.addWidget(speed_label)
        self.speed_slider = QSlider()
        self.speed_slider.setOrientation(1)  # 垂直方向
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(20)
        self.speed_slider.setValue(10)
        self.speed_slider.valueChanged.connect(self.update_speed)
        speed_layout.addWidget(self.speed_slider)
        control_layout.addLayout(speed_layout)

        # 创建坐标轴指示器
        self.axes = vtk.vtkAxesActor()
        self.axes.SetShaftTypeToCylinder()
        self.axes.SetXAxisLabelText("X")
        self.axes.SetYAxisLabelText("Y")
        self.axes.SetZAxisLabelText("Z")
        self.axes.SetTotalLength(1.0, 1.0, 1.0)
        self.axes.SetCylinderRadius(0.5 * self.axes.GetCylinderRadius())
        self.axes.SetConeRadius(1.025 * self.axes.GetConeRadius())
        self.axes.SetSphereRadius(1.5 * self.axes.GetSphereRadius())

        # 创建方向标记小部件
        self.orientation_marker = vtk.vtkOrientationMarkerWidget()
        self.orientation_marker.SetOrientationMarker(self.axes)
        self.orientation_marker.SetInteractor(self.interactor)
        self.orientation_marker.SetViewport(0.0, 0.0, 0.2, 0.2)  # 设置在左下角
        self.orientation_marker.SetEnabled(1)
        self.orientation_marker.InteractiveOff()  # 禁止交互

        # 初始化颜色图例
        self.colorbar = vtk.vtkScalarBarActor()
        self.colorbar.SetTitle("到原点距离")
        self.colorbar.SetNumberOfLabels(5)
        self.colorbar.SetLabelFormat("%.2f")
        self.colorbar.SetPosition(0.8, 0.1)  # 位置在右下角
        self.colorbar.SetWidth(0.1)
        self.colorbar.SetHeight(0.8)
        self.colorbar.SetVisibility(False)  # 初始状态隐藏
        
        # 设置颜色图例的字体样式
        title_prop = vtk.vtkTextProperty()
        title_prop.SetFontFamily(2)  # 使用等线字体
        title_prop.SetFontSize(14)
        title_prop.SetBold(True)
        title_prop.SetColor(0.0, 0.0, 0.0)  # 黑色
        title_prop.SetJustificationToCentered()
        title_prop.SetVerticalJustificationToTop()
        self.colorbar.SetTitleTextProperty(title_prop)
        
        label_prop = vtk.vtkTextProperty()
        label_prop.SetFontFamily(2)  # 使用等线字体
        label_prop.SetFontSize(12)
        label_prop.SetBold(False)
        label_prop.SetColor(0.0, 0.0, 0.0)  # 黑色
        label_prop.SetJustificationToCentered()
        self.colorbar.SetLabelTextProperty(label_prop)
        
        self.renderer.AddActor2D(self.colorbar)

        # 初始化切片器相关变量
        self.cutter = None
        self.cutter_actor = None
        self.plane = None
        self.bounds = None

        # 初始化交互器
        print("Initializing interactor...")
        self.interactor.Initialize()

        # 设置背景色为白色
        self.renderer.SetBackground(1.0, 1.0, 1.0)
        
        # 初始化当前actor
        self.current_actor = None
        print("VTKViewer initialization complete!")

    def reset_view(self):
        """重置视角"""
        if self.current_actor:
            # 获取当前相机
            camera = self.renderer.GetActiveCamera()
            
            # 保存当前的距离
            current_distance = camera.GetDistance()
            
            # 重置相机位置和方向
            camera.SetPosition(0, 0, current_distance)  # 保持距离不变
            camera.SetFocalPoint(0, 0, 0)  # 焦点在中心
            camera.SetViewUp(0, 1, 0)  # 上方向
            
            # 强制更新视图
            self.vtk_widget.GetRenderWindow().Render()
            
            print("视角已重置，保持模型大小不变")

    def delete_model(self):
        """删除当前模型"""
        if self.current_actor:
            reply = QMessageBox.question(self, '确认删除', 
                                       '确定要删除当前模型吗？',
                                       QMessageBox.Yes | QMessageBox.No, 
                                       QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.renderer.RemoveActor(self.current_actor)
                self.current_actor = None
                if self.cutter_actor:
                    self.renderer.RemoveActor(self.cutter_actor)
                    self.cutter_actor = None
                self.cutter = None
                self.plane = None
                self.bounds = None
                self.cutter_checkbox.setChecked(False)
                self.show_only_slice_checkbox.setChecked(False)
                self.vtk_widget.GetRenderWindow().Render()

    def take_screenshot(self):
        """截图并保存"""
        if not self.current_actor:
            QMessageBox.warning(self, '警告', '没有可用的模型进行截图')
            return

        # 获取当前时间作为文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"screenshot_{timestamp}.png"
        
        # 打开文件保存对话框
        file_name, _ = QFileDialog.getSaveFileName(
            self, "保存截图", default_name, "PNG Files (*.png);;All Files (*)"
        )
        
        if file_name:
            # 获取渲染窗口
            window = self.vtk_widget.GetRenderWindow()
            
            # 创建图像过滤器
            w2i = vtk.vtkWindowToImageFilter()
            w2i.SetInput(window)
            w2i.Update()
            
            # 创建PNG写入器
            writer = vtk.vtkPNGWriter()
            writer.SetFileName(file_name)
            writer.SetInputConnection(w2i.GetOutputPort())
            writer.Write()
            
            QMessageBox.information(self, '成功', f'截图已保存到：\n{file_name}')

    def toggle_cutter(self, state):
        """切换切片器显示状态"""
        if self.current_actor:
            if state == 2:  # Qt.Checked
                if not self.cutter:
                    self.setup_cutter()
                self.cutter_actor.SetVisibility(True)
                self.show_only_slice_checkbox.setEnabled(True)  # 启用只显示切片选项
            else:
                if self.cutter_actor:
                    self.cutter_actor.SetVisibility(False)
                self.show_only_slice_checkbox.setEnabled(False)  # 禁用只显示切片选项
                self.show_only_slice_checkbox.setChecked(False)  # 取消只显示切片选项
                if self.current_actor:
                    self.current_actor.SetVisibility(True)  # 确保模型可见
            self.vtk_widget.GetRenderWindow().Render()

    def toggle_show_only_slice(self, state):
        """切换只显示切片状态"""
        if self.current_actor:
            if state == 2:  # Qt.Checked
                self.current_actor.SetVisibility(False)  # 隐藏模型
            else:
                self.current_actor.SetVisibility(True)  # 显示模型
            self.vtk_widget.GetRenderWindow().Render()

    def setup_cutter(self):
        """设置切片器"""
        if not self.current_actor:
            return

        # 获取模型边界
        self.bounds = self.current_actor.GetBounds()
        
        # 创建切割平面
        self.plane = vtk.vtkPlane()
        self.plane.SetNormal(1, 0, 0)  # 默认X轴方向
        self.plane.SetOrigin((self.bounds[0] + self.bounds[1])/2, 0, 0)
        
        # 创建切割器
        self.cutter = vtk.vtkCutter()
        self.cutter.SetInputConnection(self.current_actor.GetMapper().GetInputConnection(0, 0))
        self.cutter.SetCutFunction(self.plane)
        
        # 创建切割线的映射器
        cutter_mapper = vtk.vtkPolyDataMapper()
        cutter_mapper.SetInputConnection(self.cutter.GetOutputPort())
        
        # 创建切割线的actor
        self.cutter_actor = vtk.vtkActor()
        self.cutter_actor.SetMapper(cutter_mapper)
        self.cutter_actor.GetProperty().SetColor(0, 0, 0)  # 黑色切割线
        self.cutter_actor.GetProperty().SetLineWidth(2)
        
        # 添加到渲染器
        self.renderer.AddActor(self.cutter_actor)

    def update_cutter(self, index):
        """更新切片方向"""
        if not self.plane or not self.bounds:
            return
            
        if index == 0:  # X轴
            self.plane.SetNormal(1, 0, 0)
            self.plane.SetOrigin((self.bounds[0] + self.bounds[1])/2, 0, 0)
        elif index == 1:  # Y轴
            self.plane.SetNormal(0, 1, 0)
            self.plane.SetOrigin(0, (self.bounds[2] + self.bounds[3])/2, 0)
        elif index == 2:  # Z轴
            self.plane.SetNormal(0, 0, 1)
            self.plane.SetOrigin(0, 0, (self.bounds[4] + self.bounds[5])/2)
            
        self.vtk_widget.GetRenderWindow().Render()

    def update_cutter_position(self, value):
        """更新切片位置"""
        if not self.plane or not self.bounds:
            return
            
        # 将滑块值(0-100)映射到模型边界范围内
        direction = self.direction_combo.currentIndex()
        if direction == 0:  # X轴
            pos = self.bounds[0] + (self.bounds[1] - self.bounds[0]) * value / 100
            self.plane.SetOrigin(pos, 0, 0)
        elif direction == 1:  # Y轴
            pos = self.bounds[2] + (self.bounds[3] - self.bounds[2]) * value / 100
            self.plane.SetOrigin(0, pos, 0)
        elif direction == 2:  # Z轴
            pos = self.bounds[4] + (self.bounds[5] - self.bounds[4]) * value / 100
            self.plane.SetOrigin(0, 0, pos)
            
        self.position_label.setText(f"切片位置: {pos:.2f}")
        self.vtk_widget.GetRenderWindow().Render()

    def change_display_mode(self, index):
        """改变显示模式"""
        if self.current_actor:
            prop = self.current_actor.GetProperty()
            
            if index == 0:  # 实体
                prop.SetRepresentationToSurface()
                prop.SetOpacity(1.0)
                prop.SetPointSize(1)
                prop.SetLineWidth(1)
                prop.EdgeVisibilityOff()
                prop.VertexVisibilityOff()
                
            elif index == 1:  # 线框
                prop.SetRepresentationToWireframe()
                prop.SetOpacity(1.0)
                prop.SetPointSize(1)
                prop.SetLineWidth(1)
                prop.EdgeVisibilityOff()
                prop.VertexVisibilityOff()
                
            elif index == 2:  # 点云
                prop.SetRepresentationToPoints()
                prop.SetOpacity(1.0)
                prop.SetPointSize(3)  # 增大点的大小以便更好地显示
                prop.SetLineWidth(1)
                prop.EdgeVisibilityOff()
                prop.VertexVisibilityOff()
                
            elif index == 3:  # 透明
                prop.SetRepresentationToSurface()
                prop.SetOpacity(0.5)
                prop.SetPointSize(1)
                prop.SetLineWidth(1)
                prop.EdgeVisibilityOff()
                prop.VertexVisibilityOff()
                
            elif index == 4:  # 实体+线框
                prop.SetRepresentationToSurface()
                prop.SetOpacity(1.0)
                prop.SetPointSize(1)
                prop.SetLineWidth(1)
                prop.EdgeVisibilityOn()
                prop.SetEdgeColor(0, 0, 0)  # 黑色边缘
                prop.VertexVisibilityOff()
                
            elif index == 5:  # 实体+点
                prop.SetRepresentationToSurface()
                prop.SetOpacity(1.0)
                prop.SetPointSize(3)
                prop.SetLineWidth(1)
                prop.EdgeVisibilityOff()
                prop.VertexVisibilityOn()
                prop.SetVertexColor(0, 0, 0)  # 黑色顶点
                
            elif index == 6:  # 线框+点
                prop.SetRepresentationToWireframe()
                prop.SetOpacity(1.0)
                prop.SetPointSize(3)
                prop.SetLineWidth(1)
                prop.EdgeVisibilityOff()
                prop.VertexVisibilityOn()
                prop.SetVertexColor(0, 0, 0)  # 黑色顶点
                
            elif index == 7:  # 实体+线框+点
                prop.SetRepresentationToSurface()
                prop.SetOpacity(1.0)
                prop.SetPointSize(3)
                prop.SetLineWidth(1)
                prop.EdgeVisibilityOn()
                prop.SetEdgeColor(0, 0, 0)  # 黑色边缘
                prop.VertexVisibilityOn()
                prop.SetVertexColor(0, 0, 0)  # 黑色顶点
            
            self.current_actor.SetProperty(prop)
            self.vtk_widget.GetRenderWindow().Render()

    def update_speed(self, value):
        self.style.SetMotionFactor(float(value))

    def toggle_axes(self, state):
        if state == 2:  # Qt.Checked
            self.orientation_marker.SetEnabled(1)
        else:
            self.orientation_marker.SetEnabled(0)
        self.vtk_widget.GetRenderWindow().Render()

    def toggle_colorbar(self, state):
        """切换颜色图例显示状态"""
        if self.current_actor:
            # 确保颜色图例被添加到渲染器
            if state == 2:  # Qt.Checked
                self.colorbar.SetVisibility(True)
                # 重新设置颜色图例的属性
                self.colorbar.SetTitle("到原点距离")
                self.colorbar.SetNumberOfLabels(5)
                self.colorbar.SetLabelFormat("%.2f")
                self.colorbar.SetPosition(0.8, 0.1)
                self.colorbar.SetWidth(0.1)
                self.colorbar.SetHeight(0.8)
                
                # 重新设置字体样式
                title_prop = vtk.vtkTextProperty()
                title_prop.SetFontFamily(2)  # 使用等线字体
                title_prop.SetFontSize(14)
                title_prop.SetBold(True)
                title_prop.SetColor(0.0, 0.0, 0.0)
                title_prop.SetJustificationToCentered()
                title_prop.SetVerticalJustificationToTop()
                self.colorbar.SetTitleTextProperty(title_prop)
                
                label_prop = vtk.vtkTextProperty()
                label_prop.SetFontFamily(2)  # 使用等线字体
                label_prop.SetFontSize(12)
                label_prop.SetBold(False)
                label_prop.SetColor(0.0, 0.0, 0.0)
                label_prop.SetJustificationToCentered()
                self.colorbar.SetLabelTextProperty(label_prop)
                
                # 确保颜色图例使用正确的查找表
                mapper = self.current_actor.GetMapper()
                if mapper:
                    self.colorbar.SetLookupTable(mapper.GetLookupTable())
            else:
                self.colorbar.SetVisibility(False)
            
            # 强制更新渲染
            self.vtk_widget.GetRenderWindow().Render()
            print(f"Colorbar visibility set to: {state == 2}")

    def open_file(self):
        print("Opening file dialog...")
        file_name, _ = QFileDialog.getOpenFileName(self, "打开 VTK 文件", "", "VTK Files (*.vtk)")
        if file_name:
            print(f"Selected file: {file_name}")
            self.load_vtk_file(file_name)

    def load_vtk_file(self, file_name):
        print(f"Loading VTK file: {file_name}")
        # 清除现有的 actor
        self.renderer.RemoveAllViewProps()

        # 创建 VTK 读取器
        reader = vtk.vtkPolyDataReader()
        reader.SetFileName(file_name)
        reader.Update()

        # 获取点数据
        polydata = reader.GetOutput()
        points = polydata.GetPoints()
        num_points = points.GetNumberOfPoints()

        # 计算每个点到原点的距离
        distances = vtk.vtkFloatArray()
        distances.SetName("Distances")
        distances.SetNumberOfValues(num_points)

        for i in range(num_points):
            point = points.GetPoint(i)
            # 计算到原点的距离
            distance = np.sqrt(point[0]**2 + point[1]**2 + point[2]**2)
            distances.SetValue(i, distance)

        # 将距离数组添加到点数据中
        polydata.GetPointData().SetScalars(distances)

        # 创建颜色映射表
        lut = vtk.vtkLookupTable()
        lut.SetNumberOfTableValues(256)
        lut.Build()

        # 创建 mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)
        
        # 设置颜色映射
        mapper.ScalarVisibilityOn()
        mapper.SetLookupTable(lut)
        mapper.SetScalarRange(distances.GetRange())
        
        # 创建 actor
        self.current_actor = vtk.vtkActor()
        self.current_actor.SetMapper(mapper)
        
        # 设置颜色图例
        self.colorbar.SetLookupTable(lut)
        self.colorbar.SetVisibility(False)  # 初始状态隐藏
        self.colorbar.SetTitle("到原点距离")
        self.colorbar.SetNumberOfLabels(5)
        self.colorbar.SetLabelFormat("%.2f")
        self.colorbar.SetPosition(0.8, 0.1)
        self.colorbar.SetWidth(0.1)
        self.colorbar.SetHeight(0.8)
        
        # 设置字体样式
        title_prop = vtk.vtkTextProperty()
        title_prop.SetFontFamily(2)  # 使用等线字体
        title_prop.SetFontSize(14)
        title_prop.SetBold(True)
        title_prop.SetColor(0.0, 0.0, 0.0)
        title_prop.SetJustificationToCentered()
        title_prop.SetVerticalJustificationToTop()
        self.colorbar.SetTitleTextProperty(title_prop)
        
        label_prop = vtk.vtkTextProperty()
        label_prop.SetFontFamily(2)  # 使用等线字体
        label_prop.SetFontSize(12)
        label_prop.SetBold(False)
        label_prop.SetColor(0.0, 0.0, 0.0)
        label_prop.SetJustificationToCentered()
        self.colorbar.SetLabelTextProperty(label_prop)

        # 添加 actor 到渲染器
        self.renderer.AddActor(self.current_actor)
        
        # 确保颜色图例被添加到渲染器
        if not self.renderer.HasViewProp(self.colorbar):
            self.renderer.AddActor2D(self.colorbar)

        # 重新添加坐标轴
        self.orientation_marker.SetEnabled(self.axes_checkbox.isChecked())

        # 重置相机
        self.renderer.ResetCamera()
        # 刷新显示
        self.vtk_widget.GetRenderWindow().Render()
        print("VTK file loaded successfully!")

def main():
    print("Starting application...")
    app = QApplication(sys.argv)
    viewer = VTKViewer()
    viewer.show()
    print("Application started!")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 