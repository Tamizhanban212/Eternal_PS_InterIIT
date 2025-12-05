#include <util/atomic.h>

// -------- PIN DEFINITIONS ----------
#define ENCA 2      // Encoder A
#define ENCB 3      // Encoder B
#define PWM_PIN 5   // MDD20A PWM
#define DIR_PIN 4   // MDD20A DIR
// ----------------------------------

// Globals
volatile long encoderCount = 0;

long prevT = 0;
long prevCount = 0;

float rpmFiltered = 0;
float eintegral = 0;

void setup() {
  Serial.begin(115200);

  pinMode(ENCA, INPUT);
  pinMode(ENCB, INPUT);
  pinMode(PWM_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);

  attachInterrupt(digitalPinToInterrupt(ENCA), readEncoder, RISING);

  // Optional: titles for Serial Plotter legend
  Serial.println("raw filtered target");
}

void loop() {

  // -------- SAFE ENCODER READ --------
  long count;
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
    count = encoderCount;
  }

  long currT = micros();
  float dt = (currT - prevT) / 1e6;
  prevT = currT;

  long delta = count - prevCount;
  prevCount = count;

  // Convert counts/sec → RPM (for 600 CPR)
  float cps = delta / dt;
  float rpm = (cps / 1278.75 ) * 60.0;

  // -------- FILTER RPM (VERY IMPORTANT) --------
  float alpha = 0.2;  // smoothing factor
  rpmFiltered = alpha * rpm + (1 - alpha) * rpmFiltered;

  // -------- TARGET RPM --------
  float target = 100;

  // -------- PID CONTROL --------
  float kp = 1.5;
  float ki = 2.5;

  float error = target - rpmFiltered;

  // Provisional control output
  float u = kp * error + ki * eintegral;

  // Anti-windup: update integral only if not saturated
  if (abs(u) < 255) {
    eintegral += error * dt;
    u = kp * error + ki * eintegral;
  }

  // Direction + PWM clamp
  int dir = (u >= 0) ? 1 : -1;
  int pwm = abs((int)u);
  if (pwm > 255) pwm = 255;

  setMotor(dir, pwm);

  // -------- SERIAL PLOTTER OUTPUT --------
  Serial.print(rpm);          // raw RPM
  Serial.print(" ");
  Serial.print(rpmFiltered);  // filtered RPM
  Serial.print(" ");
  Serial.println(target);     // target RPM

  delay(20); // stable sampling
}

// ------------------ MOTOR CONTROL ------------------
void setMotor(int dir, int pwm) {
  analogWrite(PWM_PIN, pwm);
  digitalWrite(DIR_PIN, dir == 1 ? HIGH : LOW);
}

// ------------------ ENCODER ISR --------------------
void readEncoder() {
  int b = digitalRead(ENCB);
  encoderCount += (b == HIGH) ? 1 : -1;
}
