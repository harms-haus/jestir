/**
 * Jestir Node.js API
 *
 * This module provides a Node.js API interface for all Jestir CLI functionality,
 * enabling web applications to use Jestir's story generation capabilities.
 *
 * @fileoverview Main API module for Jestir story generation
 * @version 1.0.0
 * @author Jestir Team
 */

import { spawn } from 'child_process';
import { promisify } from 'util';
import { readFile, writeFile, access } from 'fs/promises';
import { join, resolve } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = new URL('.', import.meta.url).pathname;

/**
 * Session management for parallel story generation
 */
class SessionManager {
    constructor() {
        this.sessions = new Map();
        this.sessionCounter = 0;
    }

    /**
     * Create a new session
     * @returns {string} Session ID
     */
    createSession() {
        const sessionId = `session_${++this.sessionCounter}_${Date.now()}`;
        this.sessions.set(sessionId, {
            id: sessionId,
            created: new Date(),
            operations: new Map(),
            status: 'active'
        });
        return sessionId;
    }

    /**
     * Get session by ID
     * @param {string} sessionId - Session identifier
     * @returns {Object|null} Session object or null if not found
     */
    getSession(sessionId) {
        return this.sessions.get(sessionId) || null;
    }

    /**
     * Add operation to session
     * @param {string} sessionId - Session identifier
     * @param {string} operationId - Operation identifier
     * @param {Object} operation - Operation details
     */
    addOperation(sessionId, operationId, operation) {
        const session = this.getSession(sessionId);
        if (session) {
            session.operations.set(operationId, {
                ...operation,
                created: new Date(),
                status: 'pending'
            });
        }
    }

    /**
     * Update operation status
     * @param {string} sessionId - Session identifier
     * @param {string} operationId - Operation identifier
     * @param {string} status - New status
     * @param {Object} result - Operation result
     */
    updateOperation(sessionId, operationId, status, result = null) {
        const session = this.getSession(sessionId);
        if (session) {
            const operation = session.operations.get(operationId);
            if (operation) {
                operation.status = status;
                operation.updated = new Date();
                if (result) {
                    operation.result = result;
                }
            }
        }
    }

    /**
     * Clean up completed sessions older than specified time
     * @param {number} maxAge - Maximum age in milliseconds
     */
    cleanup(maxAge = 24 * 60 * 60 * 1000) { // 24 hours default
        const now = new Date();
        for (const [sessionId, session] of this.sessions) {
            if (now - session.created > maxAge) {
                this.sessions.delete(sessionId);
            }
        }
    }

    /**
     * Get all sessions
     * @returns {Array} Array of session objects
     */
    getAllSessions() {
        return Array.from(this.sessions.values());
    }
}

/**
 * Progress callback system for long-running operations
 */
class ProgressTracker {
    constructor() {
        this.callbacks = new Map();
    }

    /**
     * Register progress callback for operation
     * @param {string} operationId - Operation identifier
     * @param {Function} callback - Progress callback function
     */
    registerCallback(operationId, callback) {
        this.callbacks.set(operationId, callback);
    }

    /**
     * Emit progress update
     * @param {string} operationId - Operation identifier
     * @param {Object} progress - Progress data
     */
    emitProgress(operationId, progress) {
        const callback = this.callbacks.get(operationId);
        if (callback) {
            callback(progress);
        }
    }

    /**
     * Remove callback for operation
     * @param {string} operationId - Operation identifier
     */
    removeCallback(operationId) {
        this.callbacks.delete(operationId);
    }
}

/**
 * Structured error response format
 */
class APIError extends Error {
    constructor(message, code, details = null) {
        super(message);
        this.name = 'APIError';
        this.code = code;
        this.details = details;
        this.timestamp = new Date().toISOString();
    }

    toJSON() {
        return {
            error: true,
            message: this.message,
            code: this.code,
            details: this.details,
            timestamp: this.timestamp
        };
    }
}

/**
 * Main Jestir API class
 */
