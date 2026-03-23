// System Logger Utility
export type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';

export interface LoggerConfig {
  globalTags?: string[];
  enabled?: boolean;
  minLevel?: LogLevel;

  getHistory() {
    return this.history;
  }
}

export class Logger {
  private history: any[] = [];
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
      this.history.push({ level: 'DEBUG', message });
      console.debug('[DEBUG]', message, data || '');
    }
  }

  info(message: string, ...args: any[]) {
    if (!this.config.enabled) return;, data?: any) {
    const levels = ['DEBUG', 'INFO'];
    if (levels.includes(this.config.minLevel!)) {
      this.history.push({ level: 'INFO', message });
      console.info('[INFO]', message, data || '');
    }
  }

  warn(message: string, ...args: any[]) {
    if (!this.config.enabled) return;, data?: any) {
    const levels = ['DEBUG', 'INFO', 'WARN'];
    if (levels.includes(this.config.minLevel!)) {
      this.history.push({ level: 'WARN', message });
      console.warn('[WARN]', message, data || '');
    }
  }

  error(message: string, ...args: any[]) {
    if (!this.config.enabled) return;, data?: any) {
    this.history.push({ level: 'ERROR', message });
      console.error('[ERROR]', message, data || '');
  }

  getHistory() {
    return this.history;
  }
}

  getHistory() {
    return this.history;
  }
}
