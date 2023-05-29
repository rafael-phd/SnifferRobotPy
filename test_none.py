import numpy as np
import time
import threading
from snifferpy import RobotClient, CommandType
import matplotlib.pyplot as plt


if __name__ == '__main__':
    cli = RobotClient(host='10.0.0.11', port=8080)

    cli.set_setpoints(setpoints_type=CommandType.NONE, num_measurements=5)

    fig, axs, lines = cli.plot_measurements(interval=np.zeros(0, dtype=int))

    thread1 = threading.Thread(target=cli.talk_and_close)

    thread1.start()

    display_cnt = 0
    while thread1.is_alive():
        measurements_cnt = cli.measurements_cnt
        if display_cnt < measurements_cnt:
            cli.update_measurements(fig, axs, lines, interval=slice(display_cnt, measurements_cnt))
            display_cnt = measurements_cnt
        time.sleep(1)
    if display_cnt < cli.measurements_cnt:
        cli.update_measurements(fig, axs, lines, interval=slice(display_cnt, cli.measurements_cnt))
    plt.show()