class JestirAPI {
    constructor(options = {}) {
        this.options = {
            pythonPath: options.pythonPath || 'python3',
            jestirPath: options.jestirPath || join(__dirname, '..', 'src', 'jestir'),
            timeout: options.timeout || 300000, // 5 minutes default
            verbose: options.verbose || false,
            ...options
        };

        this.sessionManager = new SessionManager();
        this.progressTracker = new ProgressTracker();

        // Cleanup old sessions every hour
        setInterval(() => {
            this.sessionManager.cleanup();
        }, 60 * 60 * 1000);
    }

    /**
     * Execute Jestir CLI command
     * @private
     * @param {Array} args - Command arguments
     * @param {Object} options - Execution options
     * @returns {Promise<Object>} Command result
     */
    async _executeCommand(args, options = {}) {
        return new Promise((resolve, reject) => {
            const command = [this.options.pythonPath, '-m', 'jestir', ...args];
            const child = spawn(command[0], command.slice(1), {
                cwd: this.options.jestirPath,
                stdio: ['pipe', 'pipe', 'pipe'],
                timeout: options.timeout || this.options.timeout
            });

            let stdout = '';
            let stderr = '';
            let progressData = '';

            child.stdout.on('data', (data) => {
                const output = data.toString();
                stdout += output;

                // Try to parse progress updates
                if (options.onProgress) {
                    try {
                        const lines = output.split('\n');
                        for (const line of lines) {
                            if (line.trim()) {
                                // Look for progress indicators in Jestir output
                                if (line.includes('Generating') || line.includes('Processing')) {
                                    options.onProgress({
                                        stage: 'processing',
                                        message: line.trim(),
                                        timestamp: new Date().toISOString()
                                    });
                                }
                            }
                        }
                    } catch (e) {
                        // Ignore parsing errors
                    }
                }
            });

            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            child.on('close', (code) => {
                if (code === 0) {
                    resolve({
                        success: true,
                        stdout: stdout.trim(),
                        stderr: stderr.trim(),
                        exitCode: code
                    });
                } else {
                    reject(new APIError(
                        `Command failed with exit code ${code}`,
                        'COMMAND_FAILED',
                        {
                            stdout: stdout.trim(),
                            stderr: stderr.trim(),
                            exitCode: code,
                            command: command.join(' ')
                        }
                    ));
                }
            });

            child.on('error', (error) => {
                reject(new APIError(
                    `Failed to execute command: ${error.message}`,
                    'COMMAND_EXECUTION_ERROR',
                    { error: error.message, command: command.join(' ') }
                ));
            });

            // Handle timeout
            if (options.timeout) {
                setTimeout(() => {
                    child.kill('SIGTERM');
                    reject(new APIError(
                        'Command timed out',
                        'COMMAND_TIMEOUT',
                        { timeout: options.timeout, command: command.join(' ') }
                    ));
                }, options.timeout);
            }
        });
    }

    /**
     * Generate or update context from natural language input
     * @param {string} inputText - Natural language description
     * @param {Object} options - Generation options
     * @param {string} options.output - Output file path (default: "context.yaml")
     * @param {string} options.length - Target word count or reading time
     * @param {number} options.tolerance - Length tolerance percentage
     * @param {string} options.sessionId - Session ID for tracking
     * @param {Function} options.onProgress - Progress callback
     * @returns {Promise<Object>} Context generation result
     */
    async generateContext(inputText, options = {}) {
        const operationId = `context_${Date.now()}`;
        const sessionId = options.sessionId || this.sessionManager.createSession();

        try {
            this.sessionManager.addOperation(sessionId, operationId, {
                type: 'context',
                input: inputText,
                options
            });

            const args = ['context', inputText];
            if (options.output) args.push('--output', options.output);
            if (options.length) args.push('--length', options.length);
            if (options.tolerance) args.push('--tolerance', options.tolerance.toString());
            if (this.options.verbose) args.push('--verbose');

            const result = await this._executeCommand(args, {
                onProgress: (progress) => {
                    this.progressTracker.emitProgress(operationId, progress);
                    if (options.onProgress) {
                        options.onProgress(progress);
                    }
                }
            });

            this.sessionManager.updateOperation(sessionId, operationId, 'completed', result);

            return {
                success: true,
                operationId,
                sessionId,
                result: {
                    output: result.stdout,
                    contextFile: options.output || 'context.yaml'
                }
            };

        } catch (error) {
            this.sessionManager.updateOperation(sessionId, operationId, 'failed', { error: error.message });
            throw error;
        }
    }

