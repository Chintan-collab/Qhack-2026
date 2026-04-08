import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/layout/Layout";
import ChatView from "./components/chat/ChatView";
import ProjectList from "./components/projects/ProjectList";
import ProjectCreate from "./components/projects/ProjectCreate";
import ProjectDetail from "./components/projects/ProjectDetail";
import DeliverableView from "./components/agents/DeliverableView";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          {/* Quick chat (no project) */}
          <Route path="/" element={<ChatView />} />
          <Route path="/chat/:conversationId" element={<ChatView />} />

          {/* Project management */}
          <Route path="/projects" element={<ProjectList />} />
          <Route path="/projects/new" element={<ProjectCreate />} />
          <Route path="/projects/:projectId" element={<ProjectDetail />} />

          {/* Project-scoped chat and deliverables */}
          <Route path="/projects/:projectId/chat" element={<ChatView />} />
          <Route path="/projects/:projectId/deliverable" element={<DeliverableView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
