# Implementation Plan - Bidirectional AI SaaS Restaurant Discovery Dashboard (Legacy Streamlit)

We will transform the Zomato Gourmet Advisor interface into a premium, full-screen AI SaaS dashboard inspired by Apple Vision Pro UI and modern AI products. All user inputs, filters, recommendation cards, and AI reasoning panels will live natively inside the main workspace to achieve maximum visual coherence.

## User Review Required

> [!IMPORTANT]
> - **Bidirectional Communication**: We use Streamlit's custom component bridge. This allows selections made in the HTML UI to trigger the backend database query and Gemini orchestrator.
> - **Responsive Height**: A `ResizeObserver` in the HTML document will automatically notify Streamlit when dropdowns expand/collapse or cards load, adjusting the iframe height in real-time to prevent scrollbars or content clipping.
> - **Decorative Sidebar**: The left sidebar will be styled as a frosted glass navigation layout (Dashboard, Discover, Settings) to match the premium Dribbble aesthetic, while all controls (location, budget, cuisine, rating, special requests) will be placed in the center workspace.

## Proposed Changes

---

### Presentation Layer

#### [NEW] index.html
We will create a custom HTML page containing:
- **Futuristic Dark Theme**: Deep violet backdrops, radial blue-aqua gradients, and animated glowing floating background blobs.
- **Glassmorphism CSS**: Frosted panels using `backdrop-filter: blur(20px)`, thin translucent borders (`rgba(255, 255, 255, 0.08)`), and soft shadows.
- **Search Panel Inputs**:
  - **Search Location**: A searchable dropdown that lists Zomato areas.
  - **Budget Band**: A custom step-slider representing Low, Medium, and High bands.
  - **Cuisine Selector**: Interactive chips for popular cuisines (North Indian, Chinese, Italian, Cafe, South Indian) with active toggle states, plus a dropdown for other options.
  - **Rating Bar**: A glowing star-selection bar (from 1 to 5 stars).
  - **Special Request Tags**: Toggle tags for "Outdoor Seating", "Family Friendly", "Romantic", "Rooftop" plus an input text field for custom requests.
  - **Recommendations Count**: A futuristic numeric stepper with `-` and `+` buttons.
- **AI Orb & Experience**:
  - A glowing, pulsing holographic AI orb near the search section.
  - Smooth loading spinners and pulsing text when a query is processing.
- **Recommendations Grid**:
  - Modern grid cards with soft blur overlays, 3D hover scale interactions, and restaurant information.
  - Automatic thematic image selection using curated Unsplash food/restaurant photos matching the cuisine.
- **AI Insights Side Panel**:
  - A right-side panel that displays the overall AI summary, matching confidence indicator (with an SVG circular progress ring), and the full AI rationale of the selected restaurant.

#### [MODIFY] main.py
Update the Streamlit entrypoint to:
- Inject CSS to hide the standard Streamlit sidebar, main header, footer, and padding, allowing the dashboard to take up 100% of the screen.
- Declare the component:
  ```python
  import streamlit.components.v1 as components
  gourmet_dashboard = components.declare_component("gourmet_dashboard", path="app/static")
  ```
- Store preferences, recommendations, and execution states in `st.session_state`.
- Capture inputs sent from the component. If the component returns a search action, parse the preferences, call `get_recommendations`, save results to `st.session_state`, and trigger `st.rerun()`.

---

## Verification Plan

### Automated Tests
- Run `.venv/bin/python -m pytest` to check that the underlying business logic remains 100% functional.

### Manual Verification
1. Spin up the Streamlit server:
   ```bash
   .venv/bin/streamlit run app/main.py
   ```
2. Open the page in a wide desktop browser. Verify that the Streamlit sidebar is hidden and the new dashboard takes the entire screen.
3. Test inputs (changing location, cuisine chips, rating, special requests) directly in the UI.
4. Click "Generate Recommendations". Verify that the loading orb triggers, and real Zomato recommendation cards are displayed with high-quality food images.
5. Click on individual cards and verify that the right-side AI Insights panel shows the detailed rationale and confidence score.
