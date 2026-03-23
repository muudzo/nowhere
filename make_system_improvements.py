import os
import subprocess

hook_dir = "app/utils"
hook_file_path = f"{hook_dir}/logger.ts"

os.makedirs(hook_dir, exist_ok=True)

subprocess.run(["git", "checkout", "-b", "feature/system-improvements-logger"])

# Commit 1
content_1 = """// System Logger Utility
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
"""
with open(hook_file_path, "w") as f: f.write(content_1)
subprocess.run(["git", "add", hook_file_path])
subprocess.run(["git", "commit", "-m", "feat(sys-logger): initialize base Logger class structure"])

# Commit 2
content_2 = content_1.replace("  }", "  }\n\n  debug(message: string, data?: any) {\n    if (this.config.minLevel === 'DEBUG') {\n      console.debug('[DEBUG]', message, data || '');\n    }\n  }\n}")
with open(hook_file_path, "w") as f: f.write(content_2)
subprocess.run(["git", "add", hook_file_path])
subprocess.run(["git", "commit", "-m", "feat(sys-logger): add debug logging method"])

# Commit 3
content_3 = content_2.replace("  }\n}", "  }\n\n  info(message: string, data?: any) {\n    const levels = ['DEBUG', 'INFO'];\n    if (levels.includes(this.config.minLevel!)) {\n      console.info('[INFO]', message, data || '');\n    }\n  }\n}")
with open(hook_file_path, "w") as f: f.write(content_3)
subprocess.run(["git", "add", hook_file_path])
subprocess.run(["git", "commit", "-m", "feat(sys-logger): add info logging method"])

# Commit 4
content_4 = content_3.replace("  }\n}", "  }\n\n  warn(message: string, data?: any) {\n    const levels = ['DEBUG', 'INFO', 'WARN'];\n    if (levels.includes(this.config.minLevel!)) {\n      console.warn('[WARN]', message, data || '');\n    }\n  }\n}")
with open(hook_file_path, "w") as f: f.write(content_4)
subprocess.run(["git", "add", hook_file_path])
subprocess.run(["git", "commit", "-m", "feat(sys-logger): add warn logging method"])

# Commit 5
content_5 = content_4.replace("  }\n}", "  }\n\n  error(message: string, data?: any) {\n    console.error('[ERROR]', message, data || '');\n  }\n}")
with open(hook_file_path, "w") as f: f.write(content_5)
subprocess.run(["git", "add", hook_file_path])
subprocess.run(["git", "commit", "-m", "feat(sys-logger): add error logging method"])

# Commit 6
content_6 = content_5.replace("  private config", "  private config: LoggerConfig;\n\n  private getTimestamp(): string {\n    return new Date().toISOString();\n  }\n")
content_6 = content_6.replace("['[DEBUG]',", "[`[DEBUG] [${this.getTimestamp()}]`,")
content_6 = content_6.replace("['[INFO]',", "[`[INFO] [${this.getTimestamp()}]`,")
content_6 = content_6.replace("['[WARN]',", "[`[WARN] [${this.getTimestamp()}]`,")
content_6 = content_6.replace("['[ERROR]',", "[`[ERROR] [${this.getTimestamp()}]`,")
with open(hook_file_path, "w") as f: f.write(content_6)
subprocess.run(["git", "add", hook_file_path])
subprocess.run(["git", "commit", "-m", "feat(sys-logger): add timestamp generation to logs"])

# Commit 7
content_7 = content_6.replace("export interface LoggerConfig {", "export interface LoggerConfig {\n  enabled?: boolean;")
content_7 = content_7.replace("minLevel: 'DEBUG'", "minLevel: 'DEBUG', enabled: process.env.NODE_ENV !== 'production'")
content_7 = content_7.replace("debug(message: string", "debug(message: string, ...args: any[]) {\n    if (!this.config.enabled) return;")
content_7 = content_7.replace("info(message: string", "info(message: string, ...args: any[]) {\n    if (!this.config.enabled) return;")
content_7 = content_7.replace("warn(message: string", "warn(message: string, ...args: any[]) {\n    if (!this.config.enabled) return;")
content_7 = content_7.replace("error(message: string", "error(message: string, ...args: any[]) {\n    if (!this.config.enabled) return;")
with open(hook_file_path, "w") as f: f.write(content_7)
subprocess.run(["git", "add", hook_file_path])
subprocess.run(["git", "commit", "-m", "feat(sys-logger): add environment checks and enabled flag"])

# Commit 8
content_8 = content_7.replace("export interface LoggerConfig {", "export interface LoggerConfig {\n  globalTags?: string[];")
content_8 = content_8.replace("return new Date()", "const tags = this.config.globalTags ? ` [${this.config.globalTags.join(',')}]` : '';\n    return new Date().toISOString() + tags;")
with open(hook_file_path, "w") as f: f.write(content_8)
subprocess.run(["git", "add", hook_file_path])
subprocess.run(["git", "commit", "-m", "feat(sys-logger): add global context/tags support"])

# Commit 9
content_9 = content_8.replace("private config", "private history: any[] = [];\n  private config")
content_9 = content_9.replace("console.debug", "this.history.push({ level: 'DEBUG', message });\n      console.debug")
content_9 = content_9.replace("console.info", "this.history.push({ level: 'INFO', message });\n      console.info")
content_9 = content_9.replace("console.warn", "this.history.push({ level: 'WARN', message });\n      console.warn")
content_9 = content_9.replace("console.error", "this.history.push({ level: 'ERROR', message });\n      console.error")
content_9 = content_9.replace("\n}", "\n\n  getHistory() {\n    return this.history;\n  }\n}")
with open(hook_file_path, "w") as f: f.write(content_9)
subprocess.run(["git", "add", hook_file_path])
subprocess.run(["git", "commit", "-m", "feat(sys-logger): add log history array tracking"])

# Commit 10
content_10 = content_9 + "\nexport const systemLogger = new Logger({ globalTags: ['SYSTEM'] });\n"
with open(hook_file_path, "w") as f: f.write(content_10)
subprocess.run(["git", "add", hook_file_path])
subprocess.run(["git", "commit", "-m", "feat(sys-logger): export singleton systemLogger instance"])

print("Successfully generated 10 commits for system improvements!")
