/**
 * Logging utility using Winston
 */

import winston from 'winston';
import { mkdir } from 'fs/promises';
import { dirname } from 'path';
import type { ILogger } from '../types/index.js';

const { combine, timestamp, printf, colorize, errors } = winston.format;

/**
 * Custom log format
 */
const logFormat = printf(({ level, message, timestamp, ...metadata }) => {
  let msg = `${timestamp} [${level}]: ${message}`;

  // Add metadata if present
  if (Object.keys(metadata).length > 0) {
    msg += ` ${JSON.stringify(metadata, null, 2)}`;
  }

  return msg;
});

/**
 * Create logger instance
 */
export async function createLogger(
  level: string = 'info',
  filePath: string = './logs/trading.log'
): Promise<ILogger> {
  // Ensure log directory exists
  try {
    await mkdir(dirname(filePath), { recursive: true });
  } catch (error) {
    console.error('Failed to create log directory:', error);
  }

  const logger = winston.createLogger({
    level,
    format: combine(
      errors({ stack: true }),
      timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
      logFormat
    ),
    transports: [
      // Console transport with colors
      new winston.transports.Console({
        format: combine(
          colorize(),
          timestamp({ format: 'HH:mm:ss' }),
          logFormat
        ),
      }),
      // File transport for all logs
      new winston.transports.File({
        filename: filePath,
        maxsize: 10 * 1024 * 1024, // 10MB
        maxFiles: 5,
      }),
      // Separate file for errors
      new winston.transports.File({
        filename: filePath.replace('.log', '-error.log'),
        level: 'error',
        maxsize: 10 * 1024 * 1024,
        maxFiles: 5,
      }),
    ],
  });

  return {
    debug: (message: string, meta?: unknown) => logger.debug(message, meta),
    info: (message: string, meta?: unknown) => logger.info(message, meta),
    warn: (message: string, meta?: unknown) => logger.warn(message, meta),
    error: (message: string, meta?: unknown) => logger.error(message, meta),
  };
}

/**
 * Default logger instance (initialized lazily)
 */
let defaultLogger: ILogger | null = null;

export async function getLogger(): Promise<ILogger> {
  if (!defaultLogger) {
    defaultLogger = await createLogger();
  }
  return defaultLogger;
}

/**
 * Initialize logger with custom config
 */
export async function initLogger(level: string, filePath: string): Promise<ILogger> {
  defaultLogger = await createLogger(level, filePath);
  return defaultLogger;
}
