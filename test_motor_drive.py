import numpy as np
import time
import threading
from snifferpy import RobotClient, CommandType
import matplotlib.pyplot as plt


if __name__ == '__main__':
    cli = RobotClient(host='10.0.0.11', port=8080)

    u_left = np.hstack((np.zeros(2), 200 * np.ones(15), np.zeros(5)))
    u_right = np.hstack((np.zeros(2), -200 * np.ones(15), np.zeros(5)))
    cli.set_setpoints(setpoints_type=CommandType.MOTOR_CTRL,
                      setpoints=np.hstack((u_left[:, None], u_right[:, None])))

    fig, axs, lines = cli.plot_measurements(interval=np.zeros(0, dtype=int))

    # Create threads for each function
    thread1 = threading.Thread(target=cli.talk_and_close)

    # Start the threads
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
