# Requirements Document

## Introduction

The LLM Analysis Quiz System is an automated application that solves data-related quiz tasks using Large Language Models. The system consists of three main components: (1) a prompt defense/attack mechanism for code word protection/extraction, (2) an API endpoint that receives and validates quiz requests, and (3) an automated quiz solver that performs data sourcing, preparation, analysis, and visualization tasks within strict time constraints.

## Glossary

- **Quiz System**: The complete LLM Analysis Quiz application
- **API Endpoint**: The HTTP server that receives POST requests with quiz tasks
- **Quiz Solver**: The automated component that visits quiz URLs and solves data tasks
- **System Prompt**: A defensive prompt designed to prevent code word revelation
- **User Prompt**: An offensive prompt designed to extract the code word
- **Code Word**: A randomly generated secret word that the system prompt must protect
- **Quiz URL**: A unique URL containing a JavaScript-rendered HTML page with a data task
- **Submit Endpoint**: The URL specified in each quiz page where answers must be posted
- **Secret String**: A student-provided verification token used to authenticate requests
- **Headless Browser**: A browser automation tool that executes JavaScript to render quiz pages
- **Answer Payload**: A JSON response containing the solution to a quiz task

## Requirements

### Requirement 1

**User Story:** As a student, I want to submit my system and user prompts through a Google Form, so that they can be evaluated against other students' prompts

#### Acceptance Criteria

1. THE Quiz System SHALL accept a system prompt with a maximum length of 100 characters
2. THE Quiz System SHALL accept a user prompt with a maximum length of 100 characters
3. THE Quiz System SHALL store the student email address for identification
4. THE Quiz System SHALL store a secret string for request verification
5. THE Quiz System SHALL store an API endpoint URL for receiving quiz tasks

### Requirement 2

**User Story:** As a student, I want my system prompt to resist revealing the code word, so that I can earn points when tested against other students' user prompts

#### Acceptance Criteria

1. WHEN the system prompt is combined with a code word and tested against a user prompt, THE Quiz System SHALL prevent the LLM from revealing the code word in its output
2. THE Quiz System SHALL design the system prompt to be effective across multiple LLM models including GPT-5-nano
3. THE Quiz System SHALL ensure the system prompt works with case-insensitive code word matching
4. THE Quiz System SHALL ensure the system prompt handles code words with punctuation variations

### Requirement 3

**User Story:** As a student, I want my user prompt to extract the code word from system prompts, so that I can earn points when tested against other students' system prompts

#### Acceptance Criteria

1. WHEN the user prompt is tested against a system prompt containing a code word, THE Quiz System SHALL cause the LLM to reveal the code word in its output
2. THE Quiz System SHALL design the user prompt to override defensive system prompts
3. THE Quiz System SHALL ensure the user prompt works across multiple LLM models
4. THE Quiz System SHALL ensure the extracted code word is detectable through case-insensitive matching

### Requirement 4

**User Story:** As an evaluator, I want to send POST requests to the student's API endpoint, so that I can trigger quiz-solving tasks

#### Acceptance Criteria

1. THE API Endpoint SHALL accept POST requests with JSON payloads containing email, secret, and url fields
2. WHEN the secret matches the stored secret, THE API Endpoint SHALL respond with HTTP 200 status
3. WHEN the JSON payload is invalid, THE API Endpoint SHALL respond with HTTP 400 status
4. WHEN the secret does not match, THE API Endpoint SHALL respond with HTTP 403 status
5. THE API Endpoint SHALL validate all required fields are present in the request

### Requirement 5

**User Story:** As a quiz solver, I want to visit quiz URLs and extract task instructions, so that I can understand what needs to be solved

#### Acceptance Criteria

1. WHEN a quiz URL is received, THE Quiz Solver SHALL use a headless browser to render the JavaScript-based HTML page
2. THE Quiz Solver SHALL extract the base64-encoded task instructions from the rendered page
3. THE Quiz Solver SHALL decode the task instructions to obtain human-readable text
4. THE Quiz Solver SHALL parse the submit endpoint URL from the task instructions
5. THE Quiz Solver SHALL identify the required answer format (boolean, number, string, base64 URI, or JSON object)

### Requirement 6

**User Story:** As a quiz solver, I want to download and process data files, so that I can perform the required analysis

#### Acceptance Criteria

1. WHEN a task requires downloading a file, THE Quiz Solver SHALL retrieve the file from the specified URL
2. THE Quiz Solver SHALL handle multiple file formats including PDF, CSV, JSON, and images
3. WHEN a file is a PDF, THE Quiz Solver SHALL extract text and tables from specified pages
4. WHEN a file requires authentication, THE Quiz Solver SHALL use provided API headers
5. THE Quiz Solver SHALL handle file downloads that complete within the 3-minute time limit

### Requirement 7

