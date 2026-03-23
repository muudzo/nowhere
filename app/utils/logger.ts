// System Logger Utility
export type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';

export interface LoggerConfig {
  minLevel?: LogLevel;
}

export class Logger {
  private config: LoggerConfig;

  constructor(config: LoggerConfig = { minLevel: 'DEBUG' }) {
    this.config = config;
  }

  debug(message: string, data?: any) {
    if (this.config.minLevel === 'DEBUG') {
      console.debug('[DEBUG]', message, data || '');
    }
  }

  info(message: string, data?: any) {
    const levels = ['DEBUG', 'INFO'];
    if (levels.includes(this.config.minLevel!)) {
      console.info('[INFO]', message, data || '');
    }
  }

  warn(message: string, data?: any) {
    const levels = ['DEBUG', 'INFO', 'WARN'];
    if (levels.includes(this.config.minLevel!)) {
      console.warn('[WARN]', message, data || '');
    }
  }
}
}
