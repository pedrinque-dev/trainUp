import { Leaf } from "lucide-react";
import { useAuth } from "../../AuthContext";
import ReportView from "../../components/ReportView";
import { Card, PageHeader } from "../../components/ui";
import { useFetch } from "../../lib/hooks";
import api from "../../services/api";

export default function Evolucao() {
  const { user } = useAuth();
  const { data: tips } = useFetch(async () => (await api.get("/analytics/tips")).data, []);
  return (
    <>
      <PageHeader title="Evolução" subtitle="Seus números, período a período." />
      <ReportView alunoId={user.id} />
      {tips && (
        <Card className="space-y-3">
          <div className="flex items-center gap-2"><Leaf size={18} className="text-ok" aria-hidden="true" /><h2>Dicas de nutrição e recuperação</h2></div>
          <ul className="grid gap-3 md:grid-cols-3">
            {tips.dicas.map((d) => <li key={d.titulo} className="rounded-xl bg-paper p-3"><p className="text-sm font-bold">{d.titulo}</p><p className="mt-1 text-sm text-muted">{d.texto}</p></li>)}
          </ul>
          <p className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-warn">{tips.aviso}</p>
        </Card>
      )}
    </>
  );
}
