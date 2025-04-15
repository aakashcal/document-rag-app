// React core and hooks
import { useState, lazy, Suspense, useCallback } from "react";
// TanStack Query for server state management
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
// Material UI components for UI building blocks
import { 
  CssBaseline,       // Basic CSS reset/normalization
  ThemeProvider,     // Provides theme context to MUI components
  createTheme,       // Function to create a custom MUI theme
  Container,         // Responsive layout container
  Paper,             // Surface element with shadow
  Typography,        // Text component
  TextField,         // Input field
  Button,            // Button component
  Box,               // Generic layout/styling box
  CircularProgress,  // Loading spinner
  Alert,             // Alert message component
} from '@mui/material';
// Component for rendering Markdown content
import ReactMarkdown from 'react-markdown';
// Material UI Icons
import { Send as SendIcon, Clear as ClearIcon } from '@mui/icons-material';

// --- Configuration --- 

// Instantiate QueryClient for managing server state cache
const queryClient = new QueryClient({
  // Default options for all queries managed by this client
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false, // Prevent automatic refetching when the browser window regains focus
      retry: 1, // Retry failed network requests once before marking as error
      staleTime: 300000, // Consider cached data fresh for 5 minutes (300,000 ms)
    },
  },
});

// Define a custom Material UI theme
const theme = createTheme({
  // Override default typography settings
  typography: {
    fontFamily: '"Avenir", "Helvetica", "Arial", sans-serif', // Set a preferred font stack
  },
  // Override default color palette settings
  palette: {
    primary: {
      main: '#1976d2', // Define the primary color used across components
    },
    // Define secondary, error, warning, info, success colors if needed
  },
  // Override default styles for specific MUI components
  components: {
    MuiPaper: { // Target the Paper component
      styleOverrides: {
        root: { // Apply styles to the root element of Paper
          padding: '20px', // Add default padding inside Paper components
          marginBottom: '16px', // Add default bottom margin to Paper components
        },
      },
    },
  },
});

// --- Lazy Loaded Components --- 

// Lazily load components to improve initial bundle size and load time.
// These components will only be downloaded when they are first needed.
const DocumentUpload = lazy(() => import("./components/DocumentUpload"));
const DocumentSelector = lazy(() => import("./components/DocumentSelector"));

// --- Main Application Component --- 

