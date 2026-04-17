import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { LoginView, CallbackView, DashboardView } from "./views";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LoginView />} />
        <Route path="/callback" element={<CallbackView />} />
        <Route path="/dashboard" element={<DashboardView />} />
      </Routes>
    </Router>
  );
}

export default App;
