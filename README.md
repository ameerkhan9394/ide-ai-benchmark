# IDE AI Benchmark

A comprehensive benchmarking framework to evaluate and compare different AI models (Claude, OpenAI, Gemini, etc.) across multiple IDEs and development environments (Cursor IDE, Windsurf IDE, Trae IDE, Claude Code CLI, VSCode + GitHub Copilot, etc.).

## 🚀 Features

- **Multi-IDE Support**: Automated testing across Cursor, Windsurf, Trae, VSCode, and more
- **Cross-Model Comparison**: Compare Claude, OpenAI, Gemini, and other AI models
- **Standardized Benchmarks**: Consistent testing methodology across all IDE/model combinations
- **Performance Metrics**: Response time, code quality, accuracy, and completion rate analysis
- **Real-world Scenarios**: Daily software engineering tasks and workflows
- **Automated Evaluation**: AI-powered judging system to assess model performance objectively
- **Comprehensive Reporting**: Detailed comparison reports with rankings and insights across IDEs

## 🎯 Supported IDEs & AI Models

### Supported IDEs
- **Cursor IDE** - Claude, OpenAI, Gemini
- **Windsurf IDE** - Claude, OpenAI, Gemini
- **Trae IDE** - Various models
- **Claude Code CLI** - Claude models
- **VSCode** - GitHub Copilot, various extensions
- **Others** - Extensible framework for adding new IDEs

### Supported AI Models
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Haiku, Claude 3 Opus
- **OpenAI**: OpenAI, OpenAI Turbo
- **Google**: Gemini Pro, Gemini Ultra
- **GitHub**: Copilot (OpenAI based)
- **Others**: Extensible for new models

## 📋 Prerequisites

- **Linux** (Ubuntu/Debian preferred)
- **Python 3.13+**
- **Target IDEs** installed and configured
- **API Keys** for AI models you want to benchmark
- **GUI Environment** (for interactive testing) or **Xvfb** (for headless automation)

## 📦 Installation

1. **Clone the repository**:

```bash
git clone https://github.com/ImBIOS/ide-ai-benchmark.git
cd ide-ai-benchmark
```

2. **Set up Python environment**:

### Using venv (recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .

# Install with test dependencies
pip install -e .[test]
```

### Using uv (fast alternative)

```bash
# Install dependencies
uv sync

# Install with test dependencies
uv sync --extra test
```

3. **Install system dependencies** (Ubuntu/Debian):

```bash
sudo apt-get update
sudo apt-get install -y \
    xvfb \
    x11-utils \
    xdotool \
    scrot \
    python3-tk \
    python3-dev \
    libxtst6 \
    libxss1 \
    libgtk-3-0 \
    python3.13-tk \
    python3.13-dev
```

4. **Install and configure IDEs**:

```bash
# Download Cursor IDE
wget https://download.cursor.sh/linux/appImage/x64 -O cursor.AppImage
chmod +x cursor.AppImage

# Download Windsurf IDE (example)
# wget <windsurf-download-url> -O windsurf.AppImage
# chmod +x windsurf.AppImage

# Install VSCode with Copilot
sudo snap install --classic code
# Then install GitHub Copilot extension
```

5. **Configure API keys**:

```bash
cp .env.example .env
# Edit .env with your API keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"
```

## 🧪 Running Benchmarks

### Quick Start

```bash
# Run benchmarks across all IDEs and models
python scripts/run_tests.py --all-ides --all-models

# Compare specific IDE/model combinations
python scripts/run_tests.py --ide cursor --model claude-3.5-sonnet
python scripts/run_tests.py --ide vscode --model github-copilot

# Run specific benchmark categories
python scripts/run_tests.py --code-generation --ide cursor,windsurf
python scripts/run_tests.py --performance --model gpt-4,claude-3.5-sonnet

# Generate cross-IDE comparison report
python scripts/run_tests.py --cross-ide-report
```

### Advanced Benchmarking

```bash
# Test specific IDE with multiple models
python scripts/run_tests.py --ide cursor --models claude-3.5-sonnet,gpt-4,gpt-4-turbo

# Run performance benchmarks only
python scripts/run_tests.py --performance --timeout 300

# Headless testing for CI/CD
python scripts/run_tests.py --headless --quick

# Custom test scenarios
python scripts/run_tests.py --custom-scenarios scenarios/web-dev-tasks.json
```

### Manual Test Execution

```bash
# Test specific IDE functionality
pytest tests/test_ide_functionality.py::TestCursorIDE -v
pytest tests/test_ide_functionality.py::TestWindsurfIDE -v

# Cross-IDE performance comparison
pytest tests/test_cross_ide_performance.py -v

# AI model quality benchmarks
pytest tests/test_ai_model_quality.py -v

