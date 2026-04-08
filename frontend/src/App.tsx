import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/layout/Layout";
import ChatView from "./components/chat/ChatView";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<ChatView />} />
          <Route path="/chat/:conversationId" element={<ChatView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
