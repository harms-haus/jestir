#!/usr/bin/env node

/**
 * Jestir API Test Runner
 *
 * Simple test runner for the Jestir API without external dependencies.
 *
 * @fileoverview Test runner for Jestir API
 * @version 1.0.0
 * @author Jestir Team
 */

import JestirAPI, { SessionManager, ProgressTracker, APIError } from './index.js';

// Test configuration
const TEST_CONFIG = {
    pythonPath: 'python3',
    jestirPath: '../src/jestir',
    timeout: 10000, // 10 seconds for tests
    verbose: false
};

// Test results tracking
let testResults = {
    passed: 0,
    failed: 0,
    total: 0,
    errors: []
};

/**
 * Test assertion helper
 */
function assert(condition, message) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}

/**
 * Test runner
 */
async function runTest(testName, testFunction) {
    testResults.total++;
    process.stdout.write(`Running ${testName}... `);

    try {
        await testFunction();
        testResults.passed++;
        console.log('✅ PASSED');
        return true;
    } catch (error) {
        testResults.failed++;
        testResults.errors.push({
            test: testName,
            error: error.message,
            stack: error.stack
        });
        console.log('❌ FAILED');
        console.log(`   Error: ${error.message}`);
        return false;
    }
}

/**
 * Test: API Constructor
 */
async function testConstructor() {
    const api = new JestirAPI(TEST_CONFIG);
    assert(api.options.pythonPath === 'python3', 'Python path should be set');
    assert(api.options.timeout === 10000, 'Timeout should be set');
    assert(api.sessionManager instanceof SessionManager, 'Session manager should be initialized');
    assert(api.progressTracker instanceof ProgressTracker, 'Progress tracker should be initialized');
}

/**
 * Test: Session Management
 */
async function testSessionManagement() {
    const api = new JestirAPI(TEST_CONFIG);

    // Test session creation
    const sessionId = api.sessionManager.createSession();
    assert(sessionId.startsWith('session_'), 'Session ID should start with session_');

    // Test session retrieval
    const session = api.sessionManager.getSession(sessionId);
    assert(session !== null, 'Session should be retrievable');
    assert(session.id === sessionId, 'Session ID should match');

    // Test operation addition
    const operationId = 'test_operation';
    const operation = { type: 'test', input: 'test input' };
    api.sessionManager.addOperation(sessionId, operationId, operation);

    const retrievedSession = api.sessionManager.getSession(sessionId);
    assert(retrievedSession.operations.has(operationId), 'Operation should be added to session');

    // Test operation update
    api.sessionManager.updateOperation(sessionId, operationId, 'completed', { result: 'success' });
    const updatedOperation = retrievedSession.operations.get(operationId);
    assert(updatedOperation.status === 'completed', 'Operation status should be updated');
    assert(updatedOperation.result.result === 'success', 'Operation result should be set');
}

/**
 * Test: Progress Tracking
 */
async function testProgressTracking() {
    const api = new JestirAPI(TEST_CONFIG);

    // Test callback registration
    const operationId = 'test_operation';
    const callback = (progress) => {
        assert(progress.stage === 'test', 'Progress stage should match');
        assert(progress.message === 'test message', 'Progress message should match');
    };

    api.progressTracker.registerCallback(operationId, callback);
    assert(api.progressTracker.callbacks.has(operationId), 'Callback should be registered');

    // Test progress emission
    api.progressTracker.emitProgress(operationId, {
        stage: 'test',
        message: 'test message'
    });

    // Test callback removal
    api.progressTracker.removeCallback(operationId);
    assert(!api.progressTracker.callbacks.has(operationId), 'Callback should be removed');
}

/**
 * Test: Error Handling
 */
async function testErrorHandling() {
    // Test APIError creation
    const error = new APIError('Test error', 'TEST_ERROR', { field: 'value' });
    assert(error.message === 'Test error', 'Error message should match');
    assert(error.code === 'TEST_ERROR', 'Error code should match');
    assert(error.details.field === 'value', 'Error details should match');
    assert(error.name === 'APIError', 'Error name should be APIError');
    assert(error.timestamp !== undefined, 'Error timestamp should be set');

    // Test error serialization
    const json = error.toJSON();
    assert(json.error === true, 'JSON error flag should be true');
    assert(json.message === 'Test error', 'JSON message should match');
    assert(json.code === 'TEST_ERROR', 'JSON code should match');
    assert(json.details.field === 'value', 'JSON details should match');
    assert(json.timestamp !== undefined, 'JSON timestamp should be set');
}

