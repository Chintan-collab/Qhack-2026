import { Outlet } from "react-router-dom";

export default function Layout() {
  return (
    <div className="flex h-screen bg-gray-950 text-white">
      <main className="flex-1 flex flex-col">
        <Outlet />
      </main>
    </div>
  );
}
