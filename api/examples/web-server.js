/**
 * Jestir Web Server Example
 *
 * This example shows how to create a web server using the Jestir API
 * for story generation through HTTP endpoints.
 *
 * @fileoverview Web server example using Jestir API
 * @version 1.0.0
 * @author Jestir Team
 */

import JestirAPI from '../index.js';
import { createServer } from 'http';
import { URL } from 'url';

// Initialize the API
const api = new JestirAPI({
    pythonPath: 'python3',
    jestirPath: '../src/jestir',
    timeout: 300000,
    verbose: false
});

// In-memory storage for demo purposes
const stories = new Map();
const sessions = new Map();

/**
 * HTTP response helper
 */
function sendResponse(res, statusCode, data, contentType = 'application/json') {
    res.writeHead(statusCode, {
        'Content-Type': contentType,
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    });
    res.end(JSON.stringify(data, null, 2));
}

/**
 * Error response helper
 */
function sendError(res, statusCode, message, code = 'UNKNOWN_ERROR') {
    sendResponse(res, statusCode, {
        error: true,
        message,
        code,
        timestamp: new Date().toISOString()
    });
}

/**
 * Parse request body
 */
async function parseBody(req) {
    return new Promise((resolve, reject) => {
        let body = '';
        req.on('data', chunk => {
            body += chunk.toString();
        });
        req.on('end', () => {
            try {
                resolve(JSON.parse(body));
            } catch (error) {
                reject(new Error('Invalid JSON'));
            }
        });
        req.on('error', reject);
    });
}

/**
 * Create HTTP server
 */
const server = createServer(async (req, res) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const method = req.method;
    const path = url.pathname;

    // Handle CORS preflight
    if (method === 'OPTIONS') {
        res.writeHead(200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        });
        res.end();
        return;
    }

    try {
        // Route handlers
        if (path === '/api/stories' && method === 'POST') {
            await handleCreateStory(req, res);
        } else if (path === '/api/stories' && method === 'GET') {
            await handleListStories(req, res);
        } else if (path.startsWith('/api/stories/') && method === 'GET') {
            await handleGetStory(req, res, path);
        } else if (path.startsWith('/api/stories/') && method === 'DELETE') {
            await handleDeleteStory(req, res, path);
        } else if (path === '/api/context' && method === 'POST') {
            await handleGenerateContext(req, res);
        } else if (path === '/api/outline' && method === 'POST') {
            await handleGenerateOutline(req, res);
        } else if (path === '/api/story' && method === 'POST') {
            await handleGenerateStory(req, res);
        } else if (path === '/api/entities/search' && method === 'GET') {
            await handleSearchEntities(req, res, url);
        } else if (path === '/api/entities/list' && method === 'GET') {
            await handleListEntities(req, res, url);
        } else if (path === '/api/validate' && method === 'POST') {
            await handleValidate(req, res);
        } else if (path === '/api/stats' && method === 'GET') {
            await handleGetStats(req, res, url);
        } else if (path === '/api/sessions' && method === 'GET') {
            await handleGetSessions(req, res);
        } else if (path === '/api/health' && method === 'GET') {
            await handleHealth(req, res);
        } else {
            sendError(res, 404, 'Endpoint not found', 'NOT_FOUND');
        }
    } catch (error) {
        console.error('Server error:', error);
        sendError(res, 500, 'Internal server error', 'INTERNAL_ERROR');
    }
});

/**
 * Handle complete story creation
 */
async function handleCreateStory(req, res) {
    const body = await parseBody(req);
    const { input, options = {} } = body;

    if (!input) {
        sendError(res, 400, 'Input text is required', 'MISSING_INPUT');
        return;
    }

    try {
        const storyId = `story_${Date.now()}`;
        const sessionId = api.sessionManager.createSession();

        // Store story metadata
        stories.set(storyId, {
            id: storyId,
            input,
            options,
            sessionId,
            status: 'generating',
            createdAt: new Date(),
            files: {}
        });

        // Start story generation
        api.generateCompleteStory(input, {
            ...options,
            sessionId,
            onProgress: (progress) => {
                // Update story status
                const story = stories.get(storyId);
                if (story) {
                    story.status = progress.stage;
                    story.progress = progress.progress || 0;
                    story.lastUpdate = new Date();
                }
            }
        }).then(result => {
            // Update story with results
            const story = stories.get(storyId);
            if (story) {
                story.status = 'completed';
                story.result = result;
                story.files = result.result.files;
                story.completedAt = new Date();
            }
        }).catch(error => {
            // Update story with error
            const story = stories.get(storyId);
            if (story) {
                story.status = 'failed';
                story.error = error.message;
                story.failedAt = new Date();
            }
        });

        sendResponse(res, 202, {
            storyId,
            sessionId,
            status: 'generating',
            message: 'Story generation started'
        });
    } catch (error) {
        sendError(res, 500, error.message, 'GENERATION_ERROR');
    }
}

/**
 * Handle story listing
 */
async function handleListStories(req, res) {
    const storyList = Array.from(stories.values()).map(story => ({
        id: story.id,
        input: story.input.substring(0, 100) + (story.input.length > 100 ? '...' : ''),
        status: story.status,
        createdAt: story.createdAt,
        completedAt: story.completedAt,
        files: story.files
    }));

    sendResponse(res, 200, {
        stories: storyList,
        total: storyList.length
    });
}

