import * as fs from 'fs';
import type { AIConfig } from './index.js';
import { AI_DEFAULTS } from './index.js';

export interface SpeechRecognitionResult {
  text: string;
  confidence: number;
  segments: SpeechSegment[];
  language: string;
  duration: number;
}

export interface SpeechSegment {
  text: string;
  startTime: number;
  endTime: number;
  confidence: number;
  speaker?: string;
}

export interface SynthesisOptions {
  voice: string;
  speed: number;
  pitch: number;
  format: 'mp3' | 'wav' | 'ogg' | 'flac';
  language: string;
}

export class SpeechAI {
  private config: AIConfig;
  private baseUrl: string;

  constructor(config?: Partial<AIConfig>) {
    this.config = { ...AI_DEFAULTS, ...config };
    this.baseUrl = this.config.baseUrl || 'https://api.openai.com/v1';
  }

  async transcribe(
    audioPath: string,
    language?: string
  ): Promise<SpeechRecognitionResult> {
    if (!fs.existsSync(audioPath)) {
      throw new Error(`Audio file not found: ${audioPath}`);
    }

    if (!this.config.apiKey) {
      return this.simulateTranscription(audioPath, language);
    }

    const audioBuffer = fs.readFileSync(audioPath);
    const formData = new FormData();
    const blob = new Blob([audioBuffer], { type: 'audio/mpeg' });
    formData.append('file', blob, 'audio.mp3');
    formData.append('model', 'whisper-1');
    if (language) {
      formData.append('language', language);
    }

    const response = await fetch(`${this.baseUrl}/audio/transcriptions`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${this.config.apiKey}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Transcription error (${response.status}): ${err}`);
    }

    const data = await response.json() as {
      text: string;
      segments?: Array<{
        text: string;
        start: number;
        end: number;
        confidence: number;
        speaker?: string;
      }>;
      language?: string;
      duration?: number;
    };

    return {
      text: data.text,
      confidence: 0.95,
      segments: (data.segments || []).map((s) => ({
        text: s.text,
        startTime: s.start,
        endTime: s.end,
        confidence: s.confidence,
        speaker: s.speaker,
      })),
      language: data.language || language || 'en',
      duration: data.duration || 0,
    };
  }

  async *transcribeStream(
    audioBuffer: Buffer
  ): AsyncGenerator<SpeechSegment, void, unknown> {
    if (!this.config.apiKey) {
      yield {
        text: 'Simulated streaming transcription',
        startTime: 0,
        endTime: 1,
        confidence: 0.9,
      };
      return;
    }

    const formData = new FormData();
    const blob = new Blob([new Uint8Array(audioBuffer)], { type: 'audio/mpeg' });
    formData.append('file', blob, 'audio.mp3');
    formData.append('model', 'whisper-1');

    const response = await fetch(`${this.baseUrl}/audio/transcriptions`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${this.config.apiKey}`,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Stream transcription error (${response.status})`);
    }

    const data = await response.json() as {
      text: string;
      segments?: Array<{
        text: string;
        start: number;
        end: number;
        confidence: number;
        speaker?: string;
      }>;
    };

    if (data.segments) {
      for (const seg of data.segments) {
        yield {
          text: seg.text,
          startTime: seg.start,
          endTime: seg.end,
          confidence: seg.confidence,
          speaker: seg.speaker,
        };
      }
    } else {
      yield {
        text: data.text,
        startTime: 0,
        endTime: 1,
        confidence: 0.95,
      };
    }
  }

  async synthesize(
    text: string,
    options?: Partial<SynthesisOptions>
  ): Promise<Buffer> {
    if (!this.config.apiKey) {
      return this.simulateSynthesis(text);
    }

    const opts: SynthesisOptions = {
      voice: 'alloy',
      speed: 1.0,
      pitch: 1.0,
      format: 'mp3',
      language: 'en',
      ...options,
    };

    const response = await fetch(`${this.baseUrl}/audio/speech`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.config.apiKey}`,
      },
      body: JSON.stringify({
        model: 'tts-1',
        input: text,
        voice: opts.voice,
        speed: opts.speed,
        response_format: opts.format,
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Synthesis error (${response.status}): ${err}`);
    }

    const arrayBuffer = await response.arrayBuffer();
    return Buffer.from(arrayBuffer);
  }

  async detectLanguage(audioPath: string): Promise<string> {
    if (!fs.existsSync(audioPath)) {
      throw new Error(`Audio file not found: ${audioPath}`);
    }

    if (!this.config.apiKey) {
      return 'en';
    }

    const audioBuffer = fs.readFileSync(audioPath);
    const formData = new FormData();
    const blob = new Blob([audioBuffer], { type: 'audio/mpeg' });
    formData.append('file', blob, 'audio.mp3');
    formData.append('model', 'whisper-1');

    const response = await fetch(`${this.baseUrl}/audio/translations`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${this.config.apiKey}`,
      },
      body: formData,
    });

    if (!response.ok) {
      return 'en';
    }

    const data = await response.json() as { text: string };
    return this.detectLanguageFromText(data.text);
  }

  async identifySpeakers(audioPath: string): Promise<string[]> {
    if (!fs.existsSync(audioPath)) {
      throw new Error(`Audio file not found: ${audioPath}`);
    }

    if (!this.config.apiKey) {
      return ['Speaker 1', 'Speaker 2'];
    }

    const result = await this.transcribe(audioPath);
    const speakers = new Set<string>();
    for (const seg of result.segments) {
      if (seg.speaker) {
        speakers.add(seg.speaker);
      }
    }

    return speakers.size > 0 ? Array.from(speakers) : ['Speaker 1'];
  }

  private simulateTranscription(
    _audioPath: string,
    language?: string
  ): SpeechRecognitionResult {
    return {
      text: 'This is a simulated transcription of the audio file.',
      confidence: 0.85,
      segments: [
        {
          text: 'This is a simulated transcription',
          startTime: 0,
          endTime: 2.5,
          confidence: 0.85,
          speaker: 'Speaker 1',
        },
        {
          text: 'of the audio file.',
          startTime: 2.5,
          endTime: 4.0,
          confidence: 0.9,
          speaker: 'Speaker 1',
        },
      ],
      language: language || 'en',
      duration: 4.0,
    };
  }

  private simulateSynthesis(_text: string): Buffer {
    const header = Buffer.from([
      0x49, 0x44, 0x33, 0x03, 0x00, 0x00, 0x00,
    ]);
    const silentFrame = Buffer.alloc(1024, 0);
    return Buffer.concat([header, silentFrame]);
  }

  private detectLanguageFromText(text: string): string {
    const langPatterns: Record<string, RegExp> = {
      en: /\b(the|is|are|was|were|this|that|and|for|with)\b/i,
      es: /\b(el|la|los|las|es|son|esta|este|y|por|con)\b/i,
      fr: /\b(le|la|les|est|sont|cet|cette|et|pour|avec)\b/i,
      de: /\b(der|die|das|ist|sind|dieser|diese|und|für|mit)\b/i,
    };

    for (const [lang, pattern] of Object.entries(langPatterns)) {
      if (pattern.test(text)) {
        return lang;
    }
    }
    return 'en';
  }
}
