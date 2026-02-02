# Data Analysis and Figure Preparation GUI

This project is a scientific graphics application designed to combine the intuitive, fluid design capabilities of a vector graphics editor with the powerful data analysis and plotting features of scientific software.

The goal is to provide a seamless, interactive, and non-modal user experience where data visualization, analysis, and the creation of publication-quality figures are part of a single workflow.

## Core Technologies

*   **Python 3.10+**
*   **PySide6 (Qt 6)** for the user interface.
*   **Matplotlib** for the plotting canvas.
*   **Pandas** for data manipulation.

## Current State

The application is built on a "v2" architecture centered around a **scene graph** model, a **tool-based controller system**, a non-modal **properties inspector**, and a **command system** with full undo/redo support.

## Getting Started

### Python Executable Path
This project is configured to run with a specific Python interpreter located at:
`C:\Users\julia\.conda\envs\data_analysis_gui\python.exe`

### Setup and Execution

1.  **Install dependencies:**
    Use the specified Python executable to install the required packages.
    ```bash
    C:\Users\julia\.conda\envs\data_analysis_gui\python.exe -m pip install -r requirements.txt
    ```

2.  **Run the application:**
    ```bash
    C:\Users\julia\.conda\envs\data_analysis_gui\python.exe main.py
    ```

### Running Tests
To verify the application's correctness, run the test suite using `pytest`. It is crucial to use the project-specific Python executable to ensure tests run in the correct environment with all necessary dependencies.

```bash
C:\Users\julia\.conda\envs\data_analysis_gui\python.exe -m pytest
```