# Real-world workflow tests
pytest tests/test_development_workflows.py -v
```

## 📊 Benchmark Categories

### 1. Code Generation Tests (`test_code_generation.py`)

Compare AI models across IDEs for:
- Function and class creation
- Algorithm implementation
- Unit test generation
- Documentation writing
- API integration code
- Database query generation

### 2. Performance & Quality Benchmarks (`test_performance_quality.py`)

Evaluate:
- Response time across IDE/model combinations
- Code quality and best practices adherence
- Memory efficiency of generated code
- Compilation/execution success rate
- Security vulnerability detection
- Code maintainability scores

### 3. Cross-IDE Workflow Tests (`test_cross_ide_workflows.py`)

Real-world engineering scenarios:
- Bug fixing efficiency
- Code refactoring quality
- Feature implementation speed
- Debugging assistance effectiveness
- Code review automation
- Project scaffolding capabilities

### 4. AI Model Capabilities (`test_ai_capabilities.py`)

Model-specific testing:
- Context understanding depth
- Multi-language programming support
- Complex reasoning tasks
- Code explanation quality
- Architecture decision support

## 🏗️ Framework Architecture

```
.
├── src/
│   ├── __init__.py
│   └── ide_automation.py          # Multi-IDE automation framework
├── tests/
│   ├── test_ide_functionality.py  # Basic IDE automation tests
│   ├── test_code_generation.py    # Code generation benchmarks
│   ├── test_performance_quality.py # Performance and quality tests
│   ├── test_cross_ide_workflows.py # Cross-IDE workflow tests
│   └── test_ai_capabilities.py    # AI model capability tests
├── scripts/
│   ├── run_tests.py               # Multi-IDE test runner
│   └── generate_reports.py       # Cross-IDE comparison reports
├── config/
│   ├── ide_configs.yml           # IDE-specific configurations
│   └── model_configs.yml         # AI model configurations
├── scenarios/
│   ├── web-dev-tasks.json        # Web development scenarios
│   ├── data-science-tasks.json   # Data science scenarios
│   └── devops-tasks.json         # DevOps scenarios
├── reports/                       # Generated benchmark reports
├── screenshots/                   # IDE screenshots during tests
└── results/                       # Raw benchmark data
```

## 🔧 Configuration

### Environment Variables

```bash
# IDE Application Paths
export CURSOR_PATH="/path/to/cursor"
export WINDSURF_PATH="/path/to/windsurf"
export VSCODE_PATH="/usr/bin/code"
export TRAE_PATH="/path/to/trae"

# AI Model API Keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"

# Display for headless mode
export DISPLAY=:99
```

### IDE Configuration (`config/ide_configs.yml`)

```yaml
cursor:
  launch_args: ["--no-sandbox", "--disable-dev-shm-usage"]
  models: ["claude-3.5-sonnet", "gpt-4", "gpt-4-turbo"]
  shortcuts:
    ai_chat: "ctrl+l"
    command_palette: "ctrl+shift+p"

windsurf:
  launch_args: ["--no-sandbox"]
  models: ["claude-3.5-sonnet", "gpt-4", "gemini-pro"]
  shortcuts:
    ai_chat: "ctrl+i"
    command_palette: "ctrl+shift+p"

vscode:
  launch_args: ["--no-sandbox"]
  models: ["github-copilot"]
  shortcuts:
    copilot_chat: "ctrl+shift+i"
    command_palette: "ctrl+shift+p"
```

## 📈 Cross-IDE AI Model Benchmarking

The framework provides comprehensive comparison across multiple dimensions:

### Performance Metrics

- **Response Time**: Time to generate code across IDE/model combinations
- **Completion Quality**: Accuracy and usefulness of generated code
- **Context Awareness**: How well models understand project context
- **IDE Integration**: Smoothness of model integration within each IDE

### Capability Assessment

- **Code Generation**: Function, class, and algorithm creation quality
- **Code Explanation**: Ability to explain existing code
- **Debugging**: Bug identification and fix suggestions
- **Refactoring**: Code improvement recommendations
- **Testing**: Unit test generation and test-driven development

### Cross-IDE Consistency

- **Model Behavior**: How consistently models perform across different IDEs
- **Feature Parity**: Comparison of AI features available in each IDE
- **Workflow Efficiency**: Which IDE/model combinations work best for specific tasks

## 🎯 Writing Custom Benchmarks

### Basic Test Structure

```python
import pytest
from ide_automation import create_ide_automation

class TestCustomBenchmark:
    @pytest.fixture(params=["cursor", "windsurf", "vscode"])
    def ide_app(self, request):
        app = create_ide_automation(request.param)
        assert app.launch_app()
        yield app
        app.close_app()

    def test_custom_ai_functionality(self, ide_app):
        # Test AI model switching
        models = ide_app.get_ai_models()
        for model in models:
            assert ide_app.switch_ai_model(model)

            # Test AI completion
            prompt = "Write a Python function to sort a list"
            assert ide_app.trigger_ai_completion(prompt)

            response = ide_app.get_ai_response()
            assert "def" in response  # Basic validation
