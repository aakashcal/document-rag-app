import { useState, useCallback, memo } from 'react';
import { 
  Button, 
  Box, 
  CircularProgress, 
  Alert,
  Stack
} from '@mui/material';
import { UploadFile as UploadIcon } from '@mui/icons-material';

interface DocumentUploadProps {
  onUploadSuccess?: (documentId: string) => void;
}

const DocumentUpload = memo(({ onUploadSuccess }: DocumentUploadProps) => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError(null);
      setSuccess(false);
    }
  }, []);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
       setError('Please select a file to upload');
       return;
    }

    try {
      setUploading(true);
      setError(null);
      setSuccess(false);
      
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Upload failed');
      }
      
      const data = await response.json();
      setSuccess(true);
      setFile(null);
      
      const fileInput = document.getElementById('document-upload') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      
      if (onUploadSuccess && data.id) {
        onUploadSuccess(data.id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload document. Please try again.');
      console.error(err);
    } finally {
      setUploading(false);
    }
  }, [file, onUploadSuccess]);

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <Stack spacing={2}>
        <Button
          variant="outlined"
          component="label"
          startIcon={<UploadIcon />}
          fullWidth
          disabled={uploading}
        >
          {file ? file.name : 'Choose File'}
          <input
            id="document-upload"
            type="file"
            accept=".pdf,.txt,.doc,.docx"
            hidden
            onChange={handleFileChange}
            disabled={uploading}
          />
        </Button>
        
        <Button
          type="submit"
          variant="contained"
          color="primary"
          disabled={!file || uploading}
          fullWidth
        >
          {uploading ? <CircularProgress size={24} /> : 'Upload'}
        </Button>
        
        {error && 
          <Alert severity="error">{error}</Alert>}
        {success && 
          <Alert severity="success">Document uploaded successfully!</Alert>}
      </Stack>
    </Box>
  );
});

DocumentUpload.displayName = 'DocumentUpload';

export default DocumentUpload;