    /**
     * Generate new context from natural language input
     * @param {string} inputText - Natural language description
     * @param {Object} options - Generation options
     * @param {string} options.output - Output file path (default: "context.yaml")
     * @param {string} options.sessionId - Session ID for tracking
     * @param {Function} options.onProgress - Progress callback
     * @returns {Promise<Object>} Context generation result
     */
    async generateNewContext(inputText, options = {}) {
        const operationId = `context_new_${Date.now()}`;
        const sessionId = options.sessionId || this.sessionManager.createSession();

        try {
            this.sessionManager.addOperation(sessionId, operationId, {
                type: 'context_new',
                input: inputText,
                options
            });

            const args = ['context-new', inputText];
            if (options.output) args.push('--output', options.output);
            if (this.options.verbose) args.push('--verbose');

            const result = await this._executeCommand(args, {
                onProgress: (progress) => {
                    this.progressTracker.emitProgress(operationId, progress);
                    if (options.onProgress) {
                        options.onProgress(progress);
                    }
                }
            });

            this.sessionManager.updateOperation(sessionId, operationId, 'completed', result);

            return {
                success: true,
                operationId,
                sessionId,
                result: {
                    output: result.stdout,
                    contextFile: options.output || 'context.yaml'
                }
            };

        } catch (error) {
            this.sessionManager.updateOperation(sessionId, operationId, 'failed', { error: error.message });
            throw error;
        }
    }

    /**
     * Generate story outline from context file
     * @param {string} contextFile - Path to context file
     * @param {Object} options - Generation options
     * @param {string} options.output - Output file path (default: "outline.md")
     * @param {string} options.length - Override target word count or reading time
     * @param {number} options.tolerance - Length tolerance percentage
     * @param {string} options.sessionId - Session ID for tracking
     * @param {Function} options.onProgress - Progress callback
     * @returns {Promise<Object>} Outline generation result
     */
    async generateOutline(contextFile, options = {}) {
        const operationId = `outline_${Date.now()}`;
        const sessionId = options.sessionId || this.sessionManager.createSession();

        try {
            this.sessionManager.addOperation(sessionId, operationId, {
                type: 'outline',
                input: contextFile,
                options
            });

            const args = ['outline', contextFile];
            if (options.output) args.push('--output', options.output);
            if (options.length) args.push('--length', options.length);
            if (options.tolerance) args.push('--tolerance', options.tolerance.toString());
            if (this.options.verbose) args.push('--verbose');

            const result = await this._executeCommand(args, {
                onProgress: (progress) => {
                    this.progressTracker.emitProgress(operationId, progress);
                    if (options.onProgress) {
                        options.onProgress(progress);
                    }
                }
            });

            this.sessionManager.updateOperation(sessionId, operationId, 'completed', result);

            return {
                success: true,
                operationId,
                sessionId,
                result: {
                    output: result.stdout,
                    outlineFile: options.output || 'outline.md',
                    contextFile
                }
            };

        } catch (error) {
            this.sessionManager.updateOperation(sessionId, operationId, 'failed', { error: error.message });
            throw error;
        }
    }

