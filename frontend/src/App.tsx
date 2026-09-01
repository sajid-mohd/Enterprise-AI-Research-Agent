import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { ResearchConsole } from './pages/ResearchConsole';
import { ResearchResult } from './pages/ResearchResult';
import { KnowledgeExplorer } from './pages/KnowledgeExplorer';
import { QueryKnowledge } from './pages/QueryKnowledge';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/research" element={<ResearchConsole />} />
          <Route path="/research/:sessionId" element={<ResearchResult />} />
          <Route path="/knowledge" element={<KnowledgeExplorer />} />
          <Route path="/query" element={<QueryKnowledge />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
