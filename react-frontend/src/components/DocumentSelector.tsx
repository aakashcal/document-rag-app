import { memo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  FormGroup,
  Checkbox, 
  Typography, 
  CircularProgress, 
  List, 
  ListItem, 
  ListItemText, 
  ListItemIcon, 
  IconButton,
} from '@mui/material';
import { Delete as DeleteIcon } from '@mui/icons-material';

interface Document {
  id: string;
  filename: string;
  upload_time: string;
}

interface DocumentSelectorProps {
  selectedDocuments: string[];
  onDocumentSelect: (documents: string[]) => void;
}

const DocumentSelector = memo(({ selectedDocuments, onDocumentSelect }: DocumentSelectorProps) => {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery<Document[]>({
    queryKey: ['documents'],
    queryFn: async () => {
      const response = await fetch('/api/documents/list');
      if (!response.ok) {
        throw new Error('Failed to fetch documents');
      }
      return response.json();
    }
  });

  const deleteMutation = useMutation<void, Error, string>({
    mutationFn: async (filename: string) => {
      const encodedFilename = encodeURIComponent(filename);
      const response = await fetch(`/api/documents/${encodedFilename}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to delete document' }));
        throw new Error(errorData.detail || 'Failed to delete document');
      }
    },
    onSuccess: (/*data,*/ filenameToDelete) => {
      console.log(`Document ${filenameToDelete} deleted successfully`);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      // @ts-ignore - TS seems confused about filenameToDelete type here, but it's a string
      onDocumentSelect(selectedDocuments.filter(id => id !== filenameToDelete));
    },
    onError: (error: Error, filenameToDelete) => {
      console.error(`Error deleting document ${filenameToDelete}:`, error);
      alert(`Failed to delete ${filenameToDelete}: ${error.message}`);
    },
  });

  const handleCheckboxChange = (docId: string) => {
    if (selectedDocuments.includes(docId)) {
      onDocumentSelect(selectedDocuments.filter(id => id !== docId));
    } else {
      onDocumentSelect([...selectedDocuments, docId]);
    }
  };

  const handleDelete = (filename: string) => (event: React.MouseEvent) => {
    event.stopPropagation();
    if (window.confirm(`Are you sure you want to delete ${filename}? This action cannot be undone.`)) {
      deleteMutation.mutate(filename);
    }
  };

  if (isLoading) {
    return <CircularProgress size={24} />;
  }

  if (error) {
    return <Typography color="error">Error loading documents</Typography>;
  }

  if (!data || data.length === 0) {
    return <Typography color="textSecondary">No documents available. Upload a document first.</Typography>;
  }

  return (
    <FormGroup>
      <List dense>
        {data.map((doc) => (
          <ListItem
            key={doc.id}
            secondaryAction={
              <IconButton
                edge="end"
                aria-label="delete"
                onClick={handleDelete(doc.filename)}
                disabled={deleteMutation.isPending && deleteMutation.variables === doc.filename}
              >
                {deleteMutation.isPending && deleteMutation.variables === doc.filename ? (
                  <CircularProgress size={20} />
                ) : (
                  <DeleteIcon fontSize="small" />
                )}
              </IconButton>
            }
            disablePadding
            sx={{ '&:hover': { backgroundColor: 'action.hover' } }}
          >
            <ListItemIcon sx={{ minWidth: 0, mr: 1 }}>
              <Checkbox
                checked={selectedDocuments.includes(doc.id)}
                onChange={() => handleCheckboxChange(doc.id)}
                color="primary"
              />
            </ListItemIcon>
            <ListItemText
              primary={doc.filename}
              onClick={() => handleCheckboxChange(doc.id)}
            />
          </ListItem>
        ))}
      </List>
    </FormGroup>
  );
});

DocumentSelector.displayName = 'DocumentSelector';

export default DocumentSelector;