import Analyzer from './components/Analyzer';

function App() {
  return (
    <div className="min-h-screen bg-gray-50 relative overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 z-0 opacity-30">
        <div className="absolute inset-0" style={{ backgroundImage: 'radial-gradient(#cbd5e1 1px, transparent 1px)', backgroundSize: '30px 30px' }}></div>
      </div>

      <div className="relative z-10 py-12 px-4 sm:px-6 lg:px-8">
        <Analyzer />
      </div>
    </div>
  );
}

export default App;
