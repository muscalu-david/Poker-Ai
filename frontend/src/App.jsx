import { useState, useEffect, useRef } from 'react';
import tableImg from './assets/poker_table.jpg'; 
import botImg from './assets/bot_avatar.png'; 
import userImg from './assets/user_avatar.png'; 

// Funcție pentru formatarea cărților (rămâne neschimbată)
const getCardDetails = (cardStr) => {
  if (!cardStr || cardStr.length < 2) return { rank: '', suit: '', isRed: false };
  const suitMap = { 
    'h': { symbol: '♥', isRed: true }, 
    'd': { symbol: '♦', isRed: true }, 
    'c': { symbol: '♣', isRed: false }, 
    's': { symbol: '♠', isRed: false } 
  };
  const rawRank = cardStr.slice(0, -1);
  const rawSuit = cardStr.slice(-1).toLowerCase();
  const rank = rawRank.toUpperCase().replace('T', '10');
  const suitInfo = suitMap[rawSuit] || { symbol: rawSuit, isRed: false };
  return { rank, suit: suitInfo.symbol, isRed: suitInfo.isRed };
};

// Componenta pentru o carte (rămâne neschimbată)
function PlayingCard({ cardStr, isHidden = false }) {
  const { rank, suit, isRed } = getCardDetails(cardStr);
  const cardColor = isRed ? '#e74c3c' : '#2c3e50';
  const cardStyle = {
    width: '65px', height: '90px', backgroundColor: isHidden ? '#34495e' : 'white',
    borderRadius: '8px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
    padding: '5px', fontSize: '1.2rem', fontWeight: 'bold', border: '1px solid #ddd',
    boxShadow: '3px 3px 8px rgba(0,0,0,0.4)', margin: '0 5px', color: cardColor, position: 'relative'
  };

  if (isHidden) return (
    <div style={cardStyle}>
      <div style={{ 
        width: '100%', height: '100%', borderRadius: '5px', 
        background: 'repeating-linear-gradient(45deg, #2c3e50, #2c3e50 5px, #34495e 5px, #34495e 10px)', 
        display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white' 
      }}>?</div>
    </div>
  );

  return (
    <div style={cardStyle}>
      <div style={{ textAlign: 'left', lineHeight: '1' }}><div>{rank}</div><div>{suit}</div></div>
      <div style={{ fontSize: '2rem', position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -40%)', opacity: '0.1' }}>{suit}</div>
      <div style={{ textAlign: 'right', lineHeight: '1', transform: 'rotate(180deg)' }}><div>{rank}</div><div>{suit}</div></div>
    </div>
  );
}

function App() {
  const [gameData, setGameData] = useState(null);
  const [botMessage, setBotMessage] = useState("");
  const logEndRef = useRef(null);

  useEffect(() => { startNewGame(); }, []);
  // Auto-scroll pentru log
  useEffect(() => { logEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [gameData?.history]);

  const startNewGame = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/new-game', { method: 'POST' });
      const data = await response.json();
      setGameData(data);
      setBotMessage("");
    } catch (err) { console.error("Eroare la pornirea jocului:", err); }
  };

  const handleAction = async (actionName) => {
    try {
      setBotMessage("");
      const response = await fetch('http://127.0.0.1:8000/api/action', {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action_name: actionName })
      });
      const newData = await response.json();
      setGameData(newData);
      if (newData.last_bot_action) setBotMessage(`Am ales: ${newData.last_bot_action}`);
    } catch (err) { console.error("Eroare la trimiterea acțiunii:", err); }
  };

  return (
    <div style={containerStyle}>
      
      {/* PANEL LOG (STÂNGA) */}
      <div style={logPanelStyle}>
        <h4 style={{margin: '0 0 10px 0', color: '#f1c40f', borderBottom: '1px solid #444', paddingBottom: '5px'}}>LIVE LOG</h4>
        <div style={{flex: 1, overflowY: 'auto', fontSize: '0.8rem', scrollbarWidth: 'none'}}>
          {gameData?.history.map((h, i) => <div key={i} style={{marginBottom: '5px', borderBottom: '1px solid #222'}}>{h}</div>)}
          <div ref={logEndRef} />
        </div>
      </div>

      {/* BOT (SUS) */}
      <div style={{ position: 'absolute', top: '5%', textAlign: 'center' }}>
        {gameData?.current_bets[1] > 0 && <div style={betChipStyle}>Bet: {gameData.current_bets[1]}</div>}
        <img src={botImg} alt="Bot" style={{ width: '65px', borderRadius: '50%', border: '2px solid #f1c40f', boxShadow: '0 0 15px rgba(241,196,15,0.4)' }} />
        <div style={infoBoxStyle}>BOT | STACK: {gameData?.stacks[1]}</div>
        
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '10px' }}>
          {/* Showdown: Arătăm cărțile botului doar dacă backend-ul le trimite (la final, dacă nu e Fold) */}
          {gameData?.bot_hand && gameData.bot_hand.length > 0 ? (
            gameData.bot_hand.map((c, i) => <PlayingCard key={i} cardStr={c} isHidden={false} />)
          ) : (
            <>
              <PlayingCard isHidden={true} />
              <PlayingCard isHidden={true} />
            </>
          )}
        </div>
        {botMessage && <div style={bubbleStyle}>{botMessage}</div>}
      </div>

      {/* MASA (CENTRU) */}
      <div style={{ textAlign: 'center', background: 'rgba(0,0,0,0.4)', padding: '25px', borderRadius: '60px', border: '2px solid rgba(255,255,255,0.1)', boxShadow: 'inset 0 0 50px rgba(0,0,0,0.5)' }}>
        <h2 style={{ color: '#f1c40f', margin: '0 0 15px 0', fontSize: '2rem', textShadow: '2px 2px 4px black' }}>POT: {gameData?.pot}</h2>
        <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', minWidth: '350px' }}>
          {gameData?.board_cards.length > 0 ? (
            gameData.board_cards.map((c, i) => <PlayingCard key={i} cardStr={c} />)
          ) : (
            <span style={{color:'white', opacity: 0.5, fontStyle: 'italic'}}>Așteptăm cărțile comunitare...</span>
          )}
        </div>
      </div>

      {/* JUCĂTOR (JOS) */}
      <div style={{ position: 'absolute', bottom: '5%', textAlign: 'center' }}>
        
        {/* Mesaj discret pentru finalul jocului */}
        {gameData?.is_terminal && (
          <div style={{ 
            color: gameData.returns[0] >= 0 ? '#2ecc71' : '#e74c3c', 
            fontWeight: 'bold', fontSize: '1.8rem', marginBottom: '15px', 
            textShadow: '2px 2px 5px black', animation: 'fadeIn 0.5s' 
          }}>
            {gameData.returns[0] >= 0 ? `AI CÂȘTIGAT! (+${gameData.returns[0]})` : `AI PIERDUT! (${gameData.returns[0]})`}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '10px' }}>
          {gameData?.player_hand.map((c, i) => <PlayingCard key={i} cardStr={c} />)}
        </div>
        
        {gameData?.current_bets[0] > 0 && <div style={betChipStyle}>Bet: {gameData.current_bets[0]}</div>}
        
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px'}}>
            <img src={userImg} alt="User" style={{ width: '65px', borderRadius: '50%', border: '2px solid white', boxShadow: '0 0 15px rgba(255,255,255,0.2)' }} />
            <div style={infoBoxStyle}>TU | STACK: {gameData?.stacks[0]}</div>
        </div>
        
        {/* Butoane Acțiune / Joc Nou */}
        <div style={{ marginTop: '20px', display: 'flex', gap: '12px', justifyContent: 'center' }}>
          {!gameData?.is_terminal ? (
            gameData?.legal_actions.map(a => (
              <button key={a} onClick={() => handleAction(a)} style={btnStyle}>{a}</button>
            ))
          ) : (
            <button onClick={startNewGame} style={{...btnStyle, backgroundColor: '#27ae60', padding: '15px 40px', fontSize: '1.2rem', boxShadow: '0 0 20px rgba(39,174,96,0.4)'}}>
              JOC NOU
            </button>
          )}
        </div>
      </div>

      {/* Stiluri injectate pentru animații */}
      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        button:active { transform: scale(0.95); }
        button:hover { filter: brightness(1.1); }
      `}</style>

    </div>
  );
}

// STILURI (Constante)
const containerStyle = { 
  width: '100vw', height: '100vh', 
  backgroundImage: `url(${tableImg})`, 
  backgroundSize: 'cover', backgroundPosition: 'center', 
  position: 'relative', display: 'flex', alignItems: 'center', 
  justifyContent: 'center', fontFamily: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif', 
  overflow: 'hidden' 
};

const logPanelStyle = { 
  position: 'absolute', left: '20px', top: '20px', bottom: '20px', 
  width: '220px', backgroundColor: 'rgba(0,0,0,0.85)', color: 'white', 
  padding: '15px', borderRadius: '12px', display: 'flex', 
  flexDirection: 'column', border: '1px solid #444', textAlign: 'left',
  boxShadow: '5px 0 15px rgba(0,0,0,0.3)'
};

const infoBoxStyle = { 
  background: 'rgba(0,0,0,0.8)', color: 'white', padding: '5px 12px', 
  borderRadius: '8px', fontSize: '0.9rem', marginTop: '5px',
  border: '1px solid rgba(255,255,255,0.2)', fontWeight: 'bold'
};

const betChipStyle = { 
  background: '#f1c40f', color: 'black', fontWeight: 'bold', 
  padding: '3px 12px', borderRadius: '15px', fontSize: '0.85rem', 
  marginBottom: '8px', display: 'inline-block', boxShadow: '0 2px 5px rgba(0,0,0,0.5)'
};

const btnStyle = { 
  padding: '12px 25px', backgroundColor: '#e67e22', color: 'white', 
  border: 'none', borderRadius: '8px', cursor: 'pointer', 
  fontWeight: 'bold', textTransform: 'uppercase', transition: 'all 0.2s',
  boxShadow: '0 4px 0 #a35d1a'
};

const bubbleStyle = { 
  position: 'absolute', left: '100px', top: '10px', 
  background: 'white', padding: '10px 15px', borderRadius: '15px', 
  color: '#2c3e50', fontSize: '0.85rem', fontWeight: 'bold', 
  width: '140px', boxShadow: '0 5px 15px rgba(0,0,0,0.3)',
  borderLeft: '4px solid #f1c40f'
};

export default App;