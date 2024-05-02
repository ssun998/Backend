import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QCheckBox, QVBoxLayout, QComboBox
import mplcursors
import sys

# Read the CSV file
data = pd.read_csv(r"C:\Users\SWEEKRITHI SHETTY\Desktop\Demo\track_data1.csv")

# Constants
overall_ratio = 3.5 
bevel_ratio = 0.667
final_drive_ratios = {
    1: 0.304,
    2: 0.375,
    3: 0.340,
    4: 0.316,
    5: 0.404,
    6: 0.426
}
gear_ratios_1st = [0.343, 0.389, 0.412, 0.441, 0.471]
gear_ratios_rest = [0.485, 0.500, 0.516, 0.533, 0.548, 0.567, 0.581, 0.593, 0.613,
                    0.633, 0.654, 0.679, 0.704, 0.720, 0.741, 0.750, 0.760, 0.769, 0.778,
                    0.786, 0.792, 0.800, 0.808, 0.815, 0.821, 0.828, 0.833, 0.840, 0.846,
                    0.852, 0.857, 0.864, 0.870, 0.875, 0.880, 0.885, 0.889, 0.893, 0.897,
                    0.900, 0.905, 0.909, 0.920, 0.929, 0.935]

# Function to calculate gear ratio considering different overall ratios
def calculate_gear_ratio(row, tire_diameter, trans_gear):
    overall_ratio = 1 / (final_drive_ratios[trans_gear] * bevel_ratio)
    denominator = ((row["EngineSpeed[rpm]"] / overall_ratio) * (tire_diameter * 3.1416) * 60)
    gear_ratio = (row["VehicleSpeed[mph]"] * 5280 * 12) / denominator if denominator != 0 else None
    return gear_ratio

    

# Function to find nearest matched gear ratio and calculate confidence factor
def find_nearest_gear_ratio_with_confidence(calculated_ratio, predefined_ratios):
    nearest_ratio = min(predefined_ratios, key=lambda x: abs(x - calculated_ratio))
    confidence = 1 - abs(nearest_ratio - calculated_ratio) / max(predefined_ratios)
    return nearest_ratio, confidence

