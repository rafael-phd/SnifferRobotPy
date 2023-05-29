import matplotlib.pyplot as plt
import numpy as np


def is_value(values):
    return [
        (
            (isinstance(value, np.ndarray) and value.ndim == 1) or
            (
                    isinstance(value, np.ndarray) and value.ndim == 0 and
                    (
                            np.issubdtype(value.dtype, np.integer) or
                            np.issubdtype(value.dtype, np.floating)
                    )
            ) or
            (isinstance(value, (float, int)))
        )
        for value in values
    ]


def update_plot(fig, ax, line, new_x, new_y):
    assert isinstance(fig, plt.Figure)
    assert isinstance(ax, plt.Axes)
    assert isinstance(line, plt.Line2D)
    assert all(is_value([new_x, new_y]))

    existing_x = line.get_xdata()
    existing_y = line.get_ydata()

    # Append new data to the existing data
    updated_x = np.hstack([existing_x, new_x])
    updated_y = np.hstack([existing_y, new_y])
    assert len(updated_x) == len(updated_y)

    # Update the data of the plot
    line.set_data(updated_x, updated_y)

    # Adjust the plot limits (optional)
    ax.relim()
    ax.autoscale_view()

    # Redraw the plot
    fig.canvas.draw()
    plt.pause(0.01)