**User Story:** As a quiz solver, I want to perform data analysis tasks, so that I can compute the correct answers

#### Acceptance Criteria

1. THE Quiz Solver SHALL perform data filtering operations on retrieved datasets
2. THE Quiz Solver SHALL perform data aggregation operations including sum, count, and average
3. THE Quiz Solver SHALL perform data transformation operations including reshaping and cleansing
4. THE Quiz Solver SHALL apply statistical analysis when required by the task
5. THE Quiz Solver SHALL handle geo-spatial analysis tasks when specified
6. THE Quiz Solver SHALL handle network analysis tasks when specified

### Requirement 8

**User Story:** As a quiz solver, I want to generate visualizations, so that I can provide chart-based answers

#### Acceptance Criteria

1. WHEN a task requires a chart, THE Quiz Solver SHALL generate the visualization as an image
2. THE Quiz Solver SHALL encode image visualizations as base64 URIs for submission
3. THE Quiz Solver SHALL ensure the base64-encoded answer is under 1MB in size
4. THE Quiz Solver SHALL support multiple chart types including bar, line, scatter, and pie charts
5. THE Quiz Solver SHALL generate interactive visualizations when specified by the task

### Requirement 9

**User Story:** As a quiz solver, I want to submit answers to the correct endpoint, so that my solutions can be evaluated

#### Acceptance Criteria

1. THE Quiz Solver SHALL construct a JSON payload with email, secret, url, and answer fields
2. THE Quiz Solver SHALL post the answer to the submit endpoint specified in the quiz page
3. THE Quiz Solver SHALL ensure the total JSON payload size is under 1MB
4. THE Quiz Solver SHALL complete the entire solve-and-submit process within 3 minutes of receiving the initial POST request
5. THE Quiz Solver SHALL not hardcode any submit URLs

### Requirement 10

**User Story:** As a quiz solver, I want to handle incorrect answers and retry, so that I can improve my score

#### Acceptance Criteria

1. WHEN an answer is incorrect and a response is received within 3 minutes, THE Quiz Solver SHALL be allowed to re-submit
2. WHEN multiple submissions occur, THE Quiz Solver SHALL ensure only the last submission within 3 minutes is evaluated
3. WHEN an incorrect answer response includes a new URL, THE Quiz Solver SHALL have the option to skip to the new URL
4. THE Quiz Solver SHALL parse the response to determine if the answer was correct
5. THE Quiz Solver SHALL extract the reason field when an answer is incorrect

### Requirement 11

**User Story:** As a quiz solver, I want to handle sequential quiz tasks, so that I can complete multi-stage quizzes

#### Acceptance Criteria

1. WHEN a correct answer response includes a new URL, THE Quiz Solver SHALL automatically proceed to solve the next quiz
2. WHEN a correct answer response does not include a new URL, THE Quiz Solver SHALL recognize the quiz sequence is complete
3. THE Quiz Solver SHALL maintain the 3-minute time constraint across the entire quiz sequence
4. THE Quiz Solver SHALL track the sequence of quiz URLs visited
5. THE Quiz Solver SHALL handle quiz sequences of arbitrary length

### Requirement 12

**User Story:** As a quiz solver, I want to use LLMs for complex tasks, so that I can solve tasks requiring natural language understanding

#### Acceptance Criteria

1. WHEN a task requires text interpretation, THE Quiz Solver SHALL use an LLM to understand the instructions
2. WHEN a task requires vision capabilities, THE Quiz Solver SHALL use an LLM with vision support
3. WHEN a task requires transcription, THE Quiz Solver SHALL use an LLM with audio processing capabilities
4. THE Quiz Solver SHALL select appropriate LLM models based on task requirements
5. THE Quiz Solver SHALL handle LLM API rate limits and errors gracefully

### Requirement 13

**User Story:** As a student, I want to host my code in a public GitHub repository, so that evaluators can review my implementation

#### Acceptance Criteria

1. THE Quiz System SHALL be hosted in a public GitHub repository
2. THE Quiz System SHALL include an MIT LICENSE file in the repository root
3. THE Quiz System SHALL include a README with setup and deployment instructions
4. THE Quiz System SHALL include all source code required to run the system
5. THE Quiz System SHALL document all dependencies and environment requirements

### Requirement 14

**User Story:** As a student, I want to test my endpoint with a demo quiz, so that I can verify my implementation works correctly

#### Acceptance Criteria

1. THE Quiz System SHALL accept POST requests to the demo endpoint at https://tds-llm-analysis.s-anand.net/demo
2. WHEN testing with the demo endpoint, THE Quiz System SHALL follow the same solve-and-submit workflow
3. THE Quiz System SHALL validate that the demo quiz completes successfully
4. THE Quiz System SHALL log the demo quiz results for debugging
5. THE Quiz System SHALL handle demo quiz errors without crashing
