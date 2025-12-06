import pigpio
import time
import threading

ENCA = 17
ENCB = 27
PWM_PIN = 18
DIR_PIN = 23

pi = pigpio.pi()
pi.set_mode(ENCA, pigpio.INPUT)
pi.set_mode(ENCB, pigpio.INPUT)
pi.set_pull_up_down(ENCA, pigpio.PUD_UP)
pi.set_pull_up_down(ENCB, pigpio.PUD_UP)

pi.set_mode(PWM_PIN, pigpio.OUTPUT)
pi.set_mode(DIR_PIN, pigpio.OUTPUT)
pi.write(DIR_PIN, 1)

PPR = 20
target_rpm = 30

encoder_count = 0
rpm = 0

Kp = 1.2
Ki = 0.4

integral = 0
running = True

def encoder_cb(gpio, level, tick):
    global encoder_count
    a = pi.read(ENCA)
    b = pi.read(ENCB)
    if a == b:
        encoder_count += 1
    else:
        encoder_count -= 1

pi.callback(ENCA, pigpio.EITHER_EDGE, encoder_cb)
pi.callback(ENCB, pigpio.EITHER_EDGE, encoder_cb)

def rpm_task():
    global encoder_count, rpm
    last = time.time()
    while running:
        time.sleep(0.1)
        now = time.time()
        dt = now - last
        last = now

        count = encoder_count
        encoder_count = 0

        revs = (count / PPR) / dt
        rpm = revs * 60

def control_task():
    global integral, rpm
    while running:
        error = target_rpm - rpm
        integral += error * 0.1

        duty = Kp * error + Ki * integral
        duty = max(0, min(100, duty))

        pi.hardware_PWM(PWM_PIN, 20000, int(duty * 10000))

        print(f"RPM = {rpm:.1f} | duty = {duty:.1f}%")
        time.sleep(0.1)

t1 = threading.Thread(target=rpm_task, daemon=True)
t2 = threading.Thread(target=control_task, daemon=True)
t1.start()
t2.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    running = False
    pi.hardware_PWM(PWM_PIN, 0, 0)
    pi.stop()
