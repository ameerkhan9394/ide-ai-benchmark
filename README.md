# ImBIOS's Cursor Model Benchmark

A personal benchmarking framework to evaluate and compare different AI models in Cursor for various software engineering tasks and use cases.

## 🚀 Features

- **AI Model Comparison**: Automated testing of different AI models (Claude, GPT-4, etc.) in Cursor
- **Software Engineering Benchmarks**: Code generation, refactoring, debugging, and documentation tasks
- **Performance Metrics**: Response time, code quality, accuracy, and completion rate analysis
- **Real-world Use Cases**: Daily software engineering scenarios and workflows
- **Automated Evaluation**: AI-powered judging system to assess model performance
- **Comprehensive Reporting**: Detailed comparison reports with rankings and insights

## 📋 Prerequisites

- **Linux** (Ubuntu/Debian preferred)
- **Python 3.13+**
- **Cursor Editor** with AI model access (Claude, GPT-4, etc.)
- **API Keys** for AI models you want to benchmark
- **GUI Environment** (for interactive testing) or **Xvfb** (for headless automation)

## 📦 Installation

1. **Clone the repository**:

```bash
git clone https://github.com/ImBIOS/benchmark-cursor-model.git
cd benchmark-cursor-model
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

4. **Verify Cursor AppImage path**:

```bash
ls -la $CURSOR_PATH
```

## 🧪 Running Tests

### Quick Start

```bash
# Run all benchmarks (quick mode)
python scripts/run_tests.py --quick

# Run specific benchmark categories
python scripts/run_tests.py --code-generation
python scripts/run_tests.py --performance
python scripts/run_tests.py --workflows

# Compare specific models
python scripts/run_tests.py --models claude,gpt4

# Generate detailed reports
python scripts/run_tests.py --detailed-report
```

### Manual Test Execution

```bash
# Code generation benchmarks
pytest tests/test_basic_functionality.py -v

# Performance and quality benchmarks
pytest tests/test_performance_benchmarks.py -v

# Real-world workflow benchmarks
pytest tests/test_user_workflows.py -v

# All AI model benchmarks
pytest tests/ -v
```

### Headless Testing (for CI/servers)

```bash
# Start Xvfb
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# Run tests
python scripts/run_tests.py --headless --all
```

## 📊 Benchmark Categories

### 1. Code Generation Tests (`test_basic_functionality.py`)

- Function and class creation
- Algorithm implementation
- Unit test generation
- Documentation writing
- Code completion accuracy
- Syntax correctness validation

### 2. Performance & Quality Benchmarks (`test_performance_benchmarks.py`)

- Response time measurement
- Code quality assessment
- Memory efficiency of generated code
- Compilation/execution success rate
- Best practices adherence
- Security vulnerability detection

### 3. Real-world Engineering Workflows (`test_user_workflows.py`)

- Bug fixing scenarios
- Code refactoring tasks
- Feature implementation workflows
- API integration challenges
- Database query optimization
- DevOps automation scripts
- Code review simulations

## 🏗️ Framework Architecture

```
.
├── src/
│   └── cursor_automation.py      # AI model benchmarking automation
├── tests/
│   ├── test_basic_functionality.py
│   ├── test_performance_benchmarks.py
│   └── test_user_workflows.py
├── scripts/
│   └── run_tests.py              # Test runner script
├── .github/workflows/
│   └── test.yml                  # CI/CD pipeline
├── pyproject.toml                # Project configuration
├── uv.lock                       # Dependency lock file
├── install.py                    # Environment setup script
├── reports/                      # Test reports (generated)
├── screenshots/                  # Screenshots (generated)
└── test_images/                  # Template images (generated)
```

## 🔧 Configuration

### Environment Variables

```bash
# Cursor application path
export CURSOR_PATH="/path/to/cursor"

# AI model API keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"

# Display for headless mode
export DISPLAY=:99
```

### Test Markers

```bash
# Run only fast tests
pytest -m "not slow"

