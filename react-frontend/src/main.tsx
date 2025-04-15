// React core utilities for StrictMode, lazy loading, and Suspense
import { StrictMode, lazy, Suspense } from 'react'
// Function to create the root React DOM node
import { createRoot } from 'react-dom/client'
// Removed direct import of App to use lazy loading below
// import App from './App.tsx'
// Import global CSS styles
import './index.css'

// --- Lazy Loading --- 
// Lazily load the main App component.
// This means the code for App.tsx (and its imports) won't be included
// in the initial JavaScript bundle. It will be loaded automatically 
// in a separate chunk when it's first needed.
const App = lazy(() => import('./App.tsx'))

// --- Fallback Components --- 

// Basic Loading Fallback Component
// This component is displayed by Suspense while the lazy-loaded App component is loading.
const LoadingFallback = () => (
  <div style={{
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    fontSize: '1.2em'
  }}>
    Loading Application...
  </div>
);

// --- Application Root Rendering --- 

// Find the root DOM element where the React app will be mounted.
// Assumes an element with id='root' exists in your public/index.html file.
const container = document.getElementById('root');

// Ensure the container element exists before trying to render into it.
if (!container) {
  throw new Error("Failed to find the root element with id 'root'");
}

// Create a React root instance associated with the container DOM element.
// This is the standard way to initialize a React 18+ application.
const root = createRoot(container);

// Render the application into the root.
root.render(
  // StrictMode is a wrapper component that activates additional checks and warnings
  // for potential problems in the application during development. It does not affect
  // the production build.
  <StrictMode>
    {/* Suspense is required to handle the loading state of lazy-loaded components. */}
    {/* It shows the 'fallback' UI until the lazy component (App) has finished loading. */}
    <Suspense fallback={<LoadingFallback />}>
      {/* Render the main App component (which was lazy-loaded) */}
      <App />
    </Suspense>
  </StrictMode>,
);