# Apply the function to get nearest matched gear ratio and confidence factor
def get_nearest_matched_gear_with_confidence(calculated_ratio):
    if calculated_ratio is None:
        return None, None
    elif calculated_ratio <= gear_ratios_1st[-1]:
        nearest_ratio, confidence = find_nearest_gear_ratio_with_confidence(calculated_ratio, gear_ratios_1st)
    else:
        nearest_ratio, confidence = find_nearest_gear_ratio_with_confidence(calculated_ratio, gear_ratios_rest)
    return nearest_ratio, confidence

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QGridLayout(self.central_widget)

        # Add the tire diameter selection combo box
        self.tire_diameter_combo = QComboBox(self)
        self.tire_diameter_combo.addItem("Road and Street Course: 27.9 in")
        self.tire_diameter_combo.addItem("Oval: 26.9 in")
        self.tire_diameter_combo.currentIndexChanged.connect(self.update_gear_ratio)
        self.layout.addWidget(self.tire_diameter_combo, 0, 0, 1, 2)

        # Create the checkbox layout for car names
        self.checkbox_layout = QVBoxLayout()
        self.layout.addLayout(self.checkbox_layout, 1, 0)

        # Plotting
        self.fig, self.ax = plt.subplots(figsize=(20, 20))
        self.canvas = FigureCanvas(self.fig)  # Create canvas
        self.layout.addWidget(self.canvas, 1, 1, 1, 1)

        # Connect mplcursors to display tooltip
        mplcursors.cursor(hover=True).connect("add", self.tooltip)
        # Initialize annotations cache
        self.annotations_cache = {}

        # Initial plot data
        self.plot_data(tire_diameter=27.9)  # Default tire diameter for road courses

    def tooltip(self, sel, car_data):
        idx = sel.target.index
        target = car_data.iloc[idx]
        engine_speed = target["EngineSpeed[rpm]"]
        vehicle_speed = target["VehicleSpeed[mph]"]
        nearest_gear_ratio = target["NearestMatchedGearRatio"]
        confidence_factor = target["ConfidenceFactor"]
        
        # Check if annotation exists in the cache, if not, create a new one and cache it
        if idx not in self.annotations_cache:
            annotation = self.ax.annotate("", xy=(0, 0), xytext=(10, 10),
                                          textcoords="offset points", ha="left", va="bottom",
                                          bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=0.5),
                                          arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"))
            self.annotations_cache[idx] = annotation
        else:
            annotation = self.annotations_cache[idx]
        
        # Update the text and position of the annotation
        annotation.set_text(f"Engine Speed: {engine_speed}\n"
                            f"Vehicle Speed: {vehicle_speed}\n"
                            f"Nearest Matched Gear Ratio: {nearest_gear_ratio}\n"
                            f"Confidence Factor: {confidence_factor}\n")
        annotation.xy = (sel.target[0], sel.target[1])
        
        # Redraw the canvas
        self.canvas.draw()

    # Function to update the gear ratio based on tire diameter selection
    def update_gear_ratio(self):
        index = self.tire_diameter_combo.currentIndex()
        tire_diameter = 27.9 if index == 0 else 26.9
        trans_gear = 1  # Default transmission gear (can be adjusted as needed)
        self.plot_data(tire_diameter, trans_gear)

    # Plot data function
    def plot_data(self, tire_diameter, trans_gear=1):
        # Clear previous plot
        self.ax.clear()

        # Make a copy of the original data to avoid modifying it
        self.data_above_4000 = data.copy()
        
        try:
            # Convert CarName column to string if necessary
            self.data_above_4000["CarName"] = self.data_above_4000["CarName"].astype(str)
            self.data_above_4000["CalculatedGearRatio"] = self.data_above_4000.apply(calculate_gear_ratio, tire_diameter=tire_diameter, trans_gear=trans_gear, axis=1)
            self.data_above_4000["NearestMatchedGearRatio"], self.data_above_4000["ConfidenceFactor"] = zip(*self.data_above_4000["CalculatedGearRatio"].apply(get_nearest_matched_gear_with_confidence))
            
            # Iterate over unique car names
            car_names = self.data_above_4000["CarName"].unique()
            colors = plt.cm.get_cmap('hsv', len(car_names))  # Define colors for each car name
            
            for i, car_name in enumerate(car_names):
                # Filter data for the current car name
                car_data = self.data_above_4000[self.data_above_4000["CarName"] == car_name]
                print(car_data)
                # Plot scatter points
                scatter = self.ax.scatter(car_data["EngineSpeed[rpm]"], car_data["VehicleSpeed[mph]"], c=[colors(i)] * len(car_data),  s=0.05)

                # Calculate and plot polynomial regression
                self.polyfit_and_plot(car_data["EngineSpeed[rpm]"], car_data["VehicleSpeed[mph]"], degree=3, color=colors(i), car_name=car_name)

                # Connect mplcursors to display tooltip
                cursor = mplcursors.cursor(scatter, hover=True, multiple=False)
                cursor.connect("add", lambda sel, car_data=car_data: self.tooltip(sel, car_data))

            # Set labels and legend
            self.ax.set_xlabel("Engine Speed (rpm)")
            self.ax.set_ylabel("Vehicle Speed (mph)")
            self.ax.set_title("Engine Speed (rpm) vs Vehicle Speed (mph)")
            self.ax.legend()
            self.ax.grid(True)
            self.canvas.draw()
        except Exception as e:
            print("Error occurred during plot_data:", e)



    # Function to calculate polynomial regression
    def polyfit_and_plot(self, x, y, degree, color, car_name):
        coeffs = np.polyfit(x, y, degree)
        poly_eq = np.poly1d(coeffs)
        x_values = np.linspace(min(x), max(x), 100)
        y_values = poly_eq(x_values)
        self.ax.plot(x_values, y_values, color=color, label=car_name)

# Create the application instance
app = QApplication(sys.argv)
window = MainWindow()
window.setGeometry(100, 100, 800, 600)  # Set initial window size

# Add checkboxes for each car name
car_names = data["CarName"].astype(str).unique()
for car_name in car_names:
    checkbox = QCheckBox(car_name, window)
    checkbox.setChecked(True)
    checkbox.stateChanged.connect(window.plot_data)
    window.checkbox_layout.addWidget(checkbox)

window.show()
sys.exit(app.exec_())
