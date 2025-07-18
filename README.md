# Pepper Edu-Assistant: An Attention-Aware Robotic Tutor

This project implements an interactive and adaptive tutoring system using the SoftBank Pepper robot. The system is designed to act as an "Educational Assistant," delivering lessons on various subjects while monitoring the student's visual attention. Based on the detected attention level, the robot adapts its feedback to enhance the learning experience.

The core of the project is a closed-loop system:
1.  **Computer Vision** analyzes the user's gaze to determine if they are "ATTENTIVE" or "DISTRACTED".
2.  **The Robot's Interaction Logic** uses this attention data to provide personalized feedback during lessons.
3.  **Data Logging and Benchmarking** tools are included to analyze the session's effectiveness and visualize the correlation between attention and performance.

## 🏛️ Project Architecture

The system operates in three main phases:

1.  **Offline - Attention Analysis (`attention_analysis.py`)**:
    This script processes a sequence of images (or frames from a video) of the user. It uses MediaPipe to detect facial landmarks and iris positions to classify each frame as `ATTENTIVE` or `DISTRACTED`. The output is a time-stamped log file (`attention_log.csv`) that serves as the "ground truth" for the user's attention during the live session.

2.  **Online - Interactive Session (`pepper_interaction.py`)**:
    This is the main interaction script, run through the **MODIM framework**. It simulates a live teaching session with the Pepper robot.
    - It reads the pre-generated `attention_log.csv`.
    - It presents lessons and quizzes on multiple subjects (Science, History, Math, Music).
    - It calculates an "Attention Score" for each topic based on the log and adapts its feedback.
    - It logs the results of the session (attention score, correctness of answers) into `benchmark_log.csv`.

3.  **Post-Hoc - Benchmarking (`generate_graphs.py`)**:
    After the session, this script reads `benchmark_log.csv` and generates a series of graphs to visualize the session's results, showing trends and correlations between student attention and learning success.

### Workflow Diagram




## ✨ Key Features

-   **Gaze-Based Attention Detection**: Uses MediaPipe for robust iris and face tracking to estimate user attention.
-   **Adaptive Interaction**: The robot's feedback changes based on whether the student was attentive during the explanation of a topic.
-   **Multi-Subject Curriculum**: Includes extendable lesson plans for Science, History, Math, and Music.
-   **Interactive Web GUI**: A simple, clean web interface displays lesson content, questions, and a real-time attention score bar.
-   **General Quiz Mode**: A randomized quiz that pulls questions from all subjects to test overall knowledge.
-   **Automated Benchmarking**: Automatically logs session data and provides a script to generate insightful performance graphs.

## 🔧 Setup and Installation

This project was developed and tested in a **Python 2.7** environment, as required by the version of the MODIM framework used.

### 1. Dependencies
Install the required Python libraries using `pip`. It is recommended to use `python -m pip` to ensure packages are installed for the correct Python interpreter.

```bash
# For attention_analysis.py and generate_graphs.py
python -m pip install opencv-python
python -m pip install mediapipe
python -m pip install numpy
python -m pip install pandas
python -m pip install matplotlib
python -m pip install seaborn
