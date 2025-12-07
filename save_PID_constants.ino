#include <util/atomic.h>

#define ENCA 2
#define ENCB 3
#define PWM_PIN 9
#define DIR_PIN 8

// Calibrated counts per revolution
const float COUNTS_PER_REVOLUTION = 349.2;

volatile long encoderCount = 0;
volatile unsigned long lastPulseTime = 0;
volatile unsigned long pulseInterval = 0;
volatile int lastDirection = 1;

float rpmFiltered = 0;
float rpmPrev = 0;  // For low-pass filter
float eintegral = 0;
float eprev = 0;  // For derivative term

void onEncoderA() {
  unsigned long currentTime = micros();
  
  // Determine direction
  int direction;
  if (digitalRead(ENCA) == digitalRead(ENCB)) {
    encoderCount++;
    direction = 1;
  } else {
    encoderCount--;
    direction = -1;
  }
  
  // Calculate time between pulses
  pulseInterval = currentTime - lastPulseTime;
  lastPulseTime = currentTime;
  lastDirection = direction;
}

void setup() {
  Serial.begin(115200);
  
  // Set pin modes BEFORE setting outputs
  pinMode(PWM_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(ENCA, INPUT_PULLUP);
  pinMode(ENCB, INPUT_PULLUP);

  // Immediately set motor outputs to 0
  digitalWrite(DIR_PIN, LOW);
  analogWrite(PWM_PIN, 0);
  
  delay(1000);  // Wait to ensure motor is fully stopped

  attachInterrupt(digitalPinToInterrupt(ENCA), onEncoderA, CHANGE);
}

void loop() {

  // int pwr = 20;
  // int dir = 1; // 1=forward, 0=backward
  // setMotor(dir, pwr, PWM_PIN, DIR_PIN);

  // Calculate RPM using time between pulses
  static unsigned long lastPrint = 0;
  unsigned long now = millis();
  
  if (now - lastPrint >= 100) {
    lastPrint = now;
    
    unsigned long interval;
    int dir;
    unsigned long timeSinceLastPulse;
    
    noInterrupts();
    interval = pulseInterval;
    dir = lastDirection;
    timeSinceLastPulse = micros() - lastPulseTime;
    interrupts();
    
    float rpm = 0;
    
    // If motor is stopped (no pulse in last 200ms), RPM is 0
    if (timeSinceLastPulse > 200000) {
      rpm = 0;
    }
    // Calculate RPM from pulse interval
    else if (interval > 0) {
      // interval is time for ONE encoder count in microseconds
      // Convert to counts per second, then to RPM
      float countsPerSecond = 1000000.0 / interval;
      rpm = (countsPerSecond / COUNTS_PER_REVOLUTION) * 60.0 * dir;
    }
    
    // Apply exponential smoothing filter
    float alpha = 0.3;
    rpmFiltered = alpha * rpm + (1 - alpha) * rpmFiltered;
    
    // Apply low-pass filter (25 Hz cutoff)
    float v2Filt = 0.854 * rpmFiltered + 0.0728 * rpm + 0.0728 * rpmPrev;
    rpmPrev = rpm;
    rpmFiltered = v2Filt;

    // Set a target rpm
    float targetRpm = 60.0;

    float kp = 0.5;
    float ki = 3.0;
    float kd = 0.001;  // Start with a small value

    float e = targetRpm - rpmFiltered;
    eintegral += e * 0.1;  // Integral term with dt=0.1s
    float dedt = (e - eprev) / 0.1;  // Derivative term
    float u = kp*e + ki*eintegral + kd*dedt;
    
    eprev = e;  // Save error for next iteration

    // Determine direction based on control signal
    if (u < 0) {
      dir = 0;  // Backward
    } else {
      dir = 1;  // Forward
    }

    int pwmVal = (int)fabs(u);
    if (pwmVal > 255) {
      pwmVal = 255;
    }

    setMotor(dir, pwmVal, PWM_PIN, DIR_PIN);

    // Output for Serial Plotter
    Serial.print("Target:");
    Serial.print(targetRpm, 2);
    Serial.print(",Filtered:");
    Serial.println(rpmFiltered, 2);
  }
}

void setMotor(int dir, int pwmVal, int pwm, int dirPin) {
  digitalWrite(DIR_PIN, dir);
  analogWrite(PWM_PIN, pwmVal);
}