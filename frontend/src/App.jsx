import React from 'react';
import tableImg from './assets/poker_table.jpg'; // Importăm imaginea

function App() {
  const containerStyle = {
    // Imaginea de fundal
    backgroundImage: `url(${tableImg})`,
    
    // Centrare și acoperire ecran
    backgroundSize: 'contain', // 'contain' păstrează proporțiile mesei fără să o taie
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'center',
    
    // Dimensiuni (ocupă tot ecranul)
    width: '100vw',
    height: '100vh',
    backgroundColor: '#1a1a1a', // Fundal negru/gri în caz că imaginea nu acoperă tot
    
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  };

  return (
    <div style={containerStyle}>
      {/* Aici vei pune mai târziu restul elementelor (cărți, butoane) */}
      <h1 style={{ color: 'white', backgroundColor: 'rgba(0,0,0,0.5)', padding: '10px' }}>
        Masa de Poker este gata
      </h1>
    </div>
  );
}

export default App;