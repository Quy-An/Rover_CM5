import time

from motor import (
    inverse_kinematics,
    omega_to_pwm,
    control_motor
)


# ==========================================================
# MOTOR LOOP
# ==========================================================

def motor_control_loop(
        vehicle,
        stop_event=None):

    print("🚗 [Motor] Controller started")

    while True:

        if stop_event and stop_event.is_set():

            control_motor(
                0.0,
                0.0
            )

            break

        with vehicle.lock:

            armed = vehicle.armed

            vx = vehicle.vx_cmd

            wz = vehicle.wz_cmd

            last_cmd = (
                vehicle.last_manual_control
            )

        # =====================================
        # FAILSAFE
        # =====================================

        if time.time() - last_cmd > 1.0:

            vx = 0.0
            wz = 0.0

        # =====================================
        # DISARM
        # =====================================

        if not armed:

            control_motor(
                0.0,
                0.0
            )

            time.sleep(0.05)

            continue

        # =====================================
        # INVERSE KINEMATICS
        # =====================================

        w_l, w_r = inverse_kinematics(
            vx,
            wz
        )

        # =====================================
        # RAD/S -> PWM
        # =====================================

        pwm_l, pwm_r = omega_to_pwm(
            w_l,
            w_r
        )

        # =====================================
        # OUTPUT
        # =====================================

        control_motor(
            pwm_l,
            pwm_r
        )

        time.sleep(0.02)

    print("🛑 Motor controller stopped")