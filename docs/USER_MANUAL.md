# FailSafe User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Web Interface](#web-interface)
4. [Browser Extension](#browser-extension)
5. [API Usage](#api-usage)
6. [Understanding Results](#understanding-results)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

## Introduction

FailSafe is an AI-powered fact-checking and misinformation analysis system that helps users verify the accuracy of claims, detect logical fallacies, and identify AI-generated content. The system provides comprehensive analysis reports with evidence, confidence scores, and detailed explanations.

### Key Features

- **Fact-Checking**: Verify claims against reliable sources
- **Logical Fallacy Detection**: Identify common reasoning errors
- **AI Content Detection**: Detect AI-generated text
- **Multilingual Support**: Analyze content in multiple languages
- **Structured Argument Graphs**: Visualize argument structure
- **Provenance Tracking**: Track analysis sources and methods
- **Human-AI Collaboration**: Provide feedback and overrides

## Getting Started

### Accessing FailSafe

1. **Web Interface**: Visit the FailSafe website
2. **Browser Extension**: Install the Chrome extension
3. **API**: Use the REST API for programmatic access

### First Analysis

1. **Enter your claim** in the text input field
2. **Click "Analyze"** to start the analysis
3. **Review the results** in the detailed report
4. **Provide feedback** to help improve the system

## Web Interface

### Main Interface

The web interface consists of several key components:

#### Input Section
- **Text Input**: Enter the claim you want to analyze
- **URL Input**: Analyze content from a web page
- **Language Selection**: Choose the language of your content
- **Analysis Options**: Configure analysis parameters

#### Results Display
- **Verdict**: Overall assessment (True/False/Mixed/Unverifiable)
- **Confidence Score**: How confident the system is in its assessment
- **Evidence**: Supporting sources and information
- **Fallacies**: Detected logical errors
- **AI Detection**: Whether content appears to be AI-generated
- **SAG Visualization**: Interactive argument graph

### Navigation Tabs

#### Overview Tab
- **Verification Details**: Method and confidence of verification
- **AI Detection**: Analysis of content generation
- **Multilingual Data**: Language detection and processing info
- **Feedback Form**: Rate the analysis quality

#### Evidence Tab
- **Source List**: All evidence sources used
- **Relevance Scores**: How relevant each source is
- **Source Types**: Academic, news, expert opinions
- **Provenance Info**: When and how sources were retrieved

#### Fallacies Tab
- **Detected Fallacies**: List of logical errors found
- **Explanations**: Detailed explanations of each fallacy
- **Severity Levels**: High, medium, or low severity
- **Examples**: How to avoid similar fallacies

#### SAG Tab
- **Interactive Graph**: Visual representation of arguments
- **Node Details**: Information about each argument component
- **Edge Relationships**: How arguments connect
- **RDF Data**: Machine-readable argument structure

#### Provenance Tab
- **Analysis Chain**: Complete history of the analysis
- **Source Tracking**: Where information came from
- **Processing Steps**: How the analysis was performed
- **Export Options**: Download analysis data

### Interactive Features

#### SAG Visualization
- **Zoom**: Use mouse wheel or zoom controls
- **Pan**: Click and drag to move around
- **Node Selection**: Click nodes to see details
- **Layout Options**: Force-directed, hierarchical, or circular layouts

#### Feedback System
- **Rating**: Rate analysis accuracy (1-5 stars)
- **Comments**: Provide detailed feedback
- **Override**: Suggest corrections to results
- **Source Rating**: Rate individual evidence sources

## Browser Extension

### Installation

1. **Download** the extension from the Chrome Web Store
2. **Add to Chrome** by clicking "Add to Chrome"
3. **Pin the extension** to your toolbar for easy access

### Usage

#### Quick Analysis
1. **Select text** on any webpage
2. **Right-click** and choose "Analyze with FailSafe"
3. **View results** in the popup window

#### Popup Interface
1. **Click the extension icon** in your toolbar
2. **Enter text** or paste content
3. **Click "Analyze"** for instant results
4. **View detailed report** in the popup

#### Context Menu
- **Analyze Selection**: Analyze selected text
- **Analyze Page**: Analyze entire page content
- **Highlight Claims**: Automatically highlight verifiable claims

### Extension Settings

Access settings by right-clicking the extension icon:

- **API URL**: Configure backend endpoint
- **Language**: Set default analysis language
- **Auto-analyze**: Enable automatic analysis
- **Notifications**: Configure alert preferences

## API Usage

### Basic Analysis

```bash
curl -X POST "https://api.failsafe.com/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The Earth is flat",
    "language": "en"
  }'
```

### Response Format

```json
{
  "success": true,
  "data": {
    "claim_id": "uuid",
    "verdict": "false",
    "confidence": 0.95,
    "evidence": [...],
    "verification": {...},
    "fallacies": [...],
    "ai_detection": {...},
    "multilingual": {...},
    "sag": {...},
    "provenance": {...}
  }
}
```

### Advanced Options

```json
{
  "text": "Your claim here",
  "url": "https://example.com/article",
  "language": "en",
  "options": {
    "include_ai_detection": true,
    "include_sag": true,
    "include_provenance": true,
    "confidence_threshold": 0.8
  },
  "metadata": {
    "source": "user_input",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

## Understanding Results

### Verdict Types

#### True
- **Meaning**: The claim is factually correct
- **Confidence**: Usually high (0.8+)
- **Evidence**: Strong supporting sources
- **Example**: "Water boils at 100°C at sea level"

#### False
- **Meaning**: The claim is factually incorrect
- **Confidence**: Usually high (0.8+)
- **Evidence**: Strong contradictory sources
- **Example**: "The Earth is flat"

#### Mixed
- **Meaning**: The claim is partially true
- **Confidence**: Variable (0.5-0.8)
- **Evidence**: Mixed supporting and contradictory sources
- **Example**: "Social media improves communication" (true but oversimplified)

#### Unverifiable
- **Meaning**: Cannot be determined with current evidence
- **Confidence**: Low (0.0-0.5)
- **Evidence**: Insufficient or conflicting sources
- **Example**: "The meaning of life is 42"

### Confidence Scores

- **0.9-1.0**: Very High Confidence
- **0.8-0.9**: High Confidence
- **0.7-0.8**: Medium-High Confidence
- **0.6-0.7**: Medium Confidence
- **0.5-0.6**: Low-Medium Confidence
- **0.0-0.5**: Low Confidence

### Evidence Quality

#### Source Types
- **Academic**: Peer-reviewed research, studies
- **News**: Reputable news organizations
- **Expert**: Expert opinions and analysis
- **Government**: Official government sources
- **International**: International organizations

#### Relevance Scores
- **0.9-1.0**: Highly Relevant
- **0.8-0.9**: Very Relevant
- **0.7-0.8**: Relevant
- **0.6-0.7**: Somewhat Relevant
- **0.5-0.6**: Marginally Relevant
- **0.0-0.5**: Not Relevant

### Logical Fallacies

#### High Severity
- **Ad Hominem**: Attacking the person instead of the argument
- **Straw Man**: Misrepresenting someone's argument
- **Cherry Picking**: Selecting only favorable evidence

#### Medium Severity
- **Hasty Generalization**: Drawing broad conclusions from limited evidence
- **False Dilemma**: Presenting only two options when more exist
- **Slippery Slope**: Assuming a chain of events without evidence

#### Low Severity
- **Appeal to Authority**: Using authority as evidence without expertise
- **Appeal to Emotion**: Using emotional language instead of logic

### AI Detection

#### Detection Methods
- **LLM Detector**: Machine learning model trained on AI-generated text
- **Stylometry**: Analysis of writing style patterns
- **Metadata Check**: Examination of document metadata
- **Ensemble Voting**: Combination of multiple detection methods

#### Confidence Levels
- **0.8-1.0**: Very Likely AI-Generated
- **0.6-0.8**: Likely AI-Generated
- **0.4-0.6**: Uncertain
- **0.2-0.4**: Likely Human-Written
- **0.0-0.2**: Very Likely Human-Written

## Advanced Features

### Structured Argument Graphs (SAG)

SAGs provide a visual representation of how arguments are structured:

#### Node Types
- **Claim**: The main assertion being made
- **Evidence**: Supporting information
- **Reasoning**: Logical connections
- **Conclusion**: Final assessment
- **Assumption**: Implicit premises

#### Edge Types
- **Supports**: Evidence that supports a claim
- **Contradicts**: Evidence that contradicts a claim
- **Implies**: Logical implication
- **Assumes**: Implicit assumption

#### Interaction
- **Zoom**: Use mouse wheel or zoom controls
- **Pan**: Click and drag to move around
- **Select**: Click nodes to see details
- **Layout**: Choose between different layout algorithms

### Provenance Tracking

Provenance provides a complete audit trail of the analysis:

#### Entry Types
- **INPUT**: Original claim or content
- **PROCESSING**: Analysis steps performed
- **EVIDENCE**: Sources retrieved and used
- **VERIFICATION**: Fact-checking process
- **ANALYSIS**: Final analysis results
- **OUTPUT**: Generated report

#### Information Included
- **Timestamp**: When each step occurred
- **Source ID**: Unique identifier for each step
- **Parent IDs**: What previous steps led to this one
- **Metadata**: Additional context and parameters
- **Data Hash**: Cryptographic hash for integrity
- **Confidence Score**: How confident the system was
- **Processing Time**: How long each step took

### Human-AI Collaboration

#### Feedback System
- **Accuracy Rating**: Rate how accurate the analysis was
- **Source Quality**: Rate the quality of evidence sources
- **Logical Flow**: Rate the logical reasoning
- **Overall Assessment**: Overall quality rating

#### Override System
- **Verdict Override**: Change the overall verdict
- **Confidence Override**: Adjust confidence scores
- **Evidence Override**: Add or remove evidence
- **Fallacy Override**: Mark fallacies as false positives

#### Collaboration Insights
- **Feedback Trends**: See how feedback changes over time
- **Override Patterns**: Identify common override reasons
- **Quality Metrics**: Track system improvement
- **User Contributions**: See your impact on the system

### Multilingual Support

#### Supported Languages
- **English**: Full support
- **Spanish**: Full support
- **French**: Full support
- **German**: Full support
- **Chinese**: Basic support
- **Arabic**: Basic support

#### Features
- **Language Detection**: Automatically detect content language
- **Translation**: Translate content for analysis
- **Cross-lingual Evidence**: Find evidence in different languages
- **Cultural Context**: Consider cultural differences in analysis

## Troubleshooting

### Common Issues

#### Analysis Not Starting
- **Check internet connection**: Ensure you're connected to the internet
- **Verify API status**: Check if the FailSafe API is running
- **Clear browser cache**: Clear your browser's cache and cookies
- **Try different browser**: Test with a different web browser

#### Results Not Loading
- **Wait for processing**: Analysis can take 10-30 seconds
- **Check text length**: Very long texts may take longer
- **Refresh the page**: Try refreshing the browser page
- **Contact support**: If the issue persists, contact support

#### Extension Not Working
- **Check installation**: Ensure the extension is properly installed
- **Enable permissions**: Grant necessary permissions to the extension
- **Update extension**: Make sure you have the latest version
- **Restart browser**: Try restarting your web browser

#### API Errors
- **Check API key**: Ensure you have a valid API key
- **Verify endpoint**: Check that you're using the correct API endpoint
- **Check rate limits**: Ensure you're not exceeding rate limits
- **Review request format**: Verify your request follows the API specification

### Error Messages

#### "Analysis Failed"
- **Cause**: Internal server error or processing failure
- **Solution**: Try again in a few minutes, contact support if persistent

#### "Invalid Input"
- **Cause**: Malformed request or unsupported content
- **Solution**: Check your input format and try again

#### "Rate Limit Exceeded"
- **Cause**: Too many requests in a short time
- **Solution**: Wait before making another request

#### "Service Unavailable"
- **Cause**: System maintenance or overload
- **Solution**: Try again later, check system status

### Getting Help

#### Self-Service
- **Documentation**: Check the user manual and API reference
- **FAQ**: Look for answers to common questions
- **Community**: Ask questions in the community forum

#### Direct Support
- **Email**: Send detailed description of your issue
- **GitHub Issues**: Report bugs and request features
- **Discord**: Get real-time help from the community

## FAQ

### General Questions

**Q: How accurate is FailSafe?**
A: FailSafe achieves high accuracy on fact-checking tasks, but results should be used as a starting point for verification, not as absolute truth.

**Q: Can FailSafe analyze any type of content?**
A: FailSafe works best with factual claims and arguments. It may struggle with creative writing, poetry, or highly subjective content.

**Q: How long does analysis take?**
A: Most analyses complete in 10-30 seconds, depending on content length and complexity.

**Q: Is my data private?**
A: Yes, FailSafe respects user privacy and does not store personal information without consent.

### Technical Questions

**Q: What languages are supported?**
A: Currently, English, Spanish, French, and German have full support, with basic support for Chinese and Arabic.

**Q: Can I use FailSafe programmatically?**
A: Yes, FailSafe provides a REST API for programmatic access.

**Q: How do I get an API key?**
A: API keys are available through the FailSafe website. Contact support for enterprise access.

**Q: What are the rate limits?**
A: Free tier: 100 requests per minute. Paid tiers have higher limits.

### Usage Questions

**Q: Can I analyze entire articles?**
A: Yes, you can analyze long-form content, but it may take longer and results may be less precise.

**Q: How do I provide feedback?**
A: Use the feedback forms in the web interface or browser extension to rate analyses and provide comments.

**Q: Can I override analysis results?**
A: Yes, you can override verdicts, confidence scores, and other results through the collaboration interface.

**Q: How do I export analysis data?**
A: Use the export options in the provenance tab to download analysis data in various formats.

### Troubleshooting Questions

**Q: Why is my analysis taking so long?**
A: Complex analyses or high system load can cause delays. Try again in a few minutes.

**Q: Why are the results different from what I expected?**
A: FailSafe uses objective criteria for analysis. Check the evidence and reasoning provided in the report.

**Q: Can I analyze images or videos?**
A: Currently, FailSafe only analyzes text content. Image and video analysis may be added in future versions.

**Q: How do I report a bug?**
A: Use the GitHub Issues page or contact support with detailed information about the problem.

### Privacy and Security Questions

**Q: Is my content stored?**
A: Content may be temporarily stored for analysis but is not permanently retained without consent.

**Q: Can I delete my analysis history?**
A: Yes, you can request deletion of your analysis history through the privacy settings.

**Q: Is the API secure?**
A: Yes, the API uses HTTPS encryption and follows security best practices.

**Q: Can I use FailSafe offline?**
A: No, FailSafe requires an internet connection to access its analysis capabilities.

## Conclusion

FailSafe is a powerful tool for fact-checking and misinformation analysis. By understanding how to use its features effectively, you can make more informed decisions about the information you encounter online.

Remember that FailSafe is a tool to assist human judgment, not replace it. Always use critical thinking and verify important information through multiple sources.

For additional help and support, visit the FailSafe website or contact our support team.