/**
 * Test: Session Info
 */
async function testSessionInfo() {
    const api = new JestirAPI(TEST_CONFIG);

    // Test session info retrieval
    const sessionId = api.sessionManager.createSession();
    const sessionInfo = api.getSessionInfo(sessionId);

    assert(sessionInfo.sessionId === sessionId, 'Session ID should match');
    assert(sessionInfo.created !== undefined, 'Session created date should be set');
    assert(sessionInfo.status === 'active', 'Session status should be active');
    assert(Array.isArray(sessionInfo.operations), 'Operations should be an array');

    // Test non-existent session
    try {
        api.getSessionInfo('non-existent');
        assert(false, 'Should throw error for non-existent session');
    } catch (error) {
        assert(error instanceof APIError, 'Should throw APIError');
        assert(error.code === 'SESSION_NOT_FOUND', 'Error code should be SESSION_NOT_FOUND');
    }
}

/**
 * Test: All Sessions
 */
async function testAllSessions() {
    const api = new JestirAPI(TEST_CONFIG);

    // Create multiple sessions
    const sessionId1 = api.sessionManager.createSession();
    const sessionId2 = api.sessionManager.createSession();

    const allSessions = api.getAllSessions();
    assert(allSessions.length >= 2, 'Should have at least 2 sessions');

    const sessionIds = allSessions.map(s => s.id);
    assert(sessionIds.includes(sessionId1), 'Should include first session');
    assert(sessionIds.includes(sessionId2), 'Should include second session');
}

/**
 * Test: Session Cleanup
 */
async function testSessionCleanup() {
    const api = new JestirAPI(TEST_CONFIG);

    // Create a session
    const sessionId = api.sessionManager.createSession();
    const session = api.sessionManager.getSession(sessionId);

    // Mock old session by setting old timestamp
    session.created = new Date(Date.now() - 25 * 60 * 60 * 1000); // 25 hours ago

    // Cleanup sessions older than 24 hours
    api.cleanupSessions(24 * 60 * 60 * 1000);

    // Session should be removed
    assert(api.sessionManager.getSession(sessionId) === null, 'Old session should be removed');
}

/**
 * Test: API Method Signatures
 */
async function testAPIMethodSignatures() {
    const api = new JestirAPI(TEST_CONFIG);

    // Test that all expected methods exist
    const expectedMethods = [
        'generateContext',
        'generateNewContext',
        'generateOutline',
        'generateStory',
        'generateCompleteStory',
        'validateContext',
        'validateTemplates',
        'searchEntities',
        'listEntities',
        'getTokenStats',
        'getSessionInfo',
        'getAllSessions',
        'cleanupSessions'
    ];

    for (const method of expectedMethods) {
        assert(typeof api[method] === 'function', `Method ${method} should exist`);
    }
}

/**
 * Main test runner
 */
async function runAllTests() {
    console.log('Jestir API Test Suite');
    console.log('====================\n');

    const tests = [
        ['API Constructor', testConstructor],
        ['Session Management', testSessionManagement],
        ['Progress Tracking', testProgressTracking],
        ['Error Handling', testErrorHandling],
        ['Session Info', testSessionInfo],
        ['All Sessions', testAllSessions],
        ['Session Cleanup', testSessionCleanup],
        ['API Method Signatures', testAPIMethodSignatures]
    ];

    for (const [testName, testFunction] of tests) {
        await runTest(testName, testFunction);
    }

    // Print summary
    console.log('\nTest Summary');
    console.log('============');
    console.log(`Total: ${testResults.total}`);
    console.log(`Passed: ${testResults.passed}`);
    console.log(`Failed: ${testResults.failed}`);

    if (testResults.failed > 0) {
        console.log('\nFailed Tests:');
        for (const error of testResults.errors) {
            console.log(`  - ${error.test}: ${error.error}`);
        }
        process.exit(1);
    } else {
        console.log('\n✅ All tests passed!');
        process.exit(0);
    }
}

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
    runAllTests().catch(error => {
        console.error('Test runner error:', error);
        process.exit(1);
    });
}

export { runAllTests, runTest, assert };
