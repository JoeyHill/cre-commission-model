# Commission Model Web App

This project provides a web-based tool to help visualize and analyze sales commission models. It allows users to input salary, commission rates, and targets, and see the effects on take-home pay and effective commission rates across a range of sales amounts.

## Features

- **Interactive Web App**: Powered by [Streamlit](https://streamlit.io/), allows dynamic adjustment of commission parameters.
- **Visualization**: Uses Altair for interactive, clear graphical output of commission versus sales.
- **Customizable Model**: Configure base salary, target compensation, commission rates (before and after reaching target), and minimum sales thresholds.

## Usage

### Quick Start

1. **Clone the repository**
    ```bash
    git clone <this-repo-url>
    cd <repo-directory>
    ```

2. **Install dependencies**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ```

3. **Run the app**
    ```bash
    streamlit run main.py
    ```
    The app will be available at [http://localhost:8501](http://localhost:8501).

### Docker

If you have Docker installed, you can run the project without installing Python or any dependencies:

```bash
docker-compose up
```

Or build and run with Docker directly:
```bash
docker build -t commission-model .
docker run -p 8501:8501 commission-model
```

## Files

- `main.py` — Streamlit web app and core commission logic.
- `Dockerfile` — Container configuration.
- `docker-compose.yml` — For easy local setup.
- `requirements.txt` — Python dependencies.

## Development

We recommend using [VS Code](https://code.visualstudio.com/) with the Python extension.
Python 3.9+ is required (the Dockerfile uses Python 3.13-slim for lightweight builds).

## License

MIT License. See [LICENSE](LICENSE) for details.