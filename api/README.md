# Jestir Node.js API

A comprehensive Node.js API for the Jestir AI-powered bedtime story generator, providing programmatic access to all CLI functionality for web applications.

## Features

- **Complete CLI Coverage**: All Jestir CLI commands available as API methods
- **Async/Await Support**: Full support for long-running operations with proper state management
- **Progress Callbacks**: Real-time progress tracking for generation stages
- **Session Management**: Parallel story generation with session isolation
- **Structured Error Handling**: Consistent error responses across all methods
- **Comprehensive Documentation**: JSDoc documentation for all API methods
- **Unit Tests**: Complete test suite for API functionality
- **Web Server Example**: Ready-to-use HTTP server implementation

## Installation

```bash
cd api
npm install
```

## Quick Start

```javascript
import JestirAPI from './index.js';

// Initialize the API
const api = new JestirAPI({
    pythonPath: 'python3',
    jestirPath: '../src/jestir',
    timeout: 300000, // 5 minutes
    verbose: true
});

// Generate a complete story
const result = await api.generateCompleteStory(
    'A brave little mouse who wants to be a knight',
    {
        length: '500', // 500 words
        tolerance: 10, // 10% tolerance
        onProgress: (progress) => {
            console.log(`${progress.stage}: ${progress.message}`);
        }
    }
);

console.log('Story files created:', result.result.files);
```

## API Reference

### JestirAPI Class

The main API class that provides access to all Jestir functionality.

#### Constructor Options

```javascript
const api = new JestirAPI({
    pythonPath: 'python3',        // Python executable path
    jestirPath: '../src/jestir',  // Jestir source path
    timeout: 300000,              // Default timeout in milliseconds
    verbose: false                // Enable verbose logging
});
```

### Core Methods

#### `generateCompleteStory(inputText, options)`

Generates a complete story through the full pipeline (context → outline → story).

**Parameters:**
- `inputText` (string): Natural language description of the story
- `options` (object): Generation options
  - `contextFile` (string): Context file path (default: "context.yaml")
  - `outlineFile` (string): Outline file path (default: "outline.md")
  - `storyFile` (string): Story file path (default: "story.md")
  - `length` (string): Target word count or reading time (e.g., "500", "5m")
  - `tolerance` (number): Length tolerance percentage (default: 10)
  - `sessionId` (string): Session ID for tracking
  - `onProgress` (function): Progress callback function

**Returns:** Promise resolving to complete pipeline result

**Example:**
```javascript
const result = await api.generateCompleteStory(
    'A magical forest adventure',
    {
        length: '5m',
        tolerance: 15,
        onProgress: (progress) => {
            console.log(`${progress.stage}: ${progress.message} (${Math.round(progress.progress * 100)}%)`);
        }
    }
);
```

#### `generateContext(inputText, options)`

Generates or updates context from natural language input.

**Parameters:**
- `inputText` (string): Natural language description
- `options` (object): Generation options
  - `output` (string): Output file path (default: "context.yaml")
  - `length` (string): Target word count or reading time
  - `tolerance` (number): Length tolerance percentage
  - `sessionId` (string): Session ID for tracking
  - `onProgress` (function): Progress callback function

**Returns:** Promise resolving to context generation result

#### `generateOutline(contextFile, options)`

Generates story outline from context file.

**Parameters:**
- `contextFile` (string): Path to context file
- `options` (object): Generation options
  - `output` (string): Output file path (default: "outline.md")
  - `length` (string): Override target word count or reading time
  - `tolerance` (number): Length tolerance percentage
  - `sessionId` (string): Session ID for tracking
  - `onProgress` (function): Progress callback function

**Returns:** Promise resolving to outline generation result

#### `generateStory(outlineFile, options)`

Generates final story from outline file.

**Parameters:**
- `outlineFile` (string): Path to outline file
- `options` (object): Generation options
  - `output` (string): Output file path (default: "story.md")
  - `context` (string): Context file path (default: "context.yaml")
  - `length` (string): Override target word count or reading time
  - `tolerance` (number): Length tolerance percentage
  - `sessionId` (string): Session ID for tracking
  - `onProgress` (function): Progress callback function

**Returns:** Promise resolving to story generation result

### Validation Methods

#### `validateContext(contextFile, options)`

Validates context file for structure and consistency.

**Parameters:**
- `contextFile` (string): Path to context file
- `options` (object): Validation options
  - `verbose` (boolean): Show detailed validation results
  - `fix` (boolean): Attempt to fix common issues
  - `sessionId` (string): Session ID for tracking

**Returns:** Promise resolving to validation result

#### `validateTemplates(options)`

Validates all template files for syntax and completeness.

**Parameters:**
- `options` (object): Validation options
  - `verbose` (boolean): Show detailed validation results
  - `fix` (boolean): Attempt to fix common issues
  - `sessionId` (string): Session ID for tracking

**Returns:** Promise resolving to template validation result

### Entity Methods

#### `searchEntities(entityType, options)`

Searches for entities in LightRAG API.