    /**
     * Generate final story from outline file
     * @param {string} outlineFile - Path to outline file
     * @param {Object} options - Generation options
     * @param {string} options.output - Output file path (default: "story.md")
     * @param {string} options.context - Context file path (default: "context.yaml")
     * @param {string} options.length - Override target word count or reading time
     * @param {number} options.tolerance - Length tolerance percentage
     * @param {string} options.sessionId - Session ID for tracking
     * @param {Function} options.onProgress - Progress callback
     * @returns {Promise<Object>} Story generation result
     */
    async generateStory(outlineFile, options = {}) {
        const operationId = `story_${Date.now()}`;
        const sessionId = options.sessionId || this.sessionManager.createSession();

        try {
            this.sessionManager.addOperation(sessionId, operationId, {
                type: 'story',
                input: outlineFile,
                options
            });

            const args = ['write', outlineFile];
            if (options.output) args.push('--output', options.output);
            if (options.context) args.push('--context', options.context);
            if (options.length) args.push('--length', options.length);
            if (options.tolerance) args.push('--tolerance', options.tolerance.toString());
            if (this.options.verbose) args.push('--verbose');

            const result = await this._executeCommand(args, {
                onProgress: (progress) => {
                    this.progressTracker.emitProgress(operationId, progress);
                    if (options.onProgress) {
                        options.onProgress(progress);
                    }
                }
            });

            this.sessionManager.updateOperation(sessionId, operationId, 'completed', result);

            return {
                success: true,
                operationId,
                sessionId,
                result: {
                    output: result.stdout,
                    storyFile: options.output || 'story.md',
                    outlineFile,
                    contextFile: options.context || 'context.yaml'
                }
            };

        } catch (error) {
            this.sessionManager.updateOperation(sessionId, operationId, 'failed', { error: error.message });
            throw error;
        }
    }

    /**
     * Complete story generation pipeline (context -> outline -> story)
     * @param {string} inputText - Natural language description
     * @param {Object} options - Generation options
     * @param {string} options.contextFile - Context file path (default: "context.yaml")
     * @param {string} options.outlineFile - Outline file path (default: "outline.md")
     * @param {string} options.storyFile - Story file path (default: "story.md")
     * @param {string} options.length - Target word count or reading time
     * @param {number} options.tolerance - Length tolerance percentage
     * @param {string} options.sessionId - Session ID for tracking
     * @param {Function} options.onProgress - Progress callback
     * @returns {Promise<Object>} Complete pipeline result
     */
    async generateCompleteStory(inputText, options = {}) {
        const sessionId = options.sessionId || this.sessionManager.createSession();
        const pipelineId = `pipeline_${Date.now()}`;

        try {
            this.sessionManager.addOperation(sessionId, pipelineId, {
                type: 'pipeline',
                input: inputText,
                options,
                status: 'running'
            });

            const results = {
                context: null,
                outline: null,
                story: null
            };

            // Step 1: Generate context
            if (options.onProgress) {
                options.onProgress({
                    stage: 'context',
                    message: 'Generating context from input...',
                    progress: 0.1
                });
            }

            results.context = await this.generateContext(inputText, {
                ...options,
                sessionId,
                onProgress: (progress) => {
                    if (options.onProgress) {
                        options.onProgress({
                            ...progress,
                            stage: 'context',
                            progress: 0.1 + (progress.progress || 0) * 0.3
                        });
                    }
                }
            });

            // Step 2: Generate outline
            if (options.onProgress) {
                options.onProgress({
                    stage: 'outline',
                    message: 'Generating story outline...',
                    progress: 0.4
                });
            }

            results.outline = await this.generateOutline(results.context.result.contextFile, {
                ...options,
                sessionId,
                onProgress: (progress) => {
                    if (options.onProgress) {
                        options.onProgress({
                            ...progress,
                            stage: 'outline',
                            progress: 0.4 + (progress.progress || 0) * 0.3
                        });
                    }
                }
            });

            // Step 3: Generate story
            if (options.onProgress) {
                options.onProgress({
                    stage: 'story',
                    message: 'Generating final story...',
                    progress: 0.7
                });
            }

            results.story = await this.generateStory(results.outline.result.outlineFile, {
                ...options,
                sessionId,
                onProgress: (progress) => {
                    if (options.onProgress) {
                        options.onProgress({
                            ...progress,
                            stage: 'story',
                            progress: 0.7 + (progress.progress || 0) * 0.3
                        });
                    }
                }
            });

            this.sessionManager.updateOperation(sessionId, pipelineId, 'completed', results);

            if (options.onProgress) {
                options.onProgress({
                    stage: 'complete',
                    message: 'Story generation completed successfully!',
                    progress: 1.0
                });
            }

            return {
                success: true,
                pipelineId,
                sessionId,
                result: {
                    context: results.context.result,
                    outline: results.outline.result,
                    story: results.story.result,
                    files: {
                        context: results.context.result.contextFile,
                        outline: results.outline.result.outlineFile,
                        story: results.story.result.storyFile
                    }
                }
            };

        } catch (error) {
            this.sessionManager.updateOperation(sessionId, pipelineId, 'failed', { error: error.message });
            throw error;
        }
    }