/**
 * Handle get specific story
 */
async function handleGetStory(req, res, path) {
    const storyId = path.split('/')[3];
    const story = stories.get(storyId);

    if (!story) {
        sendError(res, 404, 'Story not found', 'STORY_NOT_FOUND');
        return;
    }

    sendResponse(res, 200, story);
}

/**
 * Handle delete story
 */
async function handleDeleteStory(req, res, path) {
    const storyId = path.split('/')[3];
    const story = stories.get(storyId);

    if (!story) {
        sendError(res, 404, 'Story not found', 'STORY_NOT_FOUND');
        return;
    }

    stories.delete(storyId);
    sendResponse(res, 200, { message: 'Story deleted successfully' });
}

/**
 * Handle context generation
 */
async function handleGenerateContext(req, res) {
    const body = await parseBody(req);
    const { input, options = {} } = body;

    if (!input) {
        sendError(res, 400, 'Input text is required', 'MISSING_INPUT');
        return;
    }

    try {
        const result = await api.generateContext(input, options);
        sendResponse(res, 200, result);
    } catch (error) {
        sendError(res, 500, error.message, 'CONTEXT_GENERATION_ERROR');
    }
}

/**
 * Handle outline generation
 */
async function handleGenerateOutline(req, res) {
    const body = await parseBody(req);
    const { contextFile, options = {} } = body;

    if (!contextFile) {
        sendError(res, 400, 'Context file is required', 'MISSING_CONTEXT_FILE');
        return;
    }

    try {
        const result = await api.generateOutline(contextFile, options);
        sendResponse(res, 200, result);
    } catch (error) {
        sendError(res, 500, error.message, 'OUTLINE_GENERATION_ERROR');
    }
}

/**
 * Handle story generation
 */
async function handleGenerateStory(req, res) {
    const body = await parseBody(req);
    const { outlineFile, options = {} } = body;

    if (!outlineFile) {
        sendError(res, 400, 'Outline file is required', 'MISSING_OUTLINE_FILE');
        return;
    }

    try {
        const result = await api.generateStory(outlineFile, options);
        sendResponse(res, 200, result);
    } catch (error) {
        sendError(res, 500, error.message, 'STORY_GENERATION_ERROR');
    }
}

/**
 * Handle entity search
 */
async function handleSearchEntities(req, res, url) {
    const entityType = url.searchParams.get('type');
    const query = url.searchParams.get('query');
    const limit = parseInt(url.searchParams.get('limit') || '10');
    const page = parseInt(url.searchParams.get('page') || '1');

    if (!entityType) {
        sendError(res, 400, 'Entity type is required', 'MISSING_ENTITY_TYPE');
        return;
    }

    try {
        const result = await api.searchEntities(entityType, {
            query,
            limit,
            page
        });
        sendResponse(res, 200, result);
    } catch (error) {
        sendError(res, 500, error.message, 'ENTITY_SEARCH_ERROR');
    }
}

/**
 * Handle entity listing
 */
async function handleListEntities(req, res, url) {
    const entityType = url.searchParams.get('type');
    const limit = parseInt(url.searchParams.get('limit') || '20');
    const page = parseInt(url.searchParams.get('page') || '1');

    if (!entityType) {
        sendError(res, 400, 'Entity type is required', 'MISSING_ENTITY_TYPE');
        return;
    }

    try {
        const result = await api.listEntities(entityType, {
            limit,
            page
        });
        sendResponse(res, 200, result);
    } catch (error) {
        sendError(res, 500, error.message, 'ENTITY_LIST_ERROR');
    }
}

/**
 * Handle validation
 */
async function handleValidate(req, res) {
    const body = await parseBody(req);
    const { contextFile, options = {} } = body;

    if (!contextFile) {
        sendError(res, 400, 'Context file is required', 'MISSING_CONTEXT_FILE');
        return;
    }

    try {
        const result = await api.validateContext(contextFile, options);
        sendResponse(res, 200, result);
    } catch (error) {
        sendError(res, 500, error.message, 'VALIDATION_ERROR');
    }
}

/**
 * Handle get statistics
 */
async function handleGetStats(req, res, url) {
    const context = url.searchParams.get('context') || 'context.yaml';
    const period = url.searchParams.get('period') || 'monthly';
    const format = url.searchParams.get('format') || 'json';

    try {
        const result = await api.getTokenStats({
            context,
            period,
            format
        });
        sendResponse(res, 200, result);
    } catch (error) {
        sendError(res, 500, error.message, 'STATS_ERROR');
    }
}

/**
 * Handle get sessions
 */
async function handleGetSessions(req, res) {
    try {
        const sessions = api.getAllSessions();
        sendResponse(res, 200, { sessions });
    } catch (error) {
        sendError(res, 500, error.message, 'SESSIONS_ERROR');
    }
}

/**
 * Handle health check
 */
async function handleHealth(req, res) {
    sendResponse(res, 200, {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0'
    });
}

// Start server
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Jestir Web Server running on port ${PORT}`);
    console.log(`Health check: http://localhost:${PORT}/api/health`);
    console.log(`API documentation: http://localhost:${PORT}/api/docs`);
});

export default server;
