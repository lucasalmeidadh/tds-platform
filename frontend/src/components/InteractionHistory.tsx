// src/components/InteractionHistory.tsx
import { useState, useEffect } from 'react';

// Define a "forma" dos nossos dados, para o TypeScript nos ajudar
type Interaction = {
  id: number;
  original_text: string;
  sentiment: string;
  summary: string;
  created_at: string;
};

export function InteractionHistory() {
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // ATENÇÃO: Substitua a URL abaixo pela URL pública da sua PORTA 8000.
    // Você encontra essa URL na aba "PORTAS" do seu terminal no Codespaces.
    const apiUrl = 'https://supreme-journey-7vx694wp6w57cxg7x-8000.app.github.dev/api/v1/interactions';

    fetch(apiUrl)
      .then(response => response.json())
      .then(data => {
        setInteractions(data);
        setIsLoading(false);
      })
      .catch(error => {
        console.error("Erro ao buscar histórico:", error);
        setIsLoading(false);
      });
  }, []); // O array vazio faz com que isso rode apenas uma vez

  if (isLoading) {
    return <p>Carregando histórico do banco de dados...</p>;
  }

  return (
    <div style={{ marginTop: '2rem', fontFamily: 'sans-serif' }}>
      <h2>Histórico de Análises</h2>
      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '1rem' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #333' }}>
            <th style={{ textAlign: 'left', padding: '8px' }}>ID</th>
            <th style={{ textAlign: 'left', padding: '8px' }}>Texto Original</th>
            <th style={{ textAlign: 'left', padding: '8px' }}>Sentimento</th>
            <th style={{ textAlign: 'left', padding: '8px' }}>Data</th>
          </tr>
        </thead>
        <tbody>
          {interactions.map(item => (
            <tr key={item.id} style={{ borderBottom: '1px solid #ddd' }}>
              <td style={{ padding: '8px' }}>{item.id}</td>
              <td style={{ padding: '8px', maxWidth: '400px' }}>{item.original_text}</td>
              <td style={{ padding: '8px' }}>{item.sentiment}</td>
              <td style={{ padding: '8px' }}>{new Date(item.created_at).toLocaleString('pt-BR')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}