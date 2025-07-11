// src/App.tsx
import { InteractionHistory } from './components/InteractionHistory';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Painel de Gestão - TDS Platform</h1>
      </header>
      <main>
        <InteractionHistory />
      </main>
    </div>
  )
}

export default App;