**Parameters:**
- `entityType` (string): Type of entity ("characters", "locations", "items")
- `options` (object): Search options
  - `query` (string): Search query
  - `filterType` (string): Filter by specific type
  - `limit` (number): Maximum number of results
  - `page` (number): Page number for pagination
  - `format` (string): Output format ("table", "json", "yaml")
  - `export` (string): Export results to file
  - `sessionId` (string): Session ID for tracking

**Returns:** Promise resolving to search result

#### `listEntities(entityType, options)`

Lists entities from LightRAG API.

**Parameters:**
- `entityType` (string): Type of entity ("characters", "locations", "items")
- `options` (object): List options
  - `filterType` (string): Filter by specific type
  - `limit` (number): Maximum number of results
  - `page` (number): Page number for pagination
  - `format` (string): Output format ("table", "json", "yaml")
  - `export` (string): Export results to file
  - `sessionId` (string): Session ID for tracking

**Returns:** Promise resolving to list result

### Statistics Methods

#### `getTokenStats(options)`

Gets token usage statistics and cost analysis.

**Parameters:**
- `options` (object): Stats options
  - `context` (string): Context file to analyze
  - `period` (string): Report period ("daily", "weekly", "monthly")
  - `format` (string): Output format ("table", "json", "yaml")
  - `export` (string): Export report to file
  - `suggestions` (boolean): Show optimization suggestions
  - `sessionId` (string): Session ID for tracking

**Returns:** Promise resolving to statistics result

### Session Management

#### `getSessionInfo(sessionId)`

Gets information about a specific session.

**Parameters:**
- `sessionId` (string): Session identifier

**Returns:** Session information object

#### `getAllSessions()`

Gets all active sessions.

**Returns:** Array of session information objects

#### `cleanupSessions(maxAge)`

Cleans up old sessions.

**Parameters:**
- `maxAge` (number): Maximum age in milliseconds

## Error Handling

The API uses structured error responses with the `APIError` class:

```javascript
try {
    const result = await api.generateContext('invalid input');
} catch (error) {
    if (error instanceof APIError) {
        console.log('Error code:', error.code);
        console.log('Error message:', error.message);
        console.log('Error details:', error.details);
    }
}
```

### Error Codes

- `COMMAND_FAILED`: Command execution failed
- `COMMAND_TIMEOUT`: Command timed out
- `COMMAND_EXECUTION_ERROR`: Failed to execute command
- `SESSION_NOT_FOUND`: Session not found
- `MISSING_INPUT`: Required input parameter missing
- `VALIDATION_ERROR`: Validation failed
- `GENERATION_ERROR`: Story generation failed

## Progress Tracking

The API provides real-time progress updates through callback functions:

```javascript
const result = await api.generateCompleteStory(input, {
    onProgress: (progress) => {
        console.log(`Stage: ${progress.stage}`);
        console.log(`Message: ${progress.message}`);
        console.log(`Progress: ${Math.round(progress.progress * 100)}%`);
        console.log(`Timestamp: ${progress.timestamp}`);
    }
});
```

### Progress Object Structure

```javascript
{
    stage: 'context' | 'outline' | 'story' | 'complete',
    message: 'Human-readable progress message',
    progress: 0.0-1.0, // Progress percentage (0-1)
    timestamp: 'ISO 8601 timestamp'
}
```

## Session Management

Sessions allow tracking multiple parallel operations:

```javascript
// Create a session
const sessionId = api.sessionManager.createSession();

// Use session for operations
const contextResult = await api.generateContext(input, { sessionId });
const outlineResult = await api.generateOutline(contextFile, { sessionId });

// Get session information
const sessionInfo = api.getSessionInfo(sessionId);
console.log('Operations:', sessionInfo.operations.length);
```

## Examples

### Basic Story Generation

```javascript
import JestirAPI from './index.js';

const api = new JestirAPI();

// Generate a simple story
const result = await api.generateCompleteStory(
    'A brave little mouse who wants to be a knight',
    {
        length: '500',
        onProgress: (progress) => {
            console.log(`${progress.stage}: ${progress.message}`);
        }
    }
);

console.log('Files created:', result.result.files);
```

### Parallel Operations

```javascript
// Create session for tracking
const sessionId = api.sessionManager.createSession();

// Start multiple operations in parallel
const operations = [
    api.generateContext('Space adventure', { sessionId }),
    api.generateContext('Pirate treasure hunt', { sessionId }),
    api.generateContext('Fairy tale princess', { sessionId })
];

// Wait for all to complete
const results = await Promise.all(operations);
console.log('All operations completed!');
```

### Web Server Integration

See `examples/web-server.js` for a complete HTTP server implementation.

## Testing

Run the test suite:

```bash
npm test
```

The test suite includes:
- Unit tests for all API methods
- Session management tests
- Error handling tests
- Progress tracking tests
- Mock command execution tests

## Requirements

- Node.js 18.0.0 or higher
- Python 3.8 or higher
- Jestir Python package installed

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions, please refer to the main Jestir documentation or create an issue in the project repository.
