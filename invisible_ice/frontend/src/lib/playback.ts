/**
 * Pure playback state machine — no DOM, no timers. The React hook feeds it
 * requestAnimationFrame deltas; everything about play/pause/seek/speed/loop
 * lives here so it can be unit-tested exactly.
 */

export interface PlaybackOptions {
  loop?: boolean;
}

export class PlaybackEngine {
  private frameCount: number;
  private readonly frameRate: number;
  private readonly loop: boolean;

  playing = false;
  speed = 1;
  /** Fractional frame index in [0, frameCount - 1]. */
  cursor = 0;

  constructor(frameCount: number, frameRate: number, options: PlaybackOptions = {}) {
    if (frameCount < 1) throw new Error("frameCount must be >= 1");
    if (frameRate <= 0) throw new Error("frameRate must be positive");
    this.frameCount = frameCount;
    this.frameRate = frameRate;
    this.loop = options.loop ?? true;
  }

  get lastFrame(): number {
    return this.frameCount - 1;
  }

  play(): void {
    // Replaying from the end restarts the clip.
    if (this.cursor >= this.lastFrame) this.cursor = 0;
    this.playing = true;
  }

  pause(): void {
    this.playing = false;
  }

  toggle(): void {
    this.playing ? this.pause() : this.play();
  }

  seek(cursor: number): void {
    this.cursor = Math.min(Math.max(cursor, 0), this.lastFrame);
  }

  setSpeed(speed: number): void {
    if (speed <= 0) throw new Error("speed must be positive");
    this.speed = speed;
  }

  /** Swap in a new clip length, clamping the cursor into range. */
  setFrameCount(frameCount: number): void {
    if (frameCount < 1) throw new Error("frameCount must be >= 1");
    this.frameCount = frameCount;
    this.seek(this.cursor);
  }

  /**
   * Advance by `dtSeconds` of wall-clock time; returns the new cursor.
   * At the end of the clip: wrap when looping, otherwise pause exactly on
   * the last frame.
   */
  tick(dtSeconds: number): number {
    if (!this.playing) return this.cursor;
    this.cursor += dtSeconds * this.frameRate * this.speed;
    if (this.cursor > this.lastFrame) {
      if (this.loop) {
        this.cursor = this.cursor % this.lastFrame;
      } else {
        this.cursor = this.lastFrame;
        this.playing = false;
      }
    }
    return this.cursor;
  }
}
