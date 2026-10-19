# Weaponeering Analysis System UI

A comprehensive Vue.js web application for weaponeering analysis with interactive mapping, AI analysis module, and data management capabilities.

## Technology Stack

- **Frontend Framework**: Vue.js 3 (Vite)
- **CSS Framework**: Bootstrap 5
- **UI Icons**: Bootstrap Icons
- **Routing**: Vue Router 4
- **HTTP Client**: Axios (ready to use)
- **Maps**: Leaflet-compatible (with placeholder implementation)
- **Data**: Mock API with realistic sample data

## Project Features

### Left Sidebar - Target Analysis Form
1. **Target Source Selection** - Checkbox selection for:
   - เป้าหมายร่วม
   - เป้าหมาย ทอ.
   - เป้าหมาย กกล.สุรนารี
   - เป้าหมายทางลึก
   - อื่นๆ

2. **Target Type** - Dropdown menu with 10 target types
3. **Structure Type** - Dropdown for 6 structure types
4. **Strength Level** - Dropdown for 3 strength levels
5. **Coordinates** - Latitude/Longitude inputs
6. **Image Upload** - File upload for target images
7. **Target Details** - Rich text description area
8. **PK Value** - Probability of Kill (0-1)
9. **CEP Value** - Circular Error Probable in meters
10. **AI Analysis** - Launch AI analysis module
11. **Save Data** - Save form data

### Center - Interactive Map
- Geographic visualization with buffer zones
- Concentric circles showing threat radius (0-100m, 100-200m, 200-300m, 300m+)
- Current coordinates display
- Color-coded zones

### Right Panel - Results & Analysis
- **Top 5 Recommendations** - Table showing recommended targets
- **AI Analysis Results** - Detailed analysis output
- **Chatbot** - Interactive AI Assistant
- **Simulator** - Embedded video player
- **Export Functions** - Save data as PDF, Word, Excel

### Header Navigation
- Logo and system title
- Menu links (Analysis, Reports)
- Current date/time display (real-time)
- User info (Admin01)
- Logout functionality
- Data refresh button

### Reports Page
- Historical data list with statistics
- Export functionality
- Delete operations

## Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Development Server

```bash
npm run dev
```

Runs on `http://localhost:5173`

## Project Structure

```
src/
├── components/       # Reusable Vue components
├── views/           # Page components
├── services/        # Mock API and services
├── router/          # Vue Router config
├── App.vue          # Root component
└── main.js          # Entry point
```

## Browser Support

- Chrome, Firefox, Safari, Edge (latest versions)

## License

Proprietary - Weaponeering System
