import matplotlib.pyplot as plt
import matplotlib.patches as patches
import string


class Stripboard:
    def __init__(self, N):
        self.N = N
        self.fig, self.ax = plt.subplots(figsize=(8, 8))

        self._configure_plot()
        self._draw_conductive_strips()
        self._draw_holes()
        self._annotate_board()

    def _configure_plot(self):
        self.ax.set_xlim(0, self.N)
        self.ax.set_ylim(0, self.N)
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.axis("off")

    def _draw_conductive_strips(self):
        self.strip_height = 0.8
        for y in range(self.N):
            rect = patches.Rectangle(
                (0, y + (1 - self.strip_height) / 2),
                self.N,
                self.strip_height,
                facecolor="black",
                alpha=0.25,
            )
            self.ax.add_patch(rect)

    def _draw_holes(self):
        for x in range(self.N):
            for y in range(self.N):
                circle = patches.Circle((x + 0.5, y + 0.5), radius=0.2, color="white")
                self.ax.add_patch(circle)

    def _annotate_board(self):
        for x in range(self.N):
            self.ax.text(
                x + 0.5,
                -0.5,
                str(x + 1),
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
                color="black",
            )
            self.ax.text(
                x + 0.5,
                self.N + 0.5,
                str(x + 1),
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
                color="black",
            )

        for y in range(self.N):
            self.ax.text(
                -0.5,
                y + 0.5,
                string.ascii_uppercase[y],
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
                color="black",
            )
            self.ax.text(
                self.N + 0.5,
                y + 0.5,
                string.ascii_uppercase[y],
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
                color="black",
            )

    def add_component(self, start, end, color="red", name=None):
        # Drawing a component as a line between two holes with rounded ends
        self.ax.plot(
            [start[0] + 0.5, end[0] + 0.5],
            [start[1] + 0.5, end[1] + 0.5],
            color=color,
            linewidth=7.5,
            solid_capstyle="round",
        )
        self.ax.plot(
            [start[0] + 0.5, end[0] + 0.5],
            [start[1] + 0.5, end[1] + 0.5],
            ".",
            color="k",
            markersize=25,
        )

        if name:
            label_pos_x = start[0]  # - 0.5
            label_offset_y = 0.5  # (end[1] - start[1]) / 2 + 0.75 + (0.15 * self.N) # Offset the label for better visibility
            self.ax.text(
                label_pos_x,
                start[1] + label_offset_y,
                name,
                color="k",
                fontsize=14,
                ha="center",
                va="center",
                rotation=90,
            )

    def add_ic(self, start, size, name=None):
        x, y = start
        height = size / 2  # since the extent in y is half of the total pin count
        width = 2  # two units wide for the IC representation

        # Draw IC rectangle
        ic_rect = patches.Rectangle(
            (x - 0.5, y - 0.5),
            width,
            height,
            facecolor="grey",
            edgecolor="black",
            linewidth=3,
            alpha=1.0,
        )
        self.ax.add_patch(ic_rect)

        self.add_break(col=x, between=(y + 0 - 1, y + size // 2))

        if name:
            label_pos_x = x  # - 0.75
            label_pos_y = y + height / 2  # centering the label vertically
            self.ax.text(
                label_pos_x,
                label_pos_y,
                name,
                ha="right",
                va="center",
                fontsize=14,
                color="black",
                rotation=90,
            )

    def add_break(self, col, between):
        x_coord = col + 0.5  # centering the x-coordinate with the hole
        y_start = between[0]
        y_end = between[1]

        self.ax.plot(
            [x_coord, x_coord],
            [y_start, y_end],
            color="black",
            linewidth=7.5,
            linestyle="--",
        )

    def show(self):
        plt.gca().invert_yaxis()
        plt.show()


if __name__ == "__main__":

    board = Stripboard(10)
    board.add_component((1, 2), (1, 5), color="red", name="R1")
    board.add_break(4, (3, 5))
    board.add_ic(
        (6, 2), 8, name="OpAmp"
    )  # Add an IC of 8 pins starting from position (6, 2)
    board.show()
