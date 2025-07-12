// src/App.tsx
import { useState, useEffect } from 'react';
import './App.css';

// Importando os componentes que vamos usar do MUI
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import Chip from '@mui/material/Chip';

// A nossa definição de tipo continua a mesma
type Interaction = {
  id: number;
  original_text: string;
  sentiment: string;
  summary: string;
  created_at: string;
};

// Componente para exibir o histórico
function InteractionHistory() {
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // ATENÇÃO: Substitua a URL abaixo pela URL pública da sua PORTA 8000.
    const apiUrl = 'https://supreme-journey-7vx694wp6w57cxg7x-8000.app.github.dev/api/v1/interactions';

    fetch(apiUrl)
      .then(response => {
        if (!response.ok) throw new Error('Falha ao buscar dados da API.');
        return response.json();
      })
      .then(data => {
        setInteractions(data);
        setIsLoading(false);
      })
      .catch(err => {
        console.error("Erro ao buscar histórico:", err);
        setError(err.message);
        setIsLoading(false);
      });
  }, []);

  const getSentimentColor = (sentiment: string) => {
    if (sentiment === 'Positivo') return 'success';
    if (sentiment === 'Negativo') return 'error';
    return 'default';
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 10 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Ocorreu um erro ao carregar o histórico: {error}</Alert>;
  }

  return (
    <TableContainer component={Paper}>
      <Table sx={{ minWidth: 650 }} aria-label="simple table">
        <TableHead sx={{ backgroundColor: '#f5f5f5' }}>
          <TableRow>
            <TableCell>ID</TableCell>
            <TableCell>Texto Original</TableCell>
            <TableCell>Sentimento</TableCell>
            <TableCell>Data</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {interactions.map((item) => (
            <TableRow key={item.id} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
              <TableCell component="th" scope="row">{item.id}</TableCell>
              <TableCell>{item.original_text}</TableCell>
              <TableCell>
                <Chip label={item.sentiment} color={getSentimentColor(item.sentiment)} size="small" />
              </TableCell>
              <TableCell>{new Date(item.created_at).toLocaleString('pt-BR')}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

// Componente principal da aplicação
function App() {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Painel de Gestão - TDS Platform
      </Typography>
      <Box sx={{ mt: 4 }}>
        <InteractionHistory />
      </Box>
    </Container>
  );
}

export default App;
