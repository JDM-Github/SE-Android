from kivy.app import App
from kivy.uix.image import Image
from kivy.graphics import Rectangle, Color
from kivy.uix.scrollview import ScrollView
import numpy as np

class MatrixGraph(Image):
    def __init__(self, matrix, **kwargs):
        super().__init__(**kwargs)
        self.matrix = np.array(matrix)
        self.cell_size = 60  # Increased size for better visibility
        self.cols = len(self.matrix[0])
        self.rows = len(self.matrix)
        self.size = (self.cell_size * self.cols, self.cell_size * self.rows)  # Ensure widget size fits matrix
        self.draw_matrix()

    def draw_matrix(self):
        # Debug: Print matrix
        print("Drawing Matrix:")
        print(self.matrix)
        
        max_value = np.max(self.matrix)  # Get the maximum value for color scaling
        print("Max Value:", max_value)

        for row in range(self.rows):
            for col in range(self.cols):
                value = self.matrix[row, col]

                # Map the matrix value to a color (for now, just use fixed color for visibility)
                Color(0, 1, 0)  # Bright Green to make the cells visible

                # Calculate the position for each cell (bottom-left corner)
                x = col * self.cell_size
                y = (self.rows - 1 - row) * self.cell_size  # Invert the y-axis to match the expected matrix layout
                Rectangle(pos=(x, y), size=(self.cell_size, self.cell_size))

                print("TSE")

    def on_size(self, *args):
        self.draw_matrix()  # Redraw the matrix if the widget size changes


class MatrixApp(App):
    def build(self):
        # Example matrix
        matrix = [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9]
        ]
        
        matrix_graph = MatrixGraph(matrix)

        # Wrap in a ScrollView to make it scrollable if it's large
        scroll_view = ScrollView(size_hint=(None, None), size=(400, 400))
        scroll_view.add_widget(matrix_graph)

        return scroll_view


if __name__ == '__main__':
    MatrixApp().run()
