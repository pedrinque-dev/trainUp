import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./AuthContext";
import Layout from "./components/Layout";
const Agendamento = lazy(() => import("./pages/Agendamento"));
const Automacao = lazy(() => import("./pages/Automacao"));
import Login from "./pages/Login";
const AlunoPerfil = lazy(() => import("./pages/personal/AlunoPerfil"));
const Alunos = lazy(() => import("./pages/personal/Alunos"));
const Exercicios = lazy(() => import("./pages/personal/Exercicios"));
const Overview = lazy(() => import("./pages/personal/Overview"));
const Relatorios = lazy(() => import("./pages/personal/Relatorios"));
const Treinos = lazy(() => import("./pages/personal/Treinos"));
const Evolucao = lazy(() => import("./pages/aluno/Evolucao"));
const Inicio = lazy(() => import("./pages/aluno/Inicio"));
const Treinar = lazy(() => import("./pages/aluno/Treinar"));

function Guard({ role, children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (role && user.role !== role) return <Navigate to="/" replace />;
  return (
    <Layout>
      <Suspense fallback={<p className="p-6 text-sm text-muted" role="status">Carregando...</p>}>{children}</Suspense>
    </Layout>
  );
}

function Home() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={user.role === "personal" ? "/personal" : "/aluno"} replace />;
}

const P = ({ children }) => <Guard role="personal">{children}</Guard>;
const A = ({ children }) => <Guard role="aluno">{children}</Guard>;

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />

      <Route path="/personal" element={<P><Overview /></P>} />
      <Route path="/personal/alunos" element={<P><Alunos /></P>} />
      <Route path="/personal/alunos/:id" element={<P><AlunoPerfil /></P>} />
      <Route path="/personal/treinos" element={<P><Treinos /></P>} />
      <Route path="/personal/exercicios" element={<P><Exercicios /></P>} />
      <Route path="/personal/relatorios" element={<P><Relatorios /></P>} />
      <Route path="/automacao" element={<P><Automacao /></P>} />

      <Route path="/aluno" element={<A><Inicio /></A>} />
      <Route path="/aluno/treinar" element={<A><Treinar /></A>} />
      <Route path="/aluno/evolucao" element={<A><Evolucao /></A>} />

      <Route path="/agendamento" element={<Guard><Agendamento /></Guard>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
