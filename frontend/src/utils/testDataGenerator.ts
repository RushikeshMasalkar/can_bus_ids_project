// =============================================================================
// testDataGenerator.ts - Simulated CAN Bus Traffic Generator
// =============================================================================

import type { CANFrame } from '../types';

/**
 * Simulates realistic CAN bus traffic for testing the dashboard.
 * Generates a mix of normal and attack patterns.
 */
export class TestDataGenerator {
  private isRunning = false;
  private intervalId: ReturnType<typeof setInterval> | null = null;
  private frameCount = 0;

  // Realistic CAN IDs from the vocabulary (normal traffic)
  private normalCANIds = [
    '0316', '018f', '0260', '02a0', '0329', '0350', '0370',
    '0430', '043f', '0440', '04b1', '04f0', '0545', '05a0',
    '0608', '0690', '06a1', '071b', '07cf', '07d9', '07e8'
  ];

  // Attack pattern: Unknown CAN IDs (these will be mapped to UNK by backend)
  private attackCANIds = [
    '0000', '0001', 'ffff', 'aaaa', 'bbbb'
  ];

  private sendCallback: ((frame: CANFrame) => void) | null = null;

  /**
   * Start generating test data
   * @param callback Function to call with each generated frame
   * @param interval Milliseconds between frames (default: 100ms = 10 frames/sec)
   * @param attackProbability Probability of generating an attack frame (0-1)
   */
  start(
    callback: (frame: CANFrame) => void,
    interval = 100,
    attackProbability = 0.05 // 5% chance of attack
  ): void {
    if (this.isRunning) {
      console.warn('[TestGen] Already running');
      return;
    }

    this.sendCallback = callback;
    this.isRunning = true;
    this.frameCount = 0;

    console.log('[TestGen] Starting test data generation');
    console.log(`[TestGen] Interval: ${interval}ms | Attack probability: ${attackProbability * 100}%`);

    this.intervalId = setInterval(() => {
      this.generateFrame(attackProbability);
    }, interval);
  }

  /**
   * Stop generating test data
   */
  stop(): void {
    if (!this.isRunning) {
      return;
    }

    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }

    this.isRunning = false;
    console.log(`[TestGen] Stopped. Generated ${this.frameCount} frames`);
  }

  /**
   * Check if generator is running
   */
  get running(): boolean {
    return this.isRunning;
  }

  /**
   * Get total frames generated
   */
  get count(): number {
    return this.frameCount;
  }

  /**
   * Generate a single frame
   */
  private generateFrame(attackProbability: number): void {
    if (!this.sendCallback) return;

    const isAttack = Math.random() < attackProbability;

    // Select CAN ID
    const canId = isAttack
      ? this.attackCANIds[Math.floor(Math.random() * this.attackCANIds.length)]
      : this.normalCANIds[Math.floor(Math.random() * this.normalCANIds.length)];

    // Generate random data bytes
    const data = Array.from({ length: 8 }, () =>
      Math.floor(Math.random() * 256).toString(16).padStart(2, '0')
    );

    const frame: CANFrame = {
      can_id: canId,
      timestamp: Date.now() / 1000,
      dlc: 8,
      data,
    };

    this.frameCount++;
    this.sendCallback(frame);
  }

  /**
   * Inject a burst of attack frames (for testing)
   */
  injectAttackBurst(count = 10, interval = 50): void {
    console.log(`[TestGen] Injecting ${count} attack frames`);

    let sent = 0;
    const burstInterval = setInterval(() => {
      if (sent >= count) {
        clearInterval(burstInterval);
        return;
      }

      if (!this.sendCallback) {
        clearInterval(burstInterval);
        return;
      }

      const canId = this.attackCANIds[Math.floor(Math.random() * this.attackCANIds.length)];
      const data = Array.from({ length: 8 }, () =>
        Math.floor(Math.random() * 256).toString(16).padStart(2, '0')
      );

      this.sendCallback({
        can_id: canId,
        timestamp: Date.now() / 1000,
        dlc: 8,
        data,
      });

      sent++;
    }, interval);
  }
}

// Export singleton instance
export const testDataGenerator = new TestDataGenerator();