const App = () => {
  // --- State Management --- 

  // State variable to hold the list of selected document IDs (filenames)
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]); 
  // State variable to hold the file selected for upload (if any)
  const [file, setFile] = useState<File | undefined>(undefined); 
  // State variable to hold the user's current question input
  const [question, setQuestion] = useState<string>(""); 
  // State variable to track if an API request (upload or query) is in progress
  const [isLoading, setIsLoading] = useState<boolean>(false); 
  // State variable to hold the answer received from the backend API
  const [answer, setAnswer] = useState<string | null>(null); 

  // --- Event Handlers --- 

  // Callback function to update the 'question' state when the text field changes.
  // useCallback ensures the function reference is stable unless dependencies change.
  const handleQuestionChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setQuestion(e.target.value); // Update state with the input's current value
  }, []); // No dependencies, so the function reference never changes

  // Callback function to clear the 'question' state.
  const handleClearQuestion = useCallback(() => {
    setQuestion(""); // Reset question state to empty string
  }, []); // No dependencies

  // Callback function to handle the main form submission (asking a question).
  // This function handles potential file uploads and the query API call.
  // useCallback ensures the function reference is stable unless dependencies change.
  const handleSubmit = useCallback(async () => {
    // Prevent submission if the question is empty
    if (!question) return; 
    
    // Set loading state to true to indicate processing and disable inputs/buttons
    setIsLoading(true); 
    // Clear any previous answer before making a new request
    setAnswer(null); 
    
    try {
      // --- Optional File Upload --- 
      // Check if a file has been selected for upload
      if (file) {
        // Create FormData object to send the file
        const formData = new FormData();
        formData.append('file', file); // Append the file with the key 'file'
        
        // Make a POST request to the backend upload endpoint
        const uploadResponse = await fetch('/api/documents/upload', {
          method: 'POST',
          body: formData, // Send the form data containing the file
        });
        
        // Check if the upload was successful
        if (!uploadResponse.ok) {
          // Log error if upload failed
          console.error('Failed to upload document'); 
          // Clear the file state even on failure to prevent retrying with the same file automatically
          setFile(undefined); 
        } else {
          // Log success message
          console.log("Upload successful, list may need manual refresh."); 
          // Clear the file state after successful upload
          setFile(undefined); 
          // Note: Ideally, the DocumentSelector would automatically refresh after upload.
          // This might require invalidating the 'documents' query in DocumentUpload or here.
        }
      }
      
      // --- Query Backend for Answer --- 
      // Make a POST request to the backend search endpoint
      const queryResponse = await fetch('/api/query/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json', // Indicate we're sending JSON data
        },
        // Construct the JSON payload for the query
        body: JSON.stringify({ 
          q: question, // Send the user's question
          // Include selected document IDs if any are selected, otherwise send undefined
          document_ids: selectedDocuments.length > 0 ? selectedDocuments : undefined 
        }),
      });
      
      // Check if the query request was successful
      if (!queryResponse.ok) {
        // Throw an error to be caught by the catch block
        throw new Error('Failed to get answer');
      }
      
      // Parse the JSON response from the backend
      const data = await queryResponse.json();
      // Update the 'answer' state with the received answer
      setAnswer(data.answer); 
    } catch (error) {
      // Handle any errors during upload or query
      console.error("Error:", error); // Log the error
      // Set a user-friendly error message in the answer state
      setAnswer("Error processing your request. Please try again."); 
    } finally {
      // This block always executes, whether the try block succeeded or failed
      // Reset the loading state to false
      setIsLoading(false); 
    }
  // Dependencies for useCallback: the function will be recreated if these values change.
  }, [question, file, selectedDocuments]);

  // --- Render Logic --- 

  return (
    // Provide the QueryClient to the application
    <QueryClientProvider client={queryClient}>
      {/* Provide the custom MUI theme to the application */}
      <ThemeProvider theme={theme}>
        {/* Apply baseline CSS normalization */}
        <CssBaseline />
        
        {/* Header Section */}
        {/* Use Box for custom styling of the header area */}
        <Box sx={{ 
          background: 'linear-gradient(90deg, #42a5f5 0%, #90caf9 100%)', // Gradient background
          py: 2, // Vertical padding (theme spacing units)
          boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.1)' // Subtle shadow
        }}>
          {/* Use Container to constrain header width and center it */}
          <Container maxWidth="lg">
            {/* Display the application title */}
            <Typography variant="h4" sx={{ color: 'white', fontWeight: 500, fontSize: '1.5rem' }}>
              Document RAG System
            </Typography>
          </Container>
        </Box>
        
        {/* Main Content Area */}
        {/* Use Container to constrain content width and center it, with vertical padding */}
        <Container maxWidth="lg" sx={{ py: 3 }}>
          {/* Flex container for the two-column layout */}
          <Box sx={{ 
            display: 'flex', 
            // Stack columns on small screens (xs), row layout on medium screens and up (md)
            flexDirection: { xs: 'column', md: 'row' }, 
            gap: 3 // Gap between the columns (theme spacing units)
          }}>
            
            {/* Left Column: Document Management */}
            <Box sx={{ width: { xs: '100%', md: '40%' } }}> {/* Takes 40% width on medium screens */}
              {/* Paper component for the Upload section */}
              <Paper>
                {/* Section title */}
                <Typography variant="h6" gutterBottom>Upload New Document</Typography>
                {/* Suspense handles the loading state of the lazy-loaded DocumentUpload component */}
                <Suspense fallback={<CircularProgress />}> {/* Show spinner while loading */}
                  {/* Render the DocumentUpload component */}
                  <DocumentUpload 
                    // Callback prop passed to DocumentUpload
                    // This function will be called by DocumentUpload upon successful upload
                    onUploadSuccess={(docId) => {
                      // Add the newly uploaded document's ID (filename) to the selected documents list
                      // Note: This assumes the upload endpoint returns the filename/ID
                      // It also automatically selects the document after upload.
                      setSelectedDocuments(prev => [...prev, docId]); 
                    }}
                  />
                </Suspense>
              </Paper>
              
              {/* Paper component for the Selector section */}
              <Paper>
                {/* Section title */}
                <Typography variant="h6" gutterBottom>Select Documents</Typography>
                {/* Suspense handles the loading state of the lazy-loaded DocumentSelector component */}
                <Suspense fallback={<CircularProgress />}> {/* Show spinner while loading */}
                  {/* Render the DocumentSelector component */}
                  <DocumentSelector 
                    selectedDocuments={selectedDocuments} // Pass current selection state
                    onDocumentSelect={setSelectedDocuments} // Pass the state setter function to allow updates
                  />
                </Suspense>
              </Paper>
            </Box>

            {/* Right Column: Question & Answer */}
            <Box sx={{ width: { xs: '100%', md: '60%' } }}> {/* Takes 60% width on medium screens */}
              {/* Paper component for the Question Input section */}
              <Paper>
                {/* Section title */}
                <Typography variant="h6" gutterBottom>Ask a Question</Typography>
                {/* Text input field for the user's question */}
                <TextField
                  fullWidth // Take full width of the container
                  variant="outlined" // Standard input style
                  value={question} // Controlled component: value linked to state
                  onChange={handleQuestionChange} // Update state on change
                  placeholder="e.g., What is the summary of the document?" // Placeholder text
                  margin="normal" // Standard margin
                  disabled={isLoading} // Disable input while API request is loading
                />

                {/* Container for the action buttons */}
                <Box sx={{ display: 'flex', mt: 2, gap: 2 }}> {/* Flex layout, top margin, gap */}
                  {/* Clear Button */}
                  <Button
                    fullWidth
                    variant="outlined" // Outlined style
                    color="secondary" // Use secondary theme color
                    onClick={handleClearQuestion} // Call handler to clear input
                    // Disable if loading OR if the question input is empty
                    disabled={isLoading || !question} 
                    startIcon={<ClearIcon />} // Icon at the start
                  >
                    Clear
                  </Button>
                  {/* Ask Button */}
                  <Button
                    fullWidth
                    variant="contained" // Contained (filled) style
                    color="primary" // Use primary theme color
                    onClick={handleSubmit} // Call handler to submit query
                    // Disable if loading OR if no documents are selected OR if the question is empty
                    disabled={isLoading || selectedDocuments.length === 0 || !question} 
                    // Show spinner inside button if loading, otherwise show Send icon
                    startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
                  >
                    {/* Change button text based on loading state */}
                    {isLoading ? "Processing..." : "Ask"}
                  </Button>
                </Box>
                
                {/* Conditional Warning Alert */}
                {/* Show only if no documents are currently selected */}
                {selectedDocuments.length === 0 && (
                  <Alert severity="warning" sx={{ mt: 1 }}>
                    Please select at least one document
                  </Alert>
                )}
              </Paper>

              {/* Paper component for the Answer Display section */}
              <Paper>
                {/* Section title */}
                <Typography variant="h6" gutterBottom>Answer</Typography>
                {/* Conditional rendering based on loading state */}
                {isLoading ? (
                  // Display loading indicator if isLoading is true
                  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 3 }}>
                    <CircularProgress />
                    <Typography sx={{ ml: 2 }}>Generating answer...</Typography>
                  </Box>
                ) : (
                  // Display answer or placeholder text if not loading
                  <Suspense fallback={<Typography color="textSecondary">Loading...</Typography>}> {/* Fallback while answer potentially loads */}
                    {/* Check if an answer exists in the state */}
                    {answer ? (
                      // If answer exists, display it in a styled box
                      <Box sx={{ 
                        backgroundColor: '#f8f9fa', // Light background for the answer area
                        p: 2, // Padding
                        borderRadius: 1, // Slight border radius
                        border: '1px solid #e0e0e0', // Subtle border
                        boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.05)' // Inner shadow
                      }}>
                        {/* Apply specific styles for markdown rendering */}
                        <Box className="markdown-content" sx={{ 
                          lineHeight: '1.6',
                          fontSize: '1rem'
                        }}>
                          {/* Render the answer string as Markdown */}
                          <ReactMarkdown>
                            {answer}
                          </ReactMarkdown>
                        </Box>
                      </Box>
                    ) : (
                      // If no answer exists (initial state or after clearing), show placeholder text
                      <Typography color="textSecondary" sx={{ fontStyle: 'italic' }}>
                        Ask a question to see the answer here
                      </Typography>
                    )}
                  </Suspense>
                )}
              </Paper>
            </Box>
          </Box>
        </Container>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

// Export the App component as the default export
export default App;