```

### Cross-IDE Comparison Test

```python
def test_cross_ide_code_generation():
    ides = ["cursor", "windsurf", "vscode"]
    prompt = "Create a REST API endpoint for user management"
    results = {}

    for ide_name in ides:
        ide = create_ide_automation(ide_name)
        ide.launch_app()

        # Test with each available model
        for model in ide.get_ai_models():
            ide.switch_ai_model(model)
            ide.trigger_ai_completion(prompt)
            response = ide.get_ai_response()

            results[f"{ide_name}_{model}"] = {
                "response": response,
                "quality_score": evaluate_code_quality(response),
                "response_time": measure_response_time()
            }

        ide.close_app()

    # Compare results across IDEs
    generate_comparison_report(results)
```

## 📊 Reports and Output

### Cross-IDE Comparison Reports

- `reports/cross-ide-comparison.html` - Comprehensive IDE/model comparison
- `reports/model-performance-matrix.html` - Performance matrix across all combinations
- `reports/workflow-efficiency.html` - Task-specific IDE/model recommendations

### Individual IDE Reports

- `reports/cursor-benchmark.html` - Cursor IDE specific results
- `reports/windsurf-benchmark.html` - Windsurf IDE specific results
- `reports/vscode-benchmark.html` - VSCode specific results

### Raw Data

- `results/benchmark_data.json` - Complete benchmark dataset
- `results/response_times.csv` - Response time measurements
- `results/quality_scores.csv` - Code quality assessments

## 🔄 CI/CD Integration

The framework includes GitHub Actions for continuous benchmarking:

```yaml
# .github/workflows/cross-ide-benchmark.yml
name: Cross-IDE AI Model Benchmark

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  benchmark:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        ide: [cursor, windsurf, vscode]

    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          pip install -e .[test]

      - name: Run IDE benchmarks
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          xvfb-run python scripts/run_tests.py --ide ${{ matrix.ide }} --all-models

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results-${{ matrix.ide }}
          path: reports/
```

## 🚀 Getting Started Guide

### 1. Quick Setup for Cursor vs VSCode Comparison

```bash
# Install the framework
git clone https://github.com/ImBIOS/ide-ai-benchmark.git
cd ide-ai-benchmark
pip install -e .[test]

# Set up API keys
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# Run comparison
python scripts/run_tests.py --ide cursor,vscode --models claude-3.5-sonnet,github-copilot --quick
```

### 2. Full Multi-IDE Benchmark

```bash
# Download and set up all IDEs
./scripts/setup_ides.sh

# Run comprehensive benchmark
python scripts/run_tests.py --all-ides --all-models --comprehensive

# Generate reports
python scripts/generate_reports.py --cross-ide-analysis
```

## 🐛 Troubleshooting

### IDE-Specific Issues

1. **Cursor not launching**
   ```bash
   export CURSOR_PATH="/correct/path/to/cursor.AppImage"
   chmod +x cursor.AppImage
   ```

2. **VSCode Copilot not working**
   ```bash
   code --install-extension GitHub.copilot
   # Authenticate Copilot in VSCode
   ```

3. **Windsurf configuration**
   ```bash
   # Check Windsurf installation
   ./windsurf.AppImage --version
   ```

### API Key Issues

```bash
# Verify API keys
python scripts/verify_api_keys.py

# Test model access
python -c "
from ide_automation import create_ide_automation
ide = create_ide_automation('cursor')
print(ide.get_ai_models())
"
```

## 🤝 Contributing

We welcome contributions to expand IDE and model support!

### Adding New IDEs

1. Create a new class inheriting from `IDEAutomation`
2. Implement all abstract methods
3. Add configuration in `config/ide_configs.yml`
4. Create tests in `tests/test_ide_functionality.py`

### Adding New AI Models

1. Update model lists in IDE classes
2. Implement model switching logic
3. Add API integration if needed
4. Update documentation

## 📝 License

TBD (To Be Determined)

## 📞 Support

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and ideas
- **Email**: Contact for enterprise support

## 🚀 Roadmap

- [ ] **IDE Support**: JetBrains IDEs, Sublime Text, Vim/Neovim
- [ ] **Model Support**: Local models (Ollama), CodeLlama, StarCoder
- [ ] **Advanced Metrics**: Code security analysis, performance benchmarks
- [ ] **Real-time Dashboard**: Live benchmark results and leaderboards
- [ ] **Custom Scenarios**: Industry-specific benchmark suites
- [ ] **Integration**: Slack/Discord notifications, webhook support

---

**Start benchmarking your AI coding assistants today!** 🚀
