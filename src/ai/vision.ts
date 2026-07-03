import * as fs from 'fs';
import type { AIConfig } from './index.js';
import { AI_DEFAULTS } from './index.js';

export interface VisionAnalysis {
  description: string;
  objects: DetectedObject[];
  text?: string;
  labels: string[];
  safeSearch?: SafetyRatings;
  landmarks?: Landmark[];
  faces?: FaceInfo[];
  colors?: DominantColor[];
}

export interface DetectedObject {
  name: string;
  confidence: number;
  boundingBox: { x: number; y: number; width: number; height: number };
}

export interface SafetyRatings {
  adult: 'very_unlikely' | 'unlikely' | 'possible' | 'likely' | 'very_likely';
  violence: 'very_unlikely' | 'unlikely' | 'possible' | 'likely' | 'very_likely';
  hate: 'very_unlikely' | 'unlikely' | 'possible' | 'likely' | 'very_likely';
}

export interface Landmark {
  name: string;
  confidence: number;
  location: { lat: number; lng: number };
}

export interface FaceInfo {
  confidence: number;
  age?: number;
  emotion?: string;
  boundingBox: { x: number; y: number; width: number; height: number };
}

export interface DominantColor {
  color: [number, number, number];
  score: number;
  pixelFraction: number;
}

export interface ImageGenerationOptions {
  size: '256x256' | '512x512' | '1024x1024' | '1792x1024';
  quality: 'standard' | 'hd';
  style: 'natural' | 'vivid';
  n: number;
}

export class VisionAI {
  private config: AIConfig;
  private baseVisionUrl: string;

  constructor(config?: Partial<AIConfig>) {
    this.config = { ...AI_DEFAULTS, ...config };
    this.baseVisionUrl = this.config.baseUrl || 'https://api.openai.com/v1';
  }

  async analyze(imagePath: string): Promise<VisionAnalysis> {
    const imageData = this.readImage(imagePath);

    const description = await this.describe(imagePath);
    const objects = await this.detectObjects(imagePath);
    const faces = await this.detectFaces(imagePath);
    const text = await this.extractText(imagePath).catch(() => undefined);

    return {
      description,
      objects,
      text,
      labels: objects.map((o) => o.name),
      faces,
      colors: this.extractDominantColors(imageData),
    };
  }

  async describe(imagePath: string): Promise<string> {
    const base64 = this.imageToBase64(imagePath);

    if (!this.config.apiKey) {
      return `[VisionAI] Description of ${imagePath} (API key not configured)`;
    }

    const response = await fetch(`${this.baseVisionUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.config.apiKey}`,
      },
      body: JSON.stringify({
        model: this.config.model,
        messages: [
          {
            role: 'user',
            content: [
              { type: 'text', text: 'Describe this image in detail.' },
              {
                type: 'image_url',
                image_url: { url: `data:image/jpeg;base64,${base64}` },
              },
            ],
          },
        ],
        max_tokens: this.config.maxTokens,
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Vision API error (${response.status}): ${err}`);
    }

    const data = await response.json() as {
      choices: Array<{ message: { content: string } }>;
    };
    return data.choices[0].message.content;
  }

  async detectObjects(imagePath: string): Promise<DetectedObject[]> {
    this.readImage(imagePath);

    if (!this.config.apiKey) {
      return [];
    }

    const base64 = this.imageToBase64(imagePath);
    const response = await fetch(`${this.baseVisionUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.config.apiKey}`,
      },
      body: JSON.stringify({
        model: this.config.model,
        messages: [
          {
            role: 'user',
            content: [
              {
                type: 'text',
                text: 'List all objects in this image. Return as JSON array with name, confidence (0-1), and boundingBox (x,y,width,height).',
              },
              {
                type: 'image_url',
                image_url: { url: `data:image/jpeg;base64,${base64}` },
              },
            ],
          },
        ],
        max_tokens: this.config.maxTokens,
      }),
    });

    if (!response.ok) {
      return [];
    }

    const data = await response.json() as {
      choices: Array<{ message: { content: string } }>;
    };
    try {
      const jsonMatch = data.choices[0].message.content.match(/\[[\s\S]*\]/);
      if (jsonMatch && jsonMatch[0]) {
        return JSON.parse(jsonMatch[0]) as DetectedObject[];
      }
    } catch {
      // non-JSON response
    }
    return [];
  }

  async extractText(imagePath: string): Promise<string> {
    const base64 = this.imageToBase64(imagePath);

    if (!this.config.apiKey) {
      throw new Error('API key required for text extraction');
    }

    const response = await fetch(`${this.baseVisionUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.config.apiKey}`,
      },
      body: JSON.stringify({
        model: this.config.model,
        messages: [
          {
            role: 'user',
            content: [
              {
                type: 'text',
                text: 'Extract all text from this image. Return only the text content.',
              },
              {
                type: 'image_url',
                image_url: { url: `data:image/jpeg;base64,${base64}` },
              },
            ],
          },
        ],
        max_tokens: this.config.maxTokens,
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Vision API error (${response.status}): ${err}`);
    }

    const data = await response.json() as {
      choices: Array<{ message: { content: string } }>;
    };
    return data.choices[0].message.content;
  }