    /**
     * Validate context file
     * @param {string} contextFile - Path to context file
     * @param {Object} options - Validation options
     * @param {boolean} options.verbose - Show detailed validation results
     * @param {boolean} options.fix - Attempt to fix common issues
     * @param {string} options.sessionId - Session ID for tracking
     * @returns {Promise<Object>} Validation result
     */
    async validateContext(contextFile, options = {}) {
        const operationId = `validate_${Date.now()}`;
        const sessionId = options.sessionId || this.sessionManager.createSession();

        try {
            this.sessionManager.addOperation(sessionId, operationId, {
                type: 'validate',
                input: contextFile,
                options
            });

            const args = ['validate', contextFile];
            if (options.verbose) args.push('--verbose');
            if (options.fix) args.push('--fix');
            if (this.options.verbose) args.push('--verbose');

            const result = await this._executeCommand(args);

            this.sessionManager.updateOperation(sessionId, operationId, 'completed', result);

            return {
                success: true,
                operationId,
                sessionId,
                result: {
                    output: result.stdout,
                    contextFile
                }
            };

        } catch (error) {
            this.sessionManager.updateOperation(sessionId, operationId, 'failed', { error: error.message });
            throw error;
        }
    }

    /**
     * Validate template files
     * @param {Object} options - Validation options
     * @param {boolean} options.verbose - Show detailed validation results
     * @param {boolean} options.fix - Attempt to fix common issues
     * @param {string} options.sessionId - Session ID for tracking
     * @returns {Promise<Object>} Template validation result
     */
    async validateTemplates(options = {}) {
        const operationId = `validate_templates_${Date.now()}`;
        const sessionId = options.sessionId || this.sessionManager.createSession();

        try {
            this.sessionManager.addOperation(sessionId, operationId, {
                type: 'validate_templates',
                options
            });

            const args = ['validate-templates'];
            if (options.verbose) args.push('--verbose');
            if (options.fix) args.push('--fix');
            if (this.options.verbose) args.push('--verbose');

            const result = await this._executeCommand(args);

            this.sessionManager.updateOperation(sessionId, operationId, 'completed', result);

            return {
                success: true,
                operationId,
                sessionId,
                result: {
                    output: result.stdout
                }
            };

        } catch (error) {
            this.sessionManager.updateOperation(sessionId, operationId, 'failed', { error: error.message });
            throw error;
        }
    }

    /**
     * Search entities in LightRAG API
     * @param {string} entityType - Type of entity to search (characters, locations, items)
     * @param {Object} options - Search options
     * @param {string} options.query - Search query
     * @param {string} options.filterType - Filter by specific type
     * @param {number} options.limit - Maximum number of results
     * @param {number} options.page - Page number for pagination
     * @param {string} options.format - Output format (table, json, yaml)
     * @param {string} options.export - Export results to file
     * @param {string} options.sessionId - Session ID for tracking
     * @returns {Promise<Object>} Search result
     */
    async searchEntities(entityType, options = {}) {
        const operationId = `search_${Date.now()}`;
        const sessionId = options.sessionId || this.sessionManager.createSession();

        try {
            this.sessionManager.addOperation(sessionId, operationId, {
                type: 'search',
                input: { entityType, query: options.query },
                options
            });

            const args = ['search', entityType];
            if (options.query) args.push('--query', options.query);
            if (options.filterType) args.push('--type', options.filterType);
            if (options.limit) args.push('--limit', options.limit.toString());
            if (options.page) args.push('--page', options.page.toString());
            if (options.format) args.push('--format', options.format);
            if (options.export) args.push('--export', options.export);
            if (this.options.verbose) args.push('--verbose');

            const result = await this._executeCommand(args);

            this.sessionManager.updateOperation(sessionId, operationId, 'completed', result);

            return {
                success: true,
                operationId,
                sessionId,
                result: {
                    output: result.stdout,
                    entityType,
                    query: options.query
                }
            };

        } catch (error) {
            this.sessionManager.updateOperation(sessionId, operationId, 'failed', { error: error.message });
            throw error;
        }
    }

