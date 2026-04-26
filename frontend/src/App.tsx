import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Index from "./pages/Index.tsx";
import Login from "./pages/Login.tsx";
import NotFound from "./pages/NotFound.tsx";
import DashboardLayout from "./pages/dashboard/DashboardLayout.tsx";
import DashboardHome from "./pages/dashboard/DashboardHome.tsx";
import ExperimentDetail from "./pages/dashboard/ExperimentDetail.tsx";
import NewExperiment from "./pages/dashboard/NewExperiment.tsx";
import Experiments from "./pages/dashboard/Experiments.tsx";
import Literature from "./pages/dashboard/Literature.tsx";
import Collaboration from "./pages/dashboard/Collaboration.tsx";
import Reviews from "./pages/dashboard/Reviews.tsx";
import Reports from "./pages/dashboard/Reports.tsx";
import Settings from "./pages/dashboard/Settings.tsx";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<DashboardLayout />}>
            <Route index element={<DashboardHome />} />
            <Route path="experiments/:id" element={<ExperimentDetail />} />
            <Route path="new" element={<NewExperiment />} />
            <Route path="experiments" element={<Experiments />} />
            <Route path="literature" element={<Literature />} />
            <Route path="collaboration" element={<Collaboration />} />
            <Route path="reviews" element={<Reviews />} />
            <Route path="reports" element={<Reports />} />
            <Route path="settings" element={<Settings />} />
          </Route>
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
