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
}
