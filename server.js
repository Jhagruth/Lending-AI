/*
 * =================================================================
 * UNIFIED BACKEND SERVER
 * =================================================================
 * This server now handles two functions:
 * 1. Powers the AI Assistant chatbot via /api/chat.
 * 2. Acts as a proxy to the Python Risk Copilot via /api/assess.
 */

// --- 1. IMPORT NECESSARY PACKAGES ---
require('dotenv').config();
const express = require('express');
const cors = require('cors');
// This line is corrected to match package.json
const { BedrockRuntimeClient, InvokeModelCommand } = require('@aws-sdk/client-bedrock-runtime');
const multer = require('multer');
const axios = require('axios');
const path = require('path');

// --- 2. INITIALIZE THE APPLICATION ---
const app = express();
const port = 3000;

let bedrockClient;
try {
    // This line is corrected to use the correct client
    bedrockClient = new BedrockRuntimeClient({
        region: process.env.AWS_REGION || 'us-east-1'
    });
} catch (error) {
    console.error('Failed to initialize Bedrock client:', error);
}

const upload = multer({ storage: multer.memoryStorage() });

app.use(cors());
app.use(express.json({ limit: '50mb' }));

// --- 3. CHATBOT API ENDPOINT ---
app.post('/api/chat', async (req, res) => {
    if (!bedrockClient) {
        return res.status(500).json({ error: 'Bedrock client not initialized.' });
    }
    try {
        const { conversation } = req.body;
        const lastUserMessage = conversation[conversation.length - 1];
        const prompt = `Human: ${lastUserMessage.content}\n\nAssistant:`;

        const titanRequestBody = {
            inputText: prompt,
            textGenerationConfig: { maxTokenCount: 512, temperature: 0.7, topP: 0.9 }
        };

        const command = new InvokeModelCommand({
            modelId: 'amazon.titan-text-express-v1',
            contentType: 'application/json',
            accept: 'application/json',
            body: JSON.stringify(titanRequestBody)
        });

        const response = await bedrockClient.send(command);
        const responseBody = JSON.parse(new TextDecoder().decode(response.body));
        const reply = responseBody.results[0].outputText.trim();
        
        res.json({ reply });
    } catch (error) {
        console.error("Error calling AWS Bedrock API:", error);
        res.status(500).json({ error: 'An error occurred while communicating with the AI service.' });
    }
});

// --- 4. RISK COPILOT API ENDPOINT (PROXY) ---
app.post('/api/assess', upload.single('entities'), async (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: 'No file uploaded.' });
    }
    try {
        const entities = JSON.parse(req.file.buffer.toString('utf8'));
        
        const requestBody = {
            entities: Array.isArray(entities) ? entities : [entities]
        };

        const pythonApiUrl = 'http://127.0.0.1:8000/assess_batch/';
        const response = await axios.post(pythonApiUrl, requestBody, {
            headers: { 'Content-Type': 'application/json' },
            timeout: 120000 
        });

        res.json(response.data);
    } catch (error) {
        console.error("Failed to proxy request to Python API:", error.message);
        const errorResponse = error.response ? error.response.data : 'The Python API server is not responding.';
        res.status(500).json({ error: 'Error processing assessment.', details: errorResponse });
    }
});


// --- 5. HEALTH CHECK ENDPOINT ---
app.get('/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        timestamp: new Date().toISOString(),
        services: {
            chatbot: bedrockClient ? 'available' : 'unavailable',
            risk_assessment: 'available (proxy)'
        }
    });
});

// --- 6. START THE SERVER ---
app.listen(port, () => {
    console.log(`✅ Server is running and listening at http://localhost:3000`);
    console.log("Waiting for requests from the chatbot frontend...");
});