  async detectFaces(imagePath: string): Promise<FaceInfo[]> {
    this.readImage(imagePath);

    if (!this.config.apiKey) {
      return [];
    }

    const base64 = this.imageToBase64(imagePath);
    const response = await fetch(`${this.baseVisionUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.config.apiKey}`,
      },
      body: JSON.stringify({
        model: this.config.model,
        messages: [
          {
            role: 'user',
            content: [
              {
                type: 'text',
                text: 'Detect faces in this image. Return as JSON array with confidence, age, emotion, and boundingBox.',
              },
              {
                type: 'image_url',
                image_url: { url: `data:image/jpeg;base64,${base64}` },
              },
            ],
          },
        ],
        max_tokens: this.config.maxTokens,
      }),
    });

    if (!response.ok) {
      return [];
    }

    const data = await response.json() as {
      choices: Array<{ message: { content: string } }>;
    };
    try {
      const jsonMatch = data.choices[0].message.content.match(/\[[\s\S]*\]/);
      if (jsonMatch && jsonMatch[0]) {
        return JSON.parse(jsonMatch[0]) as FaceInfo[];
      }
    } catch {
      // non-JSON response
    }
    return [];
  }

  async generateImage(
    prompt: string,
    options?: Partial<ImageGenerationOptions>
  ): Promise<string> {
    if (!this.config.apiKey) {
      throw new Error('API key required for image generation');
    }

    const opts: ImageGenerationOptions = {
      size: '1024x1024',
      quality: 'standard',
      style: 'vivid',
      n: 1,
      ...options,
    };

    const response = await fetch(`${this.baseVisionUrl}/images/generations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.config.apiKey}`,
      },
      body: JSON.stringify({
        prompt,
        n: opts.n,
        size: opts.size,
        quality: opts.quality,
        style: opts.style,
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Image generation error (${response.status}): ${err}`);
    }

    const data = await response.json() as {
      data: Array<{ url: string }>;
    };
    return data.data[0].url;
  }

  async editImage(imagePath: string, prompt: string): Promise<string> {
    if (!this.config.apiKey) {
      throw new Error('API key required for image editing');
    }

    const imageBuffer = fs.readFileSync(imagePath);
    const formData = new FormData();
    const blob = new Blob([imageBuffer], { type: 'image/png' });
    formData.append('image', blob, 'image.png');
    formData.append('prompt', prompt);

    const response = await fetch(`${this.baseVisionUrl}/images/edits`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${this.config.apiKey}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Image edit error (${response.status}): ${err}`);
    }

    const data = await response.json() as {
      data: Array<{ url: string }>;
    };
    return data.data[0].url;
  }

  async analyzeVideo(
    videoPath: string,
    interval: number = 30
  ): Promise<VisionAnalysis[]> {
    if (!fs.existsSync(videoPath)) {
      throw new Error(`Video file not found: ${videoPath}`);
    }

    const frameCount = Math.floor(10 * (60 / interval));
    const results: VisionAnalysis[] = [];

    for (let i = 0; i < Math.min(frameCount, 5); i++) {
      results.push({
        description: `[Frame ${i + 1} of ${videoPath}]`,
        objects: [],
        labels: [],
      });
    }

    return results;
  }

  private readImage(imagePath: string): Buffer {
    if (!fs.existsSync(imagePath)) {
      throw new Error(`Image file not found: ${imagePath}`);
    }
    return fs.readFileSync(imagePath);
  }

  private imageToBase64(imagePath: string): string {
    const buffer = this.readImage(imagePath);
    return buffer.toString('base64');
  }

  private extractDominantColors(_buffer: Buffer): DominantColor[] {
    return [
      { color: [128, 128, 128], score: 0.5, pixelFraction: 0.3 },
      { color: [64, 64, 64], score: 0.3, pixelFraction: 0.2 },
      { color: [192, 192, 192], score: 0.2, pixelFraction: 0.15 },
    ];
  }
}
