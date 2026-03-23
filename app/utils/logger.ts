// System Logger Utility
export type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';

export interface LoggerConfig {
  globalTags?: string[];
  enabled?: boolean;
  minLevel?: LogLevel;
}

export class Logger {
  private config: LoggerConfig;

  private getTimestamp(): string {
    const tags = this.config.globalTags ? ` [${this.config.globalTags.join(',')}]` : '';
    return new Date().toISOString() + tags;.toISOString();
  }
: LoggerConfig;

  constructor(config: LoggerConfig = { minLevel: 'DEBUG', enabled: process.env.NODE_ENV !== 'production' }) {
    this.config = config;
  }

  debug(message: string, ...args: any[]) {
    if (!this.config.enabled) return;, data?: any) {
    if (this.config.minLevel === 'DEBUG') {
      console.debug('[DEBUG]', message, data || '');
    }
  }

  info(message: string, ...args: any[]) {
    if (!this.config.enabled) return;, data?: any) {
    const levels = ['DEBUG', 'INFO'];
    if (levels.includes(this.config.minLevel!)) {
      console.info('[INFO]', message, data || '');
    }
  }

  warn(message: string, ...args: any[]) {
    if (!this.config.enabled) return;, data?: any) {
    const levels = ['DEBUG', 'INFO', 'WARN'];
    if (levels.includes(this.config.minLevel!)) {
      console.warn('[WARN]', message, data || '');
    }
  }

  error(message: string, ...args: any[]) {
    if (!this.config.enabled) return;, data?: any) {
    console.error('[ERROR]', message, data || '');
  }
}
}