    /**
     * List entities from LightRAG API
     * @param {string} entityType - Type of entity to list (characters, locations, items)
     * @param {Object} options - List options
     * @param {string} options.filterType - Filter by specific type
     * @param {number} options.limit - Maximum number of results
     * @param {number} options.page - Page number for pagination
     * @param {string} options.format - Output format (table, json, yaml)
     * @param {string} options.export - Export results to file
     * @param {string} options.sessionId - Session ID for tracking
     * @returns {Promise<Object>} List result
     */
    async listEntities(entityType, options = {}) {
        const operationId = `list_${Date.now()}`;
        const sessionId = options.sessionId || this.sessionManager.createSession();

        try {
            this.sessionManager.addOperation(sessionId, operationId, {
                type: 'list',
                input: { entityType },
                options
            });

            const args = ['list', entityType];
            if (options.filterType) args.push('--type', options.filterType);
            if (options.limit) args.push('--limit', options.limit.toString());
            if (options.page) args.push('--page', options.page.toString());
            if (options.format) args.push('--format', options.format);
            if (options.export) args.push('--export', options.export);
            if (this.options.verbose) args.push('--verbose');

            const result = await this._executeCommand(args);

            this.sessionManager.updateOperation(sessionId, operationId, 'completed', result);

            return {
                success: true,
                operationId,
                sessionId,
                result: {
                    output: result.stdout,
                    entityType
                }
            };

        } catch (error) {
            this.sessionManager.updateOperation(sessionId, operationId, 'failed', { error: error.message });
            throw error;
        }
    }

    /**
     * Get token usage statistics
     * @param {Object} options - Stats options
     * @param {string} options.context - Context file to analyze
     * @param {string} options.period - Report period (daily, weekly, monthly)
     * @param {string} options.format - Output format (table, json, yaml)
     * @param {string} options.export - Export report to file
     * @param {boolean} options.suggestions - Show optimization suggestions
     * @param {string} options.sessionId - Session ID for tracking
     * @returns {Promise<Object>} Statistics result
     */
    async getTokenStats(options = {}) {
        const operationId = `stats_${Date.now()}`;
        const sessionId = options.sessionId || this.sessionManager.createSession();

        try {
            this.sessionManager.addOperation(sessionId, operationId, {
                type: 'stats',
                options
            });

            const args = ['stats'];
            if (options.context) args.push('--context', options.context);
            if (options.period) args.push('--period', options.period);
            if (options.format) args.push('--format', options.format);
            if (options.export) args.push('--export', options.export);
            if (options.suggestions) args.push('--suggestions');
            if (this.options.verbose) args.push('--verbose');

            const result = await this._executeCommand(args);

            this.sessionManager.updateOperation(sessionId, operationId, 'completed', result);

            return {
                success: true,
                operationId,
                sessionId,
                result: {
                    output: result.stdout
                }
            };

        } catch (error) {
            this.sessionManager.updateOperation(sessionId, operationId, 'failed', { error: error.message });
            throw error;
        }
    }

    /**
     * Get session information
     * @param {string} sessionId - Session identifier
     * @returns {Object} Session information
     */
    getSessionInfo(sessionId) {
        const session = this.sessionManager.getSession(sessionId);
        if (!session) {
            throw new APIError('Session not found', 'SESSION_NOT_FOUND', { sessionId });
        }

        return {
            sessionId: session.id,
            created: session.created,
            status: session.status,
            operations: Array.from(session.operations.values())
        };
    }

    /**
     * Get all sessions
     * @returns {Array} Array of session information
     */
    getAllSessions() {
        return this.sessionManager.getAllSessions();
    }

    /**
     * Clean up old sessions
     * @param {number} maxAge - Maximum age in milliseconds
     */
    cleanupSessions(maxAge) {
        this.sessionManager.cleanup(maxAge);
    }
}

// Export the main API class and supporting classes
export {
    JestirAPI,
    SessionManager,
    ProgressTracker,
    APIError
};

// Default export
export default JestirAPI;
