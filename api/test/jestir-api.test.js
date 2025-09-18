/**
 * Unit tests for Jestir Node.js API
 *
 * @fileoverview Comprehensive test suite for Jestir API functionality
 * @version 1.0.0
 * @author Jestir Team
 */

import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';
import JestirAPI, { SessionManager, ProgressTracker, APIError } from '../index.js';
import { spawn } from 'child_process';

// Mock child_process
jest.mock('child_process');

describe('JestirAPI', () => {
    let api;
    let mockSpawn;

    beforeEach(() => {
        api = new JestirAPI({
            pythonPath: 'python3',
            jestirPath: '/test/path',
            timeout: 5000,
            verbose: false
        });

        mockSpawn = jest.mocked(spawn);
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    describe('Constructor', () => {
        it('should initialize with default options', () => {
            const defaultApi = new JestirAPI();
            expect(defaultApi.options.pythonPath).toBe('python3');
            expect(defaultApi.options.timeout).toBe(300000);
            expect(defaultApi.options.verbose).toBe(false);
        });

        it('should initialize with custom options', () => {
            const customApi = new JestirAPI({
                pythonPath: 'python',
                timeout: 10000,
                verbose: true
            });
            expect(customApi.options.pythonPath).toBe('python');
            expect(customApi.options.timeout).toBe(10000);
            expect(customApi.options.verbose).toBe(true);
        });
    });

    describe('Session Management', () => {
        it('should create new session', () => {
            const sessionId = api.sessionManager.createSession();
            expect(sessionId).toMatch(/^session_\d+_\d+$/);
            expect(api.sessionManager.getSession(sessionId)).toBeDefined();
        });

        it('should get session by ID', () => {
            const sessionId = api.sessionManager.createSession();
            const session = api.sessionManager.getSession(sessionId);
            expect(session).toBeDefined();
            expect(session.id).toBe(sessionId);
        });

        it('should return null for non-existent session', () => {
            const session = api.sessionManager.getSession('non-existent');
            expect(session).toBeNull();
        });

        it('should add operation to session', () => {
            const sessionId = api.sessionManager.createSession();
            const operationId = 'test_operation';
            const operation = { type: 'test', input: 'test input' };

            api.sessionManager.addOperation(sessionId, operationId, operation);
            const session = api.sessionManager.getSession(sessionId);
            expect(session.operations.has(operationId)).toBe(true);
        });

        it('should update operation status', () => {
            const sessionId = api.sessionManager.createSession();
            const operationId = 'test_operation';
            const operation = { type: 'test', input: 'test input' };

            api.sessionManager.addOperation(sessionId, operationId, operation);
            api.sessionManager.updateOperation(sessionId, operationId, 'completed', { result: 'success' });

            const session = api.sessionManager.getSession(sessionId);
            const op = session.operations.get(operationId);
            expect(op.status).toBe('completed');
            expect(op.result).toEqual({ result: 'success' });
        });
    });

    describe('Progress Tracking', () => {
        it('should register progress callback', () => {
            const operationId = 'test_operation';
            const callback = jest.fn();

            api.progressTracker.registerCallback(operationId, callback);
            expect(api.progressTracker.callbacks.has(operationId)).toBe(true);
        });

        it('should emit progress updates', () => {
            const operationId = 'test_operation';
            const callback = jest.fn();
            const progress = { stage: 'test', message: 'test message' };

            api.progressTracker.registerCallback(operationId, callback);
            api.progressTracker.emitProgress(operationId, progress);

            expect(callback).toHaveBeenCalledWith(progress);
        });

        it('should remove callback', () => {
            const operationId = 'test_operation';
            const callback = jest.fn();

            api.progressTracker.registerCallback(operationId, callback);
            api.progressTracker.removeCallback(operationId);

            expect(api.progressTracker.callbacks.has(operationId)).toBe(false);
        });
    });

    describe('Error Handling', () => {
        it('should create APIError with message and code', () => {
            const error = new APIError('Test error', 'TEST_ERROR');
            expect(error.message).toBe('Test error');
            expect(error.code).toBe('TEST_ERROR');
            expect(error.name).toBe('APIError');
            expect(error.timestamp).toBeDefined();
        });

        it('should create APIError with details', () => {
            const details = { field: 'value' };
            const error = new APIError('Test error', 'TEST_ERROR', details);
            expect(error.details).toEqual(details);
        });

        it('should serialize to JSON', () => {
            const error = new APIError('Test error', 'TEST_ERROR', { field: 'value' });
            const json = error.toJSON();

            expect(json).toEqual({
                error: true,
                message: 'Test error',
                code: 'TEST_ERROR',
                details: { field: 'value' },
                timestamp: expect.any(String)
            });
        });
    });

    describe('Command Execution', () => {
        it('should execute command successfully', async () => {
            const mockChild = {
                stdout: { on: jest.fn() },
                stderr: { on: jest.fn() },
                on: jest.fn((event, callback) => {
                    if (event === 'close') {
                        setTimeout(() => callback(0), 10);
                    }
                }),
                kill: jest.fn()
            };

            mockSpawn.mockReturnValue(mockChild);

            // Mock stdout data
            mockChild.stdout.on.mockImplementation((event, callback) => {
                if (event === 'data') {
                    setTimeout(() => callback(Buffer.from('test output')), 5);
                }
            });

            const result = await api._executeCommand(['test', 'command']);

            expect(result.success).toBe(true);
            expect(result.stdout).toBe('test output');
            expect(result.exitCode).toBe(0);
        });

        it('should handle command failure', async () => {
            const mockChild = {
                stdout: { on: jest.fn() },
                stderr: { on: jest.fn() },
                on: jest.fn((event, callback) => {
                    if (event === 'close') {
                        setTimeout(() => callback(1), 10);
                    }
                }),
                kill: jest.fn()
            };

            mockSpawn.mockReturnValue(mockChild);

            // Mock stderr data
            mockChild.stderr.on.mockImplementation((event, callback) => {
                if (event === 'data') {
                    setTimeout(() => callback(Buffer.from('test error')), 5);
                }
            });

            await expect(api._executeCommand(['test', 'command']))
                .rejects.toThrow(APIError);
        });

        it('should handle command timeout', async () => {
            const mockChild = {
                stdout: { on: jest.fn() },
                stderr: { on: jest.fn() },
                on: jest.fn(),
                kill: jest.fn()
            };

            mockSpawn.mockReturnValue(mockChild);

            await expect(api._executeCommand(['test', 'command'], { timeout: 10 }))
                .rejects.toThrow(APIError);
        });
    });

    describe('Context Generation', () => {
        it('should generate context successfully', async () => {
            const mockChild = {
                stdout: { on: jest.fn() },
                stderr: { on: jest.fn() },
                on: jest.fn((event, callback) => {
                    if (event === 'close') {
                        setTimeout(() => callback(0), 10);
                    }
                }),
                kill: jest.fn()
            };

            mockSpawn.mockReturnValue(mockChild);
            mockChild.stdout.on.mockImplementation((event, callback) => {
                if (event === 'data') {
                    setTimeout(() => callback(Buffer.from('Context generated successfully')), 5);
                }
            });

            const result = await api.generateContext('Test story idea');

            expect(result.success).toBe(true);
            expect(result.operationId).toMatch(/^context_\d+$/);
            expect(result.sessionId).toMatch(/^session_\d+_\d+$/);
            expect(result.result.contextFile).toBe('context.yaml');
        });

        it('should generate context with custom options', async () => {
            const mockChild = {
                stdout: { on: jest.fn() },
                stderr: { on: jest.fn() },
                on: jest.fn((event, callback) => {
                    if (event === 'close') {
                        setTimeout(() => callback(0), 10);
                    }
                }),
                kill: jest.fn()
            };

            mockSpawn.mockReturnValue(mockChild);
            mockChild.stdout.on.mockImplementation((event, callback) => {
                if (event === 'data') {
                    setTimeout(() => callback(Buffer.from('Context generated')), 5);
                }
            });

            const result = await api.generateContext('Test story', {
                output: 'custom.yaml',
                length: '500',
                tolerance: 15
            });

            expect(result.result.contextFile).toBe('custom.yaml');
        });

        it('should handle context generation failure', async () => {
            const mockChild = {
                stdout: { on: jest.fn() },
                stderr: { on: jest.fn() },
                on: jest.fn((event, callback) => {
                    if (event === 'close') {
                        setTimeout(() => callback(1), 10);
                    }
                }),
                kill: jest.fn()
            };

            mockSpawn.mockReturnValue(mockChild);
            mockChild.stderr.on.mockImplementation((event, callback) => {
                if (event === 'data') {
                    setTimeout(() => callback(Buffer.from('Generation failed')), 5);
                }
            });

            await expect(api.generateContext('Test story'))
                .rejects.toThrow(APIError);
        });
    });

    describe('Outline Generation', () => {
        it('should generate outline successfully', async () => {
            const mockChild = {
                stdout: { on: jest.fn() },
                stderr: { on: jest.fn() },
                on: jest.fn((event, callback) => {
                    if (event === 'close') {
                        setTimeout(() => callback(0), 10);
                    }
                }),
                kill: jest.fn()
            };

            mockSpawn.mockReturnValue(mockChild);
            mockChild.stdout.on.mockImplementation((event, callback) => {
                if (event === 'data') {
                    setTimeout(() => callback(Buffer.from('Outline generated successfully')), 5);
                }
            });

            const result = await api.generateOutline('context.yaml');

            expect(result.success).toBe(true);
            expect(result.operationId).toMatch(/^outline_\d+$/);
            expect(result.result.outlineFile).toBe('outline.md');
        });
    });

    describe('Story Generation', () => {
        it('should generate story successfully', async () => {
            const mockChild = {
                stdout: { on: jest.fn() },
                stderr: { on: jest.fn() },
                on: jest.fn((event, callback) => {
                    if (event === 'close') {
                        setTimeout(() => callback(0), 10);
                    }
                }),
                kill: jest.fn()
            };

            mockSpawn.mockReturnValue(mockChild);
            mockChild.stdout.on.mockImplementation((event, callback) => {
                if (event === 'data') {
                    setTimeout(() => callback(Buffer.from('Story generated successfully')), 5);
                }
            });

            const result = await api.generateStory('outline.md');

            expect(result.success).toBe(true);
            expect(result.operationId).toMatch(/^story_\d+$/);
            expect(result.result.storyFile).toBe('story.md');
        });
    });

    describe('Complete Story Pipeline', () => {
        it('should generate complete story pipeline', async () => {
            // Mock successful command execution
            const mockChild = {
                stdout: { on: jest.fn() },
                stderr: { on: jest.fn() },
                on: jest.fn((event, callback) => {
                    if (event === 'close') {
                        setTimeout(() => callback(0), 10);
                    }
                }),
                kill: jest.fn()
            };

            mockSpawn.mockReturnValue(mockChild);
            mockChild.stdout.on.mockImplementation((event, callback) => {
                if (event === 'data') {
                    setTimeout(() => callback(Buffer.from('Operation completed')), 5);
                }
            });

            const result = await api.generateCompleteStory('Test story idea');

            expect(result.success).toBe(true);
            expect(result.pipelineId).toMatch(/^pipeline_\d+$/);
            expect(result.result.context).toBeDefined();
            expect(result.result.outline).toBeDefined();
            expect(result.result.story).toBeDefined();
        });

        it('should handle pipeline failure', async () => {
            const mockChild = {
                stdout: { on: jest.fn() },
                stderr: { on: jest.fn() },
                on: jest.fn((event, callback) => {
                    if (event === 'close') {
                        setTimeout(() => callback(1), 10);
                    }
                }),
                kill: jest.fn()
            };

            mockSpawn.mockReturnValue(mockChild);
            mockChild.stderr.on.mockImplementation((event, callback) => {
                if (event === 'data') {
                    setTimeout(() => callback(Buffer.from('Pipeline failed')), 5);
                }
            });

            await expect(api.generateCompleteStory('Test story'))
                .rejects.toThrow(APIError);
        });
    });

    describe('Validation', () => {
        it('should validate context successfully', async () => {
            const mockChild = {
                stdout: { on: jest.fn() },
                stderr: { on: jest.fn() },
                on: jest.fn((event, callback) => {
                    if (event === 'close') {
                        setTimeout(() => callback(0), 10);
                    }
                }),
                kill: jest.fn()
            };

            mockSpawn.mockReturnValue(mockChild);
            mockChild.stdout.on.mockImplementation((event, callback) => {
                if (event === 'data') {
                    setTimeout(() => callback(Buffer.from('Context is valid')), 5);
                }
            });

            const result = await api.validateContext('context.yaml');

            expect(result.success).toBe(true);
            expect(result.operationId).toMatch(/^validate_\d+$/);
        });

        it('should validate templates successfully', async () => {
            const mockChild = {
                stdout: { on: jest.fn() },
                stderr: { on: jest.fn() },
                on: jest.fn((event, callback) => {
                    if (event === 'close') {
                        setTimeout(() => callback(0), 10);
                    }
                }),
                kill: jest.fn()
            };

            mockSpawn.mockReturnValue(mockChild);
            mockChild.stdout.on.mockImplementation((event, callback) => {
                if (event === 'data') {
                    setTimeout(() => callback(Buffer.from('All templates are valid')), 5);
                }
            });

            const result = await api.validateTemplates();

            expect(result.success).toBe(true);
            expect(result.operationId).toMatch(/^validate_templates_\d+$/);
        });
    });

    describe('Entity Operations', () => {
        it('should search entities successfully', async () => {
            const mockChild = {
                stdout: { on: jest.fn() },
                stderr: { on: jest.fn() },
                on: jest.fn((event, callback) => {
                    if (event === 'close') {
                        setTimeout(() => callback(0), 10);
                    }
                }),
                kill: jest.fn()
            };

            mockSpawn.mockReturnValue(mockChild);
            mockChild.stdout.on.mockImplementation((event, callback) => {
                if (event === 'data') {
                    setTimeout(() => callback(Buffer.from('Search results')), 5);
                }
            });

            const result = await api.searchEntities('characters', { query: 'hero' });

            expect(result.success).toBe(true);
            expect(result.operationId).toMatch(/^search_\d+$/);
            expect(result.result.entityType).toBe('characters');
        });

        it('should list entities successfully', async () => {
            const mockChild = {
                stdout: { on: jest.fn() },
                stderr: { on: jest.fn() },
                on: jest.fn((event, callback) => {
                    if (event === 'close') {
                        setTimeout(() => callback(0), 10);
                    }
                }),
                kill: jest.fn()
            };

            mockSpawn.mockReturnValue(mockChild);
            mockChild.stdout.on.mockImplementation((event, callback) => {
                if (event === 'data') {
                    setTimeout(() => callback(Buffer.from('Entity list')), 5);
                }
            });

            const result = await api.listEntities('locations');

            expect(result.success).toBe(true);
            expect(result.operationId).toMatch(/^list_\d+$/);
            expect(result.result.entityType).toBe('locations');
        });
    });

    describe('Statistics', () => {
        it('should get token stats successfully', async () => {
            const mockChild = {
                stdout: { on: jest.fn() },
                stderr: { on: jest.fn() },
                on: jest.fn((event, callback) => {
                    if (event === 'close') {
                        setTimeout(() => callback(0), 10);
                    }
                }),
                kill: jest.fn()
            };

            mockSpawn.mockReturnValue(mockChild);
            mockChild.stdout.on.mockImplementation((event, callback) => {
                if (event === 'data') {
                    setTimeout(() => callback(Buffer.from('Token statistics')), 5);
                }
            });

            const result = await api.getTokenStats();

            expect(result.success).toBe(true);
            expect(result.operationId).toMatch(/^stats_\d+$/);
        });
    });

    describe('Session Management', () => {
        it('should get session info', () => {
            const sessionId = api.sessionManager.createSession();
            const info = api.getSessionInfo(sessionId);

            expect(info.sessionId).toBe(sessionId);
            expect(info.created).toBeDefined();
            expect(info.status).toBe('active');
        });

        it('should throw error for non-existent session', () => {
            expect(() => api.getSessionInfo('non-existent'))
                .toThrow(APIError);
        });

        it('should get all sessions', () => {
            const sessionId1 = api.sessionManager.createSession();
            const sessionId2 = api.sessionManager.createSession();
            const sessions = api.getAllSessions();

            expect(sessions).toHaveLength(2);
            expect(sessions.some(s => s.id === sessionId1)).toBe(true);
            expect(sessions.some(s => s.id === sessionId2)).toBe(true);
        });

        it('should cleanup old sessions', () => {
            const sessionId = api.sessionManager.createSession();
            const session = api.sessionManager.getSession(sessionId);

            // Mock old session
            session.created = new Date(Date.now() - 25 * 60 * 60 * 1000); // 25 hours ago

            api.cleanupSessions(24 * 60 * 60 * 1000); // 24 hours

            expect(api.sessionManager.getSession(sessionId)).toBeNull();
        });
    });
});
