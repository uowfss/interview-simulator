# interview-simulator

- A Python application that simulates technical interviews using AI-generated questions and real-time speech recognition.
- You need your own api keys to use AI question generation and responses.

## Features

- **Custom Job Descriptions**: Input any job description to generate relevant interview questions
- **AI Question Generation**: Uses OpenAI ChatGPT or Google Gemini to create interview questions
- **Speech-to-Text**: Records and transcribes verbal answers using speech recognition
- **Real-Time Feedback**: See transcriptions of your answers immediately
- **Secure Key Storage**: API keys stored securely using system keyring

## Dependencies

- Python 3.10+
- SpeechRecognition
- Google Generative AI
- OpenAI API
- Tkinter (usually included with Python)

## Usage

- Launch the application: use this command, python interview_simulator.py
- Interface:
  Select your preferred AI service (OpenAI/Google)
  Paste a job description in the text area
  Click "Generate Questions & Start Interview"
  Use "Start Listening" to answer questions verbally
  View real-time transcriptions in the chat interface

## Troubleshooting

Common Issues:
- API Errors: Ensure keys are valid and have sufficient permissions
- Microphone Access: Check system permissions for microphone
- Question Parsing: If questions don't appear, check terminal for raw API output
- Network Issues: Verify internet connection for API access

Debugging Tips:
- Run from terminal to see error logs
- Test with simple job descriptions first
- Verify API quotas haven't been exceeded

Note: This application requires valid API keys for either OpenAI or Google's Gemini services. Internet connection required for AI features.
