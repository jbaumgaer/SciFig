# Software Requirements Specification (SRS)

## 1. Introduction

This document specifies the functional and non-functional requirements for the Data Analysis and Figure Preparation GUI. It defines what the system must do from a user's perspective.

## 2. Functional Requirements

### 2.1. Canvas and Layout
-   The user shall be able to view a canvas containing one or more subplots.
-   The application shall provide a default layout of subplots upon starting.

### 2.2. Data Handling
-   The user shall be able to load data into a subplot by dragging and dropping a `.csv` file onto it.
-   The system shall parse the `.csv` file and store the data in a structured format (DataFrame).
-   The system shall automatically render a default plot upon successful data loading.

### 2.3. Object Selection and Interaction
-   The user shall be able to select a single subplot by clicking on it.
-   The user shall be able to open a properties panel for a selected subplot by double-clicking it.

### 2.4. Properties Inspector
-   The user shall be able to view and edit the properties of a selected subplot in a dedicated side panel.
-   The following properties shall be editable:
    -   Plot Title
    -   X-Axis Label
    -   Y-Axis Label
    -   Data column used for the X-Axis
    -   Data column used for the Y-Axis
    -   Minimum and maximum limits for the X-Axis
    -   Minimum and maximum limits for the Y-Axis
-   All changes made in the properties inspector shall be reflected on the canvas in real-time.

### 2.5. Command History
-   The user shall be able to undo any action that modifies the state of a plot (e.g., changing a title, axis limits, or data columns).
-   The user shall be able to redo any undone action.

## 3. Non-Functional Requirements

### 3.1. Usability
-   The interface should be intuitive and discoverable for users familiar with both graphics editors and data plotting software.
-   The workflow shall be non-modal, avoiding disruptive pop-up dialogs for core editing tasks.

### 3.2. Performance
-   The UI shall remain responsive during user interactions, including dragging objects and editing properties.
-   Data loading for moderately-sized files shall be performed in the background to prevent freezing the UI.
