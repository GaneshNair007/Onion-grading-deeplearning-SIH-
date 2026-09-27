// Web Audio API synthesizer for physical acoustic tap simulation

class AudioSynthesizer {
  private ctx: AudioContext | null = null
  private isMuted: boolean = false

  private getContext(): AudioContext {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
      this.ctx = new AudioCtx()
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume()
    }
    return this.ctx
  }

  public setMuted(muted: boolean) {
    this.isMuted = muted
  }

  public getIsMuted(): boolean {
    return this.isMuted
  }

  public playChirp(type: 'solid' | 'rot' | 'hollow' = 'solid') {
    if (this.isMuted) return

    try {
      const ctx = this.getContext()
      const now = ctx.currentTime

      // Main impact oscillator (solenoid impact transient)
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()

      // Damping envelope gain
      const filter = ctx.createBiquadFilter()

      if (type === 'solid') {
        // High resonance sharp ping (220 Hz down to 180 Hz)
        osc.type = 'sine'
        osc.frequency.setValueAtTime(240, now)
        osc.frequency.exponentialRampToValueAtTime(190, now + 0.12)

        filter.type = 'bandpass'
        filter.frequency.setValueAtTime(210, now)
        filter.Q.setValueAtTime(5, now)

        gain.gain.setValueAtTime(0.4, now)
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25)
      } else if (type === 'rot') {
        // Dampened mushy thud (95 Hz heavy decay)
        osc.type = 'triangle'
        osc.frequency.setValueAtTime(110, now)
        osc.frequency.exponentialRampToValueAtTime(70, now + 0.08)

        filter.type = 'lowpass'
        filter.frequency.setValueAtTime(120, now)
        filter.Q.setValueAtTime(1, now)

        gain.gain.setValueAtTime(0.5, now)
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12) // fast acoustic damping
      } else {
        // Hollow core hollow echo (150 Hz double peak resonance)
        osc.type = 'sine'
        osc.frequency.setValueAtTime(175, now)
        osc.frequency.exponentialRampToValueAtTime(130, now + 0.2)

        filter.type = 'peaking'
        filter.frequency.setValueAtTime(155, now)
        filter.Q.setValueAtTime(8, now)
        filter.gain.setValueAtTime(6, now)

        gain.gain.setValueAtTime(0.35, now)
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35)
      }

      osc.connect(filter)
      filter.connect(gain)
      gain.connect(ctx.destination)

      osc.start(now)
      osc.stop(now + 0.4)
    } catch {
      // Audio context fallback if blocked by browser policy
    }
  }
}

export const soundSynth = new AudioSynthesizer()
