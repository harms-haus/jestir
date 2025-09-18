/**
 * Basic Jestir API Usage Examples
 *
 * This file demonstrates how to use the Jestir Node.js API for story generation.
 *
 * @fileoverview Basic usage examples for Jestir API
 * @version 1.0.0
 * @author Jestir Team
 */

import JestirAPI from '../index.js';

// Initialize the API
const api = new JestirAPI({
    pythonPath: 'python3',
    jestirPath: '../src/jestir',
    timeout: 300000, // 5 minutes
    verbose: true
});

/**
 * Example 1: Generate a simple story
 */
async function generateSimpleStory() {
    console.log('=== Example 1: Generate Simple Story ===');

    try {
        const result = await api.generateCompleteStory(
            'A brave little mouse who wants to be a knight',
            {
                length: '500', // 500 words
                tolerance: 10, // 10% tolerance
                onProgress: (progress) => {
                    console.log(`Progress: ${progress.stage} - ${progress.message}`);
                }
            }
        );

        console.log('Story generated successfully!');
        console.log('Files created:');
        console.log(`- Context: ${result.result.files.context}`);
        console.log(`- Outline: ${result.result.files.outline}`);
        console.log(`- Story: ${result.result.files.story}`);

        return result;
    } catch (error) {
        console.error('Error generating story:', error.message);
        throw error;
    }
}

/**
 * Example 2: Step-by-step story generation
 */
async function generateStepByStep() {
    console.log('\n=== Example 2: Step-by-Step Generation ===');

    try {
        // Step 1: Generate context
        console.log('Step 1: Generating context...');
        const contextResult = await api.generateContext(
            'A magical forest where animals can talk',
            {
                output: 'magical-forest.yaml',
                length: '5m', // 5 minutes reading time
                onProgress: (progress) => {
                    console.log(`Context: ${progress.message}`);
                }
            }
        );
        console.log('Context generated:', contextResult.result.contextFile);

        // Step 2: Generate outline
        console.log('Step 2: Generating outline...');
        const outlineResult = await api.generateOutline(
            contextResult.result.contextFile,
            {
                output: 'magical-forest-outline.md',
                onProgress: (progress) => {
                    console.log(`Outline: ${progress.message}`);
                }
            }
        );
        console.log('Outline generated:', outlineResult.result.outlineFile);

        // Step 3: Generate story
        console.log('Step 3: Generating story...');
        const storyResult = await api.generateStory(
            outlineResult.result.outlineFile,
            {
                output: 'magical-forest-story.md',
                context: contextResult.result.contextFile,
                onProgress: (progress) => {
                    console.log(`Story: ${progress.message}`);
                }
            }
        );
        console.log('Story generated:', storyResult.result.storyFile);

        return {
            context: contextResult,
            outline: outlineResult,
            story: storyResult
        };
    } catch (error) {
        console.error('Error in step-by-step generation:', error.message);
        throw error;
    }
}

/**
 * Example 3: Session management for parallel operations
 */
async function parallelOperations() {
    console.log('\n=== Example 3: Parallel Operations ===');

    try {
        // Create a session for tracking
        const sessionId = api.sessionManager.createSession();
        console.log('Created session:', sessionId);

        // Start multiple operations in parallel
        const operations = [
            api.generateContext('A space adventure story', {
                sessionId,
                output: 'space-context.yaml',
                onProgress: (progress) => {
                    console.log(`Space story: ${progress.message}`);
                }
            }),
            api.generateContext('A pirate treasure hunt', {
                sessionId,
                output: 'pirate-context.yaml',
                onProgress: (progress) => {
                    console.log(`Pirate story: ${progress.message}`);
                }
            }),
            api.generateContext('A fairy tale princess', {
                sessionId,
                output: 'fairy-context.yaml',
                onProgress: (progress) => {
                    console.log(`Fairy tale: ${progress.message}`);
                }
            })
        ];

        // Wait for all operations to complete
        const results = await Promise.all(operations);

        console.log('All parallel operations completed!');
        results.forEach((result, index) => {
            console.log(`Operation ${index + 1}: ${result.result.contextFile}`);
        });

        // Get session information
        const sessionInfo = api.getSessionInfo(sessionId);
        console.log('Session info:', {
            operations: sessionInfo.operations.length,
            status: sessionInfo.status
        });

        return results;
    } catch (error) {
        console.error('Error in parallel operations:', error.message);
        throw error;
    }
}

/**
 * Example 4: Entity search and validation
 */
async function entityOperations() {
    console.log('\n=== Example 4: Entity Operations ===');

    try {
        // Search for characters
        console.log('Searching for characters...');
        const characterSearch = await api.searchEntities('characters', {
            query: 'hero',
            limit: 5,
            format: 'json'
        });
        console.log('Character search results:', characterSearch.result.output);

        // List all locations
        console.log('Listing locations...');
        const locationList = await api.listEntities('locations', {
            limit: 10,
            format: 'table'
        });
        console.log('Location list:', locationList.result.output);

        // Validate templates
        console.log('Validating templates...');
        const templateValidation = await api.validateTemplates({
            verbose: true
        });
        console.log('Template validation:', templateValidation.result.output);

        return {
            characters: characterSearch,
            locations: locationList,
            templates: templateValidation
        };
    } catch (error) {
        console.error('Error in entity operations:', error.message);
        throw error;
    }
}

/**
 * Example 5: Token usage tracking
 */
async function tokenTracking() {
    console.log('\n=== Example 5: Token Usage Tracking ===');

    try {
        // Generate a story first to have some token usage
        await api.generateCompleteStory('A simple test story', {
            output: 'test-story.md'
        });

        // Get token statistics
        console.log('Getting token statistics...');
        const stats = await api.getTokenStats({
            context: 'context.yaml',
            period: 'monthly',
            format: 'table',
            suggestions: true
        });
        console.log('Token statistics:', stats.result.output);

        return stats;
    } catch (error) {
        console.error('Error in token tracking:', error.message);
        throw error;
    }
}

/**
 * Example 6: Error handling
 */
async function errorHandling() {
    console.log('\n=== Example 6: Error Handling ===');

    try {
        // Try to generate story with invalid input
        await api.generateContext('', {
            output: 'invalid.yaml'
        });
    } catch (error) {
        console.log('Caught expected error:', error.message);
        console.log('Error code:', error.code);
        console.log('Error details:', error.details);

        // Handle different error types
        if (error.code === 'COMMAND_FAILED') {
            console.log('Command execution failed');
        } else if (error.code === 'COMMAND_TIMEOUT') {
            console.log('Command timed out');
        } else if (error.code === 'SESSION_NOT_FOUND') {
            console.log('Session not found');
        }
    }
}

/**
 * Main function to run all examples
 */
async function runExamples() {
    console.log('Jestir API Examples');
    console.log('==================');

    try {
        // Run examples
        await generateSimpleStory();
        await generateStepByStep();
        await parallelOperations();
        await entityOperations();
        await tokenTracking();
        await errorHandling();

        console.log('\n=== All Examples Completed Successfully! ===');
    } catch (error) {
        console.error('Example failed:', error);
        process.exit(1);
    }
}

// Run examples if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
    runExamples();
}

export {
    generateSimpleStory,
    generateStepByStep,
    parallelOperations,
    entityOperations,
    tokenTracking,
    errorHandling
};
