import numpy as np
import time
import threading
from snifferpy import RobotClient, CommandType
import matplotlib.pyplot as plt


if __name__ == '__main__':
    cli = RobotClient(host='10.0.0.11', port=8080)

    kp_left = 0.0
    ki_left = 1.0
    kd_left = 0.0
    tau_left = 0.0
    kp_right = 0.0
    ki_right = 1.0
    kd_right = 0.0
    tau_right = 0.0
    v_left = np.hstack((np.zeros(2), 200 * np.ones(5), np.zeros(5)))
    v_right = np.hstack((np.zeros(2), -200 * np.ones(5), np.zeros(5)))

    cli.connect()

    cli.set_setpoints(setpoints_type=CommandType.PID_LEFT,
                      setpoints=np.array([[kp_left, ki_left, kd_left, tau_left]]))
    cli.talk()

    cli.set_setpoints(setpoints_type=CommandType.PID_RIGHT,
                      setpoints=np.array([[kp_right, ki_right, kd_right, tau_right]]))
    cli.talk()

    cli.set_setpoints(setpoints_type=CommandType.SPEED_CTRL,
                      setpoints=np.hstack((v_left[:, None], v_right[:, None])))

    fig, axs, lines = cli.plot_measurements(interval=np.zeros(0, dtype=int))

    thread1 = threading.Thread(target=cli.talk)

    cli.talk()
    thread1.start()

    display_cnt = 0
    while thread1.is_alive():
        measurements_cnt = cli.measurements_cnt
        if display_cnt < measurements_cnt:
            cli.update_measurements(fig, axs, lines, interval=slice(display_cnt, measurements_cnt))
            display_cnt = measurements_cnt
        time.sleep(2)
    cli.close()
    if display_cnt < cli.measurements_cnt:
        cli.update_measurements(fig, axs, lines, interval=slice(display_cnt, cli.measurements_cnt))
    plt.show()
