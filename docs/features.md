# Features Catalog

This document lists the planned and implemented capabilities of the scientific graphics application. It is a high-level catalog for reference and planning. Tasks and implementation details are tracked in `BACKLOG.md`.

---

## 1. Main Window Layout and Functions

- Contains a central figure, a document options bar, a properties panel, a toolbar, a data management panel, a Status bar, a document window and a Help Bar (see https://helpx.adobe.com/illustrator/desktop/get-started/learn-the-basics/workspace-overview.html)

---

### 1.1. The Central Figure
- Upon opening a new project, the figure is empty with a + symbol in the middle which, if clicked, asks for the preferred layout which can then be created
- Multi-subplot canvas with default layouts
- Supports drag-and-drop of csv/txt files to load and plot in a subplot
- Supports drag-and-drop of a png/jpg file to load and plot in a subplot
- Automatic default rendering on data load
- Zooming and panning

---

### 1.2. Document Options Bar
- Horizontal bar at the top of the window for general settings
- File: New figure (empty), New figure from template, Open figure, Open recent figures, Close, Save project, Save a Copy, Export figure (vector (SVG, PDF, EPS),  raster (PNG, TIFF) and as python source code (for the matloblib plot)), Exit
- Shows keyboard shortcuts next to the commands
- Edit: Undo, Redo, Cut, Copy, Paste, Colors, Settings, Keyboard Shortcuts
- Plot:
    - Manage data
    - Arrange layout
    - Load data (One or more files for 2d or files or folders for 3d, image import PNG/JPG into plots)
    - Plot type: Line/Symbol (line plot, scatter plot, area plot, stacked area, fill area), Column/Bar (Basic, stacked, floating column/bar, 3D column), Pie/Doughnut (2D pie, 3D pie, pie of pie, bar of pie, doughnut, Pie map), Multi-axis/multi-panel (multi axis, multi panel, tile grid map), waterfall (2D waterfall, 3D waterfall), contour & heatmap (Contour, heatmap, correlation map), 3D graphs (3D symbol/trajectory/vector, 3D function, 3D waterfall, 3D surface plot) (https://www.originlab.com/index.aspx?go=products/origin/graphing)
    - axis settings (depends on plot type, e.g. for normal 2D: left/right, ticks in/out, ticks on/off, labels on/off, axis labels, axis limits, axis on/off)
    - plot settings (depends on plot type, e.g. line color, line style, line width etc.)
- Object: Transform, Align, Arrange, Distribute, Group, Ungroup, Hide, Show, Crop Image
- Type: Font, Size, Special Characters, Math mode
- Analysis: Statistical analysis, fitting functions with built-in and user-defined functions, Signal processing: smoothing, filtering, FFT
- Help: Tutorials, Updates

---

### 1.3. Properties & Layers Panel
- See https://helpx.adobe.com/illustrator/desktop/get-started/learn-the-basics/properties-panel-overview.html
- Shows the options relevant to the selected object, tool, or workflow
- Vertical panel with the options arranged in sections.
- Properties panel by default
- Selection-based controls: When you select an object, the Properties panel updates to show controls specific to your selection.
    - Image object: Crop, Black and white, contrast
    - Text object: Font, size, color, alignment, and paragraph settings
    - Multiple objects: Shared editable properties, alignment and distribution tools for objects
    - Figure: Size, orientation, and background color settings
    - Plots: Manage data (e.g. show file), Plot type, axis settings, plot settings, file path(s)
- Layers panel:
    - Layer system with visibility, locking, and z-order
    - Grouping and ungrouping of objects
    - Selection and multi-selection of objects
    - Object stacking and ordering
    - Drag-and-drop reordering of objects/layers

---

### 1.4. Toolbar
-The toolbar contains tools for creating and editing artwork, and for navigation on the canvas. It is docked to the left of the document window by default. All tools have a little icon
- Shape tools: rectangles, ellipses, lines
- Path tool (Bezier curves)
- Text tools: on-canvas text, rich text (bold, italic), LaTeX support
- Eyedropper tool for copying object styles
- Reusable styles/templates for stroke, fill, and gradients
- Plot tool: 
- Zoom tool
- Rotate tool
- Selection: Select entire objects or groups
- Direct selection: Select and adjust anchor points and segments to reshape paths
- Figure: Adjust the figure size

---

## 1.5. Data Management Panel
- Interactive data worksheet for editing data
- Multi-sheet workbook support

---

### 1.6. Status Bar
- Horizontal bar at the bottom of the window.
- Shows current zoom level and selected tool

---

### 1.7. Document Window
- Tabs for the different projects/ documents open in the same application

---

### 1.8. Help Bar
- Horizontal bar at the bottom of the window
- Shows context-specific tips, keyboard shortcuts, and step-by-step instructions for the tool you select.

---

## 2. Workflow Project & File Management
- Path handling via pathlib
- Externalized configuration management via Pydantic