# Run specific test types
pytest -m "basic"
pytest -m "performance"
pytest -m "workflow"
```

## 📈 AI Model Benchmarking

The framework evaluates AI models across multiple dimensions:

### Code Quality Metrics

- Syntax correctness and compilation success
- Code style and best practices adherence
- Performance and efficiency of generated code
- Security vulnerability assessment

### Response Performance

- Time to first response
- Complete solution generation time
- Context understanding accuracy
- Follow-up iteration speed

### Software Engineering Capabilities

- Problem-solving approach quality
- Architecture and design decisions
- Testing and debugging effectiveness
- Documentation and comment quality

## 🎯 Writing Custom Tests

### Basic Test Structure

```python
import pytest
from cursor_automation import CursorAutomation

class TestCustom:
    @pytest.fixture
    def cursor_app(self):
        app = CursorAutomation()
        assert app.launch_app()
        yield app
        app.close_app()

    def test_custom_functionality(self, cursor_app):
        cursor_app.focus_window()
        cursor_app.key_combo('ctrl', 'n')
        cursor_app.type_text('Hello World')
        screenshot = cursor_app.take_screenshot('custom_test.png')
        assert os.path.exists(screenshot)
```

### Image-Based Testing

```python
def test_image_detection(self, cursor_app):
    # Create template image first
    cursor_app.key_combo('ctrl', 'shift', 'p')
    region = (100, 100, 300, 200)
    cursor_app.create_test_image(region, 'command_palette.png')

    # Later, find and click the image
    found = cursor_app.click_image('test_images/command_palette.png')
    assert found, "Command palette should be found and clicked"
```

## 🔄 CI/CD Integration

The framework includes GitHub Actions workflow (`.github/workflows/test.yml`):

- **Multi-Python Testing**: Tests on Python 3.11, 3.12, 3.13
- **Automated Benchmarking**: Daily performance monitoring
- **Artifact Collection**: Screenshots, reports, and benchmark data
- **PR Comments**: Automatic benchmark result reporting

### Manual CI Setup

```bash
# Local CI simulation
xvfb-run -a --server-args="-screen 0 1920x1080x24 -ac +extension GLX" \
    python -m pytest tests/ -v
```

## 📊 Reports and Output

### HTML Reports

- `reports/basic-report.html` - Basic functionality results
- `reports/performance-report.html` - Performance benchmarks
- `reports/workflow-report.html` - User workflow results
- `htmlcov/index.html` - Code coverage report

### JSON Data Files

- `benchmark_results.json` - Startup time data
- `memory_benchmark.json` - Memory usage data
- `cpu_benchmark.json` - CPU utilization data
- `file_operations_benchmark.json` - File operation performance

### Screenshots

- Automatically captured during test execution
- Stored in `screenshots/` directory
- Named with timestamps and test context

## 🐛 Troubleshooting

### Common Issues

1. **Cursor application not found**

   ```bash
   export CURSOR_PATH="/correct/path/to/cursor"
   ```

2. **AI model API key issues**

   ```bash
   # Check API key configuration
   export OPENAI_API_KEY="your-actual-key"
   export ANTHROPIC_API_KEY="your-actual-key"
   ```

3. **Display issues in headless mode**

   ```bash
   Xvfb :99 -screen 0 1920x1080x24 &
   export DISPLAY=:99
   ```

4. **Model response timeout**

   ```bash
   # Increase timeout in configuration
   # Check network connectivity and API limits
   ```

### Debug Mode

```bash
# Run with verbose output
pytest tests/ -v -s

# Enable debug logging
export PYTHONPATH=$PYTHONPATH:src
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from cursor_automation import CursorAutomation
app = CursorAutomation()
app.launch_app()
"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Development Setup

```bash
# Set up development environment
python -m venv venv
source venv/bin/activate

# Install in development mode with test dependencies
pip install -e .[test]

# Or using uv
uv sync --extra test

# Run linting (install dev tools first)
pip install black flake8
black src/ tests/
flake8 src/ tests/

# Run tests with coverage
pytest --cov=src tests/
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for general questions
- **Email**: [Your email for direct support]

## 🚀 Future Enhancements

- [ ] Support for more AI models (Gemini, Anthropic Claude variants, local models)
- [ ] Multi-language programming benchmarks (Python, JS, Go, Rust, etc.)
- [ ] Complex project scenario testing (microservices, full-stack apps)
- [ ] AI model cost-effectiveness analysis
- [ ] Real-time leaderboard and ranking system
- [ ] Integration with popular development workflows
- [ ] Automated benchmark report generation and sharing

---

**Happy Benchmarking!** 🚀
